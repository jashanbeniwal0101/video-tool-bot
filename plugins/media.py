import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from core.helpers import button_generator


@Client.on_message(filters.private & (filters.video | filters.document))
async def media_handler(client: Client, message: Message):

    media = message.video or message.document
    media_type = "Video" if message.video else "Document"
    btns = button_generator()
    h = await message.reply(
        text=txt,
        quote=True,
        reply_markup=btns
    )

@Client.on_message(filters.private & filters.photo)
async def image_handler(client: Client, message: Message):
    photo = message.photo
    logging.info(photo)
    info = {
        "file_id": photo.file_id,
        "width": photo.width,
        "height": photo.height,
        "file_size": photo.file_size
    }
    await message.reply_text(
        "🖼️ Got your image!\n\n"
        + "\n".join(f"**{k}** : {v}\n" for k, v in info.items())
    )
