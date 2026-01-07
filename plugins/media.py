import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from core.helpers import button_generator


@Client.on_message(filters.private & (filters.video | filters.document))
async def media_handler(client: Client, message: Message):

    media = message.video or message.document
    media_type = "Video" if message.video else "Document"

    txt = (
        f"📁 **{media_type} Received!**\n\n"
        f"📄 **File Name:** `{media.file_name}`\n"
        f"📦 **Size:** `{round(media.file_size / 1024 / 1024, 2)} MB`\n\n"
        "👇 Choose what you want to do:"
    )

    btns = button_generator()

    await message.reply(
        text=txt,
        reply_markup=btns,
        quote=True
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
        "🖼️ **Image Received!**\n\n"
        + "\n".join(f"**{k}** : `{v}`" for k, v in info.items())
    )
