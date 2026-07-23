from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==============================
# তোমার Bot Token এখানে বসাও
# ==============================
TOKEN = "8624453473:AAGruXbUjMfE9w7iVZ7J3ciWtG6wc5oZm_M"


# ==============================
# কাল্পনিক Demo Data
# ==============================
DEMO_DATA = {
    "seat_1": [
        {
            "nid": "510673000001",
            "serial": "0001",
            "name": "মোঃ ডেমো ব্যক্তি ১",
            "father": "মোঃ ডেমো পিতা ১",
            "mother": "ডেমো মাতা ১",
            "dob": "15/07/1993",
            "gender": "পুরুষ",
            "profession": "ব্যবসা",
            "address": "ডেমো ঠিকানা, লক্ষ্মীপুর",
            "thana": "RAMGATI",
            "district": "লক্ষ্মীপুর",
            "division": "চট্টগ্রাম",
            "seat": "লক্ষ্মীপুর-১",
            "code": "510673",
        }
    ],

    "seat_2": [
        {
            "nid": "510673000002",
            "serial": "0002",
            "name": "ডেমো ব্যক্তি ২",
            "father": "ডেমো পিতা ২",
            "mother": "ডেমো মাতা ২",
            "dob": "20/08/1995",
            "gender": "পুরুষ",
            "profession": "চাকরি",
            "address": "ডেমো ঠিকানা, লক্ষ্মীপুর",
            "thana": "RAIPUR",
            "district": "লক্ষ্মীপুর",
            "division": "চট্টগ্রাম",
            "seat": "লক্ষ্মীপুর-২",
            "code": "510674",
        }
    ],

    "seat_3": [
        {
            "nid": "510673000003",
            "serial": "0003",
            "name": "ডেমো ব্যক্তি ৩",
            "father": "ডেমো পিতা ৩",
            "mother": "ডেমো মাতা ৩",
            "dob": "10/01/1990",
            "gender": "পুরুষ",
            "profession": "শিক্ষক",
            "address": "ডেমো ঠিকানা, লক্ষ্মীপুর",
            "thana": "LAXMIPUR",
            "district": "লক্ষ্মীপুর",
            "division": "চট্টগ্রাম",
            "seat": "লক্ষ্মীপুর-৩",
            "code": "510675",
        }
    ],

    "seat_4": [
        {
            "nid": "510673000004",
            "serial": "0004",
            "name": "ডেমো ব্যক্তি ৪",
            "father": "ডেমো পিতা ৪",
            "mother": "ডেমো মাতা ৪",
            "dob": "25/12/1992",
            "gender": "পুরুষ",
            "profession": "সরকারী চাকুরী",
            "address": "ডেমো ঠিকানা, রামগতি, লক্ষ্মীপুর",
            "thana": "RAMGATI",
            "district": "লক্ষ্মীপুর",
            "division": "চট্টগ্রাম",
            "seat": "লক্ষ্মীপুর-৪",
            "code": "510676",
        }
    ],
}


# ==============================
# Main Menu
# ==============================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📍 চট্টগ্রাম বিভাগ", callback_data="division")],
        [InlineKeyboardButton("ℹ️ সম্পর্কে", callback_data="about")],
    ]

    return InlineKeyboardMarkup(keyboard)


# ==============================
# Start Command
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Demo Search Bot-এ স্বাগতম!\n\n"
        "এটি একটি সম্পূর্ণ কাল্পনিক Demo System।\n"
        "শুধুমাত্র শেখা ও পরীক্ষার উদ্দেশ্যে তৈরি।\n\n"
        "📍 বিভাগ নির্বাচন করুন:",
        reply_markup=main_menu(),
    )


