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
# 2. অটোমেটিক ফাইল স্ক্যানার ও ডিটেক্টর (Auto Detector)
# =====================================================

# এই ডিকশনারিগুলো অটোমেটিক ডায়নামিকভাবে তৈরি হবে
SEAT_FILES = {}
DIVISIONS_MAP = {}  # { 'চট্টগ্রাম বিভাগ': { 'লক্ষ্মীপুর': ['seat_key_1', 'seat_key_2'] } }

def auto_load_zip_files():
    global SEAT_FILES, DIVISIONS_MAP
    SEAT_FILES.clear()
    DIVISIONS_MAP.clear()

    # আপনার প্রজেক্টের সব voters_*.zip ফাইল খুঁজে বের করবে
    zip_files = [f for f in os.listdir(".") if f.startswith("voters_") and f.endswith(".zip")]

    for index, zip_name in enumerate(sorted(zip_files), start=1):
        seat_key = f"auto_seat_{index}"
        
        # ফাইল নাম ফরম্যাট: voters_div_dist_seat.zip
        # যেমন: voters_chattogram_lakshmipur_seat1.zip
        raw_name = zip_name.replace("voters_", "").replace(".zip", "")
        parts = raw_name.split("_")

        # ডিফল্ট ভ্যালু সেট করে রাখা
        division = parts[0].capitalize() if len(parts) > 0 else "অন্যান্য"
        district = parts[1].capitalize() if len(parts) > 1 else "সাধারণ"
        seat_name = f"আসন-{parts[2]}" if len(parts) > 2 else f"আসন-{index}"

        csv_inside_expected = zip_name.replace(".zip", ".csv")

        # SEAT_FILES-এ ডাটা রাখা
        SEAT_FILES[seat_key] = {
            "name": seat_name,
            "division": division,
            "district": district,
            "zip": zip_name,
            "csv": csv_inside_expected,
        }

        # বিভাগ এবং জেলা অনুযায়ী সাজিয়ে রাখা
        if division not in DIVISIONS_MAP:
            DIVISIONS_MAP[division] = {}
        if district not in DIVISIONS_MAP[division]:
            DIVISIONS_MAP[division][district] = []
            
        DIVISIONS_MAP[division][district].append(seat_key)

    print(f"✅ মোট {len(SEAT_FILES)} টি জিপ ফাইল অটোমেটিক ডিটেক্ট করা হয়েছে!")

# বট স্টার্ট হওয়ার সাথে সাথে ফাইল লোড করবে
auto_load_zip_files()


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
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# =====================================================
# 4. Column Name Normalize
# =====================================================

def normalize(text):
    return str(text).strip().lower().replace(" ", "").replace("_", "").replace("-", "")


# =====================================================
# 5. ZIP-এর ভিতরে CSV খোঁজা
# =====================================================

def find_csv_in_zip(zip_path, expected_csv):
    if not os.path.exists(zip_path):
        return None

    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            for name in z.namelist():
                if name.endswith(expected_csv):
                    return name
            for name in z.namelist():
                if name.lower().endswith(".csv"):
                    return name
    except Exception as e:
        print("ZIP Error:", e)

    return None


# =====================================================
# 6. CSV Search (Single & Multi AND Search)
# =====================================================

def search_zip(zip_path, csv_name, search_input, search_type):
    csv_inside = find_csv_in_zip(zip_path, csv_name)

    if not csv_inside:
        print("CSV পাওয়া যায়নি:", csv_name)
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
        with zipfile.ZipFile(zip_path, "r") as z:
            with z.open(csv_inside) as file:
                text_file = io.TextIOWrapper(file, encoding="utf-8-sig", errors="replace", newline="")
                reader = csv.DictReader(text_file)

                for row in reader:
                    normalized_row = {normalize(k): str(v or "") for k, v in row.items()}

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
        print("CSV Search Error:", e)

    return results


# =====================================================
# 7. CSV থেকে Value নেওয়া
# =====================================================

def get_value(row, names):
    normalized_row = {normalize(k): v for k, v in row.items()}
    for name in names:
        value = normalized_row.get(normalize(name))
        if value is not None:
            value = str(value).strip()
            if value:
                return value
    return "N/A"


# =====================================================
# 8. রিপোর্ট তৈরি
# =====================================================

