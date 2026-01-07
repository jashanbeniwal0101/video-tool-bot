import os
import time
import asyncio
import logging
from pathlib import Path
from config import DUMP_ID
from core.ffmpeg_handlers import FFmpegHandler
from core.helpers import (
    Callbacks as cb, 
    button_generator, progress_cancel_button,
    progress_hook as progress_handler, premium_client,
    progress_handler_for_4gb, start_premium_client,
    progress_hook, PROGRESS, format_progress_bar
    )
from pyrogram import Client, filters, utils
from pyrogram.enums import ListenerTypes
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.errors import ListenerStopped


from core.wmanager import TaskManager

task_manager = TaskManager()
TIMEOUT = 180


async def cancel_job(client: Client, query: CallbackQuery):
    data = query.data.split(':')
    logging.info(data)
    job_id = data[1]
    task_manager.cancel(job_id)
    id = query.from_user.id
    await query.message.edit('**✅Task Cancelled**')
    await asyncio.sleep(10)
    await query.message.delete()


async def extract_thumb_job(client: Client, query: CallbackQuery):
    try:
        logging.info(f"Extracting thumbnail for {query.from_user.id}")
        media = query.message.reply_to_message.video or query.message.reply_to_message.document or query.message.reply_to_message.audio
        if not media or not media.thumbs:
            return await query.answer("No thumbnail? Seriously? Did you even try?", show_alert=True)
            
        thumb = media.thumbs[-1]
        await query.message.edit('**Extracting your precious thumbnail**... try not to die of suspense')
        image_path = await client.download_media(thumb)
        await query.message.reply_to_message.reply_photo(image_path)
        await query.message.edit('__Ta-da!__ Your thumbnail is here. Was it worth ?')
        await asyncio.sleep(10)
        await query.message.delete()
    except Exception as e:
        logging.error(f"Thumbnail extraction failed: {e}")
        await query.answer("Oopsie! Thumbnail extraction went kaboom. Maybe try a better file next time?", show_alert=True)


async def remove_forward_tag_job(client: Client, query: CallbackQuery):
        await query.message.edit('Poof! Forward tag vanished. Like magic, but with code.')
        await query.message.reply_to_message.forward(
            query.from_user.id,
            drop_author=True
        )
        await query.message.delete()


async def forward_job(client: Client, query: CallbackQuery):
        try:
            get_id = await client.ask(
                query.from_user.id,
                'Send the username or id of the chat',
                timeout=60
                )
            #get_id = await client.listen(
            #    filters.text,
            #    timeout=60
            #)
            id = get_id.text
            type_ = utils.get_peer_type(id)
            if not type_ in ['chat', 'channel', 'user']:
                return await query.message.reply('That chat ID is about as real as unicorns. Try again?')
            await query.message.edit('Checking Access...')
            await asyncio.sleep(2)
            test_m = await client.send_message(
                id,
                'Checking access'
            )
            await test_m.delete()
            await query.message.edit('Trying to send')
            await asyncio.sleep(2)
            await query.message.reply_to_message.forward(
                chat_id=id,
                drop_author=True
            )
            await query.message.delete()
            await query.message.reply('**Message forwarded!** Now go bother someone else.')
        except Exception as e:
            await query.message.reply('Can\'t forward this. Maybe the chat hates bots as much as I hate errors?')
            #await client.send_message(f'Got an error : {e}')
            logging.info(e)
            await asyncio.sleep(10)
            


async def edit_button_job(client: Client, query: CallbackQuery, id):
    await query.answer("Oh wow, you want to edit buttons? How original...", show_alert=True)


