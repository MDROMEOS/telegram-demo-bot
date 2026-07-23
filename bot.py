from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8624453473:AAGruXbUjMfE9w7iVZ7J3ciWtG6wc5oZm_M"


# ==========================================
# কাল্পনিক Demo Data
# ==========================================

DEMO_DATA = [
    {
        "id": "510673000001",
        "serial": "0601",
        "name": "মোঃ ডেমো ব্যক্তি ১",
        "father": "মোঃ ডেমো পিতা ১",
        "mother": "ডেমো মাতা ১",
        "dob": "15/07/1993",
        "gender": "পুরুষ",
        "profession": "ব্যবসা",
        "address": "ডেমো ঠিকানা, রামগতি, লক্ষ্মীপুর",
        "thana": "RAMGATI",
        "district": "লক্ষ্মীপুর",
        "division": "চট্টগ্রাম",
        "seat": "লক্ষ্মীপুর-১",
        "code": "510673",
    },
    {
        "id": "510673000002",
        "serial": "0602",
        "name": "ডেমো ব্যক্তি ২",
        "father": "ডেমো পিতা ২",
        "mother": "ডেমো মাতা ২",
        "dob": "20/08/1995",
        "gender": "পুরুষ",
        "profession": "চাকরি",
        "address": "ডেমো ঠিকানা, রায়পুর, লক্ষ্মীপুর",
        "thana": "RAIPUR",
        "district": "লক্ষ্মীপুর",
        "division": "চট্টগ্রাম",
        "seat": "লক্ষ্মীপুর-২",
        "code": "510674",
    },
    {
        "id": "510673000003",
        "serial": "0603",
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
    },
    {
        "id": "510673000004",
        "serial": "0609",
        "name": "মোঃ তারেক হোসেন",
        "father": "মোঃ ফারুক হোসেন",
        "mother": "মারজাহান বেগম",
        "dob": "15/07/1993",
        "gender": "পুরুষ",
        "profession": "সরকারী চাকুরী",
        "address": "ডেমো ঠিকানা, রামগতি, লক্ষ্মীপুর",
        "thana": "RAMGATI",
        "district": "লক্ষ্মীপুর",
        "division": "চট্টগ্রাম",
        "seat": "লক্ষ্মীপুর-৪",
        "code": "510676",
    },
]


