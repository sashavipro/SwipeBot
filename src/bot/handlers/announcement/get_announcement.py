"""src/bot/handlers/announcement/get_announcement.py."""

import logging
import html
import asyncio
from typing import Dict, Any, List, Optional, NamedTuple
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from src.bot.callbacks import MenuCallback, ListingCallback
from src.bot.keyboards.inline import get_item_keyboard, get_main_menu_keyboard
from src.bot.keyboards.reply import get_listings_reply_keyboard
from src.bot.states import ListingsSG
from src.database import BotUser
from src.infrastructure.api import SwipeApiClient, SwipeAPIError

router = Router()
logger = logging.getLogger(__name__)

ITEMS_PER_PAGE = 2


class ListingContext(NamedTuple):
    """Container for listing display data to avoid too many arguments."""

    text: str
    media_group: List[InputMediaPhoto]
    has_prev: bool
    has_next: bool
    offset: int
    current_item: Dict[str, Any]


async def _cleanup_batch_messages(message: Message, state: FSMContext):
    """
    Deletes all messages from the previous page/batch, including the map.
    """
    data = await state.get_data()
    msg_ids = data.get("batch_msg_ids", [])

    for msg_id in msg_ids:
        try:
            await message.bot.delete_message(message.chat.id, msg_id)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    geo_msg_id = data.get("geo_msg_id")
    if geo_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, geo_msg_id)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    menu_msg_id = data.get("menu_msg_id")
    if menu_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, menu_msg_id)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    await state.update_data(batch_msg_ids=[], geo_msg_id=None, menu_msg_id=None)


def _prepare_media_group(images: List[Dict[str, Any]]) -> List[InputMediaPhoto]:
    """
    Prepares a list of InputMediaPhoto for sending an album.
    Limits the number of images to 10 (Telegram API limit).
    """
    media_group = []
    if images:
        for img in images[:10]:
            media_group.append(InputMediaPhoto(media=img["image_url"]))
    else:
        media_group.append(
            InputMediaPhoto(media="https://via.placeholder.com/600x400?text=No+Photo")
        )
    return media_group


def _prepare_announcement_text(item: Dict[str, Any], mode: str) -> str:
    """Helper to format announcement text."""
    try:
        price_val = float(item["price"])
        price = f"${price_val:,.0f}".replace(",", " ")
    except (ValueError, TypeError):
        price = str(item.get("price", "N/A"))

    address = html.escape(item.get("address", ""))
    description = html.escape(item.get("description", "") or "")
    area = item.get("area", 0)

    owner = item.get("owner")
    phone = (
        html.escape(owner["phone"])
        if owner and owner.get("phone")
        else _("No contact info")
    )

    title_prefix = _("<b>MY LISTING</b>\n") if mode == "my" else ""

    return (
        f"{title_prefix}"
        f"<b>{price}</b> | {area} м²\n"
        f"{address}\n\n"
        f"{description}\n\n"
        f"{phone}"
    )


async def _send_listing_content(
    message: Message, state: FSMContext, context: ListingContext
) -> None:
    """Helper to send the album and control message."""
    try:
        album_messages = await message.answer_media_group(media=context.media_group)
        new_album_ids = [m.message_id for m in album_messages]

        control_msg = await message.answer(
            text=context.text,
            reply_markup=get_item_keyboard(context.current_item["id"]),
        )
        new_album_ids.append(control_msg.message_id)

        data = await state.get_data()
        current_batch_ids = data.get("batch_msg_ids", [])
        current_batch_ids.extend(new_album_ids)

        batch_coords = data.get("batch_coords", {})
        item = context.current_item
        if item.get("latitude") and item.get("longitude"):
            batch_coords[str(item["id"])] = {
                "lat": item["latitude"],
                "lon": item["longitude"],
            }

        await state.update_data(
            batch_msg_ids=current_batch_ids, batch_coords=batch_coords
        )
        await asyncio.sleep(0.3)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to send listing message: %s", e)


async def _fetch_listings(
    user: BotUser, mode: str, offset: int
) -> Optional[List[Dict[str, Any]]]:
    """Helper to fetch listings from API."""
    api = SwipeApiClient(user=user)
    try:
        fetch_func = (
            api.announcements.get_my_announcements
            if mode == "my"
            else api.announcements.get_announcements
        )
        listings = await fetch_func(limit=ITEMS_PER_PAGE + 1, offset=offset)

        return listings

    except SwipeAPIError:
        return None


