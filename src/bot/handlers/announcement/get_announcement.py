"""src/bot/handlers/announcement/get_announcement.py."""

import logging
import html
from typing import Dict, Any, List, NamedTuple, Optional
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from src.bot.callbacks import MenuCallback, ListingCallback
from src.bot.keyboards.inline import get_listings_nav_keyboard, get_main_menu_keyboard
from src.bot.keyboards.reply import get_back_to_menu_keyboard
from src.bot.states import ListingsSG
from src.database import BotUser
from src.bot.utils import execute_with_refresh
from src.infrastructure.api import SwipeApiClient, SwipeAPIError

router = Router()
logger = logging.getLogger(__name__)


class ListingContext(NamedTuple):
    """Container for listing display data to avoid too many arguments."""

    text: str
    media_group: List[InputMediaPhoto]
    has_prev: bool
    has_next: bool
    offset: int
    current_item: Dict[str, Any]


async def _cleanup_previous_messages(message: Message, data: Dict[str, Any]) -> None:
    """Helper to delete previous listing messages."""
    control_msg_id = data.get("control_msg_id")
    if control_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, control_msg_id)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    album_msg_ids = data.get("album_msg_ids", [])
    for msg_id in album_msg_ids:
        try:
            await message.bot.delete_message(message.chat.id, msg_id)
        except Exception:  # pylint: disable=broad-exception-caught
            pass


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
    if owner and owner.get("phone"):
        phone = html.escape(owner["phone"])
    else:
        phone = _("No contact info")

    title_prefix = ""
    if mode == "my":
        title_prefix = _("<b>MY LISTING</b>\n")

    return (
        f"{title_prefix}"
        f"<b>{price}</b> | {area} м²\n"
        f"{address}\n\n"
        f"{description}\n\n"
        f"{phone}"
    )


def _prepare_media_group(images: List[Dict[str, Any]]) -> List[InputMediaPhoto]:
    """Helper to prepare media group."""
    media_group = []
    if images:
        for img in images:
            url = img["image_url"]
            media_group.append(InputMediaPhoto(media=url))
    else:
        media_group.append(
            InputMediaPhoto(media="https://via.placeholder.com/600x400?text=No+Photo")
        )
    return media_group


