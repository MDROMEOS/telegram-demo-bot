import os
import csv
import zipfile
import threading
import io
import re

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
# 2. আপনার ZIP ফাইলের তথ্য
#
# এখানে ৪টি ফাইলকে আসন অনুযায়ী রাখা হয়েছে
# সবগুলো:
# বিভাগ = চট্টগ্রাম বিভাগ
# জেলা = লক্ষ্মীপুর
#
# =====================================================

SEAT_FILES = {

    "seat_1": {
        "name": "আসন-১",
        "division": "চট্টগ্রাম বিভাগ",
        "district": "লক্ষ্মীপুর",
        "zip": "voters_nfmhzgip.zip",
        "csv": "voters_nfmhzgip.csv",
    },

    "seat_2": {
        "name": "আসন-২",
        "division": "চট্টগ্রাম বিভাগ",
        "district": "লক্ষ্মীপুর",
        "zip": "voters_h05css89.zip",
        "csv": "voters_h05css89.csv",
    },

    "seat_3": {
        "name": "আসন-৩",
        "division": "চট্টগ্রাম বিভাগ",
        "district": "লক্ষ্মীপুর",
        "zip": "voters_p_8guvlz.zip",
        "csv": "voters_p_8guvlz.csv",
    },

    "seat_4": {
        "name": "আসন-৪",
        "division": "চট্টগ্রাম বিভাগ",
        "district": "লক্ষ্মীপুর",
        "zip": "voters_d_evylnn.zip",
        "csv": "voters_d_evylnn.csv",
    },

}


# =====================================================
# 3. Flask Web Server
# =====================================================

web_app = Flask(__name__)


