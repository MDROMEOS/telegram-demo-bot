import json
import urllib.request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==========================================
# BOT TOKEN
# ==========================================
TOKEN = "8624453473:AAGruXbUjMfE9w7iVZ7J3ciWtG6wc5oZm_M"


# ==========================================
# Google Drive Seat Data Direct URLs
# ==========================================
SEAT_URLS = {
    "seat_1": "https://drive.google.com/uc?export=download&id=1kfwzt0TTFE2RUHq2VDEc9dM3IoEw8ANW",
    "seat_2": "https://drive.google.com/uc?export=download&id=15P8j9bU2-25YctdJmRC5MMBOUaGo5d-Y",
    "seat_3": "https://drive.google.com/uc?export=download&id=1zzcfwzkMUfNLq5Ok5NZKbaPGlP34RnQb",
    "seat_4": "https://drive.google.com/uc?export=download&id=1CkaoqLOoO3NORHSOIqoU3mAclLiewlBA",
}

SEAT_NAMES = {
    "seat_1": "লক্ষ্মীপুর-১",
    "seat_2": "লক্ষ্মীপুর-২",
    "seat_3": "লক্ষ্মীপুর-৩",
    "seat_4": "লক্ষ্মীপুর-৪",
}

# Global Data Cache
DRIVE_DATA_CACHE = {}


def load_drive_data():
    """Download and load JSON data from Google Drive URLs"""
    global DRIVE_DATA_CACHE
    print("⏳ গুগল ড্রাইভ থেকে ৪টি আসনের ডেটা লোড করা হচ্ছে...")
    for seat_key, url in SEAT_URLS.items():
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req) as response:
                content = response.read().decode("utf-8")
                DRIVE_DATA_CACHE[seat_key] = json.loads(content)
                print(f"✅ {SEAT_NAMES[seat_key]} ডেটা সফলভাবে লোড হয়েছে।")
        except Exception as e:
            print(f"❌ {SEAT_NAMES[seat_key]} লোড করতে সমস্যা: {e}")
            DRIVE_DATA_CACHE[seat_key] = []


# ==========================================
# Main Menu
# ==========================================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📍 চট্টগ্রাম বিভাগ", callback_data="division")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==========================================
# Start Command
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🤖 Advanced Search Bot\n\n"
        "গুগল ড্রাইভ ডেটাবেজ যুক্ত করা হয়েছে।\n\n"
        "📍 বিভাগ নির্বাচন করুন:",
        reply_markup=main_menu(),
    )


