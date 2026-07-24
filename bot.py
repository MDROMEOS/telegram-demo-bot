import os
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

# ==================================================
# 🔐 আপনার নতুন Telegram Bot Token এখানে বসান
# ==================================================

TOKEN = "8624453473:AAGruXbUjMfE9w7iVZ7J3ciWtG6wc5oZm_M"


# ==================================================
# 📦 GitHub-এ থাকা ZIP ফাইলের নাম এখানে দিন
# ==================================================

SEAT_FILES = {
    "seat_1": {
        "name": "আসন-১",
        "zip": "আপনার_আসন-১_ZIP_ফাইলের_নাম.zip",
        "csv": "voters_nfmhzgip.csv",
    },

    "seat_2": {
        "name": "আসন-২",
        "zip": "আপনার_আসন-২_ZIP_ফাইলের_নাম.zip",
        "csv": "voters_h05css89.csv",
    },

    "seat_3": {
        "name": "আসন-৩",
        "zip": "আপনার_আসন-৩_ZIP_ফাইলের_নাম.zip",
        "csv": "voters_p_8guvlz.csv",
    },

    "seat_4": {
        "name": "আসন-৪",
        "zip": "আপনার_আসন-৪_ZIP_ফাইলের_নাম.zip",
        "csv": "voters_d_evylnn.csv",
    },
}


DATA = {}


# ==================================================
# ZIP থেকে CSV Load
# ==================================================

def load_zip(zip_file, csv_file):

    if not os.path.exists(zip_file):
        print(f"❌ ZIP পাওয়া যায়নি: {zip_file}")
        return []

    try:

        with zipfile.ZipFile(zip_file, "r") as z:

            target = None

            for name in z.namelist():

                if name.endswith(csv_file):
                    target = name
                    break

            if target is None:

                for name in z.namelist():

                    if name.lower().endswith(".csv"):
                        target = name
                        break

            if target is None:

                print(f"❌ CSV পাওয়া যায়নি: {csv_file}")
                return []

            print(f"📂 Loading: {target}")

            with z.open(target) as f:

                raw = f.read()

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

                print("❌ CSV Encoding পড়া যায়নি")
                return []

            reader = csv.DictReader(
                text.splitlines()
            )

            rows = []

            for row in reader:

                cleaned = {}

                for key, value in row.items():

                    if key:

                        cleaned[
                            str(key).strip()
                        ] = str(
                            value or ""
                        ).strip()

                rows.append(cleaned)

            print(
                f"✅ {csv_file} Loaded: "
                f"{len(rows)} records"
            )

            return rows

    except Exception as e:

        print(
            f"❌ ZIP Load Error: {e}"
        )

        return []


# ==================================================
# সব ডাটা Load
# ==================================================

def load_all_data():

    print("📦 ডাটা লোড হচ্ছে...")

    for seat_key, info in SEAT_FILES.items():

        DATA[seat_key] = load_zip(
            info["zip"],
            info["csv"]
        )

        print(
            f"{info['name']} → "
            f"{len(DATA[seat_key])} records"
        )

    print("✅ সব ডাটা লোড সম্পন্ন হয়েছে")


# ==================================================
# Column খোঁজা
# ==================================================

def find_column(row, names):

    for key in row.keys():

        clean_key = (
            str(key)
            .lower()
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
        )

        for name in names:

            clean_name = (
                str(name)
                .lower()
                .replace(" ", "")
                .replace("_", "")
                .replace("-", "")
            )

            if clean_key == clean_name:

                return key

    return None


# ==================================================
# Value নেওয়া
# ==================================================

def get_value(row, names):

    column = find_column(
        row,
        names
    )

    if column:

        value = str(
            row.get(column, "")
        ).strip()

        if value:

            return value

    return "N/A"


# ==================================================
# বয়স হিসাব
# ==================================================

def calculate_age(dob):

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
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
                    (today.month, today.day)
                    <
                    (birth.month, birth.day)
                )
            )

            return age

        except:

            pass

    return "N/A"


# ==================================================
# রিপোর্ট তৈরি
# ==================================================

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
            "seatcode",
            "আসনকোড"
        ]
    )

    age = calculate_age(dob)

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


# ==================================================
# START
# ==================================================

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

    await update.message.reply_text(

        "🤖 ডেমো ডাটা সার্চ বট\n\n"
        "📍 যে আসনে সার্চ করতে চান সেটি নির্বাচন করুন:",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# ==================================================
# BUTTON
# ==================================================

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

        f"🏛 {SEAT_FILES[seat]['name']} নির্বাচিত হয়েছে।\n\n"
        "🔍 এখন NID, নাম, পিতার নাম অথবা মাতার নাম লিখে পাঠান।"

    )


# ==================================================
# SEARCH
# ==================================================

async def search_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if "seat" not in context.user_data:

        await update.message.reply_text(

            "⚠️ প্রথমে /start লিখে আসন নির্বাচন করুন।"

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

        f"✅ {len(results)} টি তথ্য পাওয়া গেছে।"

    )


    for row in results[:10]:

        report = make_report(

            row,

            SEAT_FILES[
                seat
            ]["name"]

        )

        await update.message.reply_text(
            report
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
        "🤖 Telegram Bot চালু হয়েছে!"
    )


    app.run_polling()


if __name__ == "__main__":

    main()
