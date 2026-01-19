"""src/bot/handlers/announcement/create_announcement.py."""

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from src.bot.callbacks import MenuCallback
from src.bot.keyboards.inline import get_main_menu_keyboard
from src.bot.keyboards.reply import (
    get_cancel_keyboard,
    get_back_keyboard,
    get_location_keyboard,
    get_done_keyboard,
)
from src.bot.states import CreateAnnouncementSG
from src.bot.utils import (
    handle_cancel,
    cleanup_last_step,
    remove_reply_keyboard,
    execute_with_refresh,
    encode_image_to_base64,
)
from src.database import BotUser
from src.infrastructure.api import SwipeApiClient, SwipeAPIError

router = Router()


@router.callback_query(MenuCallback.filter(F.action == "create_listing"))
async def start_create_listing(query: CallbackQuery, state: FSMContext):
    """
    Starts the announcement creation flow.
    Step 1: Ask for Address.
    """
    await state.set_state(CreateAnnouncementSG.InputAddress)
    await state.set_data({"images": []})

    await query.message.delete()

    msg = await query.message.answer(
        text=_(
            "**Create New Listing**\n\n"
            "Step 1/7: Enter the **Address** (e.g. Baker St, 221B):"
        ),
        reply_markup=get_cancel_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(CreateAnnouncementSG.InputAddress)
async def input_address(message: Message, state: FSMContext):
    """
    Saves address, asks for Apartment Number.
    """
    if await handle_cancel(message, state):
        return

    await cleanup_last_step(state, message)
    await state.update_data(address=message.text)
    await state.set_state(CreateAnnouncementSG.InputApartmentNumber)

    msg = await message.answer(
        text=_("Step 2/7: Enter **Apartment Number**:"),
        reply_markup=get_back_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(CreateAnnouncementSG.InputApartmentNumber)
async def input_apt_number(message: Message, state: FSMContext):
    """
    Saves apartment number, asks for Price.
    """
    if await handle_cancel(message, state):
        return

    if message.text == _("Back"):
        await cleanup_last_step(state, message)
        await state.set_state(CreateAnnouncementSG.InputAddress)
        msg = await message.answer(
            text=_("Step 1/7: Enter the **Address**:"),
            reply_markup=get_cancel_keyboard(),
        )
        await state.update_data(last_bot_msg_id=msg.message_id)
        return

    await cleanup_last_step(state, message)
    await state.update_data(apartment_number=message.text)
    await state.set_state(CreateAnnouncementSG.InputPrice)

    msg = await message.answer(
        text=_("Step 3/7: Enter **Price** ($):"), reply_markup=get_back_keyboard()
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(CreateAnnouncementSG.InputPrice)
async def input_price(message: Message, state: FSMContext):
    """
    Saves price, asks for Area.
    """
    if await handle_cancel(message, state):
        return

    if message.text == _("Back"):
        await cleanup_last_step(state, message)
        await state.set_state(CreateAnnouncementSG.InputApartmentNumber)
        msg = await message.answer(
            text=_("Step 2/7: Enter **Apartment Number**:"),
            reply_markup=get_back_keyboard(),
        )
        await state.update_data(last_bot_msg_id=msg.message_id)
        return

    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        msg = await message.answer(_("Please enter a valid number for price."))
        await state.update_data(last_bot_msg_id=msg.message_id)
        return

    await cleanup_last_step(state, message)
    await state.update_data(price=price)
    await state.set_state(CreateAnnouncementSG.InputArea)

    msg = await message.answer(
        text=_("Step 4/7: Enter **Area** (sq. m):"), reply_markup=get_back_keyboard()
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(CreateAnnouncementSG.InputArea)
async def input_area(message: Message, state: FSMContext):
    """
    Saves area, asks for Description.
    """
    if await handle_cancel(message, state):
        return

    if message.text == _("Back"):
        await cleanup_last_step(state, message)
        await state.set_state(CreateAnnouncementSG.InputPrice)
        msg = await message.answer(
            text=_("Step 3/7: Enter **Price** ($):"), reply_markup=get_back_keyboard()
        )
        await state.update_data(last_bot_msg_id=msg.message_id)
        return

    try:
        area = float(message.text.replace(",", "."))
        if area <= 0:
            raise ValueError
    except ValueError:
        msg = await message.answer(_("Please enter a valid number for area."))
        await state.update_data(last_bot_msg_id=msg.message_id)
        return

    await cleanup_last_step(state, message)
    await state.update_data(area=area)
    await state.set_state(CreateAnnouncementSG.InputDescription)

    msg = await message.answer(
        text=_("Step 5/7: Enter **Description**:"), reply_markup=get_back_keyboard()
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(CreateAnnouncementSG.InputDescription)
async def input_description(message: Message, state: FSMContext):
    """
    Saves description, asks for Location.
    """
    if await handle_cancel(message, state):
        return

    if message.text == _("Back"):
        await cleanup_last_step(state, message)
        await state.set_state(CreateAnnouncementSG.InputArea)
        msg = await message.answer(
            text=_("Step 4/7: Enter **Area** (sq. m):"),
            reply_markup=get_back_keyboard(),
        )
        await state.update_data(last_bot_msg_id=msg.message_id)
        return

    await cleanup_last_step(state, message)
    await state.update_data(description=message.text)
    await state.set_state(CreateAnnouncementSG.InputLocation)

    msg = await message.answer(
        text=_("Step 6/7: Share **Location** using the button below:"),
        reply_markup=get_location_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(CreateAnnouncementSG.InputLocation, F.location)
async def input_location(message: Message, state: FSMContext):
    """
    Saves location coordinates, asks for Images.
    """
    latitude = str(message.location.latitude)
    longitude = str(message.location.longitude)

    await cleanup_last_step(state, message)
    await remove_reply_keyboard(message)

    await state.update_data(latitude=latitude, longitude=longitude)
    await state.set_state(CreateAnnouncementSG.InputImages)

    msg = await message.answer(
        text=_(
            "Step 7/7: Send **Photos** (one by one or album).\n\n"
            "Press **Done** when finished."
        ),
        reply_markup=get_done_keyboard(),
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


@router.message(CreateAnnouncementSG.InputImages, F.photo)
async def input_image(message: Message, state: FSMContext, bot: Bot):
    """
    Handles incoming photos, converts to Base64 and stores in state.
    """
    photo_id = message.photo[-1].file_id

    try:
        base64_img = await encode_image_to_base64(bot, photo_id)

        data = await state.get_data()
        images = data.get("images", [])
        images.append(base64_img)

        await state.update_data(images=images)

    except Exception:  # pylint: disable=broad-exception-caught
        await message.answer(_("Failed to process image."))


@router.message(CreateAnnouncementSG.InputImages, F.text == __("Done"))
async def finish_creation(message: Message, state: FSMContext):
    """
    Final step: Submit data to API.
    """
    data = await state.get_data()
    images = data.get("images", [])

    if not images:
        await message.answer(_("Please send at least one photo."))
        return

    payload = {
        "address": data["address"],
        "apartment_number": data["apartment_number"],
        "price": data["price"],
        "area": data["area"],
        "description": data["description"],
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "images": images,
        "number_of_rooms": "1",
        "communication_method": "any",
    }

    user = await BotUser.find_one(BotUser.telegram_id == message.from_user.id)
    api = SwipeApiClient()

    wait_msg = await message.answer(
        _("Creating listing..."), reply_markup=ReplyKeyboardRemove()
    )

    try:
        await execute_with_refresh(
            user, api.announcements.create_announcement, data=payload
        )

        await wait_msg.delete()
        await message.answer(
            _("**Listing created successfully!**"),
            reply_markup=get_main_menu_keyboard(),
        )
        await state.clear()

    except SwipeAPIError as e:
        await wait_msg.delete()
        await message.answer(
            _("Failed to create listing: {error}").format(error=e.message),
            reply_markup=get_main_menu_keyboard(),
        )
        await state.clear()
