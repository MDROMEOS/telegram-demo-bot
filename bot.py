import os
import csv
import zipfile
import threading
import io

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


# =====================================================
# 1. Telegram Bot Token
# =====================================================

TOKEN = "8757771538:AAFt6VmtbOkFJ_0QSxpAWW8cVX8VwTUfC_E"


# =====================================================
# 2. ZIP ফাইলের নাম
# =====================================================

SEAT_FILES = {

    "seat_1": {
        "name": "আসন-১",
        "zip": "voters_nfmhzgip.zip",
        "csv": "voters_nfmhzgip.csv",
    },

    "seat_2": {
        "name": "আসন-২",
        "zip": "voters_h05css89.zip",
        "csv": "voters_h05css89.csv",
    },

    "seat_3": {
        "name": "আসন-৩",
        "zip": "voters_p_8guvlz.zip",
        "csv": "voters_p_8guvlz.csv",
    },

    "seat_4": {
        "name": "আসন-৪",
        "zip": "voters_d_evylnn.zip",
        "csv": "voters_d_evylnn.csv",
    },

}


# =====================================================
# 3. Render Web Server
# =====================================================

web_app = Flask(__name__)


@web_app.route("/")
def home():

    return "Telegram Demo Bot is running!"


@web_app.route("/health")
def health():

    return "OK"


def run_web_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    web_app.run(
        host="0.0.0.0",
        port=port
    )


# =====================================================
# 4. Column Name Normalize
# =====================================================

def normalize(text):

    return (

        str(text)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")

    )


# =====================================================
# 5. ZIP-এর ভিতরে CSV খোঁজা
# =====================================================

def find_csv_in_zip(
    zip_path,
    expected_csv
):

    if not os.path.exists(zip_path):

        return None


    try:

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as z:

            # আগে নির্দিষ্ট CSV খুঁজবে

            for name in z.namelist():

                if name.endswith(
                    expected_csv
                ):

                    return name


            # না পেলে প্রথম CSV নেবে

            for name in z.namelist():

                if name.lower().endswith(
                    ".csv"
                ):

                    return name


    except Exception as e:

        print(
            "ZIP Error:",
            e
        )


    return None


# =====================================================
# 6. CSV Search
# সব Matching Result বের করবে
# =====================================================

def search_zip(
    zip_path,
    csv_name,
    search_text,
    search_type
):

    csv_inside = find_csv_in_zip(

        zip_path,

        csv_name

    )


    if not csv_inside:

        print(
            f"CSV পাওয়া যায়নি: {csv_name}"
        )

        return []


    results = []


    try:

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as z:

            with z.open(
                csv_inside
            ) as file:

                text_file = io.TextIOWrapper(

                    file,

                    encoding="utf-8-sig",

                    errors="replace",

                    newline=""

                )


                reader = csv.DictReader(
                    text_file
                )


                for row in reader:

                    # =================================
                    # কোন কলামে সার্চ হবে
                    # =================================

                    if search_type == "demo_id":

                        search_columns = [

                            "demo_id",
                            "demoid",
                            "id"

                        ]


                    elif search_type == "name":

                        search_columns = [

                            "name",
                            "fullname",
                            "নাম"

                        ]


                    elif search_type == "father":

                        search_columns = [

                            "father",
                            "fathername",
                            "পিতা"

                        ]


                    elif search_type == "mother":

                        search_columns = [

                            "mother",
                            "mothername",
                            "মাতা"

                        ]


                    elif search_type == "dob":

                        search_columns = [

                            "dob",
                            "dateofbirth",
                            "birthdate",
                            "জন্ম"

                        ]


                    else:

                        search_columns = []


                    # =================================
                    # CSV Column Normalize
                    # =================================

                    normalized_row = {

                        normalize(k): str(v or "")

                        for k, v in row.items()

                    }


                    # =================================
                    # Search Value
                    # =================================

                    found_value = ""


                    for column in search_columns:

                        column_name = normalize(
                            column
                        )


                        if column_name in normalized_row:

                            found_value = normalized_row[

                                column_name

                            ]

                            break


                    # =================================
                    # জন্মতারিখ Search
                    #
                    # 01/01/2000
                    # 01-01-2000
                    # 2000-01-01
                    #
                    # সব Format মিলানোর চেষ্টা
                    # =================================

                    if search_type == "dob":

                        search_value = (

                            search_text

                            .strip()

                            .replace(
                                "-",
                                "/"
                            )

                            .replace(
                                ".",
                                "/"
                            )

                        )


                        found_value_normalized = (

                            found_value

                            .strip()

                            .replace(
                                "-",
                                "/"
                            )

                            .replace(
                                ".",
                                "/"
                            )

                        )


                    else:

                        search_value = (

                            search_text

                            .strip()

                            .lower()

                        )


                        found_value_normalized = (

                            found_value

                            .strip()

                            .lower()

                        )


                    # =================================
                    # Match Check
                    # =================================

                    if (

                        search_value

                        in found_value_normalized

                    ):

                        results.append(

                            dict(row)

                        )


    except Exception as e:

        print(

            "CSV Search Error:",

            e

        )


    return results