async def _send_listing_content(
    message: Message, state: FSMContext, context: ListingContext
) -> None:
    """Helper to send the album and control message."""
    try:
        album_messages = await message.answer_media_group(media=context.media_group)
        new_album_ids = [m.message_id for m in album_messages]

        control_msg = await message.answer(
            text=context.text,
            reply_markup=get_listings_nav_keyboard(context.has_prev, context.has_next),
        )

        await state.update_data(
            offset=context.offset,
            control_msg_id=control_msg.message_id,
            album_msg_ids=new_album_ids,
            current_listing=context.current_item,
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to send listing message: %s", e)
        await message.answer(_("Error displaying listing. Please try again."))


async def _fetch_listings(
    user: BotUser, mode: str, offset: int
) -> Optional[List[Dict[str, Any]]]:
    """Helper to fetch listings from API."""
    api = SwipeApiClient()
    try:
        fetch_func = (
            api.announcements.get_my_announcements
            if mode == "my"
            else api.announcements.get_announcements
        )
        logger.info(
            "Fetching listings for user %s (mode=%s, offset=%s)",
            user.telegram_id,
            mode,
            offset,
        )
        return await execute_with_refresh(user, fetch_func, limit=2, offset=offset)
    except SwipeAPIError as e:
        logger.error("Failed to fetch listings for user %s: %s", user.telegram_id, e)
        return None


async def show_listing_page(
    message: Message, state: FSMContext, user: BotUser, offset: int
):
    """
    Fetches and displays one announcement at the given offset.
    """
    data = await state.get_data()
    mode = data.get("listing_mode", "all")

    listings = await _fetch_listings(user, mode, offset)

    if listings is None:
        await message.answer(_("Error loading listings."))
        return

    if not listings:
        logger.info("No listings found for user %s (mode=%s)", user.telegram_id, mode)
        if offset > 0:
            await message.answer(_("No more listings."))
            await state.update_data(offset=offset - 1)
        else:
            msg_text = (
                _("You haven't created any listings yet.")
                if mode == "my"
                else _("No listings found.")
            )
            await message.answer(msg_text)
        return

    current_item = listings[0]
    await _cleanup_previous_messages(message, data)

    ctx = ListingContext(
        text=_prepare_announcement_text(current_item, mode),
        media_group=_prepare_media_group(current_item.get("images", [])),
        has_prev=offset > 0,
        has_next=len(listings) > 1,
        offset=offset,
        current_item=current_item,
    )

    await _send_listing_content(message, state, ctx)


@router.callback_query(MenuCallback.filter(F.action == "listings"))
async def start_listings(query: CallbackQuery, state: FSMContext):
    """
    Enters listing browsing mode (All listings).
    """
    logger.info("User %s entered marketplace mode", query.from_user.id)
    user = await BotUser.find_one(BotUser.telegram_id == query.from_user.id)

    await state.set_state(ListingsSG.Browsing)
    await state.update_data(offset=0, listing_mode="all")

    await query.message.delete()

    menu_msg = await query.message.answer(
        _("Announcement Mode"), reply_markup=get_back_to_menu_keyboard()
    )
    await state.update_data(menu_msg_id=menu_msg.message_id)

    await show_listing_page(query.message, state, user, offset=0)


@router.callback_query(MenuCallback.filter(F.action == "my_listings"))
async def start_my_listings(query: CallbackQuery, state: FSMContext):
    """
    Enters listing browsing mode (My Listings).
    """
    logger.info("User %s entered my listings mode", query.from_user.id)
    user = await BotUser.find_one(BotUser.telegram_id == query.from_user.id)

    await state.set_state(ListingsSG.Browsing)
    await state.update_data(offset=0, listing_mode="my")

    await query.message.delete()

    menu_msg = await query.message.answer(
        _("My Listings Mode"), reply_markup=get_back_to_menu_keyboard()
    )
    await state.update_data(menu_msg_id=menu_msg.message_id)

    await show_listing_page(query.message, state, user, offset=0)


@router.callback_query(ListingCallback.filter(F.action == "next"))
async def next_page(query: CallbackQuery, state: FSMContext):
    """
    Handles the 'Next' navigation button.
    """
    logger.info("User %s requested next listing", query.from_user.id)
    user = await BotUser.find_one(BotUser.telegram_id == query.from_user.id)
    data = await state.get_data()
    new_offset = data.get("offset", 0) + 1

    await show_listing_page(query.message, state, user, new_offset)
    await query.answer()


@router.callback_query(ListingCallback.filter(F.action == "prev"))
async def prev_page(query: CallbackQuery, state: FSMContext):
    """
    Handles the 'Previous' navigation button.
    """
    logger.info("User %s requested previous listing", query.from_user.id)
    user = await BotUser.find_one(BotUser.telegram_id == query.from_user.id)
    data = await state.get_data()
    new_offset = max(0, data.get("offset", 0) - 1)

    await show_listing_page(query.message, state, user, new_offset)
    await query.answer()


@router.callback_query(ListingCallback.filter(F.action == "geo"))
async def show_geolocation(query: CallbackQuery, state: FSMContext):
    """
    Handles the 'Location' button.
    """
    data = await state.get_data()
    item = data.get("current_listing")

    if item and item.get("latitude") and item.get("longitude"):
        try:
            lat = float(item["latitude"])
            lon = float(item["longitude"])
            logger.info(
                "Showing geolocation for listing to user %s", query.from_user.id
            )
            await query.message.answer_location(latitude=lat, longitude=lon)
            await query.answer()
        except ValueError:
            logger.error("Invalid coordinates for listing: %s", item)
            await query.answer(_("Invalid coordinates data."), show_alert=True)
    else:
        logger.info("No coordinates for listing ID %s", item.get("id"))
        await query.answer(_("Geolocation not set for this listing."), show_alert=True)


@router.message(ListingsSG.Browsing, F.text == __("Back to Menu"))
async def exit_listings(message: Message, state: FSMContext):
    """
    Exits the browsing mode, clears messages, returns to Main Menu.
    """
    logger.info("User %s exiting listings mode", message.from_user.id)
    try:
        await message.delete()
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    data = await state.get_data()

    await _cleanup_previous_messages(message, data)

    menu_msg_id = data.get("menu_msg_id")
    if menu_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, menu_msg_id)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    await state.clear()

    msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await msg.delete()

    await message.answer(
        text=_("Welcome back! Select an action:"), reply_markup=get_main_menu_keyboard()
    )
