#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K | @Tellybots

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import asyncio
import json
import math
import os
import shutil
import time
import subprocess
from datetime import datetime, timedelta
from pyrogram import enums 
from plugins.config import Config
from plugins.script import Translation
from plugins.thumbnail import *
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from pyrogram.types import InputMediaPhoto
from plugins.functions.display_progress import progress_for_pyrogram, humanbytes
from plugins.database.database import db
from PIL import Image
from plugins.functions.ran_text import random_char

async def youtube_dl_call_back(bot, update):
    cb_data = update.data
    # youtube_dl extractors
    tg_send_type, youtube_dl_format, youtube_dl_ext, ranom = cb_data.split("|")
    print(cb_data)
    random1 = random_char(5)
    
    save_ytdl_json_path = Config.DOWNLOAD_LOCATION + \
        "/" + str(update.from_user.id) + f'{ranom}' + ".json"
    try:
        with open(save_ytdl_json_path, "r", encoding="utf8") as f:
            response_json = json.load(f)
    except (FileNotFoundError) as e:
        await update.message.delete()
        return False
    youtube_dl_url = update.message.reply_to_message.text
    custom_file_name = str(response_json.get("title")) + \
        "_" + youtube_dl_format + "." + youtube_dl_ext
    youtube_dl_username = None
    youtube_dl_password = None
    if "|" in youtube_dl_url:
        url_parts = youtube_dl_url.split("|")
        if len(url_parts) == 2:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
        elif len(url_parts) == 4:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
            youtube_dl_username = url_parts[2]
            youtube_dl_password = url_parts[3]
        else:
            for entity in update.message.reply_to_message.entities:
                if entity.type == "text_link":
                    youtube_dl_url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    youtube_dl_url = youtube_dl_url[o:o + l]
        if youtube_dl_url is not None:
            youtube_dl_url = youtube_dl_url.strip()
        if custom_file_name is not None:
            custom_file_name = custom_file_name.strip()
        # https://stackoverflow.com/a/761825/4723940
        if youtube_dl_username is not None:
            youtube_dl_username = youtube_dl_username.strip()
        if youtube_dl_password is not None:
            youtube_dl_password = youtube_dl_password.strip()
        logger.info(youtube_dl_url)
        logger.info(custom_file_name)
    else:
        for entity in update.message.reply_to_message.entities:
            if entity.type == "text_link":
                youtube_dl_url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                youtube_dl_url = youtube_dl_url[o:o + l]
    await update.message.edit_caption(
        caption=Translation.DOWNLOAD_START,
        parse_mode=enums.ParseMode.HTML
    )
    description = Translation.CUSTOM_CAPTION_UL_FILE
    if "fulltitle" in response_json:
        description = response_json["fulltitle"][0:1021]
        # escape Markdown and special characters
    tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + f'{random1}'
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)
    download_directory = tmp_directory_for_each_user + "/" + custom_file_name
    command_to_exec = []
    command_to_exec = []
    with open("backup.json", "r", encoding="utf8") as f:
                  b_json = json.load(f)
    if update.from_user.id in Config.ONE_BY_ONE:
      for users in b_json["users"]:
        user = users.get("user_id")
        exp_req = users.get("exp_req")
        if int(update.from_user.id) == int(user):
          if datetime.strptime(exp_req, '%Y-%m-%d %H:%M:%S.%f') > datetime.now():
            rem = datetime.strptime(exp_req, '%Y-%m-%d %H:%M:%S.%f') - datetime.now()
            await update.message.edit_text("😴 Please wait {} for next process.".format(datetime.strptime(str(rem), '%H:%M:%S.%f').strftime('%H Hrs %M Mins %S Sec')))
            return
    Config.ONE_BY_ONE.append(update.from_user.id)
    if not update.from_user.id in Config.TODAY_USERS:
       Config.TODAY_USERS.append(update.from_user.id)
       exp_date = datetime.now()
       exp_req = exp_date + timedelta(minutes=int(Config.TIME_GAP))
       fir = 0
       b_json["users"].append({
         "user_id": "{}".format(update.from_user.id),
         "total_req": "{}".format(fir),
         "exp_req": "{}".format(exp_req)
       })
       with open("backup.json", "w", encoding="utf8") as outfile:
               json.dump(b_json, outfile, ensure_ascii=False)
    user_count = 0
    for users in b_json["users"]:
      user = users.get("user_id")
      total_req = users.get("total_req")
      user_count = user_count + 1
      #if int(update.from_user.id) == int(user):
      # if int(total_req) > 3:
      #    await update.reply_text("😴 You reached per day limit. send /me to know renew time.")
      #    return
    b_json["users"].pop(user_count - 1)
    b_json["users"].append({
         "user_id": "{}".format(update.from_user.id),
         "total_req": "{}".format(int(total_req) + 1),
         "exp_req": "{}".format(datetime.now() + timedelta(minutes=int(Config.TIME_GAP)))
    })
    with open("backup.json", "w", encoding="utf8") as outfile:
          json.dump(b_json, outfile, ensure_ascii=False)
    if tg_send_type == "audio":
        command_to_exec = [
            "yt-dlp",
            "-c",
            "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
            "--prefer-ffmpeg",
            "--extract-audio",
            "--audio-format", youtube_dl_ext,
            "--audio-quality", youtube_dl_format,
            youtube_dl_url,
            "-o", download_directory
        
        ]
    else:

        command_to_exec = [
            "yt-dlp",
            "-c",
            "--geo-bypass",
            "--clean-info-json",
            "--ignore-no-formats-error",
            "--embed-subs",
            "-f",
            youtube_dl_format,
            "--prefer-ffmpeg",
            youtube_dl_url,
            "-o",
            download_directory,
        ]
 

    if Config.HTTP_PROXY != "":
        command_to_exec.append("--proxy")
        command_to_exec.append(Config.HTTP_PROXY)
    if youtube_dl_username is not None:
        command_to_exec.append("--username")
        command_to_exec.append(youtube_dl_username)
    if youtube_dl_password is not None:
        command_to_exec.append("--password")
        command_to_exec.append(youtube_dl_password)
    command_to_exec.append("--no-warnings")
    # command_to_exec.append("--quiet")
    logger.info(command_to_exec)
    start = datetime.now()
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    # LOGGER.info(e_response)
    # LOGGER.info(t_response)
    ad_string_to_replace = "please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output."
    if e_response and ad_string_to_replace in e_response:
        error_message = e_response.replace(ad_string_to_replace, "")
        await update.message.edit_caption(
            caption=error_message
        )
        return False, None
    if t_response:
        # LOGGER.info(t_response)
        # os.remove(save_ytdl_json_path)
        end_one = datetime.now()
        time_taken_for_download = (end_one -start).seconds
        dir_contents = len(os.listdir(tmp_directory_for_each_user))
        # dir_contents.sort()
        await update.message.edit_caption(
            caption=f"found {dir_contents} files"
        )
        user_id = update.from_user.id
        #
        final_response = await upload_to_tg(
            update.message,
            tmp_directory_for_each_user,
            user_id,
            {},
            True,
            description
        )
        logger.info(final_response)
        #
        try:
            shutil.rmtree(tmp_directory_for_each_user)
        except:
            pass
    # Wait


