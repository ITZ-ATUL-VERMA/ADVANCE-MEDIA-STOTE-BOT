from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from aiohttp import web
import asyncio
import string
import random
import time
import os

# ================= OWNER DETAILS =================
API_ID = 35237965  
API_HASH = "ca376f2bed12f0efced887b7ae90e067"  
BOT_TOKEN = "8713015539:AAF1Od6EuGoxnLf2CyRZoTMdXSGzpAwdAoI"  
OWNER_ID = 5884320645  
ADMIN_USERNAME = "KILLER_367"  # Without '@'
# ====================================================

# ================= MONGODB SETUP ====================
MONGO_URL = "mongodb+srv://atul_bot:uYEixMY8WZ2MIHqx@cluster0.h2it7bu.mongodb.net/?appName=Cluster0"
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["MediaSaverPro_DB"]  # Naya Database Name

media_col = db["media"]
users_col = db["users"]
settings_col = db["settings"]
# ====================================================

# ================= PREMIUM & LIMIT SETTINGS =================
MAX_FREE_LINKS = 2  
LIMIT_RESET_TIME = 43200  # 12 Hours
# ============================================================

app = Client("MediaSaverBotPro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

pending_groups = {}  
ADMIN_STATE = {}

# ================= FONT GENERATOR =================
def get_font(text):
    font_map = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ',
        'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
        'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
        'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ'
    }
    return "".join(font_map.get(c, c) for c in text)

def generate_unique_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# ================= DATABASE HELPER FUNCTIONS =================
async def init_db():
    settings = await settings_col.find_one({"_id": "bot_settings"})
    if not settings:
        await settings_col.insert_one({
            "_id": "bot_settings",
            "custom_link": None,
            "backup_link": None,
            "qr_file_id": None,
            "plan_text": get_font("🥇 **PLAN 1:** 1 DAYS - **₹10**\n🥈 **PLAN 2:** 7 DAYS - **₹40**\n🥉 **PLAN 3:** 30 DAYS - **₹100**") + " ✨"
        })

async def get_settings():
    return await settings_col.find_one({"_id": "bot_settings"})

async def update_settings(key, value):
    await settings_col.update_one({"_id": "bot_settings"}, {"$set": {key: value}})

async def get_user(user_id):
    user = await users_col.find_one({"_id": user_id})
    if not user:
        user = {"_id": user_id, "usage_count": 0, "last_reset": time.time()}
        await users_col.insert_one(user)
    return user


# ================= ADMIN DASHBOARD COMMANDS =================

@app.on_message(filters.private & filters.command("users") & filters.user(OWNER_ID))
async def show_all_users(client, message):
    total = await users_col.count_documents({})
    msg = get_font("📊 **BOT STATISTICS**\n\n**TOTAL USERS:** ") + str(total) + get_font("\n_(USERS WHO STARTED THE BOT)_") + " ✨"
    await message.reply_text(msg)

@app.on_message(filters.private & filters.command("premiumlist") & filters.user(OWNER_ID))
async def show_premium_list(client, message):
    cursor = users_col.find({"premium_expiry": {"$exists": True, "$ne": None}})
    premium_users = await cursor.to_list(length=None)
    
    if not premium_users:
        await message.reply_text(get_font("📂 **NO PREMIUM USERS FOUND.**") + " ✨")
        return
    
    text = get_font("💎 **PREMIUM USERS LIST:**\n\n")
    current_time = time.time()
    
    for i, user in enumerate(premium_users, 1):
        remaining_days = max(0, int((user["premium_expiry"] - current_time) / 86400))
        text += get_font(f"**{i}.** 👤 ") + user.get('premium_name', 'User') + get_font(" (ID: ") + f"`{user['_id']}`" + get_font(f") | ⏳ **EXPIRES IN:** {remaining_days} DAYS\n")
        
    await message.reply_text(text + " ✨")