@web_app.route("/")
def home():

    return "Telegram Demo Search Bot is running!"


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

            # প্রথমে নির্দিষ্ট CSV খুঁজবে

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
#
# Search Type:
# demo_id
# name
# father
# mother
# dob
#
# এখানে সব Matching Result সংগ্রহ হবে
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
            "CSV পাওয়া যায়নি:",
            csv_name
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
                    # কোন কলামে Search হবে
                    # =================================

                    if search_type == "demo_id":

                        search_columns = [

                            "voter_no",
                            "voterno",
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
                    # Search Value খোঁজা
                    # =================================

                    found_value = ""


                    for column in search_columns:

                        column_name = normalize(
                            column
                        )


                        if column_name in normalized_row:

                            found_value = (

                                normalized_row[

                                    column_name

                                ]

                            )

                            break


                    # =================================
                    # Search Format
                    # =================================

                    search_value = (

                        str(search_text)

                        .strip()

                        .lower()

                    )


                    found_value_normalized = (

                        str(found_value)

                        .strip()

                        .lower()

                    )


                    # =================================
                    # জন্মতারিখ Normalize
                    #
                    # 01/01/2000
                    # 01-01-2000
                    # 01.01.2000
                    # =================================

                    if search_type == "dob":

                        search_value = (

                            search_value

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

                            found_value_normalized

                            .replace(
                                "-",
                                "/"
                            )

                            .replace(
                                ".",
                                "/"
                            )

                        )


                    # =================================
                    # Match
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
# 7. CSV থেকে Value নেওয়া
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


        if value is not None:

            value = str(
                value
            ).strip()


            if value:

                return value


    return "N/A"


# =====================================================
# 8. রিপোর্ট তৈরি
#
# বিভাগ ও জেলা = মেনু থেকে
# উপজেলা/থানা ও পোস্ট কোড = CSV থেকে
# =====================================================

def make_report(
    row,
    seat_name,
    division,
    district
):

    # ==========================================
    # Basic Information
    # ==========================================

    voter_no = get_value(

        row,

        [
            "voter_no",
            "voterno",
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


    name = get_value(

        row,

        [
            "name",
            "fullname",
            "নাম"
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


    # ==========================================
    # Location Information
    # ==========================================

    area = get_value(

        row,

        [
            "area",
            "এলাকা"
        ]

    )


    upazila = get_value(

        row,

        [
            "upazila",
            "উপজেলা",
            "thana",
            "policestation",
            "থানা"
        ]

    )


    post_code = get_value(

        row,

        [
            "zip",
            "zipcode",
            "postalcode",
            "postcode",
            "পোস্টকোড",
            "পোস্ট কোড"
        ]

    )


    # ==========================================
    # রিপোর্ট
    # ==========================================

    return f"""🪪 Demo Voter Report

━━━━━━━━━━━━━━━━━━━━

🔢 Demo ID: {voter_no}

🔖 সিরিয়াল: {serial}

👤 নাম: {name}

👨 পিতা: {father}

👩 মাতা: {mother}

🎂 জন্মতারিখ: {dob}

⚧ লিঙ্গ: {gender}

💼 পেশা: {occupation}

🏠 ঠিকানা: {address}

📍 এলাকা: {area}

📌 উপজেলা/থানা: {upazila}

📮 পোস্ট কোড: {post_code}

🌍 বিভাগ: {division}

🗺 জেলা: {district}

🏛 আসন: {seat_name}

━━━━━━━━━━━━━━━━━━━━"""


# =====================================================
# 9. বিভাগ নির্বাচন
# =====================================================

async def show_division_menu(
    query
):

    keyboard = [

        [

            InlineKeyboardButton(

                "🌍 চট্টগ্রাম বিভাগ",

                callback_data="division_chattogram"

            )

        ]

    ]


    await query.edit_message_text(

        "🏠 Demo Search Bot\n\n"

        "🌍 প্রথমে একটি বিভাগ নির্বাচন করুন:",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# =====================================================
# 10. জেলা নির্বাচন
# =====================================================

async def show_district_menu(
    query,
    context
):

    keyboard = [

        [

            InlineKeyboardButton(

                "🗺 লক্ষ্মীপুর",

                callback_data="district_lakshmipur"

            )

        ],

        [

            InlineKeyboardButton(

                "🔙 পূর্বের মেনু",

                callback_data="back_division"

            )

        ]

    ]


    await query.edit_message_text(

        "🌍 বিভাগ: চট্টগ্রাম বিভাগ\n\n"

        "🗺 এখন একটি জেলা নির্বাচন করুন:",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# =====================================================
# 11. আসন নির্বাচন
# =====================================================

async def show_seat_menu(
    query,
    context
):

    keyboard = [

        [

            InlineKeyboardButton(

                "🏛 আসন-১",

                callback_data="seat_1"

            ),

            InlineKeyboardButton(

                "🏛 আসন-২",

                callback_data="seat_2"

            )

        ],

        [

            InlineKeyboardButton(

                "🏛 আসন-৩",

                callback_data="seat_3"

            ),

            InlineKeyboardButton(

                "🏛 আসন-৪",

                callback_data="seat_4"

            )

        ],

        [

            InlineKeyboardButton(

                "🔙 পূর্বের মেনু",

                callback_data="back_district"

            )

        ]

    ]


    await query.edit_message_text(

        "🌍 বিভাগ: চট্টগ্রাম বিভাগ\n"

        "🗺 জেলা: লক্ষ্মীপুর\n\n"

        "🏛 এখন একটি আসন নির্বাচন করুন:",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# =====================================================
# 12. Search Menu
# =====================================================

async def show_search_menu(

    query,

    context

):

    seat = context.user_data.get(

        "seat",

        "seat_1"

    )


    info = SEAT_FILES[seat]


    keyboard = [

        [

            InlineKeyboardButton(

                "🆔 Demo ID",

                callback_data="search_demo_id"

            ),

            InlineKeyboardButton(

                "👤 Demo নাম",

                callback_data="search_name"

            )

        ],

        [

            InlineKeyboardButton(

                "👨 Demo পিতার নাম",

                callback_data="search_father"

            ),

            InlineKeyboardButton(

                "👩 Demo মাতার নাম",

                callback_data="search_mother"

            )

        ],

        [

            InlineKeyboardButton(

                "🎂 Demo জন্মতারিখ",

                callback_data="search_dob"

            )

        ],

        [

            InlineKeyboardButton(

                "🔙 আসন পরিবর্তন",

                callback_data="back_seat"

            )

        ]

    ]


    await query.edit_message_text(

        "🌍 বিভাগ: "

        + info["division"]

        + "\n"

        "🗺 জেলা: "

        + info["district"]

        + "\n"

        "🏛 আসন: "

        + info["name"]

        + "\n\n"

        "🔎 কোন তথ্য দিয়ে সার্চ করতে চান?",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# =====================================================
# 13. /start
# =====================================================

async def start(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    context.user_data.clear()


    keyboard = [

        [

            InlineKeyboardButton(

                "🌍 বিভাগ নির্বাচন",

                callback_data="show_division"

            )

        ]

    ]


    await update.message.reply_text(

        "🏠 Demo Search Bot\n\n"

        "📍 শুরু করতে নিচের বাটনে ক্লিক করুন:",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# =====================================================
# 14. রিপোর্ট পাঠানো
# =====================================================

async def send_page(

    query,

    context

):

    results = context.user_data.get(

        "results",

        []

    )


    page = context.user_data.get(

        "page",

        0

    )


    seat = context.user_data.get(

        "seat",

        "seat_1"

    )


    info = SEAT_FILES[seat]


    per_page = 10


    start_index = (

        page

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

            info["name"],

            info["division"],

            info["district"]

        )


        await query.message.reply_text(

            report

        )


    # ==========================================
    # Button
    # ==========================================

    keyboard = []


    if end_index < len(results):

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

                callback_data="new_search"

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
# 15. Button Handler
# =====================================================

async def button_handler(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    query = update.callback_query


    await query.answer()


    data = query.data


    # ==========================================
    # বিভাগ নির্বাচন
    # ==========================================

    if data == "show_division":

        context.user_data[

            "division"

        ] = "চট্টগ্রাম বিভাগ"


        await show_division_menu(

            query

        )


        return


    # ==========================================
    # বিভাগ Confirm
    # ==========================================

    if data == "division_chattogram":

        context.user_data[

            "division"

        ] = "চট্টগ্রাম বিভাগ"


        await show_district_menu(

            query,

            context

        )


        return


    # ==========================================
    # জেলা নির্বাচন
    # ==========================================

    if data == "district_lakshmipur":

        context.user_data[

            "district"

        ] = "লক্ষ্মীপুর"


        await show_seat_menu(

            query,

            context

        )


        return


    # ==========================================
    # পূর্বের মেনু - বিভাগ
    # ==========================================

    if data == "back_division":

        await show_division_menu(

            query

        )


        return


    # ==========================================
    # পূর্বের মেনু - জেলা
    # ==========================================

    if data == "back_district":

        await show_district_menu(

            query,

            context

        )


        return


    # ==========================================
    # আসন নির্বাচন
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
    # আসন পরিবর্তন
    # ==========================================

    if data == "back_seat":

        await show_seat_menu(

            query,

            context

        )


        return


    # ==========================================
    # নতুন সার্চ
    # ==========================================

    if data == "new_search":

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
    # আরো দেখুন
    # ==========================================

    if data == "next_page":

        context.user_data[

            "page"

        ] = (

            context.user_data.get(

                "page",

                0

            )

            + 1

        )


        await send_page(

            query,

            context

        )


        return


    # ==========================================
    # Search Type
    # ==========================================

    search_types = {

        "search_demo_id": {

            "type": "demo_id",

            "title": "🆔 Demo ID"

        },

        "search_name": {

            "type": "name",

            "title": "👤 Demo নাম"

        },

        "search_father": {

            "type": "father",

            "title": "👨 Demo পিতার নাম"

        },

        "search_mother": {

            "type": "mother",

            "title": "👩 Demo মাতার নাম"

        },

        "search_dob": {

            "type": "dob",

            "title": "🎂 Demo জন্মতারিখ"

        }

    }


    if data in search_types:

        info = search_types[data]


        context.user_data[

            "search_type"

        ] = info["type"]


        if info["type"] == "dob":

            text = (

                "✅ 🎂 Demo জন্মতারিখ দিয়ে "

                "সার্চ নির্বাচন করা হয়েছে।\n\n"

                "✏️ এখন জন্মতারিখ লিখে পাঠান।\n\n"

                "📌 উদাহরণ: 01/01/2000"

            )


        else:

            text = (

                f"✅ {info['title']} দিয়ে "

                f"সার্চ নির্বাচন করা হয়েছে।\n\n"

                f"✏️ এখন আপনার "

                f"{info['title']} লিখে পাঠান।"

            )


        await query.edit_message_text(

            text

        )


# =====================================================
# 16. Search Handler
# =====================================================

async def search_handler(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    if "seat" not in context.user_data:

        await update.message.reply_text(

            "⚠️ প্রথমে /start দিয়ে "

            "বিভাগ, জেলা ও আসন নির্বাচন করুন।"

        )

        return


    if "search_type" not in context.user_data:

        await update.message.reply_text(

            "⚠️ প্রথমে সার্চের ধরন নির্বাচন করুন।"

        )

        return


    search_text = (

        update.message.text

        .strip()

    )


    search_type = context.user_data[

        "search_type"

    ]


    seat = context.user_data[

        "seat"

    ]


    info = SEAT_FILES[seat]


    # ==========================================
    # জন্মতারিখ Format Check
    # ==========================================

    if search_type == "dob":

        if not re.match(

            r"^\d{2}[\/\-\.]\d{2}[\/\-\.]\d{4}$",

            search_text

        ):

            await update.message.reply_text(

                "⚠️ জন্মতারিখ সঠিক ফরম্যাটে লিখুন।\n\n"

                "📌 উদাহরণ: 01/01/2000"

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

                    callback_data="new_search"

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
    # প্রথম ১০টি রিপোর্ট
    # ==========================================

    first_results = results[:10]


    for row in first_results:

        report = make_report(

            row,

            info["name"],

            info["division"],

            info["district"]

        )


        await update.message.reply_text(

            report

        )


    # ==========================================
    # Buttons
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

                callback_data="new_search"

            )

        ]

    )


    await update.message.reply_text(

        f"📄 মোট ফলাফল: {len(results)} টি\n\n"

        f"📑 প্রথম "

        f"{min(10, len(results))}"

        f" টি রিপোর্ট দেখানো হয়েছে।",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# =====================================================
# 17. Main
# =====================================================

def main():

    # ==========================================
    # Render Server
    # ==========================================

    threading.Thread(

        target=run_web_server,

        daemon=True

    ).start()


    print(

        "🌐 Web Server চালু হয়েছে"

    )


    # ==========================================
    # Telegram Application
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
    # Button
    # ==========================================

    app.add_handler(

        CallbackQueryHandler(

            button_handler

        )

    )


    # ==========================================
    # Text Search
    # ==========================================

    app.add_handler(

        MessageHandler(

            filters.TEXT

            & ~filters.COMMAND,

            search_handler

        )

    )


    print(

        "🤖 Telegram Demo Search Bot চালু হয়েছে!"

    )


    # ==========================================
    # Run
    # ==========================================

    app.run_polling()


# =====================================================
# 18. Start
# =====================================================

if __name__ == "__main__":

    main()