async def upload_to_tg(
    message,
    local_file_name,
    from_user,
    dict_contatining_uploaded_files,
    edit_media=False,
    custom_caption=None,
    force_doc=False,
    cfn=None
):
    LOGGER.info(local_file_name)
    base_file_name = os.path.basename(local_file_name)
    caption_str = custom_caption
    if not (caption_str or edit_media):
        LOGGER.info("fall-back to default file_name")
        caption_str = "<code>"
        caption_str += base_file_name
        caption_str += "</code>"
    # caption_str += "\n\n"
    # caption_str += "<a href='tg://user?id="
    # caption_str += str(from_user)
    # caption_str += "'>"
    # caption_str += "Here is the file to the link you sent"
    # caption_str += "</a>"
    if os.path.isdir(local_file_name):
        directory_contents = os.listdir(local_file_name)
        directory_contents.sort()
        # number_of_files = len(directory_contents)
        LOGGER.info(directory_contents)
        new_m_esg = message
        if not message.photo:
            new_m_esg = await message.reply_text(
                "Found {} files".format(len(directory_contents)),
                quote=True
                # reply_to_message_id=message.message_id
            )
        for single_file in directory_contents:
            # recursion: will this FAIL somewhere?
            await upload_to_tg(
                new_m_esg,
                os.path.join(local_file_name, single_file),
                from_user,
                dict_contatining_uploaded_files,
                edit_media,
                caption_str,
                force_doc=force_doc,
                cfn=cfn
            )
    else:
        if os.path.getsize(local_file_name) > TG_MAX_FILE_SIZE:
            LOGGER.info("TODO")
            d_f_s = humanbytes(os.path.getsize(local_file_name))
            i_m_s_g = await message.reply_text(
                "Telegram does not support uploading this file.\n"
                f"Detected File Size: {d_f_s} 😡\n"
                "\n🤖 trying to split the files 🌝🌝🌚"
            )
            splitted_dir = await split_large_files(local_file_name)
            totlaa_sleif = os.listdir(splitted_dir)
            totlaa_sleif.sort()
            number_of_files = len(totlaa_sleif)
            LOGGER.info(totlaa_sleif)
            ba_se_file_name = os.path.basename(local_file_name)
            await i_m_s_g.edit_text(
                f"Detected File Size: {d_f_s} 😡\n"
                f"<code>{ba_se_file_name}</code> splitted into {number_of_files} files.\n"
                "trying to upload to Telegram, now ..."
            )
            for le_file in totlaa_sleif:
                # recursion: will this FAIL somewhere?
                await upload_to_tg(
                    message,
                    os.path.join(splitted_dir, le_file),
                    from_user,
                    dict_contatining_uploaded_files,
                    force_doc=force_doc,
                    cfn=cfn
                )
        else:
            sent_m


