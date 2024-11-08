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

# Helper function to send the video separately
async def send_start_video(message: Message, reply_markup: InlineKeyboardMarkup):
    """Send a start video without a caption."""
    return await message.reply_video(
        video=config.START_VIDEO_URL,  # Your video URL
        supports_streaming=True,
        reply_markup=reply_markup
    )

# Function to send the text message separately
async def send_text_message(chat_id, text, reply_markup=None):
    return await app.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )

@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        if name[0:4] == "help":
            keyboard = help_pannel(_)
            caption = _["help_1"].format(config.SUPPORT_GROUP)
            await send_start_video(message, keyboard)
            return await send_text_message(message.chat.id, caption)

        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=f"{message.from_user.mention} checked the <b>sudolist</b>."
                )
            return

        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"

            try:
                # Searching for the video
                results = VideosSearch(query, limit=1)
                result = (await results.next())["result"]

                if not result:
                    await m.edit_text("No results found.")
                    return

                # Extracting details from the search result
                for video in result:
                    title = video["title"]
                    duration = video["duration"]
                    views = video["viewCount"]["short"]
                    thumbnail = video["thumbnails"][0]["url"].split("?")[0]
                    channellink = video["channel"]["link"]
                    channel = video["channel"]["name"]
                    link = video["link"]
                    published = video["publishedTime"]

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

                # Send the video first without caption
                await send_start_video(message, key)

                # Now send the text message separately
                await send_text_message(
                    chat_id=message.chat.id,
                    text=searched_text,
                    reply_markup=key
                )

                # Logging if the feature is enabled
                if await is_on_off(2):
                    await app.send_message(
                        chat_id=config.LOG_GROUP_ID,
                        text=f"{message.from_user.mention} checked <b>track information</b>."
                    )

            except Exception as e:
                await m.edit_text("An error occurred while fetching video details.")
                print(e)
            return

    # Default response if no specific command is found
    out = private_panel(_)
    UP, CPU, RAM, DISK = await bot_sys_stats()
    caption = _["start_2"].format(message.from_user.mention, app.mention, UP, DISK, CPU, RAM)
    
    # Send the video first, then the text message
    await send_start_video(message, InlineKeyboardMarkup(out))
    await send_text_message(message.chat.id, caption)

    if await is_on_off(2):
        await app.send_message(
            chat_id=config.LOG_GROUP_ID,
            text=f"{message.from_user.mention} started the bot."
        )