# ==========================================
# Button Handler
# ==========================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Division
    if data == "division":
        keyboard = [
            [
                InlineKeyboardButton(
                    "📍 লক্ষ্মীপুর জেলা", callback_data="district"
                )
            ],
            [InlineKeyboardButton("🏠 মূল মেনু", callback_data="home")],
        ]
        await query.edit_message_text(
            "📍 জেলা নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # District
    elif data == "district":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🏛 লক্ষ্মীপুর-১", callback_data="seat_1"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏛 লক্ষ্মীপুর-২", callback_data="seat_2"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏛 লক্ষ্মীপুর-৩", callback_data="seat_3"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏛 লক্ষ্মীপুর-৪", callback_data="seat_4"
                )
            ],
            [InlineKeyboardButton("⬅️ পিছনে", callback_data="division")],
        ]
        await query.edit_message_text(
            "🏛 আসন নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # Seat
    elif data.startswith("seat_"):
        context.user_data["seat"] = data
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔍 Search Menu", callback_data="search_menu"
                )
            ],
            [InlineKeyboardButton("⬅️ আসন নির্বাচন", callback_data="district")],
        ]
        await query.edit_message_text(
            f"🏛 নির্বাচিত আসন: {SEAT_NAMES.get(data, 'অজানা')}\n\n"
            "নিচের Search Menu চাপুন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # Search Menu
    elif data == "search_menu":
        keyboard = [
            [InlineKeyboardButton("🔢 ID / NID", callback_data="search_id")],
            [InlineKeyboardButton("🎂 জন্মতারিখ", callback_data="search_dob")],
            [InlineKeyboardButton("👤 নাম", callback_data="search_name")],
            [InlineKeyboardButton("👨 পিতার নাম", callback_data="search_father")],
            [InlineKeyboardButton("👩 মাতার নাম", callback_data="search_mother")],
            [InlineKeyboardButton("⬅️ পিছনে", callback_data="district")],
        ]
        await query.edit_message_text(
            "🔍 Search করার পদ্ধতি নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # Search Type Selection
    elif data.startswith("search_"):
        search_type = data.replace("search_", "")
        context.user_data["search_type"] = search_type

        labels = {
            "id": "🔢 ID / NID",
            "dob": "🎂 জন্মতারিখ",
            "name": "👤 নাম",
            "father": "👨 পিতার নাম",
            "mother": "👩 মাতার নাম",
        }

        await query.edit_message_text(
            f"{labels.get(search_type, '🔍 Search')}\n\n"
            "আপনার Search Value লিখুন:"
        )
        context.user_data["waiting_search"] = True

    # Home
    elif data == "home":
        context.user_data.clear()
        await query.edit_message_text(
            "🏠 মূল মেনু:", reply_markup=main_menu()
        )

    # About
    elif data == "about":
        await query.edit_message_text(
            "ℹ️ Search Bot\n\n"
            "গুগল ড্রাইভে থাকা ৪টি আসনের ডেটাবেজ সাপোর্ট করে।"
        )


# ==========================================
# Search Logic Handler
# ==========================================
async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_search"):
        return

    value = update.message.text.strip()
    search_type = context.user_data.get("search_type")
    selected_seat = context.user_data.get("seat")  # seat_1, seat_2, etc.

    field_map = {
        "id": ["id", "nid", "voter_id", "code"],
        "dob": ["dob", "date_of_birth"],
        "name": ["name", "voter_name"],
        "father": ["father", "father_name"],
        "mother": ["mother", "mother_name"],
    }

    possible_fields = field_map.get(search_type, [search_type])

    # Get data from Google Drive Cache for the selected seat
    seat_data = DRIVE_DATA_CACHE.get(selected_seat, [])

    results = []
    for person in seat_data:
        matched = False
        for field in possible_fields:
            if field in person and person[field]:
                if value.lower() in str(person[field]).lower():
                    matched = True
                    break
        if matched:
            results.append(person)

    context.user_data["waiting_search"] = False

    if not results:
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 আবার Search", callback_data="search_menu"
                )
            ],
            [InlineKeyboardButton("🏠 মূল মেনু", callback_data="home")],
        ]
        await update.message.reply_text(
            "❌ ড্রাইভ ডেটাবেজে কোনো তথ্য পাওয়া যায়নি।",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    await update.message.reply_text(f"🔎 মোট ফলাফল পাওয়া গেছে: {len(results)}")

    # Display Top 10 Results
    for person in results[:10]:
        report = (
            f"🪪 {person.get('name', person.get('voter_name', 'N/A'))}\n"
            "────────────────────\n"
            f"🔢 ID / NID: {person.get('id', person.get('nid', 'N/A'))}\n"
            f"🔖 সিরিয়াল: {person.get('serial', 'N/A')}\n"
            f"👨 পিতা: {person.get('father', person.get('father_name', 'N/A'))}\n"
            f"👩 মাতা: {person.get('mother', person.get('mother_name', 'N/A'))}\n"
            f"🎂 জন্ম: {person.get('dob', person.get('date_of_birth', 'N/A'))}\n"
            f"⚧ লিঙ্গ: {person.get('gender', 'N/A')}\n"
            f"💼 পেশা: {person.get('profession', 'N/A')}\n"
            f"🏠 ঠিকানা: {person.get('address', 'N/A')}\n"
            f"📍 থানা: {person.get('thana', 'N/A')}\n"
            f"🗺 জেলা: {person.get('district', 'N/A')}  ·  বিভাগ: {person.get('division', 'N/A')}\n"
            f"🏛 আসন: {person.get('seat', SEAT_NAMES.get(selected_seat, 'N/A'))}  ·  কোড: {person.get('code', 'N/A')}"
        )
        await update.message.reply_text(report)

    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 নতুন Search", callback_data="search_menu"
            )
        ],
        [InlineKeyboardButton("🏠 মূল মেনু", callback_data="home")],
    ]
    await update.message.reply_text(
        "আরও Search করতে নিচের অপশন ব্যবহার করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ==========================================
# Main Application
# ==========================================
def main():
    # Load Google Drive data on startup
    load_drive_data()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler)
    )

    print("🤖 Advanced Google Drive Search Bot চালু হয়েছে!")
    app.run_polling()


if __name__ == "__main__":
    main()
