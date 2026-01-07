import os
import time
import asyncio
import logging
from pathlib import Path
from config import DUMP_ID
from core.ffmpeg_handlers import FFmpegHandler
from core.handlers import (
    forward_job, cancel_job,
    mediainfo_job, trim_video_job, 
    edit_button_job, merge_video_job, rename_file_job, progress_job,
    edit_caption_job, extract_thumb_job, extract_stream_job,
    gen_screenshot_job, remove_forward_tag_job, cancel_job
)
from core.helpers import Callbacks as cb, progress_hook as progress_handler, progress_handler_for_4gb, start_premium_client, premium_client
from pyrogram import Client, filters, utils
from pyrogram.enums import ListenerTypes
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.errors import ListenerStopped


from core.wmanager import TaskManager
task_manager = TaskManager()


async def close_handler(client: Client, query: CallbackQuery):
    await query.message.delete()


async def cancel_handler(client: Client, query: CallbackQuery):
    try:
        await cancel_job(client, query)
    except Exception as e:
        logging.info(e)

async def work_on_progress(client: Client, query: CallbackQuery):
    if query.data == 'ca':
        await query.answer(
            'Yeah yeah, I\'m working on it... impatient much?',
            show_alert=True
        )

async def extract_thumb_handler(client: Client, query: CallbackQuery):
    try:
        await extract_thumb_job(client, query)
    except Exception as e:
        logging.info(e)


async def remove_forward_tag(client: Client, query: CallbackQuery):
    try:
        await remove_forward_tag(client, query)
    except Exception as e:
        logging.info(e)


async def forward_handler(client: Client, query: CallbackQuery):
        try:
            await forward_job(client, query)
        except Exception as e:
            logging.info(e)

      
async def edit_button_handler(client: Client, query: CallbackQuery):
    await query.answer("Oh wow, you want to edit buttons? How original...", show_alert=True)


async def edit_caption_handler(client: Client, query: CallbackQuery):
    try:
        await edit_caption_job(client, query)
    except Exception as e:
        logging.info(e)

async def trim_video_handler(client: Client, query: CallbackQuery):
    await query.answer("Trim video? Sure, let me just grab my digital scissors...", show_alert=True)


async def extract_stream_handler(client: Client, query: CallbackQuery):
    file = ''


async def rename_file_handler(client: Client, query: CallbackQuery):
    try:
        await task_manager.enqueue(
            rename_file_job,
            client, query
        )
    except Exception as e:
        logging.info(e)


async def gen_screenshot_handler(client: Client, query: CallbackQuery):
    pass


async def merge_video_handler(client: Client, query: CallbackQuery):
    await query.answer("Merging videos like a digital film editor... minus the talent", show_alert=True)


async def mediainfo_handler(client: Client, query: CallbackQuery):
    message = query.message
    file = query.message.reply_to_message.document or query.message.reply_to_message.video or query.message.reply_to_message.audio
    #TODO
    start_time = time.time()
    
    file = await client.download_media(
        file,
        progress=progress_handler,
        progress_args=(query.message, file.file_name, start_time, 'Downloading')
        )
    await query.message.edit(f'Generating Mediainfo')
    ffm = FFmpegHandler()
    mediadata = await ffm.mediainfo(file)
    await query.message.edit(mediadata)


async def progress_callback(client: Client, query: CallbackQuery):
    try:
        await progress_job(client, query)
    except Exception as e:
        logging.info(e)

CALLBACK_MAP = {
    cb.CANCEL:              cancel_handler,            # Handles cancellation
    cb.CLOSE:               close_handler,             # Handles closing the query
    cb.EDIT_CAPTION:        edit_caption_handler,      # Handles caption editing
    

    cb.EXTRACT_STREAM:      extract_stream_handler,    # Handles stream extraction
    
    cb.EXTRACT_THUMB:       extract_thumb_handler,     # Handles thumbnail extraction
    cb.FORWARD:             forward_handler,           # Handles forwarding
    
    cb.GEN_SCREENSHOT:      gen_screenshot_handler,    # Handles screenshot generation
    cb.MEDIAINFO:           mediainfo_handler,         # Handles media info retrieval
    cb.MERGE_VIDEO:         merge_video_handler,       # Handles video merging
    
    cb.REMOVE_FORWARD_TAG:  remove_forward_tag,        # Handles removal of forward tags
    
    # 🚧 Work in progress
    cb.RENAME_FILE:         rename_file_handler,       # Handles file renaming
    cb.TRIM_VIDEO:          trim_video_handler,        # Handles video trimming
    cb.CONVERT_FILE:        work_on_progress,          # File conversion not implemented
    cb.EDIT_METADATA:       work_on_progress,          # Metadata editing not implemented
    cb.GEN_SAMPLE_VIDEO:    work_on_progress,          # Sample video generation not implemented
    cb.REMOVE_STREAM:       work_on_progress           # Stream removal not implemented
}


@Client.on_callback_query()
async def callback_handlers(client: Client, query: CallbackQuery):
    data = query.data
    if data.startswith('cancel'):
        await cancel_handler(client, query)
        return
    elif data.startswith('progress'):
        await progress_callback(client, query)
        return
    handler = CALLBACK_MAP.get(data)
    if handler:
        await handler(client, query)