@app.on_message(filters.private & filters.command("gcast") & filters.user(OWNER_ID))
async def broadcast_message(client, message):
    is_reply = True if message.reply_to_message else False
    
    if not is_reply and len(message.command) < 2:
        await message.reply_text(get_font("⚠️ **INVALID FORMAT!**\n**USAGE:** `/gcast Hello everyone!`\nOR REPLY TO A PHOTO/MESSAGE WITH `/gcast`.") + " ✨")
        return

    wait_msg = await message.reply_text(get_font("⏳ **BROADCAST STARTING... PLEASE WAIT.**") + " ✨")
    success_count = 0
    failed_count = 0

    cursor = users_col.find({}, {"_id": 1})
    async for user in cursor:
        try:
            if is_reply:
                await message.reply_to_message.copy(user["_id"])
            else:
                text_to_send = message.text.split(None, 1)[1]
                await client.send_message(user["_id"], get_font(text_to_send) + " ✨")
            
            success_count += 1
            await asyncio.sleep(0.1)  
        except Exception:
            failed_count += 1
            
    await wait_msg.edit_text(
        get_font("✅ **BROADCAST COMPLETE!**\n\n🟢 **SENT SUCCESSFULLY:** ") + str(success_count) + 
        get_font("\n🔴 **FAILED/BLOCKED:** ") + str(failed_count) + " ✨"
    )

@app.on_message(filters.private & filters.command("link") & filters.user(OWNER_ID))
async def set_media_link(client, message):
    cmd = message.text.split(None, 1)
    if len(cmd) < 2:
        await message.reply_text(get_font("⚠️ **INVALID FORMAT!**\n**USAGE:** `/link https://example.com`\n_(TO DISABLE: `/link off`)_") + " ✨")
        return
    
    link = cmd[1].strip()
    if link.lower() == "off":
        await update_settings("custom_link", None)
        await message.reply_text(get_font("✅ **LINK BUTTON REMOVED!**\nTHE BUTTON WILL NO LONGER APPEAR BELOW THE MEDIA.") + " ✨")
    else:
        await update_settings("custom_link", link)
        await message.reply_text(get_font("✅ **LINK SET SUCCESSFULLY!**\nNOW A 'MORE' BUTTON WILL APPEAR UNDER ALL MEDIA REDIRECTING TO:\n") + f"{link} ✨")

@app.on_message(filters.private & filters.command("backup") & filters.user(OWNER_ID))
async def set_backup_link(client, message):
    cmd = message.text.split(None, 1)
    if len(cmd) < 2:
        await message.reply_text(get_font("⚠️ **INVALID FORMAT!**\n**USAGE:** `/backup https://example.com`\n_(TO DISABLE: `/backup off`)_") + " ✨")
        return
    
    link = cmd[1].strip()
    if link.lower() == "off":
        await update_settings("backup_link", None)
        await message.reply_text(get_font("✅ **BACKUP BUTTON REMOVED!**\nTHE BUTTON WILL NO LONGER APPEAR BELOW THE MEDIA.") + " ✨")
    else:
        await update_settings("backup_link", link)
        await message.reply_text(get_font("✅ **BACKUP LINK SET SUCCESSFULLY!**\nNOW A 'BACKUP' BUTTON WILL APPEAR UNDER ALL MEDIA REDIRECTING TO:\n") + f"{link} ✨")

@app.on_message(filters.private & filters.command("approve") & filters.user(OWNER_ID))
async def approve_premium(client, message):
    try:
        cmd = message.text.split()
        if len(cmd) < 3:
            await message.reply_text(get_font("⚠️ **INVALID FORMAT!**\n**USAGE:** `/approve USER_ID DAYS`\nEXAMPLE: `/approve 123456789 30`") + " ✨")
            return
        
        target_user = int(cmd[1]) if cmd[1].isdigit() else cmd[1]
        days = int(cmd[2])
            
        try:
            user = await client.get_users(target_user)
            target_user_id = user.id
            user_name = user.first_name
        except Exception:
            await message.reply_text(get_font("❌ **USER NOT FOUND.**") + " ✨")
            return

        expiry_time = time.time() + (days * 86400) 
        await users_col.update_one(
            {"_id": target_user_id}, 
            {"$set": {"premium_expiry": expiry_time, "premium_name": user_name}}, 
            upsert=True
        )
        
        await message.reply_text(get_font("✅ **PREMIUM APPROVED!**\n👤 **USER:** ") + user_name + get_font(" (ID: ") + f"`{target_user_id}`" + get_font(f")\n⏳ **DURATION:** {days} DAYS") + " ✨")
        
        await client.send_message(
            target_user_id,
            get_font(f"🎉 **CONGRATULATIONS!**\n**THE ADMIN HAS GRANTED YOU PREMIUM ACCESS FOR {days} DAYS!**") + " ✨"
        )
    except Exception as e:
        await message.reply_text(get_font("❌ **ERROR:** ") + str(e) + " ✨")