# =====================================================
# 7. CSV Value নেওয়া
# =====================================================

def get_value(
    row,
    names
):

    normalized_row = {

        normalize(k): v

        for k, v in row.items()

    }


    for name in names:

        value = normalized_row.get(

            normalize(name)

        )


        if value:

            return str(

                value

            ).strip()


    return "N/A"


# =====================================================
# 8. Demo Report
# =====================================================

def make_report(
    row,
    seat_name
):

    name = get_value(

        row,

        [
            "name",
            "fullname",
            "নাম"
        ]

    )


    demo_id = get_value(

        row,

        [
            "demo_id",
            "demoid",
            "id"
        ]

    )


    serial = get_value(

        row,

        [
            "serial",
            "serialnumber",
            "সিরিয়াল"
        ]

    )


    father = get_value(

        row,

        [
            "father",
            "fathername",
            "পিতা"
        ]

    )


    mother = get_value(

        row,

        [
            "mother",
            "mothername",
            "মাতা"
        ]

    )


    dob = get_value(

        row,

        [
            "dob",
            "dateofbirth",
            "birthdate",
            "জন্ম"
        ]

    )


    gender = get_value(

        row,

        [
            "gender",
            "sex",
            "লিঙ্গ"
        ]

    )


    occupation = get_value(

        row,

        [
            "occupation",
            "profession",
            "পেশা"
        ]

    )


    address = get_value(

        row,

        [
            "address",
            "ঠিকানা"
        ]

    )


    thana = get_value(

        row,

        [
            "thana",
            "policestation",
            "থানা"
        ]

    )


    district = get_value(

        row,

        [
            "district",
            "জেলা"
        ]

    )


    division = get_value(

        row,

        [
            "division",
            "বিভাগ"
        ]

    )


    code = get_value(

        row,

        [
            "code",
            "seatcode",
            "আসনকোড"
        ]

    )


    return f"""🪪 {name}

────────────────────

🔢 Demo ID  {demo_id}

🔖 সিরিয়াল  {serial}

👨 পিতা  {father}

👩 মাতা  {mother}

🎂 জন্ম  {dob}

⚧ লিঙ্গ  {gender}

💼 পেশা  {occupation}

🏠 ঠিকানা  {address}

📍 থানা  {thana}

🗺 জেলা  {district} · বিভাগ  {division}

🏛 আসন  {seat_name} · কোড  {code}"""


# =====================================================
# 9. Search Menu
# =====================================================

