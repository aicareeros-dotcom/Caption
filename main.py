import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import MessageMediaType
from flask import Flask
from threading import Thread

# --- FLASK SERVER FOR RENDER ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_web():
    web_app.run(host="0.0.0.0", port=8080)

# --- BOT LOGIC ---

# Environment variables (Render Environment me set karein)
API_ID = int(os.environ.get("API_ID", "12345"))
API_HASH = os.environ.get("API_HASH", "your_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")

app = Client("haklesh_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_remove_words = {}
user_caption_store = {}
user_queues = {}

def clean_caption(original: str, remove_words: list) -> str:
    if not original:
        return ""
    for word in remove_words:
        if word in original:
            original = original.split(word)[0].strip()
    return original.strip()

async def process_queue(client, user_id):
    while True:
        queue = user_queues.get(user_id)
        if not queue: break
        
        msg = await queue.get()
        try:
            remove_words = user_remove_words.get(user_id, [])
            caption_to_add = user_caption_store.get(user_id, {}).get("caption", "")
            
            original = msg.caption or ""
            cleaned = clean_caption(original, remove_words)
            final_caption = f"{cleaned}\n\n{caption_to_add}".strip()

            if msg.media == MessageMediaType.VIDEO:
                await client.send_video(chat_id=msg.chat.id, video=msg.video.file_id, caption=final_caption)
            elif msg.media == MessageMediaType.DOCUMENT:
                await client.send_document(chat_id=msg.chat.id, document=msg.document.file_id, caption=final_caption)
            
            await asyncio.sleep(2) # Flood wait se bachne ke liye
            await msg.delete()
        except Exception as e:
            print(f"Error processing for {user_id}: {e}")
        finally:
            queue.task_done()

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    await message.reply("👋 Hello! Use `/setremove word1 word2` to filter text.\nThen send your **Custom Caption**.")

@app.on_message(filters.command("setremove") & filters.private)
async def set_remove_words(client, message: Message):
    words = message.text.split()[1:]
    if not words:
        return await message.reply("❌ Usage: `/setremove word1 word2`")
    user_remove_words[message.from_user.id] = words
    await message.reply(f"✅ Removed words updated.")

@app.on_message(filters.private & filters.text)
async def receive_caption(client, message: Message):
    user_id = message.from_user.id
    # Agar ye command nahi hai, toh ise caption maan lo
    if not message.text.startswith("/"):
        user_caption_store[user_id] = {"step": "ready", "caption": message.text}
        if user_id not in user_queues:
            user_queues[user_id] = asyncio.Queue()
            asyncio.create_task(process_queue(client, user_id))
        await message.reply("✅ Caption Set! Ab Videos/Files bhejein.")

@app.on_message(filters.private & (filters.video | filters.document))
async def enqueue_media(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_caption_store:
        return await message.reply("❌ Pehle ek caption bhejein!")
    await user_queues[user_id].put(message)

if __name__ == "__main__":
    # Start Flask in a separate thread
    Thread(target=run_web).start()
    print("🚀 Bot is starting...")
    app.run()
            
