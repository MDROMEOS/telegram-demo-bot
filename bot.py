import os
import csv
import zipfile
import glob
import re
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==================================================
# BOT TOKEN
# ==================================================
# GitHub Secrets-এ BOT_TOKEN নামে Token রাখুন
TOKEN = os.getenv("8624453473:AAGruXbUjMfE9w7iVZ7J3ciWtG6wc5oZm_M")

if not TOKEN:
    raise ValueError("BOT_TOKEN পাওয়া যায়নি। GitHub Secrets-এ BOT_TOKEN সেট করুন।")


# ==================================================
# ZIP FILE CONFIGURATION
# GitHub Repository-তে ZIP ফাইলগুলোর সঠিক নাম দিন
# ==================================================

SEAT_FILES = {
    "seat_1": {
        "name": "লক্ষ্মীপুর-১",
        "zip": "আসন-১.zip",
        "csv": "voters_nfmhzgip.csv",
    },
    "seat_2": {
        "name": "লক্ষ্মীপুর-২",
        "zip": "আসন-২.zip",
        "csv": "voters_h05css89.csv",
    },
    "seat_3": {
        "name": "লক্ষ্মীপুর-৩",
        "zip": "আসন-৩.zip",
        "csv": "voters_p_8guvlz.csv",
    },
    "seat_4": {
        "name": "লক্ষ্মীপুর-৪",
        "zip": "আসন-৪.zip",
        "csv": "voters_d_evylnn.csv",
    },
}


# ==================================================
# DATA CACHE
# ==================================================

SEAT_DATA = {}


# ==================================================
# ZIP থেকে CSV Load
# ==================================================

def load_csv_from_zip(zip_path, csv_name):
    if not os.path.exists(zip_path):
        print(f"❌ ZIP পাওয়া যায়নি: {zip_path}")
        return []

    try:
        with zipfile.ZipFile(zip_path, "r") as z:

            # প্রথমে নির্দিষ্ট CSV খোঁজা
            target = None

            for name in z.namelist():
                if name.endswith(csv_name):
                    target = name
                    break

            # না পেলে ZIP-এর যেকোনো CSV নেওয়া
            if target is None:
                csv_files = [
                    name for name in z.namelist()
                    if name.lower().endswith(".csv")
                ]

                if not csv_files:
                    print(f"❌ {zip_path}-এর মধ্যে CSV পাওয়া যায়নি")
                    return []

                target = csv_files[0]

            print(f"📂 Loading: {target}")

            with z.open(target) as f:

                raw = f.read()

                # বিভিন্ন Encoding চেষ্টা
                text = None

                for encoding in [
                    "utf-8-sig",
                    "utf-8",
                    "cp1252",
                    "latin-1",
                ]:
                    try:
                        text = raw.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue

                if text is None:
                    print("❌ CSV Encoding পড়া যায়নি")
                    return []

                # CSV Reader
                reader = csv.DictReader(text.splitlines())

                data = []

                for row in reader:

                    cleaned = {}

                    for key, value in row.items():

                        if key is None:
                            continue

                        key = str(key).strip()
                        value = str(value or "").strip()

                        cleaned[key] = value

                    data.append(cleaned)

                print(
                    f"✅ {csv_name} Loaded: {len(data)} rows"
                )

                if data:
                    print(
                        "📌 Columns:",
                        list(data[0].keys())
                    )

                return data

    except Exception as e:
        print(
            f"❌ ZIP Load Error ({zip_path}): {e}"
        )
        return []


# ==================================================
# সব আসনের ডাটা Load
# ==================================================

def load_all_data():

    print("\n==============================")
    print("📦 ZIP DATA LOADING")
    print("==============================")

    for seat_key, info in SEAT_FILES.items():

        data = load_csv_from_zip(
            info["zip"],
            info["csv"]
        )

        SEAT_DATA[seat_key] = data

        print(
            f"{info['name']} → {len(data)} records"
        )

    print("==============================")
    print("✅ DATA LOADING COMPLETE")
    print("==============================\n")


# ==================================================
# Column Detection
# ==================================================

def find_column(row, possible_names):

    normalized = {}

    for key in row.keys():

        clean = (
            str(key)
            .strip()
            .lower()
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
        )

        normalized[clean] = key

    for name in possible_names:

        clean_name = (
            name.lower()
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
        )

        if clean_name in normalized:
            return normalized[clean_name]

    return None


# ==================================================
# Search Column Mapping
# ==================================================

SEARCH_COLUMNS = {

    "id": [
        "nid",
        "nidnumber",
        "id",
        "nationalid",
        "nationalidnumber",
    ],

    "dob": [
        "dob",
        "dateofbirth",
        "birthdate",
        "জন্ম",
        "জন্মতারিখ",
    ],

    "name": [
        "name",
        "fullname",
        "নাম",
    ],

    "father": [
        "father",
        "fathername",
        "পিতা",
        "পিতারনাম",
    ],

    "mother": [
        "mother",
        "mothername",
        "মাতা",
        "মাতারনাম",
    ],
}


# ==================================================
# Search Function
# ==================================================

def search_data(
    data,
    search_type,
    search_value
):

    results = []

    possible_columns = SEARCH_COLUMNS.get(
        search_type,
        []
    )

    for row in data:

        column = find_column(
            row,
            possible_columns
        )

        if column:

            value = str(
                row.get(column, "")
            ).strip().lower()

            if search_value.lower() in value:

                results.append(row)

    return results


