#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import json
import math
import os
import requests
import subprocess
import time

from plugins.config import Config
from plugins.script import Translation

import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from plugins.functions.help_uploadbot import *
from plugins.functions.display_progress import *
from plugins.functions.help_Nekmo_ffmpeg import *
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
# https://stackoverflow.com/a/37631799/4723940
from PIL import Image
from pyrogram.types import *
from pyrogram import Client, filters


@Client.on_message(filters.text & filters.private, group=1)
def echo(bot, update):

    text = update.text
    if(text.startswith("https://")):
        url = text
        if "|" in url:


            url, file_name = url.split("|")
            url = url.strip()
            # https://stackoverflow.com/a/761825/4723940
            file_name = file_name.strip()
            logger.info(url)
            logger.info(file_name)
            a = bot.send_message(
                chat_id=update.from_user.id,
                text=Translation.DOWNLOAD_START,
                reply_to_message_id=update.id
            )
            after_download_path = DownLoadFile(
                url, Config.DOWNLOAD_LOCATION + "/" + file_name)
            description = Translation.CUSTOM_CAPTION_UL_FILE
            bot.edit_message_text(
                text=Translation.SAVED_RECVD_DOC_FILE,
                chat_id=update.from_user.id,
                message_id=a.id
            )
            bot.edit_message_text(
                text=Translation.UPLOAD_START,
                chat_id=update.from_user.id,
                message_id=a.id
            )
            file_size = os.stat(after_download_path).st_size
            if file_size > Config.TG_MAX_FILE_SIZE:
                bot.edit_message_text(
                    text=Translation.RCHD_TG_API_LIMIT,
                    chat_id=update.from_user.id,
                    message_id=a.id
                )
            else:
                # try to upload file
                bot.send_document(
                    chat_id=update.from_user.id,
                    document=after_download_path,
                    caption=description,
                    # reply_markup=reply_markup,
                    #thumb=thumb_image_path,
                    reply_to_message_id=update.id
                )
                bot.edit_message_text(
                    text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG,
                    chat_id=update.from_user.id,
                    message_id=a.id,
                    disable_web_page_preview=True
                )
            try:
                os.remove(after_download_path)
                
            except:
                pass
        else:
            try:
                if "hotstar.com" in url:
                    command_to_exec = [
                        "yt-dlp", "--no-warnings", "-j", url, "--proxy", Config.HTTP_PROXY]
                else:
                    command_to_exec = ["yt-dlp",
                                       "--no-warnings", "-j", url]
                logger.info(command_to_exec)
                t_response = subprocess.check_output(
                    command_to_exec, stderr=subprocess.STDOUT)
                # https://github.com/rg3/youtube-dl/issues/2630#issuecomment-38635239
            except subprocess.CalledProcessError as exc:
                # print("Status : FAIL", exc.returncode, exc.output)
                bot.send_message(
                    chat_id=update.from_user.id,
                    text=exc.output.decode("UTF-8"),
                    reply_to_message_id=update.id
                )
            else:
                # logger.info(t_response)
                x_reponse = t_response.decode("UTF-8")
                response_json = json.loads(x_reponse)
                # logger.info(response_json)
                inline_keyboard = []
                if "formats" in response_json:
                    for formats in response_json["formats"]:
                        format_id = formats["format_id"]
                        format_string = formats["format"]
                        format_ext = formats["ext"]
                        approx_file_size = ""
                        if "filesize" in formats:
                            approx_file_size = humanbytes(formats["filesize"])
                        cb_string = "{}|{}|{}".format(
                            "video", format_id, format_ext)
                        if not "audio only" in format_string:
                            ikeyboard = [
                                InlineKeyboardButton(
                                    "[" + format_string +
                                    "] (" + format_ext + " - " +
                                    approx_file_size + ")",
                                    callback_data=(cb_string).encode("UTF-8")
                                )
                            ]
                            inline_keyboard.append(ikeyboard)
                    cb_string = "{}|{}|{}".format("audio", "5", "mp3")
                    inline_keyboard.append([
                        InlineKeyboardButton(
                            "MP3 " + "(" + "medium" + ")", callback_data=cb_string.encode("UTF-8"))
                    ])
                    cb_string = "{}|{}|{}".format("audio", "0", "mp3")
                    inline_keyboard.append([
                        InlineKeyboardButton(
                            "MP3 " + "(" + "best" + ")", callback_data=cb_string.encode("UTF-8"))
                    ])
                else:
                    format_id = response_json["format_id"]
                    format_ext = response_json["ext"]
                    cb_string = "{}|{}|{}".format(
                        "file", format_id, format_ext)
                    inline_keyboard.append([
                        InlineKeyboardButton(
                            "unknown video format", callback_data=cb_string.encode("UTF-8"))
                    ])
                reply_markup = InlineKeyboardMarkup(inline_keyboard)
                logger.info(reply_markup)
                thumbnail = Config.DEF_THUMB_NAIL_VID_S
                thumbnail_image = Config.DEF_THUMB_NAIL_VID_S
                if "thumbnail" in response_json:
                    thumbnail = response_json["thumbnail"]
                    thumbnail_image = response_json["thumbnail"]
                thumb_image_path = DownLoadFile(
                    thumbnail_image, Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + ".jpg")
                bot.send_message(
                    chat_id=update.from_user.id,
                    text=Translation.FORMAT_SELECTION.format(thumbnail),
                    reply_markup=reply_markup,
                    #parse_mode=pyrogram.ParseMode.HTML,
                    reply_to_message_id=update.id
                )
    elif "===" in text:
        logger.info("cult_small_video")

        if update.reply_to_message is not None:
            a = bot.send_message(
                chat_id=update.from_user.id,
                text=Translation.DOWNLOAD_START,
                reply_to_message_id=update.id
            )
            url = update.reply_to_message.text
            for entity in update.reply_to_message.entities:
                if entity.type == "text_link":
                    url = entity.url
            start_time, end_time = text.split("===")

            mp4_file = cult_small_video(
                url, Config.DOWNLOAD_LOCATION, start_time, end_time)
            bot.edit_message_text(
                text=Translation.SAVED_RECVD_DOC_FILE,
                chat_id=update.from_user.id,
                message_id=a.id
            )

            bot.send_video(
                chat_id=update.from_user.id,
                video=mp4_file,
                # caption=description,
                duration=duration,
                width=width,
                height=height,
                supports_streaming=True,
                # reply_markup=reply_markup,
                #thumb=thumb_image_path,
                reply_to_message_id=update.id
            )
            os.remove(mp4_file)
            bot.edit_message_text(
                text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG,
                chat_id=update.from_user.id,
                message_id=a.id,
                disable_web_page_preview=True
            )
        else:
            bot.send_message(
                chat_id=update.from_user.id,
                text=Translation.START_TEXT,
                reply_to_message_id=update.id
            )
    elif ":" in text:
        logger.info("take_screen_shot")

        if update.reply_to_message is not None:
            a = bot.send_message(
                chat_id=update.from_user.id,
                text=Translation.DOWNLOAD_START,
                reply_to_message_id=update.id
            )
            url = update.reply_to_message.text
            for entity in update.reply_to_message.entities:
                if entity.type == "text_link":
                    url = entity.url
            img_file = take_screen_shot(url, Config.DOWNLOAD_LOCATION, text)
            # try to upload file
            bot.edit_message_text(
                text=Translation.UPLOAD_START,
                chat_id=update.from_user.id,
                message_id=a.id
            )
            bot.send_document(
                chat_id=update.from_user.id,
                document=img_file,
                # caption=description,
                # reply_markup=reply_markup,
                # thumb=thumb_image_path,
                reply_to_message_id=update.id
            )
            bot.send_photo(
                chat_id=update.from_user.id,
                photo=img_file,
                # caption=description,
                # reply_markup=reply_markup,
                # thumb=thumb_image_path,
                reply_to_message_id=update.id
            )
            os.remove(img_file)
            bot.edit_message_text(
                text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG,
                chat_id=update.from_user.id,
                message_id=a.id,
                disable_web_page_preview=True
            )
        else:
            bot.send_message(
                chat_id=update.from_user.id,
                text=Translation.FF_MPEG_RO_BOT_RE_SURRECT_ED,
                reply_to_message_id=update.id
            )
