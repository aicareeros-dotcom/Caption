import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import MessageMediaType
from keep_alive import keep_alive  # ✅ Add this

# 🔐 Load environment variables from Replit secrets
API_ID = int(os.environ.get("API_ID", "123456"))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

app = Client("haklesh_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_remove_words = {}
user_caption_store = {}
user_queues = {}

@app.on_message(filters.command("setremove") & filters.private)
async def set_remove_words(client, message: Message):
    words = message.text.split()[1:]
    if not words:
        return await message.reply("❌ Use like:\n`/setremove word1 word2 ...`")
    user_remove_words[message.from_user.id] = words
    await message.reply(f"✅ Remove from word(s):\n`{', '.join(words)}`")

@app.on_message(filters.command("start") & filters.private)
async def start_caption(client, message: Message):
    user_caption_store[message.from_user.id] = {"step": "waiting_caption", "caption": ""}
    await message.reply("✍️ Kripya caption bheje jo har media ke neeche add karna chahte hain:")

@app.on_message(filters.private & filters.text)
async def receive_caption(client, message: Message):
    user_id = message.from_user.id
    if user_id in user_caption_store and user_caption_store[user_id]["step"] == "waiting_caption":
        user_caption_store[user_id]["caption"] = message.text
        user_caption_store[user_id]["step"] = "ready"
        user_queues[user_id] = asyncio.Queue()
        asyncio.create_task(process_queue(client, user_id))
        await message.reply("📥 Ab video/PDF bheje 1-by-1.\nBot same order me reply karega.")

@app.on_message(filters.private & (filters.video | filters.document))
async def enqueue_media(client, message: Message):
    user_id = message.from_user.id
    if user_caption_store.get(user_id, {}).get("step") != "ready":
        return
    await user_queues[user_id].put(message)

def clean_caption(original: str, remove_words: list) -> str:
    for word in remove_words:
        if word in original:
            return original.split(word)[0].strip()
    return original.strip()

async def process_queue(client, user_id):
    while True:
        queue = user_queues.get(user_id)
        if not queue:
            break

        msg: Message = await queue.get()
        remove_words = user_remove_words.get(user_id, [])
        caption_to_add = user_caption_store[user_id]["caption"]
        original = msg.caption or ""
        cleaned = clean_caption(original, remove_words)
        final_caption = f"{cleaned}\n\n{caption_to_add}".strip()

        try:
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
            await asyncio.sleep(1.5)
            await msg.delete()
        except Exception as e:
            await msg.reply(f"❌ Error: {e}")

        queue.task_done()

# 🔁 Replit keep alive
keep_alive()

if __name__ == "__main__":
    print("🚀 Starting Haklesh Bot...")
    try:
        app.run()
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
