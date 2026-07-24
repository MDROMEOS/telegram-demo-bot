import os
import csv
import zipfile
import threading

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =====================================================
# 1. এখানে আপনার Telegram Bot Token বসান
# =====================================================

TOKEN = "8624453473:AAGruXbUjMfE9w7iVZ7J3ciWtG6wc5oZm_M"


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
    port = int(os.environ.get("PORT", 10000))

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

def find_csv_in_zip(zip_path, expected_csv):

    if not os.path.exists(zip_path):
        return None

    try:
        with zipfile.ZipFile(zip_path, "r") as z:

            # আগে নির্দিষ্ট CSV খুঁজবে
            for name in z.namelist():

                if name.endswith(expected_csv):
                    return name

            # না পেলে প্রথম CSV নেবে
            for name in z.namelist():

                if name.lower().endswith(".csv"):
                    return name

    except Exception as e:

        print("ZIP Error:", e)

    return None


# =====================================================
# 6. CSV Search
# একসাথে পুরো CSV RAM-এ লোড করবে না
# =====================================================

def search_zip(zip_path, csv_name, search_text):

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

                # Text stream
                import io

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

                    # সার্চের জন্য পুরো Row-এর
                    # টেক্সট তৈরি
                    searchable = " ".join(

                        str(value or "")

                        for value in row.values()

                    ).lower()


                    if search_text.lower() in searchable:

                        results.append(
                            dict(row)
                        )


                        # RAM ও Telegram message
                        # সীমিত রাখার জন্য ১০টি ফলাফল
                        if len(results) >= 10:
                            break


    except Exception as e:

        print(
            "CSV Search Error:",
            e
        )


    return results


# =====================================================
# 7. Demo Report
# =====================================================

def get_value(row, names):

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
# 8. /start
# =====================================================

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

        "🤖 Demo Data Search Bot\n\n"
        "📍 একটি আসন নির্বাচন করুন:",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =====================================================
# 9. Seat Button
# =====================================================

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

        f"✅ {SEAT_FILES[seat]['name']} "
        f"নির্বাচিত হয়েছে।\n\n"

        "🔍 এখন Demo ID বা নাম লিখে "
        "সার্চ করুন।"

    )


# =====================================================
# 10. Search
# =====================================================

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

    )


    seat = context.user_data[
        "seat"
    ]


    info = SEAT_FILES[
        seat
    ]


    await update.message.reply_text(

        "🔍 Demo Data সার্চ করা হচ্ছে..."

    )


    results = search_zip(

        info["zip"],

        info["csv"],

        search_text

    )


    if not results:

        await update.message.reply_text(

            "❌ কোনো Demo Data পাওয়া যায়নি।"

        )

        return


    await update.message.reply_text(

        f"✅ {len(results)} টি "
        f"Demo Data পাওয়া গেছে।"

    )


    for row in results:

        report = make_report(

            row,

            info["name"]

        )


        await update.message.reply_text(

            report

        )


# =====================================================
# 11. Main
# =====================================================

def main():

    # Render Web Server
    threading.Thread(

        target=run_web_server,

        daemon=True

    ).start()


    print(
        "🌐 Web Server চালু হয়েছে"
    )


    # Telegram Bot
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
        "🤖 Telegram Demo Bot চালু হয়েছে!"
    )


    app.run_polling()


# =====================================================
# 12. Run
# =====================================================

if __name__ == "__main__":

    main()