# ==================================================
# Get Value
# ==================================================

def get_value(
    row,
    possible_names,
    default="N/A"
):

    column = find_column(
        row,
        possible_names
    )

    if column:

        value = str(
            row.get(column, "")
        ).strip()

        if value:
            return value

    return default


# ==================================================
# Calculate Age
# ==================================================

def calculate_age(dob):

    try:

        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d.%m.%Y",
        ]

        birth_date = None

        for fmt in formats:

            try:
                birth_date = datetime.strptime(
                    dob,
                    fmt
                )
                break
            except:
                pass

        if birth_date is None:
            return "N/A"

        today = datetime.today()

        age = (
            today.year
            - birth_date.year
            - (
                (today.month, today.day)
                <
                (birth_date.month, birth_date.day)
            )
        )

        return str(age)

    except:

        return "N/A"


# ==================================================
# Format Report
# ==================================================

def format_report(row, seat_name):

    name = get_value(
        row,
        ["name", "fullname", "নাম"]
    )

    nid = get_value(
        row,
        [
            "nid",
            "nidnumber",
            "nationalid",
            "nationalidnumber"
        ]
    )

    serial = get_value(
        row,
        [
            "serial",
            "serialnumber",
            "ক্রমিক",
            "সিরিয়াল"
        ]
    )

    father = get_value(
        row,
        [
            "father",
            "fathername",
            "পিতা",
            "পিতারনাম"
        ]
    )

    mother = get_value(
        row,
        [
            "mother",
            "mothername",
            "মাতা",
            "মাতারনাম"
        ]
    )

    dob = get_value(
        row,
        [
            "dob",
            "dateofbirth",
            "birthdate",
            "জন্ম",
            "জন্মতারিখ"
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
            "police station",
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

    seat = get_value(
        row,
        [
            "seat",
            "আসন"
        ],
        seat_name
    )

    seat_code = get_value(
        row,
        [
            "seatcode",
            "seat code",
            "আসনকোড"
        ]
    )

    age = calculate_age(dob)

    report = f"""
🪪 {name}
────────────────────
🔢 NID  {nid}
🔖 সিরিয়াল  {serial}
👨 পিতা  {father}
👩 মাতা  {mother}
🎂 জন্ম  {dob} · {age} বছর
⚧ লিঙ্গ  {gender}
💼 পেশা  {occupation}
🏠 ঠিকানা  {address}
📍 থানা  {thana}
🗺 জেলা  {district}  ·  বিভাগ  {division}
🏛 আসন  {seat}  ·  কোড  {seat_code}
"""

    return report.strip()


# ==================================================
# Main Menu
# ==================================================

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

        "🤖 CSV Search Bot\n\n"
        "📊 ৪টি আসনের ডেমো ডাটাবেজ প্রস্তুত আছে।\n\n"
        "📍 বিভাগ নির্বাচন করুন:",

        reply_markup=main_menu()
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

    data = query.data


    # Division
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
            )
        )


    # District
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
            )
        )


    # Seat
    elif data.startswith("seat_"):

        context.user_data["seat"] = data

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
            f"{SEAT_FILES[data]['name']}\n\n"
            "নিচের Search Menu চাপুন:",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )


    # Search Menu
    elif data == "search_menu":

        keyboard = [

            [
                InlineKeyboardButton(
                    "🔢 ID / NID",
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
            )
        )


    # Search Type
    elif data.startswith("search_"):

        search_type = data.replace(
            "search_",
            ""
        )

        context.user_data[
            "search_type"
        ] = search_type

        context.user_data[
            "waiting_search"
        ] = True

        labels = {

            "id": "🔢 ID / NID",

            "dob": "🎂 জন্মতারিখ",

            "name": "👤 নাম",

            "father": "👨 পিতার নাম",

            "mother": "👩 মাতার নাম",

        }

        await query.edit_message_text(

            f"{labels.get(search_type)}\n\n"
            "আপনার Search Value লিখুন:"
        )


    # Home
    elif data == "home":

        context.user_data.clear()

        await query.edit_message_text(

            "🏠 মূল মেনু:",

            reply_markup=main_menu()
        )


    # About
    elif data == "about":

        await query.edit_message_text(

            "ℹ️ Demo CSV Search Bot\n\n"
            "৪টি আসনের ডেমো CSV ডাটাবেজ থেকে তথ্য খোঁজা হয়।"
        )


# ==================================================
# SEARCH HANDLER
# ==================================================

async def search_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get(
        "waiting_search"
    ):

        return


    value = (
        update.message.text
        .strip()
    )

    search_type = context.user_data.get(
        "search_type"
    )

    selected_seat = context.user_data.get(
        "seat"
    )


    data = SEAT_DATA.get(
        selected_seat,
        []
    )


    results = search_data(

        data,

        search_type,

        value
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

            "❌ কোনো তথ্য পাওয়া যায়নি।",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return


    await update.message.reply_text(

        f"✅ মোট {len(results)} টি ফলাফল পাওয়া গেছে।"
    )


    seat_name = SEAT_FILES[
        selected_seat
    ]["name"]


    # সর্বোচ্চ ১০টি ফলাফল
    for row in results[:10]:

        report = format_report(
            row,
            seat_name
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
        )
    )


# ==================================================
# MAIN
# ==================================================

def main():

    load_all_data()

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
        "🤖 CSV Search Bot চালু হয়েছে!"
    )


    app.run_polling()


if __name__ == "__main__":

    main()
