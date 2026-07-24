import csv
import zipfile
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# 1️⃣ এখানে আপনার নতুন Telegram Bot Token বসান
# =========================================================

TOKEN = "8624453473:AAGruXbUjMfE9w7iVZ7J3ciWtG6wc5oZm_M"


# =========================================================
# 2️⃣ আপনার ZIP এবং CSV ফাইল
# =========================================================

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


# =========================================================
# DATA STORAGE
# =========================================================

DATA = {}


# =========================================================
# ZIP থেকে CSV Load
# =========================================================

def load_zip(zip_file, csv_file):

    print(f"📦 Loading ZIP: {zip_file}")

    try:

        with zipfile.ZipFile(zip_file, "r") as z:

            target = None

            # নির্দিষ্ট CSV খোঁজা
            for name in z.namelist():

                if name.endswith(csv_file):

                    target = name
                    break


            # নির্দিষ্ট CSV না পেলে ZIP-এর যেকোনো CSV খোঁজা
            if target is None:

                for name in z.namelist():

                    if name.lower().endswith(".csv"):

                        target = name
                        break


            if target is None:

                print(
                    f"❌ CSV পাওয়া যায়নি: {csv_file}"
                )

                return []


            print(
                f"📄 CSV পাওয়া গেছে: {target}"
            )


            # CSV Read
            with z.open(target) as f:

                raw = f.read()


            # Encoding
            text = None

            for encoding in [
                "utf-8-sig",
                "utf-8",
                "cp1252",
                "latin-1"
            ]:

                try:

                    text = raw.decode(encoding)

                    break

                except UnicodeDecodeError:

                    continue


            if text is None:

                print(
                    "❌ CSV Encoding পড়া যায়নি"
                )

                return []


            # CSV Reader
            reader = csv.DictReader(
                text.splitlines()
            )


            rows = []


            for row in reader:

                clean_row = {}

                for key, value in row.items():

                    if key:

                        clean_row[
                            str(key).strip()
                        ] = str(
                            value or ""
                        ).strip()


                rows.append(clean_row)


            print(
                f"✅ Loaded: {len(rows)} records"
            )


            # Column দেখাবে
            if rows:

                print(
                    "📌 Columns:",
                    list(rows[0].keys())
                )


            return rows


    except FileNotFoundError:

        print(
            f"❌ ZIP ফাইল পাওয়া যায়নি: {zip_file}"
        )

        return []


    except Exception as e:

        print(
            f"❌ ZIP Error: {e}"
        )

        return []


# =========================================================
# সব আসনের ডাটা Load
# =========================================================

def load_all_data():

    print(
        "================================"
    )

    print(
        "📦 CSV DATABASE LOADING..."
    )

    print(
        "================================"
    )


    for seat_key, info in SEAT_FILES.items():

        DATA[seat_key] = load_zip(

            info["zip"],

            info["csv"]

        )


        print(

            f"🏛 {info['name']} : "

            f"{len(DATA[seat_key])} records"

        )


    print(
        "================================"
    )

    print(
        "✅ DATABASE LOADING COMPLETE"
    )

    print(
        "================================"
    )


# =========================================================
# Column খোঁজা
# =========================================================

def find_column(row, possible_names):

    for key in row.keys():

        clean_key = (

            str(key)

            .strip()

            .lower()

            .replace(" ", "")

            .replace("_", "")

            .replace("-", "")

        )


        for name in possible_names:

            clean_name = (

                str(name)

                .strip()

                .lower()

                .replace(" ", "")

                .replace("_", "")

                .replace("-", "")

            )


            if clean_key == clean_name:

                return key


    return None


# =========================================================
# Value নেওয়া
# =========================================================

def get_value(row, possible_names):

    column = find_column(

        row,

        possible_names

    )


    if column:

        value = str(

            row.get(

                column,

                ""

            )

        ).strip()


        if value:

            return value


    return "N/A"


# =========================================================
# বয়স হিসাব
# =========================================================

def calculate_age(dob):

    if not dob:

        return "N/A"


    formats = [

        "%d/%m/%Y",

        "%d-%m-%Y",

        "%Y-%m-%d",

        "%d.%m.%Y",

    ]


    for fmt in formats:

        try:

            birth = datetime.strptime(

                dob,

                fmt

            )


            today = datetime.today()


            age = (

                today.year

                - birth.year

                - (

                    (

                        today.month,

                        today.day

                    )

                    <

                    (

                        birth.month,

                        birth.day

                    )

                )

            )


            return str(age)


        except:

            continue


    return "N/A"


# =========================================================
# রিপোর্ট তৈরি
# =========================================================

def make_report(row, seat_name):

    name = get_value(

        row,

        [

            "name",

            "fullname",

            "নাম"

        ]

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

            "policestation",

            "police station",

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


    seat_code = get_value(

        row,

        [

            "seatcode",

            "seat code",

            "আসনকোড"

        ]

    )


    age = calculate_age(

        dob

    )


    return f"""🪪 {name}
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
🏛 আসন  {seat_name}  ·  কোড  {seat_code}"""


# =========================================================
# START COMMAND
# =========================================================

async def start(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

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

        "🤖 ডেমো ডাটা সার্চ বট\n\n"

        "📍 যে আসনে সার্চ করতে চান "

        "সেটি নির্বাচন করুন:",

        reply_markup=InlineKeyboardMarkup(

            keyboard

        )

    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    query = update.callback_query


    await query.answer()


    seat = query.data


    context.user_data[

        "seat"

    ] = seat


    await query.edit_message_text(

        f"🏛 {SEAT_FILES[seat]['name']} "

        f"নির্বাচিত হয়েছে।\n\n"

        "🔍 এখন NID, নাম, পিতার নাম "

        "অথবা মাতার নাম লিখে পাঠান।"

    )


# =========================================================
# SEARCH HANDLER
# =========================================================

async def search_handler(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    if "seat" not in context.user_data:

        await update.message.reply_text(

            "⚠️ প্রথমে /start লিখে "

            "আসন নির্বাচন করুন।"

        )

        return


    search_text = (

        update.message.text

        .strip()

        .lower()

    )


    seat = context.user_data[

        "seat"

    ]


    rows = DATA.get(

        seat,

        []

    )


    results = []


    for row in rows:

        all_text = " ".join(

            str(value)

            .lower()

            for value in row.values()

        )


        if search_text in all_text:

            results.append(row)


    if not results:

        await update.message.reply_text(

            "❌ কোনো তথ্য পাওয়া যায়নি।"

        )

        return


    await update.message.reply_text(

        f"✅ মোট {len(results)} টি "

        f"তথ্য পাওয়া গেছে।"

    )


    # সর্বোচ্চ ১০টি ফলাফল দেখাবে

    for row in results[:10]:

        report = make_report(

            row,

            SEAT_FILES[seat]["name"]

        )


        await update.message.reply_text(

            report

        )


# =========================================================
# MAIN
# =========================================================

def main():

    # Database Load

    load_all_data()


    # Telegram Application

    app = (

        Application

        .builder()

        .token(TOKEN)

        .build()

    )


    # /start

    app.add_handler(

        CommandHandler(

            "start",

            start

        )

    )


    # Button

    app.add_handler(

        CallbackQueryHandler(

            button_handler

        )

    )


    # Search

    app.add_handler(

        MessageHandler(

            filters.TEXT

            & ~filters.COMMAND,

            search_handler

        )

    )


    print(

        "🤖 Telegram Bot চালু হয়েছে!"

    )


    # Run

    app.run_polling()


# =========================================================
# RUN BOT
# =========================================================

if __name__ == "__main__":

    main()
