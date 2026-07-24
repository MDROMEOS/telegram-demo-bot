import os
import sqlite3
import threading
import re
import zipfile
import gdown

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import BadRequest


# =====================================================
# 1. Google Drive থেকে অটো-ডাউনলোড সেকশন
# =====================================================

DRIVE_FILES = [
    {"id": "1CfbqdJP_T7XPG0-Va0J3eLZLma6qFohQ", "filename": "file1.zip"},
    {"id": "1KBPfUexBd5zBqcrrgSRXfb6DED5ExVqM", "filename": "file2.zip"}
]

def download_drive_files():
    for item in DRIVE_FILES:
        file_id = item["id"]
        output_name = item["filename"]
        
        if not os.path.exists(output_name):
            print(f"⏳ Google Drive থেকে {output_name} ডাউনলোড হচ্ছে...")
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, output_name, quiet=False)
            
            if output_name.endswith(".zip") and os.path.exists(output_name):
                print(f"📦 {output_name} আনজিপ করা হচ্ছে...")
                try:
                    with zipfile.ZipFile(output_name, 'r') as zip_ref:
                        zip_ref.extractall(".")
                    print(f"✅ {output_name} সফলভাবে এক্সট্র্যাক্ট হয়েছে!")
                except Exception as e:
                    print(f"⚠️ Extraction error: {e}")

# অ্যাপ চালুর আগে ফাইল নিশ্চিত ডাউনলোড করবে
download_drive_files()


# =====================================================
# 2. Telegram Bot Token & DB Connection
# =====================================================

TOKEN = "8757771538:AAFt6VmtbOkFJ_0QSxpAWW8cVX8VwTUfC_E"
DB_NAME = "database.db"


# =====================================================
# 3. অটোমেটিক ডাটাবেজ ও মেনু লোডার
# =====================================================

SEAT_FILES = {}
DIVISIONS_MAP = {}

def load_menu_from_db():
    global SEAT_FILES, DIVISIONS_MAP
    SEAT_FILES.clear()
    DIVISIONS_MAP.clear()

    if not os.path.exists(DB_NAME):
        print("❌ database.db পাওয়া যায়নি!")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT seat_key, division, district, seat_name FROM voters")
    rows = cursor.fetchall()

    for seat_key, division, district, seat_name in rows:
        SEAT_FILES[seat_key] = {
            "name": seat_name,
            "division": division,
            "district": district
        }

        if division not in DIVISIONS_MAP:
            DIVISIONS_MAP[division] = {}
        if district not in DIVISIONS_MAP[division]:
            DIVISIONS_MAP[division][district] = []

        if seat_key not in DIVISIONS_MAP[division][district]:
            DIVISIONS_MAP[division][district].append(seat_key)

    conn.close()
    print(f"✅ ডাটাবেজ থেকে {len(SEAT_FILES)} টি আসন লোড হয়েছে!")

load_menu_from_db()


# =====================================================
# 4. Web Server (Render Port Binding)
# =====================================================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running perfectly!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# =====================================================
# 5. SQLite Search Function
# =====================================================