# ==============================
# Button Handler
# ==============================
async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    # বিভাগ
    if query.data == "division":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📍 লক্ষ্মীপুর জেলা",
                    callback_data="district"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ মূল মেনু",
                    callback_data="home"
                )
            ],
        ]

        await query.message.edit_text(
            "📍 জেলা নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


    # জেলা
    elif query.data == "district":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🏛 লক্ষ্মীপুর-১",
                    callback_data="seat_1"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏛 লক্ষ্মীপুর-২",
                    callback_data="seat_2"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏛 লক্ষ্মীপুর-৩",
                    callback_data="seat_3"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏛 লক্ষ্মীপুর-৪",
                    callback_data="seat_4"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ পিছনে",
                    callback_data="division"
                )
            ],
        ]

        await query.message.edit_text(
            "🏛 আসন নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


    # আসন
    elif query.data.startswith("seat_"):

        seat = query.data

        context.user_data["selected_seat"] = seat

        seat_name = {
            "seat_1": "লক্ষ্মীপুর-১",
            "seat_2": "লক্ষ্মীপুর-২",
            "seat_3": "লক্ষ্মীপুর-৩",
            "seat_4": "লক্ষ্মীপুর-৪",
        }

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔍 Demo Search",
                    callback_data="search"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ আসনে ফিরে যান",
                    callback_data="district"
                )
            ],
        ]

        await query.message.edit_text(
            f"🏛 নির্বাচিত আসন: {seat_name[seat]}\n\n"
            "🔍 Demo Search চাপুন।\n"
            "তারপর NID অথবা জন্মতারিখ লিখুন।",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


    # Search Button
    elif query.data == "search":

        await query.message.edit_text(
            "🔍 Demo Search চালু হয়েছে।\n\n"
            "এখন NID অথবা জন্মতারিখ লিখুন।\n\n"
            "উদাহরণ:\n"
            "510673000004\n"
            "অথবা\n"
            "25/12/1992"
        )

        context.user_data["waiting_search"] = True


    # Home
    elif query.data == "home":

        await query.message.edit_text(
            "🏠 মূল মেনু:",
            reply_markup=main_menu(),
        )


    # About
    elif query.data == "about":

        await query.message.edit_text(
            "ℹ️ এটি একটি কাল্পনিক Demo Search Bot।\n\n"
            "কোনো বাস্তব ব্যক্তিগত তথ্য ব্যবহার করা হয়নি।\n"
            "শুধুমাত্র শেখা ও পরীক্ষার উদ্দেশ্যে তৈরি।"
        )


# ==============================
# Search Handler
# ==============================
async def search_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get("waiting_search"):
        return

    search_value = update.message.text.strip()

    selected_seat = context.user_data.get(
        "selected_seat"
    )

    if not selected_seat:
        await update.message.reply_text(
            "❌ আগে একটি আসন নির্বাচন করুন।"
        )
        return

    records = DEMO_DATA.get(
        selected_seat,
        []
    )

    results = []

    for record in records:

        if (
            search_value == record["nid"]
            or search_value == record["dob"]
        ):
            results.append(record)


    context.user_data["waiting_search"] = False


    if not results:

        await update.message.reply_text(
            "❌ কোনো Demo তথ্য পাওয়া যায়নি।"
        )

        return


    for record in results:

        text = (
            f"🪪 {record['name']}\n"
            "────────────────────\n"
            f"🔢 NID  {record['nid']}\n"
            f"🔖 সিরিয়াল  {record['serial']}\n"
            f"👨 পিতা  {record['father']}\n"
            f"👩 মাতা  {record['mother']}\n"
            f"🎂 জন্ম  {record['dob']}\n"
            f"⚧ লিঙ্গ  {record['gender']}\n"
            f"💼 পেশা  {record['profession']}\n"
            f"🏠 ঠিকানা  {record['address']}\n"
            f"📍 থানা  {record['thana']}\n"
            f"🗺 জেলা  {record['district']}  ·  "
            f"বিভাগ  {record['division']}\n"
            f"🏛 আসন  {record['seat']}  ·  "
            f"কোড  {record['code']}"
        )

        await update.message.reply_text(text)


# ==============================
# Main
# ==============================
def main():

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search_handler
        )
    )

    print(
        "🤖 Demo Bot সফলভাবে চালু হয়েছে!"
    )

    app.run_polling()


if __name__ == "__main__":
    main()
