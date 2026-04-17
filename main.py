import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import MessageMediaType
from flask import Flask
from threading import Thread

# --- FLASK SERVER ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is Alive!"

def run_web():
    web_app.run(host="0.0.0.0", port=8080)

# --- BOT CONFIG ---
API_ID = int(os.environ.get("API_ID", "12345"))
API_HASH = os.environ.get("API_HASH", "your_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")

app = Client("haklesh_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_remove_words = {}
user_caption_store = {}
user_queues = {}

def clean_caption(original: str, remove_words: list) -> str:
    if not original: return ""
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
            
            await asyncio.sleep(2)
            await msg.delete()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            queue.task_done()

@app.on_message(filters.command("start") & filters.private)
async def start_handler(c, m):
    await m.reply("Bot is ready! Send your caption first.")

@app.on_message(filters.command("setremove") & filters.private)
async def set_remove(c, m):
    words = m.text.split()[1:]
    user_remove_words[m.from_user.id] = words
    await m.reply(f"✅ Removed words set: {words}")

@app.on_message(filters.private & filters.text)
async def receive_caption(c, m):
    if m.text.startswith("/"): return
    user_id = m.from_user.id
    user_caption_store[user_id] = {"step": "ready", "caption": m.text}
    if user_id not in user_queues:
        user_queues[user_id] = asyncio.Queue()
        asyncio.create_task(process_queue(c, user_id))
    await m.reply("✅ Caption set! Now send media.")

@app.on_message(filters.private & (filters.video | filters.document))
async def enqueue_media(c, m):
    user_id = m.from_user.id
    if user_id not in user_caption_store:
        return await m.reply("❌ Send caption first!")
    await user_queues[user_id].put(m)

# --- CORRECT WAY TO RUN ON RENDER ---
async def main():
    # Start Flask thread
    Thread(target=run_web, daemon=True).start()
    # Start Bot
    await app.start()
    print("🚀 Bot Started!")
    await asyncio.Event().wait() # Keep bot running

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