def search_database(seat_key, search_input, search_type):
    if not os.path.exists(DB_NAME):
        return []

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    results = []

    try:
        if search_type == "multi":
            query = "SELECT * FROM voters WHERE seat_key = ?"
            params = [seat_key]

            for field, search_val in search_input.items():
                if search_val:
                    if field in ["name", "father", "mother", "address", "area", "upazila"]:
                        query += f" AND {field} LIKE ?"
                        params.append(f"%{search_val}%")
                    elif field in ["voter_no", "dob"]:
                        s_val = search_val.replace("-", "/").replace(".", "/")
                        query += f" AND ({field} LIKE ? OR REPLACE(REPLACE({field}, '-', '/'), '.', '/') LIKE ?)"
                        params.append(f"%{search_val}%")
                        params.append(f"%{s_val}%")

            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]

        else:
            col_map = {
                "demo_id": "voter_no",
                "name": "name",
                "father": "father",
                "mother": "mother",
                "dob": "dob"
            }
            col = col_map.get(search_type, "name")

            if search_type == "dob":
                s_val = str(search_input).replace("-", "/").replace(".", "/")
                query = f"SELECT * FROM voters WHERE seat_key = ? AND ({col} LIKE ? OR REPLACE(REPLACE({col}, '-', '/'), '.', '/') LIKE ?)"
                cursor.execute(query, [seat_key, f"%{search_input}%", f"%{s_val}%"])
            else:
                query = f"SELECT * FROM voters WHERE seat_key = ? AND {col} LIKE ?"
                cursor.execute(query, [seat_key, f"%{search_input}%"])

            results = [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        print("DB Search Error:", e)
    finally:
        conn.close()

    return results


def make_report(row):
    return f"""🪪 Demo Voter Report

━━━━━━━━━━━━━━━━━━━━

🔢 Demo ID: {row.get('voter_no') or 'N/A'}

🔖 সিরিয়াল: {row.get('serial') or 'N/A'}

👤 নাম: {row.get('name') or 'N/A'}

👨 পিতা: {row.get('father') or 'N/A'}

👩 মাতা: {row.get('mother') or 'N/A'}

🎂 জন্মতারিখ: {row.get('dob') or 'N/A'}

⚧ লিঙ্গ: {row.get('gender') or 'N/A'}

💼 পেশা: {row.get('occupation') or 'N/A'}

🏠 ঠিকানা: {row.get('address') or 'N/A'}

📍 এলাকা: {row.get('area') or 'N/A'}

📌 উপজেলা/থানা: {row.get('upazila') or 'N/A'}

📮 পোস্ট কোড: {row.get('post_code') or 'N/A'}

🌍 বিভাগ: {row.get('division') or 'N/A'}

🗺 জেলা: {row.get('district') or 'N/A'}

🏛 আসন: {row.get('seat_name') or 'N/A'}

━━━━━━━━━━━━━━━━━━━━"""


async def safe_edit_message(query, text, reply_markup=None, parse_mode=None):
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        else:
            raise e


# =====================================================
# 6. Menus & Handlers (পূর্বের বিভাগ/জেলা/আসন সিস্টেম)
# =====================================================

async def show_division_menu(query_or_message):
    keyboard = []
    divisions = list(DIVISIONS_MAP.keys())

    if not divisions:
        text = "⚠️ কোনো ডাটা পাওয়া যায়নি! গুগল ড্রাইভের ZIP ফাইলে database.db বা সঠিক CSV ফাইলগুলো সংসংযুক্ত আছে কিনা চেক করুন।"
        if hasattr(query_or_message, 'edit_message_text'):
            await safe_edit_message(query_or_message, text)
        else:
            await query_or_message.reply_text(text)
        return

    for i in range(0, len(divisions), 2):
        row = [InlineKeyboardButton(f"🌍 {divisions[i]}", callback_data=f"div_{divisions[i]}")]
        if i + 1 < len(divisions):
            row.append(InlineKeyboardButton(f"🌍 {divisions[i+1]}", callback_data=f"div_{divisions[i+1]}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🏠 Demo Search Bot\n\n🌍 একটি বিভাগ নির্বাচন করুন:"

    if hasattr(query_or_message, 'edit_message_text'):
        await safe_edit_message(query_or_message, text, reply_markup=reply_markup)
    else:
        await query_or_message.reply_text(text, reply_markup=reply_markup)


async def show_district_menu(query, context):
    division = context.user_data.get("division")
    districts = list(DIVISIONS_MAP.get(division, {}).keys())

    keyboard = []
    for i in range(0, len(districts), 2):
        row = [InlineKeyboardButton(f"🗺 {districts[i]}", callback_data=f"dis_{districts[i]}")]
        if i + 1 < len(districts):
            row.append(InlineKeyboardButton(f"🗺 {districts[i+1]}", callback_data=f"dis_{districts[i+1]}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 পূর্বের মেনু", callback_data="back_division")])

    await safe_edit_message(
        query,
        f"🌍 বিভাগ: {division}\n\n🗺 এখন একটি জেলা নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_seat_menu(query, context):
    division = context.user_data.get("division")
    district = context.user_data.get("district")

    seat_keys = DIVISIONS_MAP.get(division, {}).get(district, [])

    keyboard = []
    for i in range(0, len(seat_keys), 2):
        seat_1 = SEAT_FILES[seat_keys[i]]
        row = [InlineKeyboardButton(f"🏛 {seat_1['name']}", callback_data=seat_keys[i])]

        if i + 1 < len(seat_keys):
            seat_2 = SEAT_FILES[seat_keys[i+1]]
            row.append(InlineKeyboardButton(f"🏛 {seat_2['name']}", callback_data=seat_keys[i+1]))

        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 পূর্বের মেনু", callback_data="back_district")])

    await safe_edit_message(
        query,
        f"🌍 বিভাগ: {division}\n🗺 জেলা: {district}\n\n🏛 এখন একটি আসন নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_search_menu(query_or_message, context):
    seat = context.user_data.get("seat")
    info = SEAT_FILES.get(seat, {})

    keyboard = [
        [InlineKeyboardButton("⚡ Multi Search (AND Search)", callback_data="search_multi")],
        [InlineKeyboardButton("🆔 Demo ID", callback_data="search_demo_id"), InlineKeyboardButton("👤 Demo নাম", callback_data="search_name")],
        [InlineKeyboardButton("👨 Demo পিতার নাম", callback_data="search_father"), InlineKeyboardButton("👩 Demo মাতার নাম", callback_data="search_mother")],
        [InlineKeyboardButton("🎂 Demo জন্মতারিখ", callback_data="search_dob")],
        [InlineKeyboardButton("🔙 আসন পরিবর্তন", callback_data="back_seat")]
    ]

    text = (
        f"🌍 বিভাগ: {info.get('division', 'N/A')}\n"
        f"🗺 জেলা: {info.get('district', 'N/A')}\n"
        f"🏛 আসন: {info.get('name', 'N/A')}\n\n"
        "🔎 কোন তথ্য দিয়ে সার্চ করতে চান?"
    )

    if hasattr(query_or_message, 'edit_message_text'):
        await safe_edit_message(query_or_message, text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query_or_message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    load_menu_from_db()
    await show_division_menu(update.message)


async def send_page(query, context):
    results = context.user_data.get("results", [])
    page = context.user_data.get("page", 0)

    per_page = 10
    start_index = page * per_page
    end_index = start_index + per_page
    page_results = results[start_index:end_index]

    for row in page_results:
        report = make_report(row)
        await query.message.reply_text(report)

    keyboard = []
    if end_index < len(results):
        keyboard.append([InlineKeyboardButton("➡️ আরো দেখুন", callback_data="next_page")])

    keyboard.append([InlineKeyboardButton("🔎 নতুন সার্চ (পূর্বের মেনু)", callback_data="new_search")])
    keyboard.append([InlineKeyboardButton("🏠 মূল মেনু (Start)", callback_data="show_division")])

    await query.message.reply_text(
        f"📄 মোট ফলাফল: {len(results)} টি\n📑 দেখানো হয়েছে: {start_index + 1} - {min(end_index, len(results))}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "show_division":
        context.user_data.clear()
        await show_division_menu(query)
        return

    if data.startswith("div_"):
        div_name = data.replace("div_", "")
        context.user_data["division"] = div_name
        await show_district_menu(query, context)
        return

    if data.startswith("dis_"):
        dis_name = data.replace("dis_", "")
        context.user_data["district"] = dis_name
        await show_seat_menu(query, context)
        return

    if data == "back_division":
        await show_division_menu(query)
        return

    if data == "back_district":
        await show_district_menu(query, context)
        return

    if data in SEAT_FILES:
        context.user_data["seat"] = data
        context.user_data.pop("search_type", None)
        await show_search_menu(query, context)
        return

    if data == "back_seat":
        await show_seat_menu(query, context)
        return

    if data == "new_search":
        context.user_data.pop("results", None)
        context.user_data.pop("page", None)
        context.user_data.pop("search_type", None)
        await show_search_menu(query, context)
        return

    if data == "next_page":
        context.user_data["page"] = context.user_data.get("page", 0) + 1
        await send_page(query, context)
        return

    search_types = {
        "search_demo_id": {"type": "demo_id", "title": "🆔 Demo ID"},
        "search_name": {"type": "name", "title": "👤 Demo নাম"},
        "search_father": {"type": "father", "title": "👨 Demo পিতার নাম"},
        "search_mother": {"type": "mother", "title": "👩 Demo মাতার নাম"},
        "search_dob": {"type": "dob", "title": "🎂 Demo জন্মতারিখ"}
    }

    if data == "search_multi":
        context.user_data["search_type"] = "multi"
        text = (
            "⚡ **Multi Search (AND Search)**\n\n"
            "আপনি চাইলে নাম, পিতার নাম, মাতার নাম এবং জন্মতারিখ যেকোনো কম্বিনেশনে লিখে পাঠাতে পারেন।\n\n"
            "📌 **ফরম্যাট:**\n"
            "নাম: [আপনার নাম]\n"
            "পিতা: [পিতার নাম]\n"
            "মাতা: [মাতার নাম]\n"
            "জন্ম: [01/01/2000]"
        )
        await safe_edit_message(query, text, parse_mode="Markdown")
        return

    if data in search_types:
        info = search_types[data]
        context.user_data["search_type"] = info["type"]
        if info["type"] == "dob":
            text = "✅ 🎂 Demo জন্মতারিখ দিয়ে সার্চ নির্বাচন করা হয়েছে।\n\n✏️ এখন জন্মতারিখ লিখে পাঠান।\n\n📌 উদাহরণ: 01/01/2000"
        else:
            text = f"✅ {info['title']} দিয়ে সার্চ নির্বাচন করা হয়েছে।\n\n✏️ এখন আপনার {info['title']} লিখে পাঠান।"
        await safe_edit_message(query, text)


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "seat" not in context.user_data:
        await update.message.reply_text("⚠️ প্রথমে /start দিয়ে বিভাগ, জেলা ও আসন নির্বাচন করুন।")
        return

    if "search_type" not in context.user_data:
        await update.message.reply_text("⚠️ প্রথমে সার্চের ধরন নির্বাচন করুন।")
        return

    raw_text = update.message.text.strip()
    search_type = context.user_data["search_type"]
    seat = context.user_data["seat"]

    search_input = None

    if search_type == "multi":
        parsed = {"name": "", "father": "", "mother": "", "dob": ""}
        lines = raw_text.split("\n")

        for line in lines:
            if ":" in line:
                key, val = line.split(":", 1)
            elif "：" in line:
                key, val = line.split("：", 1)
            else:
                continue

            key = key.strip().lower()
            val = val.strip()

            if key in ["নাম", "name"]:
                parsed["name"] = val
            elif key in ["পিতা", "পিতার নাম", "father", "fathername"]:
                parsed["father"] = val
            elif key in ["মাতা", "মাতার নাম", "mother", "mothername"]:
                parsed["mother"] = val
            elif key in ["জন্ম", "জন্মতারিখ", "dob", "dateofbirth"]:
                parsed["dob"] = val

        non_empty = {k: v for k, v in parsed.items() if v}

        if not non_empty:
            if len(lines) == 1 and ":" not in raw_text and "：" not in raw_text:
                parsed["name"] = raw_text
                non_empty = {"name": raw_text}
            else:
                await update.message.reply_text("⚠️ সঠিক ফরম্যাটে তথ্য দিন।")
                return

        if len(non_empty) == 1:
            single_key = list(non_empty.keys())[0]
            search_type = single_key
            search_input = non_empty[single_key]
        else:
            search_input = parsed

    else:
        search_input = raw_text
        if search_type == "dob":
            if not re.match(r"^\d{2}[\/\-\.]\d{2}[\/\-\.]\d{4}$", search_input):
                await update.message.reply_text("⚠️ জন্মতারিখ সঠিক ফরম্যাটে লিখুন। (যেমন: 01/01/2000)")
                return

    await update.message.reply_text("🔍 Demo Data সার্চ করা হচ্ছে...\n\n⏳ একটু অপেক্ষা করুন।")

    results = search_database(seat, search_input, search_type)

    if not results:
        keyboard = [
            [InlineKeyboardButton("🔎 নতুন সার্চ (পূর্বের মেনু)", callback_data="new_search")],
            [InlineKeyboardButton("🏠 মূল মেনু (Start)", callback_data="show_division")]
        ]
        await update.message.reply_text("❌ কোনো Demo Data পাওয়া যায়নি।\n\n🔎 অন্য তথ্য দিয়ে আবার চেষ্টা করুন।", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    context.user_data["results"] = results
    context.user_data["page"] = 0

    first_results = results[:10]

    for row in first_results:
        report = make_report(row)
        await update.message.reply_text(report)

    keyboard = []
    if len(results) > 10:
        keyboard.append([InlineKeyboardButton("➡️ আরো দেখুন", callback_data="next_page")])

    keyboard.append([InlineKeyboardButton("🔎 নতুন সার্চ (পূর্বের মেনু)", callback_data="new_search")])
    keyboard.append([InlineKeyboardButton("🏠 মূল মেনু (Start)", callback_data="show_division")])

    summary_text = f"📄 মোট ফলাফল: {len(results)} টি\n\n📑 প্রথম {min(10, len(results))} টি রিপোর্ট দেখানো হয়েছে।"
    await update.message.reply_text(summary_text, reply_markup=InlineKeyboardMarkup(keyboard))


# =====================================================
# 7. Main Function
# =====================================================

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    print("🌐 Web Server চালু হয়েছে")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))

    print("🤖 Telegram Demo Search Bot চালু হয়েছে!")
    app.run_polling()


if __name__ == "__main__":
    main()
