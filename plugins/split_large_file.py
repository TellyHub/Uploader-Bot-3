# @Tellybots
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


import asyncio
import os
import time
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from plugins.config import Config

async def split_large_files(input_file):
    working_directory = os.path.dirname(os.path.abspath(input_file))
    new_working_directory = os.path.join(
        working_directory,
        str(time.time())
    )
    # create download directory, if not exist
    if not os.path.isdir(new_working_directory):
        os.makedirs(new_working_directory)
    # if input_file.upper().endswith(("MKV", "MP4", "WEBM", "MP3", "M4A", "FLAC", "WAV")):
    """The below logic is DERPed, so removing temporarily
    """
    if (
        Config.SP_LIT_ALGO_RITH_M.lower() != "rar" and
        input_file.upper().endswith(("MKV", "MP4", "WEBM"))
    ):
        # handle video / audio files here
        metadata = extractMetadata(createParser(input_file))
        total_duration = 0
        if metadata.has("duration"):
            total_duration = metadata.get('duration').seconds
        # proprietary logic to get the seconds to trim (at)
        logger.info(total_duration)
        total_file_size = os.path.getsize(input_file)
        logger.info(total_file_size)
        minimum_duration = (
            total_duration / total_file_size
        ) * (
            Config.MAX_TG_SPLIT_FILE_SIZE
        )
        # casting to int cuz float Time Stamp can cause errors
        minimum_duration = int(minimum_duration)
        
        logger.info(minimum_duration)
        # END: proprietary
        start_time = 0
        end_time = minimum_duration
        base_name = os.path.basename(input_file)
        input_extension = base_name.split(".")[-1]
        logger.info(input_extension)
        
        i = 0
        flag = False
        
        while end_time <= total_duration:
            logger.info(i)
            # file name generate
            parted_file_name = "{}_PART_{}.{}".format(str(base_name),str(i).zfill(5),str(input_extension))

            output_file = os.path.join(new_working_directory, parted_file_name)
            logger.info(output_file)
            logger.info(await cult_small_video(
                input_file,
                output_file,
                str(start_time),
                str(end_time)
            ))
            logger.info(
                f"Start time {start_time}, End time {end_time}, Itr {i}"
            )

            # adding offset of 3 seconds to ensure smooth playback 
            start_time = end_time - 3
            end_time = end_time + minimum_duration
            i = i + 1

            if (end_time > total_duration) and not flag:
                 end_time = total_duration
                 flag = True
            elif flag:
                break

    elif Config.SP_LIT_ALGO_RITH_M.lower() == "hjs":
        # handle normal files here
        o_d_t = os.path.join(
            new_working_directory,
            os.path.basename(input_file)
        )
        o_d_t = o_d_t + "."
        file_genertor_command = [
            "split",
            "--numeric-suffixes=1",
            "--suffix-length=5",
            f"--bytes={Config.MAX_TG_SPLIT_FILE_SIZE}",
            input_file,
            o_d_t
        ]
        await run_comman_d(file_genertor_command)
        
    elif Config.SP_LIT_ALGO_RITH_M.lower() == "rar":
        o_d_t = os.path.join(
            new_working_directory,
            os.path.basename(input_file),
        )
        logger.info(o_d_t)
        file_genertor_command = [
            "rar",
            "a",
            f"-v{Config.MAX_TG_SPLIT_FILE_SIZE}b",
            "-m0",
            o_d_t,
            input_file
        ]
        await run_comman_d(file_genertor_command)

    return new_working_directory