# ==========================================
# Main Menu
# ==========================================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "📍 চট্টগ্রাম বিভাগ",
                callback_data="division"
            )
        ],
        [
            InlineKeyboardButton(
                "ℹ️ About",
                callback_data="about"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ==========================================
# Start
# ==========================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(
        "🤖 Advanced Demo Search Bot\n\n"
        "⚠️ এটি সম্পূর্ণ কাল্পনিক Demo System।\n"
        "শুধুমাত্র পরীক্ষামূলক ব্যবহারের জন্য।\n\n"
        "📍 বিভাগ নির্বাচন করুন:",
        reply_markup=main_menu(),
    )


# ==========================================
# Button Handler
# ==========================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data


    # --------------------------
    # Division
    # --------------------------

    if data == "division":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📍 লক্ষ্মীপুর জেলা",
                    callback_data="district"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 মূল মেনু",
                    callback_data="home"
                )
            ],
        ]

        await query.edit_message_text(
            "📍 জেলা নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )


    # --------------------------
    # District
    # --------------------------

    elif data == "district":

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

        await query.edit_message_text(
            "🏛 আসন নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )


    # --------------------------
    # Seat
    # --------------------------

    elif data.startswith("seat_"):

        context.user_data["seat"] = data

        seat_name = {
            "seat_1": "লক্ষ্মীপুর-১",
            "seat_2": "লক্ষ্মীপুর-২",
            "seat_3": "লক্ষ্মীপুর-৩",
            "seat_4": "লক্ষ্মীপুর-৪",
        }

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔍 Search Menu",
                    callback_data="search_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ আসন নির্বাচন",
                    callback_data="district"
                )
            ],
        ]

        await query.edit_message_text(
            f"🏛 নির্বাচিত আসন: "
            f"{seat_name[data]}\n\n"
            "নিচের Search Menu চাপুন:",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )


    # --------------------------
    # Search Menu
    # --------------------------

    elif data == "search_menu":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔢 Demo ID",
                    callback_data="search_id"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎂 জন্মতারিখ",
                    callback_data="search_dob"
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 নাম",
                    callback_data="search_name"
                )
            ],
            [
                InlineKeyboardButton(
                    "👨 পিতার নাম",
                    callback_data="search_father"
                )
            ],
            [
                InlineKeyboardButton(
                    "👩 মাতার নাম",
                    callback_data="search_mother"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ পিছনে",
                    callback_data="district"
                )
            ],
        ]

        await query.edit_message_text(
            "🔍 Search করার পদ্ধতি নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )


    # --------------------------
    # Search Type
    # --------------------------

    elif data.startswith("search_"):

        search_type = data.replace(
            "search_",
            ""
        )

        context.user_data[
            "search_type"
        ] = search_type

        labels = {
            "id": "🔢 Demo ID",
            "dob": "🎂 জন্মতারিখ",
            "name": "👤 নাম",
            "father": "👨 পিতার নাম",
            "mother": "👩 মাতার নাম",
        }

        await query.edit_message_text(
            f"{labels.get(search_type, '🔍 Search')}\n\n"
            "আপনার Search Value লিখুন:\n\n"
            "উদাহরণ:\n"
            "510673000004\n"
            "অথবা\n"
            "15/07/1993"
        )

        context.user_data[
            "waiting_search"
        ] = True


    # --------------------------
    # Home
    # --------------------------

    elif data == "home":

        context.user_data.clear()

        await query.edit_message_text(
            "🏠 মূল মেনু:",
            reply_markup=main_menu(),
        )


    # --------------------------
    # About
    # --------------------------

    elif data == "about":

        await query.edit_message_text(
            "ℹ️ Advanced Demo Search Bot\n\n"
            "এই Bot সম্পূর্ণ কাল্পনিক Demo Data "
            "দিয়ে তৈরি করা হয়েছে।"
        )


# ==========================================
# Search
# ==========================================

async def search_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get(
        "waiting_search"
    ):
        return


    value = update.message.text.strip()

    search_type = context.user_data.get(
        "search_type"
    )

    selected_seat = context.user_data.get(
        "seat"
    )


    field_map = {
        "id": "id",
        "dob": "dob",
        "name": "name",
        "father": "father",
        "mother": "mother",
    }


    field = field_map.get(
        search_type
    )


    if not field:

        await update.message.reply_text(
            "❌ Search Type পাওয়া যায়নি।"
        )

        return


    results = []

    for person in DEMO_DATA:

        if (
            person["seat"]
            == {
                "seat_1": "লক্ষ্মীপুর-১",
                "seat_2": "লক্ষ্মীপুর-২",
                "seat_3": "লক্ষ্মীপুর-৩",
                "seat_4": "লক্ষ্মীপুর-৪",
            }.get(
                selected_seat
            )
        ):

            if value.lower() in person[
                field
            ].lower():

                results.append(
                    person
                )


    context.user_data[
        "waiting_search"
    ] = False


    if not results:

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 আবার Search",
                    callback_data="search_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 মূল মেনু",
                    callback_data="home"
                )
            ],
        ]

        await update.message.reply_text(
            "❌ কোনো Demo তথ্য পাওয়া যায়নি।",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return


    await update.message.reply_text(
        f"🔎 মোট Demo ফলাফল: "
        f"{len(results)}"
    )


    for person in results:

        report = (
            f"🪪 {person['name']}\n"
            "────────────────────\n"
            f"🔢 Demo ID  {person['id']}\n"
            f"🔖 সিরিয়াল  {person['serial']}\n"
            f"👨 পিতা  {person['father']}\n"
            f"👩 মাতা  {person['mother']}\n"
            f"🎂 জন্ম  {person['dob']}\n"
            f"⚧ লিঙ্গ  {person['gender']}\n"
            f"💼 পেশা  {person['profession']}\n"
            f"🏠 ঠিকানা  {person['address']}\n"
            f"📍 থানা  {person['thana']}\n"
            f"🗺 জেলা  {person['district']}"
            f"  ·  বিভাগ  {person['division']}\n"
            f"🏛 আসন  {person['seat']}"
            f"  ·  কোড  {person['code']}"
        )


        await update.message.reply_text(
            report
        )


    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 নতুন Search",
                callback_data="search_menu"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 মূল মেনু",
                callback_data="home"
            )
        ],
    ]


    await update.message.reply_text(
        "আরও Search করতে নিচের অপশন ব্যবহার করুন:",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


# ==========================================
# Main
# ==========================================

def main():

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            search_handler
        )
    )


    print(
        "🤖 Advanced Demo Bot চালু হয়েছে!"
    )


    app.run_polling()


if __name__ == "__main__":
    main()
