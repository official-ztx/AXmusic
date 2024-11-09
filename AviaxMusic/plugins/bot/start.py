import time
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython import VideosSearch

import config
from AviaxMusic import app
from AviaxMusic.misc import _boot_
from AviaxMusic.plugins.sudo.sudoers import sudoers_list
from AviaxMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from AviaxMusic.utils import bot_sys_stats
from AviaxMusic.utils.decorators.language import LanguageStart
from AviaxMusic.utils.formatters import get_readable_time
from AviaxMusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS, SUPPORT_GROUP, START_VIDEO_URL
from strings import get_string


# Helper function to send the start video
async def send_start_video(chat_id, reply_markup):
    """Send the start video without a caption."""
    try:
        sent_video = await app.send_video(
            chat_id=chat_id,
            video=config.START_VIDEO_URL,
            supports_streaming=True,
            reply_markup=reply_markup
        )
        return sent_video
    except Exception as e:
        print(f"Error sending video: {e}")
        return None


# Function to send a separate text message as a reply to the video
async def send_text_message(chat_id, text, reply_to_message_id):
    """Send a text message as a reply to the video."""
    try:
        await app.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id
        )
    except Exception as e:
        print(f"Error sending text: {e}")


# Handler for the /start command in private chat
@app.on_message(filters.command("start") & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)

    # Check if the command has additional parameters
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        if name.startswith("help"):
            keyboard = help_pannel(_)
            caption = _["help_1"].format(SUPPORT_GROUP)
            video_message = await send_start_video(message.chat.id, keyboard)

            if video_message:
                await send_text_message(
                    chat_id=message.chat.id,
                    text=caption,
                    reply_to_message_id=video_message.message_id
                )
            return

        if name.startswith("sud"):
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=f"{message.from_user.mention} checked the <b>sudolist</b>."
                )
            return

    # Default /start behavior
    out = private_panel(_)
    UP, CPU, RAM, DISK = await bot_sys_stats()
    caption = _["start_2"].format(
        message.from_user.mention, app.mention, UP, DISK, CPU, RAM
    )

    # Send the video first
    video_message = await send_start_video(message.chat.id, InlineKeyboardMarkup(out))

    if video_message:
        # Send the text as a separate message replying to the video
        await send_text_message(
            chat_id=message.chat.id,
            text=caption,
            reply_to_message_id=video_message.message_id
        )

    # Logging if enabled
    if await is_on_off(2):
        await app.send_message(
            chat_id=config.LOG_GROUP_ID,
            text=f"{message.from_user.mention} started the bot."
        )


# Handler for the /start command in group chat
@app.on_message(filters.command("start") & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_group(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    caption = _["start_1"].format(app.mention, get_readable_time(uptime))

    # Send the video first in the group chat
    video_message = await send_start_video(message.chat.id, InlineKeyboardMarkup(out))

    if video_message:
        await send_text_message(
            chat_id=message.chat.id,
            text=caption,
            reply_to_message_id=video_message.message_id
        )
    await add_served_chat(message.chat.id)


# Welcome new chat members
@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)

            # Check if the new member is banned
            if await is_banned_user(member.id):
                await message.chat.ban_member(member.id)

            # If the bot is added to a non-supergroup, leave
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)

                # Check if the chat is blacklisted
                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            SUPPORT_GROUP
                        ),
                        disable_web_page_preview=True
                    )
                    return await app.leave_chat(message.chat.id)

                # Send welcome video and message
                out = start_panel(_)
                caption = _["start_3"].format(
                    message.from_user.first_name,
                    app.mention,
                    message.chat.title,
                    app.mention
                )
                video_message = await send_start_video(message.chat.id, InlineKeyboardMarkup(out))

                if video_message:
                    await send_text_message(
                        chat_id=message.chat.id,
                        text=caption,
                        reply_to_message_id=video_message.message_id
                    )
                await add_served_chat(message.chat.id)
        except Exception as ex:
            print(f"Error welcoming new members: {ex}")
