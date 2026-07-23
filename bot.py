import csv
import os
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# ==================================================
# BOT TOKEN
# ==================================================

TOKEN = "8624453473:AAGruXbUjMfE9w7iVZ7J3ciWtG6wc5oZm_M"


# ==================================================
# CSV DATA FOLDER
# ==================================================

DATA_DIR = os.path.expanduser("~/demo_data")


# ==================================================
# আসন অনুযায়ী CSV ফাইল
# ==================================================

SEAT_FILES = {

    "1": os.path.join(
        DATA_DIR,
        "voters_nfmhzgip.csv"
    ),

    "2": os.path.join(
        DATA_DIR,
        "voters_h05css89.csv"
    ),

    "3": os.path.join(
        DATA_DIR,
        "voters_p_8guvlz.csv"
    ),

    "4": os.path.join(
        DATA_DIR,
        "voters_d_evylnn.csv"
    ),

}


# ==================================================
# জেলা / বিভাগ
# ==================================================

DISTRICT = "লক্ষীপুর"
DIVISION = "চট্টগ্রাম"


# ==================================================
# মূল মেনু
# ==================================================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "🗺 চট্টগ্রাম বিভাগ",
                callback_data="division"
            )
        ],

        [
            InlineKeyboardButton(
                "ℹ️ আমাদের সম্পর্কে",
                callback_data="about"
            )
        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ==================================================
# START
# ==================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(

        "🏠 Demo Search Bot-এ স্বাগতম!\n\n"
        "🗺 বিভাগ নির্বাচন করুন:",

        reply_markup=main_menu()

    )


# ==================================================
# CSV LOAD
# ==================================================