# pylint: disable=too-many-locals, too-many-statements
async def show_listings_batch(
    message: Message, state: FSMContext, user: BotUser, offset: int
):
    """
    Fetches a batch of listings from the API and displays them sequentially.
    Handles pagination via Reply Keyboards.
    """
    data = await state.get_data()
    mode = data.get("listing_mode", "all")

    listings = await _fetch_listings(user, mode, offset)

    if listings is None:
        await message.answer(_("Error loading listings."))
        return

    if not listings:
        if offset > 0:
            await message.answer(_("No more listings."))
        else:
            msg = (
                _("You haven't created any listings yet.")
                if mode == "my"
                else _("No listings found.")
            )
            await message.answer(msg)
        return

    await _cleanup_batch_messages(message, state)

    has_next = len(listings) > ITEMS_PER_PAGE
    has_prev = offset > 0

    items_to_show = listings[:ITEMS_PER_PAGE]

    await state.update_data(batch_msg_ids=[], batch_coords={})

    for item in items_to_show:
        text = _prepare_announcement_text(item, mode)
        media_group = _prepare_media_group(item.get("images", []))

        ctx = ListingContext(
            text=text,
            media_group=media_group,
            has_prev=False,
            has_next=False,
            offset=offset,
            current_item=item,
        )
        await _send_listing_content(message, state, ctx)

    page_num = (offset // ITEMS_PER_PAGE) + 1
    nav_msg = await message.answer(
        text=_("**Announcement Page {page}**").format(page=page_num),
        reply_markup=get_listings_reply_keyboard(has_prev, has_next),
    )

    data = await state.get_data()
    batch_ids = data.get("batch_msg_ids", [])
    batch_ids.append(nav_msg.message_id)
    await state.update_data(batch_msg_ids=batch_ids, offset=offset)


# --- ENTRY HANDLERS ---


@router.callback_query(MenuCallback.filter(F.action == "listings"))
async def start_listings(query: CallbackQuery, state: FSMContext):
    """
    Enters listing browsing mode (All listings).
    """
    user = await BotUser.find_one(BotUser.telegram_id == query.from_user.id)
    await state.set_state(ListingsSG.Browsing)
    await state.update_data(offset=0, listing_mode="all")
    await query.message.delete()

    await show_listings_batch(query.message, state, user, offset=0)


@router.callback_query(MenuCallback.filter(F.action == "my_listings"))
async def start_my_listings(query: CallbackQuery, state: FSMContext):
    """
    Enters listing browsing mode (My Listings).
    """
    user = await BotUser.find_one(BotUser.telegram_id == query.from_user.id)
    await state.set_state(ListingsSG.Browsing)
    await state.update_data(offset=0, listing_mode="my")
    await query.message.delete()

    await show_listings_batch(query.message, state, user, offset=0)


# --- PAGINATION HANDLERS (Reply Buttons) ---


@router.message(ListingsSG.Browsing, F.text == "➡️")
async def page_next_reply(message: Message, state: FSMContext):
    """
    Handles Next Page button.
    """
    user = await BotUser.find_one(BotUser.telegram_id == message.from_user.id)
    data = await state.get_data()
    new_offset = data.get("offset", 0) + ITEMS_PER_PAGE

    try:
        await message.delete()
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    await show_listings_batch(message, state, user, new_offset)


@router.message(ListingsSG.Browsing, F.text == "⬅️")
async def page_prev_reply(message: Message, state: FSMContext):
    """
    Handles Previous Page button.
    """
    user = await BotUser.find_one(BotUser.telegram_id == message.from_user.id)
    data = await state.get_data()
    new_offset = max(0, data.get("offset", 0) - ITEMS_PER_PAGE)

    try:
        await message.delete()
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    await show_listings_batch(message, state, user, new_offset)


@router.callback_query(ListingCallback.filter(F.action == "geo"))
async def show_geolocation(
    query: CallbackQuery, callback_data: ListingCallback, state: FSMContext
):
    """
    Shows geolocation for a specific item in the batch using stored coordinates.
    """
    data = await state.get_data()
    coords_map = data.get("batch_coords", {})

    item_coords = coords_map.get(str(callback_data.id))
    if not item_coords:
        item_coords = coords_map.get(callback_data.id)

    prev_geo_id = data.get("geo_msg_id")
    if prev_geo_id:
        try:
            await query.message.bot.delete_message(query.message.chat.id, prev_geo_id)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    if item_coords:
        try:
            lat = float(item_coords["lat"])
            lon = float(item_coords["lon"])
            geo_msg = await query.message.answer_location(latitude=lat, longitude=lon)
            await state.update_data(geo_msg_id=geo_msg.message_id)
            await query.answer()
        except ValueError:
            await query.answer(_("Invalid coordinates."), show_alert=True)
    else:
        await query.answer(_("Location not found for this item."), show_alert=True)


@router.message(ListingsSG.Browsing, F.text == __("Back to Menu"))
async def exit_listings(message: Message, state: FSMContext):
    """
    Exits the browsing mode, clears all messages, returns to Main Menu.
    """
    try:
        await message.delete()
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    await _cleanup_batch_messages(message, state)

    await state.clear()

    msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await msg.delete()

    await message.answer(
        text=_("Welcome back! Select an action:"), reply_markup=get_main_menu_keyboard()
    )
