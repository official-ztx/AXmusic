import time
import asyncio
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


async def send_start_video(chat_id, reply_markup):
    """Send the start video and return the message object."""
    try:
        sent_video = await app.send_video(
            chat_id=chat_id,
            video=config.START_VIDEO_URL,
            supports_streaming=True,
            reply_markup=reply_markup
        )
        print("Video sent successfully")
        return sent_video
    except Exception as e:
        print(f"Error sending video: {e}")
        return None


@app.on_message(filters.command("start") & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)

    # Generate panels and system stats
    out = private_panel(_)
    UP, CPU, RAM, DISK = await bot_sys_stats()
    caption = _["start_2"].format(
        message.from_user.mention, app.mention, UP, DISK, CPU, RAM
    )

    # Step 1: Send the video first
    video_message = await send_start_video(message.chat.id, InlineKeyboardMarkup(out))

    if video_message:
        # Step 2: Wait for a short moment to ensure the video is fully sent
        await asyncio.sleep(0.5)

        # Step 3: Send the caption text as a reply to the video
        try:
            await app.send_message(
                chat_id=message.chat.id,
                text=caption,
                reply_to_message_id=video_message.message_id
            )
            print("Caption sent successfully")
        except Exception as e:
            print(f"Error sending caption text: {e}")
    else:
        print("Failed to send video")


@app.on_message(filters.command("start") & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_group(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    caption = _["start_1"].format(app.mention, get_readable_time(uptime))

    # Step 1: Send the video in the group
    video_message = await send_start_video(message.chat.id, InlineKeyboardMarkup(out))

    if video_message:
        await asyncio.sleep(0.5)
        try:
            await app.send_message(
                chat_id=message.chat.id,
                text=caption,
                reply_to_message_id=video_message.message_id
            )
        except Exception as e:
            print(f"Error sending caption text in group: {e}")

    await add_served_chat(message.chat.id)


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)

            if await is_banned_user(member.id):
                await message.chat.ban_member(member.id)

            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)

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

                out = start_panel(_)
                caption = _["start_3"].format(
                    message.from_user.first_name,
                    app.mention,
                    message.chat.title,
                    app.mention
                )

                video_message = await send_start_video(message.chat.id, InlineKeyboardMarkup(out))

                if video_message:
                    await asyncio.sleep(0.5)
                    await app.send_message(
                        chat_id=message.chat.id,
                        text=caption,
                        reply_to_message_id=video_message.message_id
                    )
                await add_served_chat(message.chat.id)

        except Exception as ex:
            print(f"Error welcoming new members: {ex}")
