import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import MessageMediaType
from flask import Flask
from threading import Thread

# --- RENDER HEALTH CHECK ---
web_app = Flask(__name__)
@web_app.route('/')
def home():
    return "Haklesh Bot is Active!"

def run_web():
    web_app.run(host="0.0.0.0", port=8080)

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID", "123456"))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

app = Client("haklesh_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- CUSTOM NAME ---
MY_NAME = "𝆺⎯⎯꯭፝֟͡ 𝐇᷎𝐚𝆭𝆆𝐤͢𝐥𝐞𝐬𝐡⃨፝֟⃕⃔⎯꯭⎯ 𝆺"

BAD_WORDS = ["@avengers_ownerr", "@Harsh_bhadanaa"]

# --- CHANNEL SYSTEM ---
user_queues = {}
user_channels = {}   # 👈 NEW (channel storage)

# --- TEXT PROCESSOR ---
def process_text(text: str) -> str:
    if not text:
        return ""
    for word in BAD_WORDS:
        text = text.replace(word, MY_NAME)
    return text.strip()

# --- QUEUE WORKER ---
async def queue_worker(client, user_id):
    while True:
        queue = user_queues.get(user_id)
        if not queue:
            break

        msg: Message = await queue.get()

        try:
            channel_id = user_channels.get(user_id)

            if not channel_id:
                await msg.reply("❌ Pehle /setchannel use karo!")
                return

            final_caption = process_text(msg.caption)

            # --- VIDEO ---
            if msg.media == MessageMediaType.VIDEO:
                await client.send_video(
                    chat_id=channel_id,
                    video=msg.video.file_id,
                    caption=final_caption
                )

            # --- DOCUMENT ---
            elif msg.media == MessageMediaType.DOCUMENT:
                await client.send_document(
                    chat_id=channel_id,
                    document=msg.document.file_id,
                    caption=final_caption
                )

            await asyncio.sleep(1.5)
            await msg.delete()

        except Exception as e:
            print(f"Error: {e}")

        finally:
            queue.task_done()

# --- START COMMAND ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply(
        "🚀 **Bot Active Hai!**\n\n"
        "👉 /setchannel - Channel set karo\n"
        "👉 Video/PDF bhejo - Auto upload hoga"
    )

# --- SET CHANNEL COMMAND ---
@app.on_message(filters.command("setchannel") & filters.private)
async def set_channel(client, message):
    await message.reply("📢 Apna Channel ID bhejo (example: -100xxxxxxxxxx)")

    try:
        msg = await client.listen(message.chat.id, timeout=30)
        ch_id = int(msg.text.strip())
        user_channels[message.from_user.id] = ch_id

        await message.reply(f"✅ Channel set ho gaya!\n\nID: `{ch_id}`")

    except:
        await message.reply("❌ Invalid input ya timeout")

# --- GET ID COMMAND ---
@app.on_message(filters.command("id") & filters.private)
async def get_id(client, message):
    await message.reply(f"🆔 Chat ID:\n`{message.chat.id}`")

# --- MEDIA HANDLER ---
@app.on_message(filters.private & (filters.video | filters.document))
async def handle_media(client, message: Message):
    user_id = message.from_user.id

    if user_id not in user_queues:
        user_queues[user_id] = asyncio.Queue()
        asyncio.create_task(queue_worker(client, user_id))

    await user_queues[user_id].put(message)

# --- STARTUP ---
async def start_services():
    Thread(target=run_web, daemon=True).start()
    await app.start()
    print("✅ Bot is running on Render!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
