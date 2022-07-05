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



from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
# https://stackoverflow.com/a/37631799/4723940
from PIL import Image




@pyrogram.Client.on_callback_query()
def button(bot, update):
    # logger.info(update)
    cb_data = update.data.decode("UTF-8")
    if cb_data.find("|") == -1:
        return ""
    tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("|")
    youtube_dl_url = update.message.reply_to_message.text

    thumb_image_path = Config.DOWNLOAD_LOCATION + \
        "/" + str(update.from_user.id) + ".jpg"
    bot.edit_message_text(
        text=Translation.DOWNLOAD_START,
        chat_id=update.from_user.id,
        message_id=update.message.message_id
    )
    description = Translation.CUSTOM_CAPTION_UL_FILE
    download_directory = ""
    command_to_exec = []
    if tg_send_type == "audio":
        download_directory = Config.DOWNLOAD_LOCATION + "/" + \
            str(update.from_user.id) + "_" + \
            youtube_dl_format + "." + youtube_dl_ext + ""
        command_to_exec = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", youtube_dl_ext,
            "--audio-quality", youtube_dl_format,
            youtube_dl_url,
            "-o", download_directory
        ]
    else:
        download_directory = Config.DOWNLOAD_LOCATION + "/" + \
            str(update.from_user.id) + "_" + \
            youtube_dl_format + "." + youtube_dl_ext
        # command_to_exec = ["youtube-dl", "-f", youtube_dl_format, "--hls-prefer-ffmpeg", "--recode-video", "mp4", "-k", youtube_dl_url, "-o", download_directory]
        command_to_exec = [
            "yt-dlp",
            "--embed-subs",
            "-f", youtube_dl_format,
            "-k",
            "--hls-prefer-ffmpeg", youtube_dl_url,
            "-o", download_directory
        ]
    if "hotstar.com" in youtube_dl_url:
        command_to_exec.append("--proxy")
        command_to_exec.append(Config.HTTP_PROXY)
    logger.info(command_to_exec)
    try:
        t_response = subprocess.check_output(
            command_to_exec, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        logger.info("Status : FAIL", exc.returncode, exc.output)
        bot.edit_message_text(
            chat_id=update.from_user.id,
            message_id=update.id,
            text=exc.output.decode("UTF-8"),
            # reply_markup=reply_markup
        )
    else:
        logger.info(t_response)
        bot.edit_message_text(
            text=Translation.UPLOAD_START,
            chat_id=update.from_user.id,
            message_id=update.id
        )
        file_size = os.stat(download_directory).st_size
        if file_size > Config.TG_MAX_FILE_SIZE:
            url = "https://transfer.sh/{}".format(download_directory)
            max_days = "5"
            command_to_exec = [
                "curl",
                # "-H", 'Max-Downloads: 1',
                "-H", 'Max-Days: 5',  # + max_days + '',
                "--upload-file", download_directory,
                url
            ]
            bot.edit_message_text(
                text=Translation.UPLOAD_START,
                chat_id=update.from_user.id,
                message_id=a.id
            )
            try:
                logger.info(command_to_exec)
                t_response = subprocess.check_output(
                    command_to_exec, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as exc:
                logger.info("Status : FAIL", exc.returncode, exc.output)
                bot.edit_message_text(
                    chat_id=update.from_user.id,
                    text=exc.output.decode("UTF-8"),
                    message_id=a.id
                )
            else:
                t_response_arry = t_response.decode(
                    "UTF-8").split("\n")[-1].strip()
                bot.edit_message_text(
                    chat_id=update.from_user.id,
                    text=Translation.AFTER_GET_DL_LINK.format(
                        t_response_arry, max_days),
                    #parse_mode=pyrogram.ParseMode.HTML,
                    message_id=a.id,
                    disable_web_page_preview=True
                )
                try:
                    os.remove(after_download_file_name)
                except:
                    pass
        else:
            # get the correct width, height, and duration for videos greater than 10MB
            # ref: message from @BotSupport
            width = 0
            height = 0
            duration = 0
            metadata = extractMetadata(createParser(download_directory))
            if metadata.has("duration"):
                duration = metadata.get('duration').seconds
            metadata = extractMetadata(createParser(thumb_image_path))
            if metadata.has("width"):
                width = metadata.get("width")
            if metadata.has("height"):
                height = metadata.get("height")
            # get the correct width, height, and duration for videos greater than 10MB
            if os.path.exists(thumb_image_path):
                # resize image
                # ref: https://t.me/PyrogramChat/44663
                # https://stackoverflow.com/a/21669827/4723940
                Image.open(thumb_image_path).convert(
                    "RGB").save(thumb_image_path)
                img = Image.open(thumb_image_path)
                # https://stackoverflow.com/a/37631799/4723940
                new_img = img.resize((90, 90))
                new_img.save(thumb_image_path, "JPEG", optimize=True)
            else:
                thumb_image_path = None
            # try to upload file
            if tg_send_type == "audio":
                bot.send_audio(
                    chat_id=update.from_user.id,
                    audio=download_directory,
                    caption=description,
                    duration=duration,
                    # performer=response_json["uploader"],
                    # title=response_json["title"],
                    # reply_markup=reply_markup,
                    thumb=thumb_image_path,
                    reply_to_message_id=update.id
                )
            elif tg_send_type == "file":
                bot.send_document(
                    chat_id=update.from_user.id,
                    document=download_directory,
                    thumb=thumb_image_path,
                    caption=description,
                    # reply_markup=reply_markup,
                    reply_to_message_id=update.id
                )
            else:
                bot.send_video(
                    chat_id=update.from_user.id,
                    video=download_directory,
                    caption=description,
                    duration=duration,
                    width=width,
                    height=height,
                    supports_streaming=True,
                    # reply_markup=reply_markup,
                    thumb=thumb_image_path,
                    reply_to_message_id=update.id
                )
            try:
                os.remove(download_directory)
                os.remove(thumb_image_path)
            except:
                pass
            bot.edit_message_text(
                text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG,
                chat_id=update.from_user.id,
                message_id=update.id,
                disable_web_page_preview=True
            )
