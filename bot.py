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
# 2. আপনার ZIP ফাইলের তথ্য (পূর্বের ও নতুন ডাটা একসাথে)
# =====================================================

SEAT_FILES = {

    # --- চট্টগ্রাম বিভাগ (পূর্বের ডাটা) ---
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

    # --- লালমনিরহাট বিভাগ (নতুন ডাটা) ---
    "lal_seat_1": {
        "name": "আসন-১",
        "division": "লালমনিরহাট বিভাগ",
        "district": "লালমনিরহাট",
        "zip": "voters_q_hde8oz.zip",
        "csv": "voters_q_hde8oz.csv",
    },

    "lal_seat_3": {
        "name": "আসন-৩",
        "division": "লালমনিরহাট বিভাগ",
        "district": "লালমনিরহাট",
        "zip": "voters_e7arvkn5.zip",
        "csv": "voters_e7arvkn5.csv",
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

            for name in z.namelist():

                if name.endswith(
                    expected_csv
                ):

                    return name


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
# 6. CSV Search (Single & Multi AND Search)
# =====================================================

def search_zip(
    zip_path,
    csv_name,
    search_input,
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


    column_mappings = {

        "demo_id": ["voter_no", "voterno", "demo_id", "demoid", "id"],

        "name": ["name", "fullname", "নাম"],

        "father": ["father", "fathername", "পিতা"],

        "mother": ["mother", "mothername", "মাতা"],

        "dob": ["dob", "dateofbirth", "birthdate", "জন্ম"]

    }


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

                    normalized_row = {

                        normalize(k): str(v or "")

                        for k, v in row.items()

                    }


                    if search_type == "multi":

                        is_match = True


                        for field, search_val in search_input.items():

                            if not search_val:

                                continue


                            possible_cols = column_mappings.get(field, [])


                            found_value = ""


                            for col in possible_cols:

                                norm_col = normalize(col)


                                if norm_col in normalized_row:

                                    found_value = normalized_row[norm_col]

                                    break


                            s_val = str(search_val).strip().lower()

                            f_val = str(found_value).strip().lower()


                            if field == "dob":

                                s_val = s_val.replace("-", "/").replace(".", "/")

                                f_val = f_val.replace("-", "/").replace(".", "/")


                            if s_val not in f_val:

                                is_match = False

                                break


                        if is_match:

                            results.append(dict(row))


                    else:

                        search_columns = column_mappings.get(search_type, [])


                        found_value = ""


                        for column in search_columns:

                            column_name = normalize(column)


                            if column_name in normalized_row:

                                found_value = normalized_row[column_name]

                                break


                        search_value = str(search_input).strip().lower()

                        found_value_normalized = str(found_value).strip().lower()


                        if search_type == "dob":

                            search_value = search_value.replace("-", "/").replace(".", "/")

                            found_value_normalized = found_value_normalized.replace("-", "/").replace(".", "/")


                        if search_value in found_value_normalized:

                            results.append(dict(row))


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
# =====================================================

def make_report(
    row,
    seat_name,
    division,
    district
):

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

        ],

        [

            InlineKeyboardButton(

                "🌍 লালমনিরহাট বিভাগ",

                callback_data="division_lalmonirhat"

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

    division = context.user_data.get("division", "চট্টগ্রাম বিভাগ")


    if division == "চট্টগ্রাম বিভাগ":

        keyboard = [

            [

                InlineKeyboardButton(

                    "🗺 লক্ষ্মীপুর",

                    callback_data="district_lakshmipur"

                )

            ]

        ]

    else:

        keyboard = [

            [

                InlineKeyboardButton(

                    "🗺 লালমনিরহাট",

                    callback_data="district_lalmonirhat"

                )

            ]

        ]


    keyboard.append([InlineKeyboardButton("🔙 পূর্বের মেনু", callback_data="back_division")])


    await query.edit_message_text(

        f"🌍 বিভাগ: {division}\n\n"

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

    district = context.user_data.get("district", "লক্ষ্মীপুর")

    division = context.user_data.get("division", "চট্টগ্রাম বিভাগ")


    if district == "লক্ষ্মীপুর":

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

            ]

        ]

    else:

        keyboard = [

            [

                InlineKeyboardButton(

                    "🏛 আসন-১",

                    callback_data="lal_seat_1"

                ),

                InlineKeyboardButton(

                    "🏛 আসন-৩",

                    callback_data="lal_seat_3"

                )

            ]

        ]


    keyboard.append([InlineKeyboardButton("🔙 পূর্বের মেনু", callback_data="back_district")])


    await query.edit_message_text(

        f"🌍 বিভাগ: {division}\n"

        f"🗺 জেলা: {district}\n\n"

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


    info = SEAT_FILES.get(seat, SEAT_FILES["seat_1"])


    keyboard = [

        [

            InlineKeyboardButton(

                "⚡ Multi Search (AND Search)",

                callback_data="search_multi"

            )

        ],

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


    info = SEAT_FILES.get(seat, SEAT_FILES["seat_1"])


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


    if data == "show_division":

        await show_division_menu(

            query

        )


        return


    if data == "division_chattogram":

        context.user_data[

            "division"

        ] = "চট্টগ্রাম বিভাগ"


        await show_district_menu(

            query,

            context

        )


        return


    if data == "division_lalmonirhat":

        context.user_data[

            "division"

        ] = "লালমনিরহাট বিভাগ"


        await show_district_menu(

            query,

            context

        )


        return


    if data == "district_lakshmipur":

        context.user_data[

            "district"

        ] = "লক্ষ্মীপুর"


        await show_seat_menu(

            query,

            context

        )


        return


    if data == "district_lalmonirhat":

        context.user_data[

            "district"

        ] = "লালমনিরহাট"


        await show_seat_menu(

            query,

            context

        )


        return


    if data == "back_division":

        await show_division_menu(

            query

        )


        return


    if data == "back_district":

        await show_district_menu(

            query,

            context

        )


        return


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


    if data == "back_seat":

        await show_seat_menu(

            query,

            context

        )


        return


    if data == "new_search":

        context.user_data.pop(

            "results",

            None

        )


        context.user_data.pop(

            "page",