@app.on_message(filters.private & filters.command("unapprove") & filters.user(OWNER_ID))
async def unapprove_premium(client, message):
    cmd = message.text.split()
    if len(cmd) < 2:
        await message.reply_text(get_font("⚠️ **INVALID FORMAT!**\n**USAGE:** `/unapprove USER_ID`") + " ✨")
        return
    
    target_user = int(cmd[1]) if cmd[1].isdigit() else cmd[1]
    res = await users_col.update_one({"_id": target_user}, {"$unset": {"premium_expiry": "", "premium_name": ""}})
    
    if res.modified_count > 0:
        await message.reply_text(get_font("✅ **PREMIUM REMOVED SUCCESSFULLY FOR USER **") + f"`{target_user}`." + " ✨")
        try:
            await client.send_message(target_user, get_font("⚠️ **NOTICE:** **YOUR PREMIUM ACCESS HAS BEEN CANCELLED BY THE ADMIN.**") + " ✨")
        except Exception:
            pass
    else:
        await message.reply_text(get_font("❌ **THIS USER IS NOT IN THE PREMIUM LIST.**") + " ✨")

@app.on_message(filters.private & filters.command("refresh") & filters.user(OWNER_ID))
async def refresh_limits(client, message):
    wait_msg = await message.reply_text(get_font("⏳ **REFRESHING LIMITS FOR ALL FREE USERS... PLEASE WAIT.**") + " ✨")
    current_time = time.time()
    
    await users_col.update_many({}, {"$set": {"usage_count": 0, "last_reset": current_time}})
    
    cursor = users_col.find({"usage_count": 0}) 
    reset_count = 0
    async for user in cursor:
        try:
            await app.send_message(
                user["_id"],
                get_font(f"🎉 **GOOD NEWS! ADMIN HAS REFRESHED YOUR LIMITS!** 🎉\n\n**YOU CAN NOW OPEN {MAX_FREE_LINKS} MORE LINKS ABSOLUTELY FREE!**") + " ✨"
            )
            reset_count += 1
            await asyncio.sleep(0.1)
        except Exception:
            pass
            
    await wait_msg.edit_text(get_font("✅ **LIMITS REFRESHED SUCCESSFULLY!**\n\n**TOTAL USERS NOTIFIED:** ") + str(reset_count) + " ✨")

@app.on_message(filters.private & filters.command("dlmedia") & filters.user(OWNER_ID))
async def delete_media_cmd(client, message):
    cmd = message.text.split()
    if len(cmd) < 2:
        await message.reply_text(get_font("⚠️ **INVALID FORMAT!**\n**USAGE:** `/dlmedia <LINK OR CODE>`") + " ✨")
        return
    
    code = cmd[1].split("start=")[-1] if "start=" in cmd[1] else cmd[1]
    res = await media_col.delete_one({"_id": code})
    
    if res.deleted_count > 0:
        await message.reply_text(get_font("✅ **MEDIA WITH CODE **") + f"`{code}`" + get_font("** HAS BEEN DELETED FROM THE DATABASE.**") + " ✨")
    else:
        await message.reply_text(get_font("❌ **MEDIA CODE NOT FOUND IN THE DATABASE.**") + " ✨")

@app.on_message(filters.private & filters.command("plan") & filters.user(OWNER_ID))
async def setup_plan(client, message):
    ADMIN_STATE[OWNER_ID] = "WAITING_FOR_PLAN"
    await message.reply_text(get_font("📝 **PLAN SETUP INITIATED!**\n**PLEASE TYPE AND SEND YOUR NEW PLAN DETAILS NOW.**\n_EXAMPLE:_\n1 DAYS = ₹10\n7 DAYS = ₹40") + " ✨")

@app.on_message(filters.private & filters.command("premium") & filters.user(OWNER_ID))
async def premium_setup(client, message):
    ADMIN_STATE[OWNER_ID] = "WAITING_FOR_QR"
    await message.reply_text(get_font("🛠 **PREMIUM QR SETUP!**\n**PLEASE UPLOAD YOUR PAYMENT QR CODE (PHOTO).**") + " ✨")

