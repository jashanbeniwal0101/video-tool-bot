import asyncio
import os, logging
import random
import json
import string
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

class FFmpegError(Exception):
    """Base exception for FFmpeg operations"""
    pass

class FFmpegCancelledError(FFmpegError):
    """Raised when operation is cancelled by user"""
    pass

@dataclass
class FFmpegProgress:
    frame: int
    fps: float
    bitrate: str
    total_size: int
    out_time: str
    progress: float
    speed: float

class FFmpegHandler:
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.temp_dir = "temp_ffmpeg"
        self._cancel_flag = False
        os.makedirs(self.temp_dir, exist_ok=True)

    def cancel(self) -> None:
        self._cancel_flag = True

    async def _execute_ffmpeg(self, args: List[str], progress_callback=None):
        process = await asyncio.create_subprocess_exec(
            self.ffmpeg_path,
            *args,
            stderr=asyncio.subprocess.PIPE
        )
        
        while True:
            if self._cancel_flag:
                process.terminate()
                raise FFmpegCancelledError()
                
            line = await process.stderr.readline()
            if not line:
                break
                
            line = line.decode().strip()
            if "frame=" in line and progress_callback:
                await progress_callback(line)
        
        await process.wait()

    async def _send_progress_update(self, client: Client, message: Message, 
                                 progress_text: str, msg_id: int, 
                                 reply_markup=None):
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg_id,
            text=progress_text,
            reply_markup=reply_markup
        )

    async def execute_with_updates(self, args: List[str], operation: str,
                                 client: Client, message: Message):
        cancel_btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_ffmpeg")]]
        )
        
        msg = await message.reply_text(
            f"⏳ Starting {operation}...",
            reply_markup=cancel_btn
        )
        
        last_update = 0
        async def progress_callback(line: str):
            nonlocal last_update
            now = time.time()
            if now - last_update < 1.0:
                return
            last_update = now
            parts = dict(p.split('=') for p in line.split() if '=' in p)
            progress = int(float(parts.get('time', '0').split(':')[-1]) / 100)
            
            await self._send_progress_update(
                client, message,
                f"⏳ {operation}\nProgress: {progress}%",
                msg.id,
                cancel_btn
            )
        
        try:
            await self._execute_ffmpeg(args, progress_callback)
            await self._send_progress_update(
                client, message,
                f"✅ {operation} completed",
                msg.id
            )
        except FFmpegCancelledError:
            await self._send_progress_update(
                client, message,
                "❌ Operation cancelled",
                msg.id
            )
            raise
        except Exception as e:
            await self._send_progress_update(
                client, message,
                f"⚠️ Error: {str(e)}",
                msg.id
            )
            raise

    async def trim(self, client: Client, message: Message,
                 input_path: str, output_path: str,
                 start: str, end: str):
        args = [
            "-y", "-ss", start, "-to", end,
            "-i", input_path, "-c", "copy", output_path
        ]
        await self.execute_with_updates(args, "Video trim", client, message)

    async def merge(self, client: Client, message: Message,
                  inputs: List[str], output_path: str):
        list_file = self._get_temp_path(".txt")
        with open(list_file, "w") as f:
            f.write("\n".join(f"file '{f}'" for f in inputs))
        
        args = [
            "-y", "-f", "concat", "-safe", "0",
            "-i", list_file, "-c", "copy", output_path
        ]
        await self.execute_with_updates(args, "Video merge", client, message)
        os.remove(list_file)

    async def add_subtitle(self, client: Client, message: Message,
                         video_path: str, sub_path: str,
                         output_path: str, lang: str = "eng"):
        args = [
            "-y", "-i", video_path, "-i", sub_path,
            "-c", "copy", "-c:s", "mov_text",
            "-metadata:s:s:0", f"language={lang}", output_path
        ]
        await self.execute_with_updates(args, "Add subtitle", client, message)

    async def remove_stream(self, client: Client, message: Message,
                          input_path: str, output_path: str,
                          stream_type: str, index: int = 0):
        args = [
            "-y", "-i", input_path,
            "-map", "0", f"-map", f"0:{stream_type}:{index}",
            "-c", "copy", output_path
        ]
        await self.execute_with_updates(args, "Remove stream", client, message)

    async def extract_stream(self, client: Client, message: Message,
                           input_path: str, output_path: str,
                           stream_type: str, index: int = 0):
        args = [
            "-y", "-i", input_path,
            "-map", f"0:{stream_type}:{index}",
            "-c", "copy", output_path
        ]
        await self.execute_with_updates(args, "Extract stream", client, message)

    async def add_metadata(self, client: Client, message: Message,
                         input_path: str, output_path: str,
                         metadata: Dict[str, str]):
        args = ["-y", "-i", input_path, "-c", "copy"]
        for k, v in metadata.items():
            args.extend(["-metadata", f"{k}={v}"])
        args.append(output_path)
        await self.execute_with_updates(args, "Add metadata", client, message)

    def _get_temp_path(self, ext: str) -> str:
        rand = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return os.path.join(self.temp_dir, f"temp_{rand}{ext}")

    async def _probe_json(self, args: List[str]) -> Dict:
        proc = await asyncio.create_subprocess_exec(
            self.ffprobe_path, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise FFmpegError(stderr.decode() or "ffprobe failed")
        return json.loads(stdout)

    async def view_streams(
        self,
        input_path: str,
    ) -> List[Dict]:
        data = await self._probe_json([
            "-v", "error",
            "-show_entries", "stream",
            "-of", "json",
            input_path,
        ])

        streams = data.get("streams", [])

        # Build a human‑readable summary
        rows = []
        for s in streams:
            idx   = s.get("index")
            typ   = s.get("codec_type")
            codec = s.get("codec_name")
            lang  = s.get("tags", {}).get("language", "und")
            extra = []
            if typ == "video":
                w, h = s.get("width"), s.get("height")
                fps  = s.get("avg_frame_rate")
                extra.append(f"{w}x{h}")
                if fps and "/" in fps:
                    num, den = map(int, fps.split("/"))
                    fps_val = round(num / den, 2) if den else 0
                    extra.append(f"{fps_val} fps")
            elif typ == "audio":
                ch  = s.get("channels")
                sr  = s.get("sample_rate")
                extra.append(f"{ch} ch")
                extra.append(f"{sr} Hz")
            bitrate = s.get("bit_rate")
            if bitrate:
                extra.append(f"{int(bitrate)//1000} kb/s")

            rows.append(f"*{idx}* · `{typ}` · {codec} · {lang} · " +
                        ", ".join(extra))

        text = "🔍 **Streams detected:**\n" + indent("\n".join(rows), "  ")

        return streams

    async def mediainfo(
        self,
        input_path: str,
    ) -> Dict:
        data = await self._probe_json([
            "-v", "error",
            "-show_entries", "streams",
            "-of", "json",
            input_path,
        ])

        fmt  = data.get("format", {})
        dur  = float(fmt.get("duration", 0))
        size = int(fmt.get("size", 0))
        br   = int(fmt.get("bit_rate", 0))
        name = os.path.basename(input_path)
        codecs = [i['codec_name'] for i in data.get('streams', [])]

        h, m = divmod(int(dur), 3600)
        m, s = divmod(m, 60)
        duration = f"{h:02}:{m:02}:{s:02}"

        overview = (
            f"📄 **{name}**\n"

            f"• Container : `{fmt.get('format_name')}`\n"
            f"• Duration  : {duration}\n"
            f"• Size      : {size/1_048_576:.2f} MiB\n"
            f"• Bit‑rate  : {br/1000:.0f} kb/s\n"
            f"• Streams   : {len(data.get('streams', []))}\n"
            f"• Stream name : {[f'{i['codec_name']}:{i['codec_type']}' for i in data.get('streams', [])]}"
        )
        return overview


    async def extract_thumb(self, input_path: str, output_image_path: str, timestamp: str = "00:01:20.000"):
        logging.info(f'check: {input_path} {output_image_path} {timestamp}')
        Path(output_image_path).parent.mkdir(parents=True, exist_ok=True)
        logging.info(f'pa:: {output_image_path}')
        cmd = [
            self.ffmpeg_path,
            "-ss", timestamp,
            "-i", input_path,
            "-frames:v", "1",
            "-q:v", "2",
            "-y",
            output_image_path
        ]

        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()
        if proc.returncode != 0:
            raise FFmpegError("Failed to extract frame.")
        return output_image_path