def load_csv(file_path):

    if not os.path.exists(file_path):

        return []


    data = []


    try:

        with open(
            file_path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                data.append(row)


    except Exception as e:

        print(
            "CSV Error:",
            e
        )

        return []


    return data


# ==================================================
# বয়স হিসাব
# ==================================================

def calculate_age(dob):

    try:

        birth_date = datetime.strptime(
            dob,
            "%d/%m/%Y"
        )

        today = datetime.today()


        age = (

            today.year
            - birth_date.year

            - (

                (
                    today.month,
                    today.day

                )

                <

                (
                    birth_date.month,
                    birth_date.day

                )

            )

        )


        return str(age)


    except Exception:

        return ""


# ==================================================
# লিঙ্গ বাংলায়
# ==================================================

def get_gender(gender):

    gender = (

        gender
        or ""

    ).strip().lower()


    if gender == "male":

        return "পুরুষ"


    if gender == "female":

        return "নারী"


    return gender


# ==================================================
# ফলাফল তৈরি
# ==================================================

def format_result(
    row,
    seat,
    index
):

    name = row.get(
        "name",
        ""
    )


    voter_no = row.get(
        "voter_no",
        ""
    )


    serial = row.get(
        "serial",
        ""
    )


    father = row.get(
        "father",
        ""
    )


    mother = row.get(
        "mother",
        ""
    )


    dob = row.get(
        "dob",
        ""
    )


    gender = get_gender(

        row.get(
            "gender",
            ""
        )

    )


    occupation = row.get(
        "occupation",
        ""
    )


    address = row.get(
        "address",
        ""
    )


    upazila = row.get(
        "upazila",
        ""
    )


    area = row.get(
        "area",
        ""
    )


    age = calculate_age(
        dob
    )


    if age:

        birth_text = (

            f"{dob} · {age} বছর"

        )

    else:

        birth_text = dob


    result = (

        f"🪪 {name}\n"

        f"────────────────────\n"

        f"🔢 NID  {voter_no}\n"

        f"🔖 সিরিয়াল  {serial}\n"

        f"👨 পিতা  {father}\n"

        f"👩 মাতা  {mother}\n"

        f"🎂 জন্ম  {birth_text}\n"

        f"⚧ লিঙ্গ  {gender}\n"

        f"💼 পেশা  {occupation}\n"

        f"🏠 ঠিকানা  {address}\n"

        f"📍 থানা  {upazila}\n"

        f"🗺 জেলা  {DISTRICT}  ·  "
        f"বিভাগ  {DIVISION}\n"

        f"🏛 আসন  {DISTRICT}-{seat}"
        f"  ·  কোড  {area}\n"

    )


    return result


# ==================================================
# ফলাফল দেখানো
# ==================================================

async def show_results(
    query,
    context,
    page=0
):

    results = context.user_data.get(
        "results",
        []
    )


    seat = context.user_data.get(
        "selected_seat",
        "1"
    )


    if not results:

        await query.message.edit_text(

            "❌ কোনো Demo তথ্য পাওয়া যায়নি।"

        )

        return


    per_page = 10


    start_index = (

        page
        * per_page

    )


    end_index = (

        start_index
        + per_page

    )


    current_results = results[

        start_index:end_index

    ]


    text = (

        f"🔎 মোট Demo ফলাফল: "
        f"{len(results)}\n\n"

    )


    for index, row in enumerate(

        current_results,

        start=start_index + 1

    ):

        text += (

            format_result(

                row,

                seat,

                index

            )

        )

        text += (

            "\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"

        )


    keyboard = []


    # আরও দেখুন

    if end_index < len(results):

        keyboard.append(

            [

                InlineKeyboardButton(

                    "➡️ আরও দেখুন",

                    callback_data=(

                        f"page_{page + 1}"

                    )

                )

            ]

        )


    keyboard.append(

        [

            InlineKeyboardButton(

                "🔍 নতুন সার্চ",

                callback_data="new_search"

            )

        ]

    )


    keyboard.append(

        [

            InlineKeyboardButton(

                "🏠 মূল মেনু",

                callback_data="home"

            )

        ]

    )


    await query.message.edit_text(

        text,

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# ==================================================
# BUTTON HANDLER
# ==================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    # ==============================================
    # বিভাগ
    # ==============================================

    if query.data == "division":

        keyboard = [

            [

                InlineKeyboardButton(

                    "🗺 চট্টগ্রাম বিভাগ",

                    callback_data="chattogram"

                )

            ],

            [

                InlineKeyboardButton(

                    "⬅️ পিছনে",

                    callback_data="home"

                )

            ],

        ]


        await query.message.edit_text(

            "🗺 বিভাগ বাছুন:",

            reply_markup=InlineKeyboardMarkup(

                keyboard

            )

        )


    # ==============================================
    # জেলা
    # ==============================================

    elif query.data == "chattogram":

        keyboard = [

            [

                InlineKeyboardButton(

                    "📍 লক্ষীপুর জেলা",

                    callback_data="lakshmipur"

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

            "📍 জেলা বাছুন:",

            reply_markup=InlineKeyboardMarkup(

                keyboard

            )

        )


    # ==============================================
    # আসন
    # ==============================================

    elif query.data == "lakshmipur":

        keyboard = [

            [

                InlineKeyboardButton(

                    "🏛 লক্ষীপুর-১",

                    callback_data="seat_1"

                )

            ],

            [

                InlineKeyboardButton(

                    "🏛 লক্ষীপুর-২",

                    callback_data="seat_2"

                )

            ],

            [

                InlineKeyboardButton(

                    "🏛 লক্ষীপুর-৩",

                    callback_data="seat_3"

                )

            ],

            [

                InlineKeyboardButton(

                    "🏛 লক্ষীপুর-৪",

                    callback_data="seat_4"

                )

            ],

            [

                InlineKeyboardButton(

                    "⬅️ পিছনে",

                    callback_data="chattogram"

                )

            ],

        ]


        await query.message.edit_text(

            "🏛 লক্ষীপুর জেলার আসন বাছুন:",

            reply_markup=InlineKeyboardMarkup(

                keyboard

            )

        )


    # ==============================================
    # আসন নির্বাচন
    # ==============================================

    elif query.data.startswith("seat_"):

        seat = query.data.replace(

            "seat_",

            ""

        )


        context.user_data[

            "selected_seat"

        ] = seat


        keyboard = [

            [

                InlineKeyboardButton(

                    "👤 নাম দিয়ে সার্চ",

                    callback_data="search_name"

                )

            ],

            [

                InlineKeyboardButton(

                    "👨 পিতার নাম দিয়ে সার্চ",

                    callback_data="search_father"

                )

            ],

            [

                InlineKeyboardButton(

                    "👩 মাতার নাম দিয়ে সার্চ",

                    callback_data="search_mother"

                )

            ],

            [

                InlineKeyboardButton(

                    "🎂 জন্মতারিখ দিয়ে সার্চ",

                    callback_data="search_dob"

                )

            ],

            [

                InlineKeyboardButton(

                    "🆔 NID দিয়ে সার্চ",

                    callback_data="search_voter_no"

                )

            ],

            [

                InlineKeyboardButton(

                    "⬅️ আসনে ফিরে যান",

                    callback_data="lakshmipur"

                )

            ],

        ]


        await query.message.edit_text(

            f"🏛 {DISTRICT}-{seat}\n\n"

            "🔍 সার্চের ধরন নির্বাচন করুন:",

            reply_markup=InlineKeyboardMarkup(

                keyboard

            )

        )


    # ==============================================
    # SEARCH TYPE
    # ==============================================

    elif query.data.startswith("search_"):

        search_type = query.data.replace(

            "search_",

            ""

        )


        context.user_data[

            "search_type"

        ] = search_type


        messages = {

            "name":

                "👤 নাম লিখুন:",


            "father":

                "👨 পিতার নাম লিখুন:",


            "mother":

                "👩 মাতার নাম লিখুন:",


            "dob":

                "🎂 জন্মতারিখ লিখুন:\n\n"

                "উদাহরণ:\n"

                "15/07/1993",


            "voter_no":

                "🆔 NID লিখুন:",

        }


        await query.message.edit_text(

            messages.get(

                search_type,

                "সার্চ তথ্য লিখুন:"

            )

        )


    # ==============================================
    # PAGINATION
    # ==============================================

    elif query.data.startswith("page_"):

        page = int(

            query.data.replace(

                "page_",

                ""

            )

        )


        await show_results(

            query,

            context,

            page

        )


    # ==============================================
    # NEW SEARCH
    # ==============================================

    elif query.data == "new_search":

        keyboard = [

            [

                InlineKeyboardButton(

                    "👤 নাম",

                    callback_data="search_name"

                )

            ],

            [

                InlineKeyboardButton(

                    "👨 পিতা",

                    callback_data="search_father"

                )

            ],

            [

                InlineKeyboardButton(

                    "👩 মাতা",

                    callback_data="search_mother"

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

                    "🆔 NID",

                    callback_data="search_voter_no"

                )

            ],

        ]


        await query.message.edit_text(

            "🔍 নতুন সার্চ নির্বাচন করুন:",

            reply_markup=InlineKeyboardMarkup(

                keyboard

            )

        )


    # ==============================================
    # HOME
    # ==============================================

    elif query.data == "home":

        context.user_data.clear()


        await query.message.edit_text(

            "🏠 মূল মেনু:",

            reply_markup=main_menu()

        )


    # ==============================================
    # ABOUT
    # ==============================================

    elif query.data == "about":

        await query.message.edit_text(

            "ℹ️ এটি একটি কাল্পনিক Demo Search Bot।\n\n"

            "শুধুমাত্র শেখা ও প্র্যাকটিসের উদ্দেশ্যে তৈরি।"

        )


# ==================================================
# TEXT SEARCH
# ==================================================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    search_type = context.user_data.get(

        "search_type"

    )


    seat = context.user_data.get(

        "selected_seat"

    )


    if not search_type or not seat:

        await update.message.reply_text(

            "⚠️ আগে বিভাগ, জেলা ও আসন নির্বাচন করুন।"

        )

        return


    search_value = (

        update.message.text

        .strip()

        .lower()

    )


    file_path = SEAT_FILES.get(

        seat

    )


    rows = load_csv(

        file_path

    )


    results = []


    for row in rows:

        value = (

            row.get(

                search_type,

                ""

            )

            or ""

        )


        value = (

            value

            .strip()

            .lower()

        )


        if search_value in value:

            results.append(

                row

            )


    context.user_data[

        "results"

    ] = results


    if not results:

        await update.message.reply_text(

            "❌ কোনো তথ্য পাওয়া যায়নি।"

        )

        return


    # ==============================================
    # প্রথম ১০টি ফলাফল
    # ==============================================

    per_page = 10


    current_results = results[

        :per_page

    ]


    text = (

        f"🔎 মোট ফলাফল: "
        f"{len(results)}\n\n"

    )


    for index, row in enumerate(

        current_results,

        start=1

    ):

        text += (

            format_result(

                row,

                seat,

                index

            )

        )


        text += (

            "\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"

        )


    keyboard = []


    if len(results) > 10:

        keyboard.append(

            [

                InlineKeyboardButton(

                    "➡️ আরও দেখুন",

                    callback_data="page_1"

                )

            ]

        )


    keyboard.append(

        [

            InlineKeyboardButton(

                "🔍 নতুন সার্চ",

                callback_data="new_search"

            )

        ]

    )


    keyboard.append(

        [

            InlineKeyboardButton(

                "🏠 মূল মেনু",

                callback_data="home"

            )

        ]

    )


    await update.message.reply_text(

        text,

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# ==================================================
# MAIN
# ==================================================

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

            text_handler

        )

    )


    print(

        "🤖 Demo Bot চালু হয়েছে..."

    )


    app.run_polling()


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    main()
