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
async def send_start_video(message: Message, reply_markup: InlineKeyboardMarkup):
    """Send a start video without a caption."""
    return await message.reply_video(
        video=config.START_VIDEO_URL,
        supports_streaming=True,
        reply_markup=reply_markup
    )


# Function to send the text message separately as a reply to the video
async def send_text_message(chat_id, text, reply_to_message_id, reply_markup=None):
    """Send a text message as a reply to a video."""
    return await app.send_message(
        chat_id=chat_id,
        text=text,
        reply_to_message_id=reply_to_message_id,
        reply_markup=reply_markup
    )


# Private start command handler
@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)

    # Handling optional parameters after /start
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        if name[0:4] == "help":
            keyboard = help_pannel(_)
            caption = _["help_1"].format(config.SUPPORT_GROUP)
            video_message = await send_start_video(message, keyboard)
            return await send_text_message(
                chat_id=message.chat.id,
                text=caption,
                reply_to_message_id=video_message.message_id
            )

        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=f"{message.from_user.mention} checked the <b>sudolist</b>."
                )
            return

        if name[0:3] == "inf":
            m = await message.reply_text("🔎 Searching...")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"

            try:
                results = VideosSearch(query, limit=1)
                result = (await results.next())["result"]

                if not result:
                    await m.edit_text("No results found.")
                    return

                # Extract video details
                video_info = result[0]
                title = video_info["title"]
                duration = video_info["duration"]
                views = video_info["viewCount"]["short"]
                channellink = video_info["channel"]["link"]
                channel = video_info["channel"]["name"]
                link = video_info["link"]
                published = video_info["publishedTime"]

                searched_text = _["start_6"].format(
                    title, duration, views, published, channellink, channel, app.mention
                )

                key = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text=_["S_B_8"], url=link),
                            InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_GROUP)
                        ]
                    ]
                )

                await m.delete()

                # Send the video first without a caption
                video_message = await send_start_video(message, key)

                # Send the text as a reply to the video
                await send_text_message(
                    chat_id=message.chat.id,
                    text=searched_text,
                    reply_to_message_id=video_message.message_id,
                    reply_markup=key
                )

                if await is_on_off(2):
                    await app.send_message(
                        chat_id=config.LOG_GROUP_ID,
                        text=f"{message.from_user.mention} checked <b>track information</b>."
                    )

            except Exception as e:
                await m.edit_text("An error occurred while fetching video details.")
                print(e)
            return

    # Default start message for new users
    out = private_panel(_)
    UP, CPU, RAM, DISK = await bot_sys_stats()
    caption = _["start_2"].format(
        message.from_user.mention, app.mention, UP, DISK, CPU, RAM
    )

    # Send the video first
    video_message = await send_start_video(message, InlineKeyboardMarkup(out))

    # Send the caption as a reply to the video
    await send_text_message(
        chat_id=message.chat.id,
        text=caption,
        reply_to_message_id=video_message.message_id
    )

    if await is_on_off(2):
        await app.send_message(
            chat_id=config.LOG_GROUP_ID,
            text=f"{message.from_user.mention} started the bot."
        )


# Group start command handler
@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    caption = _["start_1"].format(app.mention, get_readable_time(uptime))

    video_message = await send_start_video(message, InlineKeyboardMarkup(out))
    await send_text_message(
        chat_id=message.chat.id,
        text=caption,
        reply_to_message_id=video_message.message_id
    )
    return await add_served_chat(message.chat.id)


# Welcome new chat members
@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)

            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass

            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)

                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_GROUP
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

                video_message = await send_start_video(message, InlineKeyboardMarkup(out))
                await send_text_message(
                    chat_id=message.chat.id,
                    text=caption,
                    reply_to_message_id=video_message.message_id
                )
                await add_served_chat(message.chat.id)

        except Exception as ex:
            print(ex)
