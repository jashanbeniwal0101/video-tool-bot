import time
import logging
from enum import Enum
from typing import Dict, Any
from pyrogram import Client, filters, utils
from pyrogram.errors import MessageNotModified, MessageIdInvalid, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message


MIN_EDIT_INTERVAL = 1.8
last_edit_time: dict[int, float] = {}
PROGRESS: Dict[int, Dict[str, Any]] = {} 

strpec = ''
premium_client = Client(
    'g_p', 
    session_string=strpec,
    device_model='cpython_vp23',
    client_platform='linux_cloud2',
    no_updates=True
    )

async def start_premium_client():
    try:
        logging.critical('Starting the premium client')
        await premium_client.start()
    except ConnectionError as e:
        logging.critical(f'Error Starting premium client: {e}')
    except Exception as e:
        logging.critical(f"Error PrC (start): {e}")

    try:
        logging.critical('Connecting the premium client')
        await premium_client.connect()
    except ConnectionError as e:
        logging.critical(f'Error Connecting premium client: {e}')
    except Exception as e:
        logging.critical(f"Error PrC (connect): {e}")

class Callbacks:
    CANCEL = "cancel"
    CLOSE = "close"
    CONVERT_FILE = "convert_file"
    EDIT_BUTTON = "edit_button"
    EDIT_CAPTION = "edit_caption"
    EDIT_METADATA = "edit_metadata"
    EXTRACT_STREAM = "extract_stream"
    EXTRACT_THUMB = "extract_thumb"
    FORWARD = "forward_it"
    GEN_SAMPLE_VIDEO = "gen_sample_video"
    GEN_SCREENSHOT = "gen_screenshot"
    MEDIAINFO = "mediainfo"
    MERGE_VIDEO = "merge_video"
    REMOVE_FORWARD_TAG = "remove_forward_tag"
    REMOVE_STREAM = "remove_stream"
    RENAME_FILE = "rename_file"
    TRIM_VIDEO = "trim_video"

    
def button_generator():    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="🖼️ Extract Thumbnail", callback_data=Callbacks.EXTRACT_THUMB)
        ],
        [
            InlineKeyboardButton(text="✏️ Caption Editor", callback_data=Callbacks.EDIT_CAPTION),
        ],
        [
            InlineKeyboardButton(text="📝 Edit Metadata", callback_data=Callbacks.EDIT_METADATA),
            InlineKeyboardButton(text="🔃 Forwarder", callback_data=Callbacks.FORWARD)
        ],
        [
            InlineKeyboardButton(text="📺 Stream Remover", callback_data=Callbacks.REMOVE_STREAM),
            InlineKeyboardButton(text="📺 Stream Extractor", callback_data=Callbacks.EXTRACT_STREAM)
        ],        
        [
            InlineKeyboardButton(text="✂️ Trim Video", callback_data=Callbacks.TRIM_VIDEO),
            InlineKeyboardButton(text="➕ Merge Video", callback_data=Callbacks.MERGE_VIDEO)
        ],
        [
            InlineKeyboardButton(text="🏷️ Rename Video", callback_data=Callbacks.RENAME_FILE),
            InlineKeyboardButton(text="🔄 Convert Video", callback_data=Callbacks.CONVERT_FILE)
        ],
        [
            InlineKeyboardButton(text="📸 Screenshot", callback_data=Callbacks.GEN_SCREENSHOT),
            InlineKeyboardButton(text="🎞️ Generate Sample", callback_data=Callbacks.GEN_SAMPLE_VIDEO)
        ],
        [
            InlineKeyboardButton(text="Extract Mediainfo", callback_data=Callbacks.MEDIAINFO)
        ],
        [
            InlineKeyboardButton(text="Remove 'Forward From' tag", callback_data=Callbacks.REMOVE_FORWARD_TAG)
        ],
        [
            InlineKeyboardButton(text="Cancel Task", callback_data=Callbacks.CANCEL)
        ]    
    ])
    return buttons

def progress_cancel_button() -> InlineKeyboardMarkup:
    btn = [
            [
            InlineKeyboardButton(text="Progress ⚡", callback_data=f'progress:{task_id}'),
            InlineKeyboardButton(text="Cancel ❌", callback_data=f'cancel:{task_id}'),
            ]
            ]
    return InlineKeyboardMarkup(btn)

def format_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

def format_size(size):
    size = int(size)
    if size < 1024:
        return f"{size} B"
    elif size < 1024 ** 2:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 ** 3:
        return f"{size / 1024 ** 2:.2f} MB"
    else:
        return f"{size / 1024 ** 3:.2f} GB"

async def progress_handler_for_4gb(
        current: int, 
        total: int, 
        client: Client,
        message: Message, 
        filename: str, 
        start_time: float = 0, 
        title: str = "", 
        bar_length: int = 20
    ):

    now = time.time()
    chat_id = message.chat.id

    last = last_edit_time.get(chat_id, 0.0)
    if now - last < MIN_EDIT_INTERVAL:
        if not total == current:
            return

    last_edit_time[chat_id] = now

    elapsed = now - start_time
    text = format_progress_bar(
        filename=filename,
        done=current,
        total_size=total,
        elapsed=int(elapsed),
        status=title
    )

    try:
        await client.edit_message_text(
            chat_id=message.from_user.id,
            text=text,
            message_id=message.id
        )
    except MessageNotModified:
        return
    except FloodWait as e:
        retry_after = e.retry_after
        logger(__name__).info(f"FloodWait of {retry_after}s for {filename}")
        last_edit_time[chat_id] = time.time() + retry_after
        await asyncio.sleep(retry_after)


def progress_hook(
    current: int,
    total: int,
    file_name: str,
    start_time: float,
    job_id: int,
    status: str,
    **kwargs
):
    PROGRESS[job_id] = {
        "status": status,
        "file_name": file_name,
        "start_time": start_time,
        "total": total,
        "done": current,
    }


def format_progress_bar(filename: str, done: float, total_size: float, elapsed: float, status: str) -> str:
    percentage = (done / total_size) * 100 if total_size else 0.0
    speed = done / elapsed if elapsed > 0 else 0.0
    remaining = max(total_size - done, 0.0)
    eta_seconds = remaining / speed if speed > 0 else 0.0
    bar_length = 10
    filled_length = int(bar_length * percentage / 100)
    bar = '■' * filled_length + '□' * (bar_length - filled_length)
    return (
        f"{status}.... media\n\n"
        f"[{bar}] {percentage:5.1f}%\n\n"
        f"➩ {format_size(done)} of {format_size(total_size)}\n\n"
        f"➩ Speed: {format_size(speed)}/s\n\n"
        f"➩ Time Left: {format_time(eta_seconds)}\n"
    )