@app.on_message(filters.private & filters.text & filters.user(OWNER_ID) & ~filters.command(["start", "plan", "premium", "approve", "unapprove", "gcast", "link", "backup", "dlmedia", "users", "premiumlist", "refresh"]))
async def admin_text_handler(client, message):
    if ADMIN_STATE.get(OWNER_ID) == "WAITING_FOR_PLAN":
        await update_settings("plan_text", get_font(message.text) + " ✨")
        ADMIN_STATE[OWNER_ID] = None
        await message.reply_text(get_font("✅ **NEW PLAN UPDATED SUCCESSFULLY!**\n**USERS WILL NOW SEE THIS NEW PLAN.**") + " ✨")


# ================= MEDIA UPLOAD & FORWARD LOGIC =================

@app.on_message(filters.private & ~filters.user(OWNER_ID) & (filters.photo | filters.document | filters.video | filters.audio))
async def forward_user_media(client, message):
    user = message.from_user
    caption = get_font("📩 **NEW MEDIA RECEIVED FROM USER!**\n👤 **NAME:** ") + user.first_name + get_font("\n🆔 **ID:** ") + f"`{user.id}`"
    if message.caption:
        caption += get_font("\n📝 **USER CAPTION:** ") + message.caption
    caption += " ✨"
        
    await message.copy(OWNER_ID, caption=caption)
    await message.reply_text(get_font("✅ **YOUR MEDIA HAS BEEN SENT TO THE ADMIN. PLEASE WAIT!**") + " ✨")

async def process_media_group(client, message, group_id):
    await asyncio.sleep(3) 
    if group_id in pending_groups:
        media_list = pending_groups.pop(group_id)
        unique_code = generate_unique_code()
        
        await media_col.insert_one({"_id": unique_code, "files": media_list})
        
        bot_info = await client.get_me()
        link = f"https://t.me/{bot_info.username}?start={unique_code}"
        await message.reply_text(get_font(f"✅ **ALBUM SAVED! ({len(media_list)} FILES)**\n🔗 **LINK:**\n") + f"`{link}` ✨", quote=True)

@app.on_message(filters.private & filters.user(OWNER_ID) & (filters.document | filters.video | filters.photo | filters.audio))
async def save_media(client, message):
    if ADMIN_STATE.get(OWNER_ID) == "WAITING_FOR_QR" and message.photo:
        await update_settings("qr_file_id", message.photo.file_id)
        ADMIN_STATE[OWNER_ID] = None  
        await message.reply_text(get_font("🎉 **QR CODE SAVED SUCCESSFULLY!**\n**PREMIUM SETUP IS COMPLETE.**") + " ✨")
        return 

    if message.document: file_id, media_type = message.document.file_id, "document"
    elif message.video: file_id, media_type = message.video.file_id, "video"
    elif message.photo: file_id, media_type = message.photo.file_id, "photo"
    elif message.audio: file_id, media_type = message.audio.file_id, "audio"
    else: return

    media_data = {"file_id": file_id, "type": media_type}

    if message.media_group_id:
        group_id = message.media_group_id
        if group_id not in pending_groups:
            pending_groups[group_id] = [media_data]
            asyncio.create_task(process_media_group(client, message, group_id))
        else:
            pending_groups[group_id].append(media_data)
    else:
        unique_code = generate_unique_code()
        await media_col.insert_one({"_id": unique_code, "files": [media_data]})
        
        bot_info = await client.get_me()
        link = f"https://t.me/{bot_info.username}?start={unique_code}"
        await message.reply_text(get_font("✅ **SINGLE MEDIA SAVED!**\n🔗 **LINK:**\n") + f"`{link}` ✨", quote=True)


# ================= MEDIA SENDING & AUTO DELETE WITH "GET AGAIN" =================