async def show_search_menu(

    query,

    context

):

    seat = context.user_data.get(

        "seat",

        "seat_1"

    )


    seat_name = SEAT_FILES[seat][

        "name"

    ]


    keyboard = [

        [

            InlineKeyboardButton(

                "🆔 Demo ID",

                callback_data="search_demo_id"

            ),

            InlineKeyboardButton(

                "👤 Demo নাম",

                callback_data="search_name"

            ),

        ],

        [

            InlineKeyboardButton(

                "👨 Demo পিতার নাম",

                callback_data="search_father"

            ),

            InlineKeyboardButton(

                "👩 Demo মাতার নাম",

                callback_data="search_mother"

            ),

        ],

        [

            InlineKeyboardButton(

                "🎂 Demo জন্মতারিখ",

                callback_data="search_dob"

            ),

        ],

        [

            InlineKeyboardButton(

                "🏠 আসন পরিবর্তন",

                callback_data="change_seat"

            ),

        ],

    ]


    await query.edit_message_text(

        f"🏠 Demo Search Bot\n\n"

        f"📍 নির্বাচিত: {seat_name}\n\n"

        "🆔 Demo ID দিয়ে সার্চ\n"

        "👤 Demo নাম দিয়ে সার্চ\n"

        "👨 Demo পিতার নাম দিয়ে সার্চ\n"

        "👩 Demo মাতার নাম দিয়ে সার্চ\n"

        "🎂 Demo জন্মতারিখ দিয়ে সার্চ\n\n"

        "👇 নিচের বাটন থেকে সার্চের ধরন নির্বাচন করুন:",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# =====================================================
# 10. /start
# =====================================================

async def start(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    context.user_data.clear()


    keyboard = [

        [

            InlineKeyboardButton(

                "🏛 আসন-১",

                callback_data="seat_1"

            ),

            InlineKeyboardButton(

                "🏛 আসন-২",

                callback_data="seat_2"

            ),

        ],

        [

            InlineKeyboardButton(

                "🏛 আসন-৩",

                callback_data="seat_3"

            ),

            InlineKeyboardButton(

                "🏛 আসন-৪",

                callback_data="seat_4"

            ),

        ],

    ]


    await update.message.reply_text(

        "🏠 Demo Search Bot\n\n"

        "📍 প্রথমে একটি আসন নির্বাচন করুন:",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# =====================================================
# 11. রিপোর্ট দেখানো
# =====================================================

async def send_results(

    query,

    context

):

    results = context.user_data.get(

        "results",

        []

    )


    current_page = context.user_data.get(

        "page",

        0

    )


    seat = context.user_data.get(

        "seat",

        "seat_1"

    )


    # প্রতি পেজে ১০টি

    per_page = 10


    start_index = (

        current_page

        * per_page

    )


    end_index = (

        start_index

        + per_page

    )


    page_results = results[

        start_index:end_index

    ]


    # ==========================================
    # রিপোর্ট পাঠানো
    # ==========================================

    for row in page_results:

        report = make_report(

            row,

            SEAT_FILES[seat][

                "name"

            ]

        )


        await query.message.reply_text(

            report

        )


    # ==========================================
    # Pagination Buttons
    # ==========================================

    keyboard = []


    # আরো রিপোর্ট আছে কিনা

    if end_index < len(results):

        keyboard.append(

            [

                InlineKeyboardButton(

                    "➡️ আরো দেখুন",

                    callback_data="next_page"

                )

            ]

        )


    # Search Menu

    keyboard.append(

        [

            InlineKeyboardButton(

                "🔎 নতুন সার্চ",

                callback_data="back_search_menu"

            )

        ]

    )


    await query.message.reply_text(

        f"📄 মোট ফলাফল: {len(results)} টি\n"

        f"📑 দেখানো হয়েছে: "

        f"{start_index + 1} - "

        f"{min(end_index, len(results))}",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# =====================================================
# 12. Button Handler
# =====================================================

async def button_handler(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    query = update.callback_query


    await query.answer()


    data = query.data


    # ==========================================
    # Seat Selection
    # ==========================================

    if data in SEAT_FILES:

        context.user_data[

            "seat"

        ] = data


        context.user_data.pop(

            "search_type",

            None

        )


        await show_search_menu(

            query,

            context

        )


        return


    # ==========================================
    # Change Seat
    # ==========================================

    if data == "change_seat":

        keyboard = [

            [

                InlineKeyboardButton(

                    "🏛 আসন-১",

                    callback_data="seat_1"

                ),

                InlineKeyboardButton(

                    "🏛 আসন-২",

                    callback_data="seat_2"

                ),

            ],

            [

                InlineKeyboardButton(

                    "🏛 আসন-৩",

                    callback_data="seat_3"

                ),

                InlineKeyboardButton(

                    "🏛 আসন-৪",

                    callback_data="seat_4"

                ),

            ],

        ]


        await query.edit_message_text(

            "📍 একটি আসন নির্বাচন করুন:",

            reply_markup=InlineKeyboardMarkup(

                keyboard

            )

        )


        return


    # ==========================================
    # Back to Search Menu
    # ==========================================

    if data == "back_search_menu":

        context.user_data.pop(

            "results",

            None

        )


        context.user_data.pop(

            "page",

            None

        )


        context.user_data.pop(

            "search_type",

            None

        )


        await show_search_menu(

            query,

            context

        )


        return


    # ==========================================
    # Next Page
    # ==========================================

    if data == "next_page":

        context.user_data[

            "page"

        ] = context.user_data.get(

            "page",

            0

        ) + 1


        await send_results(

            query,

            context

        )


        return


    # ==========================================
    # Search Type Selection
    # ==========================================

    search_types = {

        "search_demo_id": {

            "type": "demo_id",

            "title": "🆔 Demo ID",

            "example": ""

        },

        "search_name": {

            "type": "name",

            "title": "👤 Demo নাম",

            "example": ""

        },

        "search_father": {

            "type": "father",

            "title": "👨 Demo পিতার নাম",

            "example": ""

        },

        "search_mother": {

            "type": "mother",

            "title": "👩 Demo মাতার নাম",

            "example": ""

        },

        "search_dob": {

            "type": "dob",

            "title": "🎂 Demo জন্মতারিখ",

            "example": "01/01/2000"

        },

    }


    if data in search_types:

        search_info = search_types[

            data

        ]


        context.user_data[

            "search_type"

        ] = search_info[

            "type"

        ]


        if search_info["type"] == "dob":

            message_text = (

                "✅ 🎂 Demo জন্মতারিখ দিয়ে "

                "সার্চ নির্বাচন করা হয়েছে।\n\n"

                "✏️ এখন জন্মতারিখ লিখে পাঠান।\n\n"

                "📌 উদাহরণ: "

                "`01/01/2000`"

            )


        else:

            message_text = (

                f"✅ {search_info['title']} "

                f"দিয়ে সার্চ নির্বাচন করা হয়েছে।\n\n"

                f"✏️ এখন আপনার "

                f"{search_info['title']} লিখে পাঠান।"

            )


        await query.edit_message_text(

            message_text,

            parse_mode="Markdown"

        )


# =====================================================
# 13. Search Handler
# =====================================================

async def search_handler(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    # ==========================================
    # Seat Check
    # ==========================================

    if "seat" not in context.user_data:

        await update.message.reply_text(

            "⚠️ প্রথমে /start লিখে "

            "আসন নির্বাচন করুন।"

        )

        return


    # ==========================================
    # Search Type Check
    # ==========================================

    if "search_type" not in context.user_data:

        await update.message.reply_text(

            "⚠️ প্রথমে সার্চের ধরন নির্বাচন করুন।"

        )

        return


    search_text = (

        update.message.text

        .strip()

    )


    if not search_text:

        await update.message.reply_text(

            "⚠️ কোনো তথ্য পাওয়া যায়নি।"

        )

        return


    seat = context.user_data[

        "seat"

    ]


    search_type = context.user_data[

        "search_type"

    ]


    info = SEAT_FILES[

        seat

    ]


    # ==========================================
    # জন্মতারিখ Format Check
    # ==========================================

    if search_type == "dob":

        import re


        if not re.match(

            r"^\d{2}[\/\-\.]\d{2}[\/\-\.]\d{4}$",

            search_text

        ):

            await update.message.reply_text(

                "⚠️ জন্মতারিখ সঠিক ফরম্যাটে লিখুন।\n\n"

                "📌 উদাহরণ:\n"

                "`01/01/2000`",

                parse_mode="Markdown"

            )

            return


    await update.message.reply_text(

        "🔍 Demo Data সার্চ করা হচ্ছে...\n\n"

        "⏳ একটু অপেক্ষা করুন।"

    )


    # ==========================================
    # Search
    # ==========================================

    results = search_zip(

        info["zip"],

        info["csv"],

        search_text,

        search_type

    )


    # ==========================================
    # No Result
    # ==========================================

    if not results:

        keyboard = [

            [

                InlineKeyboardButton(

                    "🔎 নতুন সার্চ",

                    callback_data="back_search_menu"

                )

            ]

        ]


        await update.message.reply_text(

            "❌ কোনো Demo Data পাওয়া যায়নি।\n\n"

            "🔎 অন্য তথ্য দিয়ে আবার চেষ্টা করুন।",

            reply_markup=InlineKeyboardMarkup(

                keyboard

            )

        )

        return


    # ==========================================
    # Results Save
    # ==========================================

    context.user_data[

        "results"

    ] = results


    context.user_data[

        "page"

    ] = 0


    # ==========================================
    # Fake Query Object ব্যবহার না করে
    # প্রথম ১০টি রিপোর্ট সরাসরি পাঠানো
    # ==========================================

    per_page = 10


    page_results = results[

        0:per_page

    ]


    for row in page_results:

        report = make_report(

            row,

            info["name"]

        )


        await update.message.reply_text(

            report

        )


    # ==========================================
    # Pagination Buttons
    # ==========================================

    keyboard = []


    if len(results) > 10:

        keyboard.append(

            [

                InlineKeyboardButton(

                    "➡️ আরো দেখুন",

                    callback_data="next_page"

                )

            ]

        )


    keyboard.append(

        [

            InlineKeyboardButton(

                "🔎 নতুন সার্চ",

                callback_data="back_search_menu"

            )

        ]

    )


    await update.message.reply_text(

        f"📄 মোট ফলাফল: {len(results)} টি\n\n"

        f"📑 প্রথম {min(10, len(results))} টি "

        f"রিপোর্ট দেখানো হয়েছে।",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# =====================================================
# 14. Main
# =====================================================

def main():

    # ==========================================
    # Render Web Server
    # ==========================================

    threading.Thread(

        target=run_web_server,

        daemon=True

    ).start()


    print(

        "🌐 Web Server চালু হয়েছে"

    )


    # ==========================================
    # Telegram Bot
    # ==========================================

    app = (

        Application

        .builder()

        .token(TOKEN)

        .build()

    )


    # ==========================================
    # /start
    # ==========================================

    app.add_handler(

        CommandHandler(

            "start",

            start

        )

    )


    # ==========================================
    # Button Handler
    # ==========================================

    app.add_handler(

        CallbackQueryHandler(

            button_handler

        )

    )


    # ==========================================
    # Search Handler
    # ==========================================

    app.add_handler(

        MessageHandler(

            filters.TEXT

            & ~filters.COMMAND,

            search_handler

        )

    )


    print(

        "🤖 Telegram Demo Bot চালু হয়েছে!"

    )


    # ==========================================
    # Run Bot
    # ==========================================

    app.run_polling()


# =====================================================
# 15. Run
# =====================================================

if __name__ == "__main__":

    main()