async def edit_caption_job(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    cap = await client.ask(
        user_id,
        '**Send me the Caption**\n\nUse `/help caption` to list the availaible options'
    )
    await cap.sent_message.delete()
    await cap.delete()
    await query.message.reply_to_message.copy(
        chat_id=user_id,
        caption=cap.text,
        caption_entities=cap.caption_entities or cap.entities
    )
    await query.message.delete()


async def trim_video_job(client: Client, query: CallbackQuery, id):
    await query.answer("Trim video? Sure, let me just grab my digital scissors...", show_alert=True)


async def extract_stream_job(client: Client, query: CallbackQuery, id):
    file = ''


async def rename_file_job(client: Client, query: CallbackQuery, task_id):
    file = query.message.reply_to_message.document or query.message.reply_to_message.video or query.message.reply_to_message.audio
    user_id = query.from_user.id
    query_id = query.id
    init_r_text = f'**🎥📽Video Renamer:** Rename words limit is not given in the option, May be occur Errors for long name,'
    init_r_text += f'\nFor Better knowledge search TG Limits on google'
    await query.message.edit('🚀 Initializing the Process...')
    ype_btn = [
        [InlineKeyboardButton('Rename', callback_data='as_vid')],
        [
            InlineKeyboardButton('Rename as Video', callback_data='as_vid'),
            InlineKeyboardButton('Rename as File', callback_data='as_doc'),
        ]
    ]
    await query.message.edit(
       text = init_r_text,

    )
    raw_file_name = await client.ask(
        chat_id=user_id,
        text=f"Please send the new file name you'd like to use. \n<i>⏳ Timeout: 3 min</i>",
        filters=filters.text,
        timeout=TIMEOUT
    )
    

    listen_for_type: CallbackQuery = client.listen(
        listener_type=ListenerTypes.CALLBACK_QUERY,
        user_id=user_id,
        timeout=TIMEOUT
    )
    send_type = 'as_vid' if listen_for_type.data == 'as_vid' else 'as_doc'
    await raw_file_name.sent_message.delete()
    ask_type = 'as_vid'
    print(ask_type)
    file_name_text = raw_file_name.text
    file_name = file_name_text if (file_name_text).endswith(('mp4', 'mkv')) else f'{file_name_text}.mkv'
    caption_entities_ = raw_file_name.entities
    start_time = time.time()
    df_name =f'downloads/downloaded_file_{user_id}_{query_id}.mkv'
    await query.message.edit(
        text=f'**Your Media file is Downloading....**',
        reply_markup=progress_cancel_button()
        )

    logging.info(f'{'_'*20}')
    logging.info(query.message.reply_to_message.document)
    logging.info(f'{'_'*20}')
    input_file = await client.download_media(
        file, 
        file_name=df_name,
        progress=progress_hook,
        progress_args=(file_name, start_time, task_id , 'Downloading')
        )
    input_file = df_name
    print(input_file)
    ffm = FFmpegHandler()
    thumbnail_path = await ffm.extract_thumb(input_file, f'downloads/downloaded_thumb_file_{user_id}_{query_id}.jpg')
    print(Path(input_file).as_posix())
    fph = Path(input_file).rename(file_name)
    u_start_time = time.time()
    
    
    is_big = os.path.getsize(file_name) > 2 * 1024 * 1024 * 1024

    if is_big:
        await start_premium_client()
        bot = client
        client = premium_client
        await premium_client.get_chat(int(DUMP_ID))
        to_id = DUMP_ID
        prog_args = (bot, query.message, file_name, u_start_time, 'Uploading')       
    else:
        to_id = user_id
        prog_args = (file_name, u_start_time, task_id, 'Uploading')
    if ask_type == 'as_vid':
        upd = await client.send_video(
            to_id,
            fph.as_posix(),
            caption=file_name_text,
            caption_entities=caption_entities_,
            file_name=file_name_text,
            thumb=thumbnail_path,
            progress=progress_handler if not is_big else progress_handler_for_4gb,
            progress_args=prog_args,

        )
    else:
        upd = await client.send_document(
            to_id,
            fph.as_posix(),
            caption=file_name_text,
            thumb=thumbnail_path,
            caption_entities=caption_entities_,
            progress=progress_handler if not is_big else progress_handler_for_4gb,
            progress_args=prog_args
        )
    await query.message.delete()
    if is_big:
        await upd.copy(user_id)
    os.remove(fph)
    os.remove(thumbnail_path)

async def gen_screenshot_job(client: Client, query: CallbackQuery):
    pass


async def merge_video_job(client: Client, query: CallbackQuery):
    await query.answer("Merging videos like a digital film editor... minus the talent", show_alert=True)


async def mediainfo_job(client: Client, query: CallbackQuery):
    message = query.message
    file = query.message.reply_to_message.document or query.message.reply_to_message.video or query.message.reply_to_message.audio
    
    if not file:
        await query.message.edit("No file found to process.")
        return
    
    start_time = time.time()
    
    try:
        file_path = await client.download_media(
            file,
            progress=progress_handler,
            progress_args=(query.message, file.file_name, start_time, 'Downloading')
        )
        await query.message.edit('Generating Mediainfo...')
        
        ffm = FFmpegHandler()
        mediadata = await ffm.mediainfo(file_path)
        
        await query.message.edit(mediadata)
        
    except Exception as e:
        logging.error(f"Error in mediainfo_job: {e}")
        await query.message.edit("Failed to generate mediainfo. Please try again later.")
    finally:
    
        pass

async def progress_job(client: Client, query: CallbackQuery):
    job_id = int(query.data.split(":")[1])
    info = PROGRESS.get(job_id)
    now = time.time()
    elapsed = now - float(info["start_time"])
    text = format_progress_bar(
        info["file_name"],
        info["done"],
        info["total"],
        elapsed,
        info["status"]
    )
    await query.answer(
        text, 
        show_alert=True
    )
    