async def auto_delete_and_notify(client, chat_id, message_ids, unique_code):
    await asyncio.sleep(300) 
    try:
        await client.delete_messages(chat_id=chat_id, message_ids=message_ids)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(get_font("GET AGAIN") + " ✨", callback_data=f"get_again_{unique_code}")]
        ])
        await client.send_message(
            chat_id,
            get_font("⚠️ **YOUR FILES GOT DELETED. IF YOU WANT THEM AGAIN, THEN CLICK 'GET AGAIN'.**") + " ✨",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Delete/Notify Error: {e}")

async def process_and_send_media(client, chat_id, user_id, unique_code, count_limit=True):
    media_data = await media_col.find_one({"_id": unique_code})
    if not media_data:
        await client.send_message(chat_id, get_font("❌ **THIS LINK IS INVALID, EXPIRED, OR HAS BEEN DELETED.**") + " ✨")
        return

    user = await get_user(user_id)
    is_premium = False
    current_time = time.time()

    if "premium_expiry" in user and user["premium_expiry"]:
        if current_time < user["premium_expiry"]:
            is_premium = True
        else:
            await users_col.update_one({"_id": user_id}, {"$unset": {"premium_expiry": "", "premium_name": ""}})
            await client.send_message(user_id, get_font("⚠️ **PLAN EXPIRED: YOUR PREMIUM HAS ENDED.**") + " ✨")

    if user_id != OWNER_ID and not is_premium:
        if count_limit:
            if current_time - user.get("last_reset", 0) >= LIMIT_RESET_TIME:
                await users_col.update_one({"_id": user_id}, {"$set": {"usage_count": 0, "last_reset": current_time}})
                user["usage_count"] = 0
            
            if user.get("usage_count", 0) >= MAX_FREE_LINKS:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(get_font("BUY PREMIUM NOW") + " ✨", callback_data="buy_premium")]])
                await client.send_message(
                    chat_id,
                    get_font("🚫 **FREE LIMIT REACHED!**\n\n**YOUR FREE LIMIT IS EXHAUSTED. IT WILL RESET AUTOMATICALLY IN 8 HOURS.**\n**BUY PREMIUM TO UNLOCK UNLIMITED ACCESS NOW.**") + " ✨", 
                    reply_markup=keyboard
                )
                return  
            else:
                await users_col.update_one({"_id": user_id}, {"$inc": {"usage_count": 1}})
                user["usage_count"] += 1

    media_list = media_data["files"]
    
    status_msg = ""
    if user_id != OWNER_ID:
        if is_premium: 
            status_msg = get_font("\n💎 **_PREMIUM MEMBER_**")
        elif count_limit: 
            status_msg = get_font(f"\n💡 **_FREE LINKS LEFT: {MAX_FREE_LINKS - user['usage_count']}_**")
        else:
            status_msg = get_font("\n💡 **_FREE (GET AGAIN USED)_**")

    top_message = get_font(f"📂 **YOU ARE RECEIVING {len(media_list)} FILES!**\n⏳ **ADVICE:** ALL FILES WILL BE AUTO-DELETED IN 5 MINUTES.") + status_msg + " ✨"
    await client.send_message(chat_id, top_message)
    
    settings = await get_settings()
    reply_markup = None
    buttons_row = []
    
    if settings.get("custom_link"):
        buttons_row.append(InlineKeyboardButton(get_font("MORE") + " ✨", url=settings["custom_link"]))
    if settings.get("backup_link"):
        buttons_row.append(InlineKeyboardButton(get_font("BACKUP") + " ✨", url=settings["backup_link"]))
        
    if buttons_row:
        reply_markup = InlineKeyboardMarkup([buttons_row])
    
    sent_message_ids = []
    try:
        for media in media_list:
            file_id, m_type = media["file_id"], media["type"]
            sent_msg = None
            if m_type == "document": sent_msg = await client.send_document(chat_id, file_id, caption="", reply_markup=reply_markup)
            elif m_type == "video": sent_msg = await client.send_video(chat_id, file_id, caption="", reply_markup=reply_markup)
            elif m_type == "photo": sent_msg = await client.send_photo(chat_id, file_id, caption="", reply_markup=reply_markup)
            elif m_type == "audio": sent_msg = await client.send_audio(chat_id, file_id, caption="", reply_markup=reply_markup)
            
            if sent_msg: sent_message_ids.append(sent_msg.id)
            await asyncio.sleep(0.5) 
        
        if sent_message_ids:
            asyncio.create_task(auto_delete_and_notify(client, chat_id, sent_message_ids, unique_code))
            
    except Exception as e:
        await client.send_message(chat_id, get_font("❌ **ERROR SENDING MEDIA:** ") + str(e) + " ✨")

# ================= USER COMMANDS & CALLBACKS =================

@app.on_message(filters.private & filters.command("start"))
async def handle_start(client, message):
    await get_user(message.from_user.id) # Ensure user is in DB
    text = message.text.split()
    
    if len(text) == 1:
        await message.reply_text(get_font("👋 **HELLO! I AM A PREMIUM MEDIA BOT. PLEASE ACCESS ME THROUGH VALID LINKS.**") + " ✨")
        return
    
    unique_code = text[1]
    await process_and_send_media(client, message.chat.id, message.from_user.id, unique_code, count_limit=True)

