import sqlite3
import time
import random
import re
import asyncio

from telegram import Update
from telegram.ext import (
Application,
CommandHandler,
MessageHandler,
ChatMemberHandler,
ContextTypes,
filters
)

=========================================================

تنظیمات

=========================================================

TOKEN = "توکن_جدید_ربات_را_اینجا_بگذار"

OWNER_ID = 6314127564

COOLDOWN = 4 * 60

LEVEL_2 = 50
LEVEL_3 = 100

BATCH_SIZE = 50

=========================================================

دیتابیس

=========================================================

conn = sqlite3.connect("hana_point.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
first_name TEXT,
username TEXT,
hana_points INTEGER DEFAULT 0,
hadi_points INTEGER DEFAULT 0,
emad_points INTEGER DEFAULT 0,
last_hana REAL DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS groups_list (
chat_id INTEGER PRIMARY KEY,
title TEXT,
username TEXT,
added_at REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS group_messages (
id INTEGER PRIMARY KEY AUTOINCREMENT,
chat_id INTEGER,
message_id INTEGER,
user_id INTEGER,
first_name TEXT,
username TEXT,
message_type TEXT,
protected INTEGER DEFAULT 0,
created_at REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS send_progress (
owner_id INTEGER,
chat_id INTEGER,
last_id INTEGER DEFAULT 0,
PRIMARY KEY(owner_id, chat_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS support_messages (
owner_message_id INTEGER PRIMARY KEY,
user_id INTEGER,
created_at REAL
)
""")

conn.commit()

=========================================================

ابزارها

=========================================================

def normalize_number(text):
if not text:
return ""

table = str.maketrans(  
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",  
    "01234567890123456789"  
)  

return text.translate(table)

def get_user_name(user):
if user.username:
return f"@{user.username}"

return user.first_name or "بدون نام"

def save_user(user):
if not user:
return

cursor.execute("""  
INSERT INTO users  
(user_id, first_name, username)  
VALUES (?, ?, ?)  
ON CONFLICT(user_id) DO UPDATE SET  
    first_name = excluded.first_name,  
    username = excluded.username  
""", (  
    user.id,  
    user.first_name or "",  
    user.username or ""  
))  

conn.commit()

def save_group(chat):
if not chat:
return

cursor.execute("""  
INSERT INTO groups_list  
(chat_id, title, username, added_at)  
VALUES (?, ?, ?, ?)  
ON CONFLICT(chat_id) DO UPDATE SET  
    title = excluded.title,  
    username = excluded.username  
""", (  
    chat.id,  
    chat.title or "",  
    chat.username or "",  
    time.time()  
))  

conn.commit()

=========================================================

START

=========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

user = update.effective_user  
chat = update.effective_chat  

if user:  
    save_user(user)  

if chat.type == "private":  

    await update.message.reply_text(  
        "به ربات خوش آمدید 🌹\n\n"  
        "پیام خود را بفرستید و در اسرع وقت جواب خود را دریافت کنید."  
    )  

    return  

if chat.type in ["group", "supergroup"]:  

    save_group(chat)  

    await update.message.reply_text(  
        "🍯 ربات حنا پوینت فعال شد!\n\n"  
        "برای گرفتن امتیاز بنویسید:\n"  
        "حنا پوینت\n\n"  
        "⚠️ ربات باید ادمین کامل گروه باشد."  
    )

=========================================================

وقتی ربات وارد گروه می‌شود

=========================================================

async def bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):

chat_member = update.my_chat_member  

if not chat_member:  
    return  

chat = chat_member.chat  

if chat.type not in ["group", "supergroup"]:  
    return  

save_group(chat)  

new_status = chat_member.new_chat_member.status  

if new_status in ["administrator", "creator"]:  

    await context.bot.send_message(  
        chat_id=chat.id,  
        text=(  
            "🍯 ربات حنا پوینت فعال شد!\n\n"  
            "✅ ربات ادمین کامل است و آماده کار است."  
        )  
    )  

elif new_status in ["member", "restricted"]:  

    await context.bot.send_message(  
        chat_id=chat.id,  
        text=(  
            "⚠️ برای کار کردن ربات، لطفاً ربات را ادمین کامل کنید."  
        )  
    )

=========================================================

بررسی ادمین بودن ربات

=========================================================

async def is_bot_admin(context, chat_id):

try:  

    me = await context.bot.get_me()  

    member = await context.bot.get_chat_member(  
        chat_id,  
        me.id  
    )  

    return member.status in ["administrator", "creator"]  

except Exception as e:  

    print("خطا در بررسی ادمین:", e)  

    return False

=========================================================

حنا پوینت

=========================================================

async def hana(update: Update, context: ContextTypes.DEFAULT_TYPE):

message = update.message  

if not message:  
    return  

user = update.effective_user  
chat = update.effective_chat  

if not user:  
    return  

if not await is_bot_admin(context, chat.id):  

    await message.reply_text(  
        "⚠️ برای کار کردن ربات، لطفاً ربات را ادمین کامل کنید."  
    )  

    return  

save_user(user)  
save_group(chat)  

now = time.time()  

if user.id == OWNER_ID:  

    await message.reply_text(  
        f"👑 {get_user_name(user)}\n\n"  
        "حنا پوینت شما نامحدود است ♾️"  
    )  

    return  

cursor.execute("""  
SELECT hana_points, last_hana  
FROM users  
WHERE user_id = ?  
""", (user.id,))  

row = cursor.fetchone()  

if not row:  
    return  

points = row[0] or 0  
last_hana = row[1] or 0  

remaining = COOLDOWN - (now - last_hana)  

if remaining > 0:  

    minutes = int(remaining // 60)  
    seconds = int(remaining % 60)  

    await message.reply_text(  
        f"⏳ هنوز زوده!\n"  
        f"دوباره {minutes} دقیقه و {seconds} ثانیه دیگه امتحان کن."  
    )  

    return  

if points < LEVEL_2:  

    reward = 10  
    level = 1  

elif points < LEVEL_3:  

    reward = 20  
    level = 2  

else:  

    reward = 20  
    level = 3  

new_points = points + reward  

cursor.execute("""  
UPDATE users  
SET hana_points = ?,  
    last_hana = ?  
WHERE user_id = ?  
""", (  
    new_points,  
    now,  
    user.id  
))  

conn.commit()  

await message.reply_text(  
    f"🍯 {get_user_name(user)}\n\n"  
    f"🎁 +{reward} حنا پوینت\n"  
    f"💰 موجودی: {new_points}\n"  
    f"⭐ لول: {level}"  
)

=========================================================

انتقال حنا پوینت

=========================================================

async def transfer_points(update: Update, context: ContextTypes.DEFAULT_TYPE):

message = update.message  
user = update.effective_user  

if not message or not user:  
    return  

if user.id != OWNER_ID:  
    await message.reply_text("❌ فقط مالک ربات می‌تواند انتقال انجام دهد.")  
    return  

if not message.reply_to_message:  
    await message.reply_text(  
        "⚠️ باید روی پیام شخص موردنظر ریپلای کنید.\n\n"  
        "مثال:\n"  
        "انتقال ۱۰ حنا پوینت"  
    )  
    return  

text = normalize_number(message.text)  

match = re.fullmatch(  
    r"انتقال\s+(\d+)\s+حنا\s+پوینت",  
    text  
)  

if not match:  
    return  

amount = int(match.group(1))  

target = message.reply_to_message.from_user  

if not target:  
    await message.reply_text("❌ کاربر پیدا نشد.")  
    return  

save_user(target)  

cursor.execute("""  
UPDATE users  
SET hana_points = hana_points + ?  
WHERE user_id = ?  
""", (  
    amount,  
    target.id  
))  

conn.commit()  

cursor.execute("""  
SELECT hana_points  
FROM users  
WHERE user_id = ?  
""", (target.id,))  

new_balance = cursor.fetchone()[0]  

await message.reply_text(  
    f"✅ انتقال انجام شد.\n\n"  
    f"👤 {get_user_name(target)}\n"  
    f"🎁 +{amount} حنا پوینت\n"  
    f"💰 موجودی جدید: {new_balance}"  
)

=========================================================

شیپ

=========================================================

async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE):

chat = update.effective_chat  

if chat.type not in ["group", "supergroup"]:  
    return  

cursor.execute("""  
SELECT user_id, first_name, username  
FROM users  
WHERE user_id != ?  
""", (OWNER_ID,))  

users = cursor.fetchall()  

if len(users) < 2:  

    await update.message.reply_text(  
        "😂 هنوز کاربر کافی برای شیپ کردن نداریم!"  
    )  

    return  

a, b = random.sample(users, 2)  

percent = random.randint(1, 100)  

name_a = a[1] or "کاربر"  
name_b = b[1] or "کاربر"  

await update.message.reply_text(  
    f"💘 شیپ امروز\n\n"  
    f"👤 {name_a} ❤️ {name_b}\n\n"  
    f"💕 درصد هماهنگی: {percent}%"  
)

=========================================================

ذخیره پیام‌های گروه

=========================================================

async def save_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

message = update.message  

if not message:  
    return  

chat = update.effective_chat  

if chat.type not in ["group", "supergroup"]:  
    return  

user = update.effective_user  

if user:  
    save_user(user)  

save_group(chat)  

if user:  

    message_type = "unknown"  

    if message.text:  
        message_type = "text"  
    elif message.photo:  
        message_type = "photo"  
    elif message.video:  
        message_type = "video"  
    elif message.animation:  
        message_type = "animation"  
    elif message.sticker:  
        message_type = "sticker"  
    elif message.voice:  
        message_type = "voice"  
    elif message.audio:  
        message_type = "audio"  
    elif message.document:  
        message_type = "document"  
    elif message.video_note:  
        message_type = "video_note"  
    elif message.contact:  
        message_type = "contact"  
    elif message.location:  
        message_type = "location"  
    elif message.venue:  
        message_type = "venue"  
    elif message.poll:  
        message_type = "poll"  
    elif message.dice:  
        message_type = "dice"  

    protected = 1 if message.has_protected_content else 0  

    cursor.execute("""  
    INSERT INTO group_messages  
    (  
        chat_id,  
        message_id,  
        user_id,  
        first_name,  
        username,  
        message_type,  
        protected,  
        created_at  
    )  
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)  
    """, (  
        chat.id,  
        message.message_id,  
        user.id,  
        user.first_name or "",  
        user.username or "",  
        message_type,  
        protected,  
        time.time()  
    ))  

    conn.commit()

=========================================================

فرمت دستورهای ارسال پیام

=========================================================

SEND_PATTERN = re.compile(
r"^(?:"
r"ارسال\s+تمام\s+پیام\s+ها\s+-?\d+"
r"|"
r"بعدی\s+-?\d+"
r"|"
r"ارسال\s+\d+\s+-?\d+"
r")$"
)

def get_send_request(text):

text = normalize_number(text or "").strip()  

match = re.fullmatch(  
    r"ارسال\s+تمام\s+پیام\s+ها\s+(-?\d+)",  
    text  
)  

if match:  

    return int(match.group(1)), BATCH_SIZE  

match = re.fullmatch(  
    r"بعدی\s+(-?\d+)",  
    text  
)  

if match:  

    return int(match.group(1)), BATCH_SIZE  

match = re.fullmatch(  
    r"ارسال\s+(\d+)\s+(-?\d+)",  
    text  
)  

if match:  

    amount = int(match.group(1))  

    if amount <= 0:  
        return None  

    return int(match.group(2)), amount  

return None

=========================================================

ارسال پیام‌های گروه برای مالک

=========================================================

async def send_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

message = update.message  

if not message:  
    return  

user = update.effective_user  

if not user or user.id != OWNER_ID:  
    return  

request = get_send_request(message.text)  

if not request:  
    return  

chat_id, amount = request  

cursor.execute("""  
SELECT title  
FROM groups_list  
WHERE chat_id = ?  
""", (chat_id,))  

group_row = cursor.fetchone()  

if not group_row:  

    await message.reply_text(  
        "❌ این گروه در لیست ربات ثبت نشده است."  
    )  

    return  

cursor.execute("""  
SELECT last_id  
FROM send_progress  
WHERE owner_id = ? AND chat_id = ?  
""", (  
    OWNER_ID,  
    chat_id  
))  

progress_row = cursor.fetchone()  

last_id = progress_row[0] if progress_row else 0  

cursor.execute("""  
SELECT  
    id,  
    message_id,  
    user_id,  
    first_name,  
    username,  
    protected  
FROM group_messages  
WHERE chat_id = ?  
  AND id > ?  
ORDER BY id ASC  
LIMIT ?  
""", (  
    chat_id,  
    last_id,  
    amount  
))  

rows = cursor.fetchall()  

if not rows:  

    await message.reply_text(  
        "📭 پیام جدیدی برای ارسال باقی نمانده است."  
    )  

    return  

sent = 0  
skipped = 0  

for row in rows:  

    db_id = row[0]  
    message_id = row[1]  
    user_id = row[2]  
    first_name = row[3]  
    username = row[4]  
    protected = row[5]  

    if protected:  

        skipped += 1  

        cursor.execute("""  
        INSERT OR REPLACE INTO send_progress  
        (owner_id, chat_id, last_id)  
        VALUES (?, ?, ?)  
        """, (  
            OWNER_ID,  
            chat_id,  
            db_id  
        ))  

        conn.commit()  

        continue  

    try:  

        # =================================================  
        # اول تلاش می‌کنیم پیام را به صورت FORWARD بفرستیم  
        # =================================================  

        await context.bot.forward_message(  
            chat_id=OWNER_ID,  
            from_chat_id=chat_id,  
            message_id=message_id  
        )  

        sent += 1  

    except Exception as forward_error:  

        print(  
            "⚠️ فوروارد نشد:",  
            forward_error  
        )  

        # =================================================  
        # اگر فوروارد نشد، اول مشخصات فرستنده را می‌فرستیم  
        # =================================================  

        sender_name = first_name or "بدون نام"  

        if username:  

            sender_text = (  
                f"👤 فرستنده: {sender_name}\n"  
                f"🔗 @{username}\n"  
                f"🆔 آیدی: {user_id}"  
            )  

        else:  

            sender_text = (  
                f"👤 فرستنده: {sender_name}\n"  
                f"🆔 آیدی: {user_id}"  
            )  

        try:  

            await context.bot.send_message(  
                chat_id=OWNER_ID,  
                text=sender_text  
            )  

            # =================================================  
            # بعد خود پیام را کپی می‌کنیم  
            # =================================================  

            await context.bot.copy_message(  
                chat_id=OWNER_ID,  
                from_chat_id=chat_id,  
                message_id=message_id  
            )  

            sent += 1  

        except Exception as copy_error:  

            print(  
                "❌ کپی پیام هم نشد:",  
                copy_error  
            )  

            skipped += 1  

    # ذخیره پیشرفت  
    cursor.execute("""  
    INSERT OR REPLACE INTO send_progress  
    (owner_id, chat_id, last_id)  
    VALUES (?, ?, ?)  
    """, (  
        OWNER_ID,  
        chat_id,  
        db_id  
    ))  

    conn.commit()  

    await asyncio.sleep(0.08)  

await message.reply_text(  
    f"📤 ارسال انجام شد.\n\n"  
    f"✅ ارسال‌شده: {sent}\n"  
    f"⏭ ردشده: {skipped}\n"  
    f"📦 تعداد بررسی‌شده: {len(rows)}"  
)

=========================================================

لیست گروه‌ها

=========================================================

async def groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

user = update.effective_user  
chat = update.effective_chat  

if not user or user.id != OWNER_ID:  
    return  

if chat.type != "private":  
    return  

cursor.execute("""  
SELECT chat_id, title, username  
FROM groups_list  
ORDER BY added_at DESC  
""")  

groups = cursor.fetchall()  

if not groups:  

    await update.message.reply_text(  
        "📭 هنوز هیچ گروهی ثبت نشده."  
    )  

    return  

text = "📋 گروه‌های ثبت‌شده:\n\n"  

for index, row in enumerate(groups, 1):  

    chat_id = row[0]  
    title = row[1] or "بدون نام"  
    username = row[2]  

    text += f"{index}. {title}\n"  
    text += f"🆔 {chat_id}\n"  

    if username:  
        text += f"🔗 @{username}\n"  

    text += "\n"  

await update.message.reply_text(text)

=========================================================

گرفتن آیدی اعضای شناسایی‌شده گروه

=========================================================

async def group_member_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):

message = update.message  
user = update.effective_user  

if not message or not user:  
    return  

if user.id != OWNER_ID:  
    return  

text = normalize_number(message.text or "").strip()  

match = re.fullmatch(  
    r"آیدی اعضا\s+(-?\d+)",  
    text  
)  

if not match:  
    return  

chat_id = int(match.group(1))  

cursor.execute("""  
SELECT title  
FROM groups_list  
WHERE chat_id = ?  
""", (chat_id,))  

group = cursor.fetchone()  

if not group:  

    await message.reply_text(  
        "❌ این گروه ثبت نشده است."  
    )  

    return  

cursor.execute("""  
SELECT  
    user_id,  
    first_name,  
    username  
FROM users  
WHERE user_id IN (  
    SELECT DISTINCT user_id  
    FROM group_messages  
    WHERE chat_id = ?  
)  
ORDER BY first_name COLLATE NOCASE  
""", (chat_id,))  

members = cursor.fetchall()  

if not members:  

    await message.reply_text(  
        "📭 هنوز اطلاعات هیچ عضوی از این گروه ثبت نشده است."  
    )  

    return  

group_title = group[0] or "بدون نام"  

text = (  
    f"👥 اعضای شناسایی‌شده\n"  
    f"🏷 گروه: {group_title}\n"  
    f"🆔 گروه: {chat_id}\n\n"  
)  

for index, member in enumerate(members, 1):  

    user_id = member[0]  
    first_name = member[1] or "بدون نام"  
    username = member[2]  

    text += f"{index}. {first_name}\n"  

    if username:  
        text += f"   🔗 @{username}\n"  

    text += f"   🆔 {user_id}\n\n"  

    # تلگرام محدودیت طول پیام دارد  
    if len(text) > 3500:  

        await message.reply_text(text)  

        text = ""  

if text:  

    await message.reply_text(text)

=========================================================

پشتیبانی خصوصی

=========================================================

async def private_support(update: Update, context: ContextTypes.DEFAULT_TYPE):

message = update.message  

if not message:  
    return  

if update.effective_chat.type != "private":  
    return  

user = update.effective_user  

if not user:  
    return  

# =====================================================  
# اگر مالک جواب یک پیام را بدهد  
# =====================================================  

if user.id == OWNER_ID:  

    if not message.reply_to_message:  
        return  

    replied = message.reply_to_message  

    cursor.execute("""  
    SELECT user_id  
    FROM support_messages  
    WHERE owner_message_id = ?  
    """, (  
        replied.message_id,  
    ))  

    row = cursor.fetchone()  

    if not row:  
        return  

    target_user_id = row[0]  

    try:  

        await context.bot.copy_message(  
            chat_id=target_user_id,  
            from_chat_id=OWNER_ID,  
            message_id=message.message_id  
        )  

        await message.reply_text(  
            "✅ پاسخ برای کاربر ارسال شد."  
        )  

    except Exception as e:  

        print(  
            "❌ خطا در ارسال پاسخ پشتیبانی:",  
            e  
        )  

        await message.reply_text(  
            "❌ نتوانستم پاسخ را برای کاربر ارسال کنم."  
        )  

    return  

# =====================================================  
# پیام کاربر → مالک  
# =====================================================  

save_user(user)  

try:  

    forwarded = await context.bot.forward_message(  
        chat_id=OWNER_ID,  
        from_chat_id=user.id,  
        message_id=message.message_id  
    )  

except Exception as e:  

    print(  
        "⚠️ فوروارد نشد، تلاش با کپی:",  
        e  
    )  

    try:  

        forwarded = await context.bot.copy_message(  
            chat_id=OWNER_ID,  
            from_chat_id=user.id,  
            message_id=message.message_id  
        )  

    except Exception as e2:  

        print(  
            "❌ خطا در ارسال پیام کاربر به مالک:",  
            e2  
        )  

        return  

cursor.execute("""  
INSERT OR REPLACE INTO support_messages  
(  
    owner_message_id,  
    user_id,  
    created_at  
)  
VALUES (?, ?, ?)  
""", (  
    forwarded.message_id,  
    user.id,  
    time.time()  
))  

conn.commit()

=========================================================

MAIN

=========================================================

def main():

app = Application.builder().token(TOKEN).build()  

# -----------------------------------------  
# دستورات  
# -----------------------------------------  

app.add_handler(  
    CommandHandler(  
        "start",  
        start  
    ),  
    group=0  
)  

app.add_handler(  
    CommandHandler(  
        "groups",  
        groups_command  
    ),  
    group=0  
)  

# -----------------------------------------  
# ورود ربات به گروه  
# -----------------------------------------  

app.add_handler(  
    ChatMemberHandler(  
        bot_added_to_group,  
        ChatMemberHandler.MY_CHAT_MEMBER  
    ),  
    group=0  
)  

# -----------------------------------------  
# حنا پوینت  
# -----------------------------------------  

app.add_handler(  
    MessageHandler(  
        filters.ChatType.GROUPS  
        & filters.Regex(r"^حنا پوینت$"),  
        hana  
    ),  
    group=0  
)  

# -----------------------------------------  
# انتقال  
# -----------------------------------------  

app.add_handler(  
    MessageHandler(  
        filters.ChatType.GROUPS  
        & filters.Regex(  
            r"^انتقال\s+\d+\s+حنا\s+پوینت$"  
        ),  
        transfer_points  
    ),  
    group=0  
)  

# -----------------------------------------  
# شیپ  
# -----------------------------------------  

app.add_handler(  
    MessageHandler(  
        filters.ChatType.GROUPS  
        & filters.Regex(r"^شیپ$"),  
        ship  
    ),  
    group=0  
)  

# -----------------------------------------  
# آیدی اعضای گروه  
# -----------------------------------------  

app.add_handler(  
    MessageHandler(  
        filters.ChatType.PRIVATE  
        & filters.TEXT  
        & filters.Regex(r"^آیدی اعضا\s+-?\d+$"),  
        group_member_ids  
    ),  
    group=0  
)  

# -----------------------------------------  
# ارسال پیام‌های ذخیره‌شده گروه  
# -----------------------------------------  

app.add_handler(  
    MessageHandler(  
        filters.ChatType.PRIVATE  
        & filters.TEXT  
        & filters.Regex(SEND_PATTERN),  
        send_group_messages  
    ),  
    group=0  
)  

# -----------------------------------------  
# پشتیبانی خصوصی  
# -----------------------------------------  

app.add_handler(  
    MessageHandler(  
        filters.ChatType.PRIVATE  
        & ~filters.COMMAND,  
        private_support  
    ),  
    group=1  
)  

# -----------------------------------------  
# ذخیره پیام‌های گروه  
# -----------------------------------------  

app.add_handler(  
    MessageHandler(  
        filters.ChatType.GROUPS  
        & filters.ALL,  
        save_group_message  
    ),  
    group=1  
)  

print("🍯 ربات حنا پوینت روشن شد...")  

app.run_polling(  
    drop_pending_updates=True  
)

=========================================================

اجرا

=========================================================

if name == "main":
main()
