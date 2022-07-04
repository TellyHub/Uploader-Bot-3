
# the logging things
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

import asyncio
import os
import time
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from pyrogram.types import (
    InputMediaDocument,
    InputMediaVideo,
    InputMediaAudio
)
from plugins.functions.display_progress import (
    progress_for_pyrogram,
    humanbytes
)
from plugins.functions.help_Nekmo_ffmpeg import *
from plugins.functions.ibk import *
from plugins.functions.copy_similar_file import copy_file
from plugins.config import Config 




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
    logger.info(local_file_name)
    base_file_name = os.path.basename(local_file_name)
    caption_str = custom_caption
    if not (caption_str or edit_media):
        logger.info("fall-back to default file_name")
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
        logger.info(directory_contents)
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
        if os.path.getsize(local_file_name) > Config.TG_MAX_FILE_SIZE:
            logger.info("TODO")
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
            logger.info(totlaa_sleif)
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
            sent_message = await upload_single_file(
                message,
                local_file_name,
                caption_str,
                from_user,
                edit_media,
                force_doc,
                cfn
            )
            if sent_message is not None:
                dict_contatining_uploaded_files[os.path.basename(local_file_name)] = sent_message.message_id
    # await message.delete()
    return dict_contatining_uploaded_files

   


async def upload_single_file(
    message,
    local_file_name,
    caption_str,
    from_user,
    edit_media,
    force_doc=False,
    cfn=None
):
    await asyncio.sleep(Config.EDIT_SLEEP_TIME_OUT)
    sent_message = None
    if cfn:
        os.rename(local_file_name, cfn)
        local_file_name = cfn
    start_time = time.time()
    #
    thumbnail_location = os.path.join(
        Config.DOWNLOAD_LOCATION,
        "thumbnails",
        str(from_user) + ".jpg"
    )
    logger.info(thumbnail_location)
    #
    message_for_progress_display = message
    if not edit_media:
        message_for_progress_display = await message.reply_text(
            "starting upload of {}".format(os.path.basename(local_file_name))
        )

    if local_file_name.upper().endswith((
        "M4V", "MP4", "MOV", "FLV", "WMV", "3GP", "MPEG", "WEBM", "MKV"
    )) and not force_doc:
        metadata = extractMetadata(createParser(local_file_name))
        duration = 0
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
        #
        width = 0
        height = 0

        # send video
        if edit_media and message.photo:
            sent_message = await message.edit_media(
                media=InputMediaVideo(
                    media=local_file_name,
                    #thumb=thumb,
                    caption=caption_str,
                    #parse_mode="html",
                    width=width,
                    height=height,
                    duration=duration,
                    supports_streaming=True
                )
                # quote=True,
            )
        else:
            sent_message = await message.reply_video(
                video=local_file_name,
                # quote=True,
                caption=caption_str,
                #parse_mode="html",
                duration=duration,
                width=width,
                height=height,
                #thumb=thumb,
                supports_streaming=True,
                disable_notification=True,
                # reply_to_message_id=message.id,
                progress=progress_for_pyrogram,
                progress_args=(
                    "trying to upload",
                    message_for_progress_display,
                    start_time
                )
            )
        

    elif local_file_name.upper().endswith((
        "MP3", "M4A", "M4B", "FLAC", "WAV", "AIF", "OGG", "AAC", "DTS"
    )) and not force_doc:
        metadata = extractMetadata(createParser(local_file_name))
        duration = 0
        title = ""
        artist = ""
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
        if metadata.has("title"):
            title = metadata.get("title")
        if metadata.has("artist"):
            artist = metadata.get("artist")

        # send audio
        if edit_media and message.photo:
            sent_message = await message.edit_media(
                media=InputMediaAudio(
                    media=local_file_name,
                    #thumb=thumb,
                    caption=caption_str,
                    #parse_mode="html",
                    duration=duration,
                    performer=artist,
                    title=title
                )
                # quote=True,
            )
        else:
            sent_message = await message.reply_audio(
                audio=local_file_name,
                quote=True,
                caption=caption_str,
                #parse_mode="html",
                duration=duration,
                performer=artist,
                title=title,
                #thumb=thumb,
                disable_notification=True,
                # reply_to_message_id=message.id,
                progress=progress_for_pyrogram,
                progress_args=(
                    "trying to upload",
                    message_for_progress_display,
                    start_time
                )
            )