@app.on_callback_query(filters.regex(r"^get_again_(.*)"))
async def handle_get_again(client, callback_query):
    unique_code = callback_query.matches[0].group(1)
    
    try:
        await callback_query.message.delete()
    except Exception:
        pass
        
    await process_and_send_media(client, callback_query.message.chat.id, callback_query.from_user.id, unique_code, count_limit=False)

@app.on_callback_query(filters.regex("buy_premium"))
async def show_premium_details(client, callback_query):
    settings = await get_settings()
    
    if not settings.get("qr_file_id"):
        await callback_query.message.edit_text(get_font("🛠 **PLAN UPDATE IN PROGRESS!**\n**PLEASE MESSAGE THE ADMIN:** ") + f"@{ADMIN_USERNAME} ✨")
        return

    plan_text = get_font("💎 **PREMIUM SUBSCRIPTION PLANS** 💎\n\n") + settings['plan_text'] + get_font(
        "\n\n**👉 HOW TO BUY?**\n"
        "**1.** PAY THE AMOUNT OF YOUR DESIRED PLAN ON THE QR CODE ABOVE.\n"
        "**2.** TAKE A SCREENSHOT OF THE PAYMENT AND **SEND IT DIRECTLY TO THIS BOT** OR TO ADMIN "
    ) + f"@{ADMIN_USERNAME}\n" + get_font(
        "**3.** THE ADMIN WILL VERIFY AND GRANT YOUR PREMIUM ACCESS."
    ) + " ✨"
    
    await callback_query.message.delete()
    await client.send_photo(
        chat_id=callback_query.from_user.id,
        photo=settings["qr_file_id"],
        caption=plan_text
    )


# ================= DUMMY WEB SERVER =================
async def handle(request):
    return web.Response(text="Bot is running smoothly! ✨")

async def web_server():
    web_app = web.Application()
    web_app.router.add_get('/', handle)
    runner = web.AppRunner(web_app)
    await runner.setup()
    
    # Render automatically $PORT assign karta hai
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Dummy Web Server started on port {port}")


# ================= BACKGROUND TASKS =================

async def daily_premium_check():
    while True:
        await asyncio.sleep(86400) 
        current_time = time.time()
        
        cursor = users_col.find({"premium_expiry": {"$exists": True, "$ne": None}})
        async for user in cursor:
            expiry = user["premium_expiry"]
            if current_time >= expiry:
                await users_col.update_one({"_id": user["_id"]}, {"$unset": {"premium_expiry": "", "premium_name": ""}})
                try: await app.send_message(user["_id"], get_font("⚠️ **PREMIUM EXPIRED!**\n**YOUR PREMIUM SUBSCRIPTION HAS ENDED.**") + " ✨")
                except: pass
            else:
                remaining_days = int((expiry - current_time) / 86400)
                if remaining_days > 0:
                    try: await app.send_message(user["_id"], get_font(f"🔔 **PREMIUM REMINDER:**\n**YOUR PREMIUM WILL EXPIRE IN {remaining_days} DAYS.**") + " ✨")
                    except: pass

async def free_limit_reset_check():
    while True:
        await asyncio.sleep(60) 
        current_time = time.time()
        
        cursor = users_col.find({"usage_count": {"$gt": 0}})
        async for user in cursor:
            if (current_time - user.get("last_reset", 0)) >= LIMIT_RESET_TIME:
                await users_col.update_one({"_id": user["_id"]}, {"$set": {"usage_count": 0, "last_reset": current_time}})
                try:
                    await app.send_message(
                        user["_id"], 
                        get_font(f"🔔 **GOOD NEWS!**\n\n**YOUR FREE LIMIT HAS BEEN RESET! 🎉**\n**YOU CAN NOW ACCESS {MAX_FREE_LINKS} LINKS FOR FREE AGAIN!**") + " ✨"
                    )
                except Exception:
                    pass

# ================= STARTUP LOGIC =================

async def main():
    print("Connecting to MongoDB...")
    await init_db()
    
    await app.start()
    print("BOT IS STARTING (MONGODB & WEB SERVER ACTIVE)...")
    
    # Background tasks
    asyncio.create_task(daily_premium_check())
    asyncio.create_task(free_limit_reset_check())
    asyncio.create_task(web_server())
    
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())