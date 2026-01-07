import logging
import psutil
import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from core.handlers import task_manager


@Client.on_message(filters.command(['start']) & filters.private)
async def echo_(client: Client, message: Message):
    """Handle /start command - welcome message"""
    txt = """
I'm MediaBot—your all-in-one media assistant. 

Send over any video, audio file, document or URL, and I'll trim, merge, convert formats, edit tags, extract or remove audio/subtitles, archive and more.

Want to customize? Hit /settings to rename uploads, set quality, default trim times or save presets.

Ready to roll? Drop your file let's work some media magic! ✨
    """
    await message.reply(txt)


@Client.on_message(filters.command(['help']) & filters.private)
async def help_command(client: Client, message: Message):
    #TODO
    help_text = """
📚 *Available Commands*:

/start - Welcome message and bot introduction
/help - Show this help message  
/settings - Configure your preferences
/status - Show bot system status

🎥 *Media Tools*:
- Send any video/file to access editing tools
- Thumbnail extraction
- Video trimming/merging
- Format conversion
- Metadata editing
"""
    await message.reply(help_text)


@Client.on_message(filters.command(['empty']) & filters.private)
async def empty_(client: Client, message: Message):
    logging.info(message.text)


@Client.on_message(filters.command(['settings']) & filters.private)
async def settings_command(client: Client, message: Message):
     #TODO
    await message.reply(
        "⚙️ *Settings Menu*\n\n"
        "1. Default video quality\n"
        "2. Auto-delete processed files\n"
        "3. Notification preferences\n"
        "Reply with the number to configure"
    )


@Client.on_message(filters.command(['status']) & filters.private)
async def status_command(client: Client, message: Message):
    uptime = datetime.datetime.now() - client.uptime
    await message.reply(
        f"🤖 *Bot Status*\n\n"
        f"• Uptime: {uptime}\n"
        f"• CPU: {psutil.cpu_percent()}%\n"
        f"• Memory: {psutil.virtual_memory().percent}%\n"
        f"• Disk: {psutil.disk_usage('/').percent}%"
    )

@Client.on_message(filters.command(['tstatus']) & filters.private)
async def task_status(client: Client, message: Message):
    try:
        logging.info(message)
        id = message.command[0]
        t = task_manager.status(id)
        await message.reply(f'Task Status:\n\n{t}')
    except Exception as e:
        await message.reply(f'failed to get\n\n{e}')
        logging.info(e)
