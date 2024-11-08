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

# Helper function to send the start video and caption
async def send_start_video(message: Message, caption: str, reply_markup: InlineKeyboardMarkup):
    """Send a start video instead of an image."""
    return await message.reply_video(
        video=START_VIDEO_URL,  # Make sure to set this in your config
        caption=caption,
        supports_streaming=True,
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
            return await send_start_video(message, caption, keyboard)

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
                result = await results.next()  # Get the next batch of results

                if not result or not result.get("result"):
                    await m.edit_text("No results found.")
                    return

                video = result["result"][0]
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

                # Send the thumbnail as a photo (not a video)
                await app.send_photo(
                    chat_id=message.chat.id,
                    photo=thumbnail,
                    reply_markup=key
                )

                # Send the caption as a separate message
                await app.send_message(
                    chat_id=message.chat.id,
                    text=searched_text
                )

                # Logging if the feature is enabled
                if await is_on_off(2):
                    await app.send_message(
                        chat_id=config.LOG_GROUP_ID,
                        text=f"{message.from_user.mention} checked <b>track information</b>."
                    )

            except Exception as e:
                await m.edit_text(f"An error occurred: {str(e)}")
                print(f"Error fetching video details: {e}")

            return

    # Default response if no specific command is found
    out = private_panel(_)
    UP, CPU, RAM, DISK = await bot_sys_stats()
    caption = _["start_2"].format(message.from_user.mention, app.mention, UP, DISK, CPU, RAM)
    await send_start_video(message, caption, InlineKeyboardMarkup(out))

    if await is_on_off(2):
        await app.send_message(
            chat_id=config.LOG_GROUP_ID,
            text=f"{message.from_user.mention} started the bot."
        )

@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    caption = _["start_1"].format(app.mention, get_readable_time(uptime))
    await send_start_video(message, caption, InlineKeyboardMarkup(out))
    return await add_served_chat(message.chat.id)

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
                await send_start_video(message, caption, InlineKeyboardMarkup(out))
                await add_served_chat(message.chat.id)
                message.stop_propagation()

        except Exception as ex:
            print(f"Error handling new chat member: {ex}")
