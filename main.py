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
def home(): return "Haklesh Bot is Active!"

def run_web():
    web_app.run(host="0.0.0.0", port=8080)

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID", "123456"))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

app = Client("haklesh_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Jo naam aapko lagana hai
MY_NAME = "𝆺⎯⎯꯭፝֟͡ 𝐇᷎𝐚𝆭𝆆𝐤͢𝐥𝐞𝐬𝐡⃨፝֟⃕⃔⎯꯭⎯ 𝆺"

# Jo usernames hatane hain
BAD_WORDS = ["@avengers_ownerr", "@Harsh_bhadanaa"]

user_queues = {}

def process_text(text: str) -> str:
    if not text:
        return ""
    new_text = text
    for word in BAD_WORDS:
        # Purana username dhoond kar naye naam se replace karega
        new_text = new_text.replace(word, MY_NAME)
    return new_text.strip()

async def queue_worker(client, user_id):
    while True:
        queue = user_queues.get(user_id)
        if not queue: break

        msg: Message = await queue.get()
        try:
            # Original caption uthao aur replace karo
            final_caption = process_text(msg.caption)

            if msg.media == MessageMediaType.VIDEO:
                await client.send_video(
                    chat_id=msg.chat.id,
                    video=msg.video.file_id,
                    caption=final_caption
                )
            elif msg.media == MessageMediaType.DOCUMENT:
                await client.send_document(
                    chat_id=msg.chat.id,
                    document=msg.document.file_id,
                    caption=final_caption
                )
            
            await asyncio.sleep(1.5) # Anti-flood delay
            await msg.delete() # Purana message delete (optional)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            queue.task_done()

# --- BOT HANDLERS ---

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply("🚀 **Bot Start Ho Gaya Hai!**\n\nAb Video ya PDF bhejein, main usernames badal kar wapas bhej dunga.")

@app.on_message(filters.private & (filters.video | filters.document))
async def handle_media(client, message: Message):
    user_id = message.from_user.id
    
    # Har user ke liye queue check/create karna
    if user_id not in user_queues:
        user_queues[user_id] = asyncio.Queue()
        asyncio.create_task(queue_worker(client, user_id))
    
    await user_queues[user_id].put(message)

# --- STARTUP LOGIC ---
async def start_services():
    Thread(target=run_web, daemon=True).start()
    await app.start()
    print("✅ Bot is running on Render!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
