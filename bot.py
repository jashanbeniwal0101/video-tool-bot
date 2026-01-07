import sys
from aiohttp import web
from datetime import datetime
from plugins.web_routes import web_server
from pyrogram import Client, utils 


utils.MIN_CHAT_ID = -999999999999
utils.MIN_CHANNEL_ID = -100999999999999

from config import (
    ADMINS, 
    API_HASH, 
    APP_ID, 
    LOGGER, 
    BOT_TOKEN, 
    BOT_WORKERS, 
    FORCE_SUB_CHANNEL,
    DUMP_ID, 
    PORT, 
    OWNER_ID)


def get_peer_type_new(peer_id: int) -> str:
    peer_id_str = str(peer_id)
    if not peer_id_str.startswith("-"):
        return "user"
    elif peer_id_str.startswith("-100"):
        return "channel"
    else:
        return "chat"
utils.get_peer_type = get_peer_type_new



class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=BOT_WORKERS,
            bot_token=BOT_TOKEN,
            sleep_threshold=10
        )
        self.LOGGER = LOGGER
        

    async def start(self, *args, **kwargs):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()
        self.username = usr_bot_me.username

        if FORCE_SUB_CHANNEL:
            try:
                link = (await self.get_chat(FORCE_SUB_CHANNEL)).invite_link # type: ignore
                if not link:
                    await self.export_chat_invite_link(FORCE_SUB_CHANNEL) # type: ignore
                    link = (await self.get_chat(FORCE_SUB_CHANNEL)).invite_link # type: ignore
                self.invitelink = link
            except Exception as a:
                self.LOGGER(__name__).warning(a)
                self.LOGGER(__name__).warning("Bot can't Export Invite link from Force Sub Channel!")
                self.LOGGER(__name__).warning(f"Please Double check the FORCE_SUB_CHANNEL value and Make sure Bot is Admin in channel with Invite Users via Link Permission, Current Force Sub Channel Value: {FORCE_SUB_CHANNEL}")
                sys.exit()
        if DUMP_ID:
            try:
                db_channel = await self.get_chat(DUMP_ID)
                self.db_channel = db_channel
                test = await self.send_message(chat_id = db_channel.id, text = "Test Message") # type: ignore
                await test.delete()
            except Exception as e:
                self.LOGGER(__name__).warning(e)
                self.LOGGER(__name__).warning(f"Make Sure bot is Admin in DB Channel, and Double check the CHANNEL_ID Value, Current Value {DUMP_ID}")
                sys.exit()
        
        await self.send_message(
            chat_id=OWNER_ID,
            text="Bot has started! 😉"
        )
        self.LOGGER(__name__).info(f"Bot Running..!")
        
        
        
        #web-response
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):        
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")