def make_report(row, seat_name, division, district):
    voter_no = get_value(row, ["voter_no", "voterno", "demo_id", "demoid", "id"])
    serial = get_value(row, ["serial", "serialnumber", "সিরিয়াল"])
    name = get_value(row, ["name", "fullname", "নাম"])
    father = get_value(row, ["father", "fathername", "পিতা"])
    mother = get_value(row, ["mother", "mothername", "মাতা"])
    dob = get_value(row, ["dob", "dateofbirth", "birthdate", "জন্ম"])
    gender = get_value(row, ["gender", "sex", "লিঙ্গ"])
    occupation = get_value(row, ["occupation", "profession", "পেশা"])
    address = get_value(row, ["address", "ঠিকানা"])
    area = get_value(row, ["area", "এলাকা"])
    upazila = get_value(row, ["upazila", "উপজেলা", "thana", "policestation", "থানা"])
    post_code = get_value(row, ["zip", "zipcode", "postalcode", "postcode", "পোস্টকোড", "পোস্ট কোড"])

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
# 9. ডাইনামিক বিভাগ নির্বাচন
# =====================================================

async def show_division_menu(query_or_message):
    keyboard = []
    divisions = list(DIVISIONS_MAP.keys())

    if not divisions:
        text = "⚠️ কোনো voters_*.zip ফাইল পাওয়া যায়নি! ফাইল আপলোড করে নিশ্চিত করুন।"
        if hasattr(query_or_message, 'edit_message_text'):
            await query_or_message.edit_message_text(text)
        else:
            await query_or_message.reply_text(text)
        return

    # ২ টি করে বিভাগ একসাথে বোতামে দেখাবে
    for i in range(0, len(divisions), 2):
        row = [InlineKeyboardButton(f"🌍 {divisions[i]}", callback_data=f"div_{divisions[i]}")]
        if i + 1 < len(divisions):
            row.append(InlineKeyboardButton(f"🌍 {divisions[i+1]}", callback_data=f"div_{divisions[i+1]}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🏠 Demo Search Bot\n\n🌍 একটি বিভাগ নির্বাচন করুন:"

    if hasattr(query_or_message, 'edit_message_text'):
        await query_or_message.edit_message_text(text, reply_markup=reply_markup)
    else:
        await query_or_message.reply_text(text, reply_markup=reply_markup)


# =====================================================
# 10. ডাইনামিক জেলা নির্বাচন
# =====================================================

async def show_district_menu(query, context):
    division = context.user_data.get("division")
    districts = list(DIVISIONS_MAP.get(division, {}).keys())

    keyboard = []
    for i in range(0, len(districts), 2):
        row = [InlineKeyboardButton(f"🗺 {districts[i]}", callback_data=f"dis_{districts[i]}")]
        if i + 1 < len(districts):
            row.append(InlineKeyboardButton(f"🗺 {districts[i+1]}", callback_data=f"dis_{districts[i+1]}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 পূর্বের মেনু", callback_data="back_division")])

    await query.edit_message_text(
        f"🌍 বিভাগ: {division}\n\n🗺 এখন একটি জেলা নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =====================================================
# 11. ডাইনামিক আসন নির্বাচন
# =====================================================

async def show_seat_menu(query, context):
    division = context.user_data.get("division")
    district = context.user_data.get("district")

    seat_keys = DIVISIONS_MAP.get(division, {}).get(district, [])

    keyboard = []
    for i in range(0, len(seat_keys), 2):
        seat_1 = SEAT_FILES[seat_keys[i]]
        row = [InlineKeyboardButton(f"🏛 {seat_1['name']}", callback_data=seat_keys[i])]
        
        if i + 1 < len(seat_keys):
            seat_2 = SEAT_FILES[seat_keys[i+1]]
            row.append(InlineKeyboardButton(f"🏛 {seat_2['name']}", callback_data=seat_keys[i+1]))
            
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 পূর্বের মেনু", callback_data="back_district")])

    await query.edit_message_text(
        f"🌍 বিভাগ: {division}\n🗺 জেলা: {district}\n\n🏛 এখন একটি আসন নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =====================================================
# 12. Search Menu
# =====================================================

async def show_search_menu(query_or_message, context):
    seat = context.user_data.get("seat")
    info = SEAT_FILES.get(seat, {})

    keyboard = [
        [InlineKeyboardButton("⚡ Multi Search (AND Search)", callback_data="search_multi")],
        [InlineKeyboardButton("🆔 Demo ID", callback_data="search_demo_id"), InlineKeyboardButton("👤 Demo নাম", callback_data="search_name")],
        [InlineKeyboardButton("👨 Demo পিতার নাম", callback_data="search_father"), InlineKeyboardButton("👩 Demo মাতার নাম", callback_data="search_mother")],
        [InlineKeyboardButton("🎂 Demo জন্মতারিখ", callback_data="search_dob")],
        [InlineKeyboardButton("🔙 আসন পরিবর্তন", callback_data="back_seat")]
    ]

    text = (
        f"🌍 বিভাগ: {info.get('division', 'N/A')}\n"
        f"🗺 জেলা: {info.get('district', 'N/A')}\n"
        f"🏛 আসন: {info.get('name', 'N/A')}\n\n"
        "🔎 কোন তথ্য দিয়ে সার্চ করতে চান?"
    )

    if hasattr(query_or_message, 'edit_message_text'):
        await query_or_message.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query_or_message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# =====================================================
# 13. /start
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    auto_load_zip_files()  # প্রতিবার স্টার্ট দিলে নতুন আপলোড করা ফাইল লোড করে নেবে
    await show_division_menu(update.message)


# =====================================================
# 14. রিপোর্ট পাঠানো
# =====================================================

async def send_page(query, context):
    results = context.user_data.get("results", [])
    page = context.user_data.get("page", 0)
    seat = context.user_data.get("seat")
    info = SEAT_FILES.get(seat, {})

    per_page = 10
    start_index = page * per_page
    end_index = start_index + per_page
    page_results = results[start_index:end_index]

    for row in page_results:
        report = make_report(row, info.get("name", "N/A"), info.get("division", "N/A"), info.get("district", "N/A"))
        await query.message.reply_text(report)

    keyboard = []
    if end_index < len(results):
        keyboard.append([InlineKeyboardButton("➡️ আরো দেখুন", callback_data="next_page")])

    keyboard.append([InlineKeyboardButton("🔎 নতুন সার্চ (পূর্বের মেনু)", callback_data="new_search")])
    keyboard.append([InlineKeyboardButton("🏠 মূল মেনু (Start)", callback_data="show_division")])

    await query.message.reply_text(
        f"📄 মোট ফলাফল: {len(results)} টি\n📑 দেখানো হয়েছে: {start_index + 1} - {min(end_index, len(results))}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =====================================================
# 15. Button Handler
# =====================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "show_division":
        context.user_data.clear()
        await show_division_menu(query)
        return

    if data.startswith("div_"):
        div_name = data.replace("div_", "")
        context.user_data["division"] = div_name
        await show_district_menu(query, context)
        return

    if data.startswith("dis_"):
        dis_name = data.replace("dis_", "")
        context.user_data["district"] = dis_name
        await show_seat_menu(query, context)
        return

    if data == "back_division":
        await show_division_menu(query)
        return

    if data == "back_district":
        await show_district_menu(query, context)
        return

    if data in SEAT_FILES:
        context.user_data["seat"] = data
        context.user_data.pop("search_type", None)
        await show_search_menu(query, context)
        return

    if data == "back_seat":
        await show_seat_menu(query, context)
        return

    if data == "new_search":
        context.user_data.pop("results", None)
        context.user_data.pop("page", None)
        context.user_data.pop("search_type", None)
        await show_search_menu(query, context)
        return

    if data == "next_page":
        context.user_data["page"] = context.user_data.get("page", 0) + 1
        await send_page(query, context)
        return

    search_types = {
        "search_demo_id": {"type": "demo_id", "title": "🆔 Demo ID"},
        "search_name": {"type": "name", "title": "👤 Demo নাম"},
        "search_father": {"type": "father", "title": "👨 Demo পিতার নাম"},
        "search_mother": {"type": "mother", "title": "👩 Demo মাতার নাম"},
        "search_dob": {"type": "dob", "title": "🎂 Demo জন্মতারিখ"}
    }

    if data == "search_multi":
        context.user_data["search_type"] = "multi"
        text = (
            "⚡ **Multi Search (AND Search)**\n\n"
            "আপনি চাইলে নাম, পিতার নাম, মাতার নাম এবং জন্মতারিখ যেকোনো কম্বিনেশনে লিখে পাঠাতে পারেন।\n\n"
            "📌 **ফরম্যাট:**\n"
            "নাম: [আপনার নাম]\n"
            "পিতা: [পিতার নাম]\n"
            "মাতা: [মাতার নাম]\n"
            "জন্ম: [01/01/2000]\n\n"
            "*(যেকোনো ১টি বা একাধিক ফিল্ড একসাথে দিতে পারেন)*"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
        return

    if data in search_types:
        info = search_types[data]
        context.user_data["search_type"] = info["type"]
        if info["type"] == "dob":
            text = "✅ 🎂 Demo জন্মতারিখ দিয়ে সার্চ নির্বাচন করা হয়েছে।\n\n✏️ এখন জন্মতারিখ লিখে পাঠান।\n\n📌 উদাহরণ: 01/01/2000"
        else:
            text = f"✅ {info['title']} দিয়ে সার্চ নির্বাচন করা হয়েছে।\n\n✏️ এখন আপনার {info['title']} লিখে পাঠান।"
        await query.edit_message_text(text)


# =====================================================
# 16. Search Handler
# =====================================================

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "seat" not in context.user_data:
        await update.message.reply_text("⚠️ প্রথমে /start দিয়ে বিভাগ, জেলা ও আসন নির্বাচন করুন।")
        return

    if "search_type" not in context.user_data:
        await update.message.reply_text("⚠️ প্রথমে সার্চের ধরন নির্বাচন করুন।")
        return

    raw_text = update.message.text.strip()
    search_type = context.user_data["search_type"]
    seat = context.user_data["seat"]
    info = SEAT_FILES.get(seat, {})

    search_input = None

    if search_type == "multi":
        parsed = {"name": "", "father": "", "mother": "", "dob": ""}
        lines = raw_text.split("\n")

        for line in lines:
            if ":" in line:
                key, val = line.split(":", 1)
            elif "：" in line:
                key, val = line.split("：", 1)
            else:
                continue

            key = key.strip().lower()
            val = val.strip()

            if key in ["নাম", "name"]:
                parsed["name"] = val
            elif key in ["পিতা", "পিতার নাম", "father", "fathername"]:
                parsed["father"] = val
            elif key in ["মাতা", "মাতার নাম", "mother", "mothername"]:
                parsed["mother"] = val
            elif key in ["জন্ম", "জন্মতারিখ", "dob", "dateofbirth"]:
                parsed["dob"] = val

        non_empty = {k: v for k, v in parsed.items() if v}

        if not non_empty:
            if len(lines) == 1 and ":" not in raw_text and "：" not in raw_text:
                parsed["name"] = raw_text
                non_empty = {"name": raw_text}
            else:
                await update.message.reply_text("⚠️ সঠিক ফরম্যাটে তথ্য দিন।")
                return

        if len(non_empty) == 1:
            single_key = list(non_empty.keys())[0]
            search_type = single_key
            search_input = non_empty[single_key]
        else:
            search_input = parsed

    else:
        search_input = raw_text
        if search_type == "dob":
            if not re.match(r"^\d{2}[\/\-\.]\d{2}[\/\-\.]\d{4}$", search_input):
                await update.message.reply_text("⚠️ জন্মতারিখ সঠিক ফরম্যাটে লিখুন। (যেমন: 01/01/2000)")
                return

    await update.message.reply_text("🔍 Demo Data সার্চ করা হচ্ছে...\n\n⏳ একটু অপেক্ষা করুন।")

    results = search_zip(info["zip"], info["csv"], search_input, search_type)

    if not results:
        keyboard = [
            [InlineKeyboardButton("🔎 নতুন সার্চ (পূর্বের মেনু)", callback_data="new_search")],
            [InlineKeyboardButton("🏠 মূল মেনু (Start)", callback_data="show_division")]
        ]
        await update.message.reply_text("❌ কোনো Demo Data পাওয়া যায়নি।\n\n🔎 অন্য তথ্য দিয়ে আবার চেষ্টা করুন।", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    context.user_data["results"] = results
    context.user_data["page"] = 0

    first_results = results[:10]

    for row in first_results:
        report = make_report(row, info.get("name", "N/A"), info.get("division", "N/A"), info.get("district", "N/A"))
        await update.message.reply_text(report)

    keyboard = []
    if len(results) > 10:
        keyboard.append([InlineKeyboardButton("➡️ আরো দেখুন", callback_data="next_page")])

    keyboard.append([InlineKeyboardButton("🔎 নতুন সার্চ (পূর্বের মেনু)", callback_data="new_search")])
    keyboard.append([InlineKeyboardButton("🏠 মূল মেনু (Start)", callback_data="show_division")])

    summary_text = f"📄 মোট ফলাফল: {len(results)} টি\n\n📑 প্রথম {min(10, len(results))} টি রিপোর্ট দেখানো হয়েছে।"
    await update.message.reply_text(summary_text, reply_markup=InlineKeyboardMarkup(keyboard))


# =====================================================
# 17. Main
# =====================================================

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    print("🌐 Web Server চালু হয়েছে")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))

    print("🤖 Telegram Demo Search Bot চালু হয়েছে!")
    app.run_polling()


if __name__ == "__main__":
    main()
