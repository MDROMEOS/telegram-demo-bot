import os
import csv
import zipfile
import py7zr  # 7z ফাইল রিড করার জন্য
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
from telegram.error import BadRequest


# =====================================================
# 1. Telegram Bot Token
# =====================================================

TOKEN = "8757771538:AAFt6VmtbOkFJ_0QSxpAWW8cVX8VwTUfC_E"


# =====================================================
# 2. ইংরেজি ফাইল নেম থেকে বাংলা নাম ম্যাপিং
# =====================================================

BANGLA_MAP = {
    # বিভাগসমূহ
    "rangpur": "রংপুর বিভাগ",
    "rajshahi": "রাজশাহী বিভাগ",
    "khulna": "খুলনা বিভাগ",
    "barishal": "বরিশাল বিভাগ",
    "dhaka": "ঢাকা বিভাগ",
    "mymensingh": "ময়মনসিংহ বিভাগ",
    "sylhet": "সিলেট বিভাগ",
    "chattogram": "চট্টগ্রাম বিভাগ",

    # জেলাসমূহ
    "panchagarh": "পঞ্চগড়", "thakurgaon": "ঠাকুরগাঁও", "dinajpur": "দিনাজপুর",
    "nilphamari": "নীলফামারী", "lalmonirhat": "লালমনিরহাট", "kurigram": "কুড়িগ্রাম",
    "gaibandha": "গাইবান্ধা", "joypurhat": "জয়পুরহাট", "bogura": "বগুড়া",
    "chapainawabganj": "চাঁপাইনবাবগঞ্জ", "naogaon": "নওগাঁ", "natore": "নাটোর",
    "sirajganj": "সিরাজগঞ্জ", "pabna": "পাবনা", "meherpur": "মেহেরপুর",
    "kushtia": "কুষ্টিয়া", "chuadanga": "চুয়াডাঙ্গা", "jhenaidah": "ঝিনাইদহ",
    "jashore": "যশোর", "magura": "মাগুরা", "narail": "নড়াইল",
    "bagerhat": "বাগেরহাট", "satkhira": "সাতক্ষীরা", "barguna": "বরগুনা",
    "patuakhali": "পটুয়াখালী", "bhola": "ভোলা", "jhalokati": "ঝালকাঠি",
    "pirojpur": "পিরোজপুর", "tangail": "টাঙ্গাইল", "kishoreganj": "কিশোরগঞ্জ",
    "manikganj": "মানিকগঞ্জ", "munshiganj": "মুন্সীগঞ্জ", "gazipur": "গাজীপুর",
    "narsingdi": "নরসিংদী", "narayanganj": "নারায়ণগঞ্জ", "rajbari": "রাজবাড়ী",
    "faridpur": "ফরিদপুর", "gopalganj": "গোপালগঞ্জ", "madaripur": "মাদারীপুর",
    "shariatpur": "শরীয়তপুর", "jamalpur": "জামালপুর", "sherpur": "শেরপুর",
    "netrokona": "নেত্রকোণা", "sunamganj": "সুনামগঞ্জ", "moulvibazar": "মৌলভীবাজার",
    "habiganj": "হবিগঞ্জ", "brahmanbaria": "ব্রাহ্মণবাড়িয়া", "cumilla": "কুমিল্লা",
    "chandpur": "চাঁদপুর", "feni": "ফেনী", "noakhali": "নোখালী",
    "lakshmipur": "লক্ষ্মীপুর", "coxsbazar": "কক্সবাজার", "khagrachhari": "খাগড়াছড়ি",
    "rangamati": "রাঙ্গামাটি", "bandarban": "বান্দরবান"
}


# =====================================================
# 3. অটোমেটিক ফাইল স্ক্যানার ও ডিটেক্টর (ZIP + 7Z)
# =====================================================

SEAT_FILES = {}
DIVISIONS_MAP = {}

def auto_load_zip_files():
    global SEAT_FILES, DIVISIONS_MAP
    SEAT_FILES.clear()
    DIVISIONS_MAP.clear()

    archive_files = [
        f for f in os.listdir(".") 
        if f.startswith("voters_") and (f.endswith(".zip") or f.endswith(".7z"))
    ]

    for index, archive_name in enumerate(sorted(archive_files), start=1):
        seat_key = f"auto_seat_{index}"
        
        raw_name = archive_name.replace("voters_", "")
        raw_name = re.sub(r'\.(zip|7z)$', '', raw_name)
        parts = raw_name.split("_")

        division_raw = parts[0].lower() if len(parts) > 0 else "other"
        district_raw = parts[1].lower() if len(parts) > 1 else "general"
        seat_raw = parts[2] if len(parts) > 2 else f"{index}"

        division = BANGLA_MAP.get(division_raw, division_raw.capitalize())
        district = BANGLA_MAP.get(district_raw, district_raw.capitalize())
        seat_name = f"আসন-{seat_raw.replace('seat', '')}"

        SEAT_FILES[seat_key] = {
            "name": seat_name,
            "division": division,
            "district": district,
            "archive": archive_name,
        }

        if division not in DIVISIONS_MAP:
            DIVISIONS_MAP[division] = {}
        if district not in DIVISIONS_MAP[division]:
            DIVISIONS_MAP[division][district] = []
            
        DIVISIONS_MAP[division][district].append(seat_key)

    print(f"✅ মোট {len(SEAT_FILES)} টি (ZIP/7Z) ফাইল লোড হয়েছে!")

auto_load_zip_files()


# =====================================================
# 4. Flask Web Server
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
# 5. Column Name Normalize
# =====================================================

def normalize(text):
    if not text:
        return ""
    return str(text).strip().lower().replace(" ", "").replace("_", "").replace("-", "")


# =====================================================
# 6. Archive (ZIP / 7Z) থেকে CSV সার্চ (Debug Enabled)
# =====================================================

def search_archive(archive_path, search_input, search_type):
    if not os.path.exists(archive_path):
        print(f"❌ File not found: {archive_path}")
        return []

    results = []
    column_mappings = {
        "demo_id": ["voter_no", "voterno", "demo_id", "demoid", "id", "voter_id", "voterid", "ভোটার নম্বর", "আইডি", "sl", "slno", "voter"],
        "name": ["name", "fullname", "नाम", "নাম", "votername"],
        "father": ["father", "fathername", "father_name", "পিতা", "পিতার নাম", "fathersname"],
        "mother": ["mother", "mothername", "mother_name", "মাতা", "মাতার নাম", "mothersname"],
        "dob": ["dob", "dateofbirth", "birthdate", "birth_date", "জন্ম", "জন্মতারিখ", "birth"]
    }

    try:
        file_bytes = None
        
        if archive_path.endswith(".7z"):
            with py7zr.SevenZipFile(archive_path, mode='r') as z:
                all_files = z.getnames()
                csv_file_name = next((f for f in all_files if f.lower().endswith(".csv")), None)
                
                if csv_file_name:
                    extracted = z.readall()
                    # 7z Extraction Check
                    for k, v in extracted.items():
                        if k.lower().endswith(".csv"):
                            file_bytes = v.read()
                            break

        elif archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as z:
                all_files = z.namelist()
                csv_file_name = next((f for f in all_files if f.lower().endswith(".csv")), None)
                if csv_file_name:
                    with z.open(csv_file_name) as file:
                        file_bytes = file.read()

        if file_bytes:
            # Decode Logic
            decoded_text = ""
            for enc in ['utf-8-sig', 'utf-8', 'utf-16', 'latin-1', 'cp1252']:
                try:
                    decoded_text = file_bytes.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue

            text_file = io.StringIO(decoded_text)
            
            # Auto Delimiter Detect (Comma or Tab)
            sample = decoded_text[:2000]
            delimiter = '\t' if '\t' in sample and sample.count('\t') > sample.count(',') else ','
            
            reader = csv.DictReader(text_file, delimiter=delimiter)
            
            # Print Column Names in Console for Debugging
            print(f"📌 {archive_path} এর কলামসমূহ:", reader.fieldnames)
            
            results = process_csv_search(reader, search_input, search_type, column_mappings)

    except Exception as e:
        print(f"❌ Archive Reading Error ({archive_path}):", e)

    return results


def process_csv_search(reader, search_input, search_type, column_mappings):
    results = []
    
    if not reader.fieldnames:
        print("⚠️ CSV কলাম বা হেডার খালি পাওয়া গেছে!")
        return []

    for row in reader:
        # Check empty rows
        if not any(row.values()):
            continue

        normalized_row = {normalize(k): str(v or "").strip() for k, v in row.items() if k}

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
                    s_val = re.sub(r'[\.\-\/]', '', s_val)
                    f_val = re.sub(r'[\.\-\/]', '', f_val)

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

            # Fallback: Search all columns if column map missing
            if not found_value and search_type == "name":
                for k, v in normalized_row.items():
                    if str(search_input).strip().lower() in v.lower():
                        results.append(dict(row))
                        break
                continue

            search_value = str(search_input).strip().lower()
            found_value_normalized = str(found_value).strip().lower()

            if search_type == "dob":
                search_value = re.sub(r'[\.\-\/]', '', search_value)
                found_value_normalized = re.sub(r'[\.\-\/]', '', found_value_normalized)

            if search_value and search_value in found_value_normalized:
                results.append(dict(row))

    return results


# =====================================================
# 7. CSV থেকে Value নেওয়া
# =====================================================

def get_value(row, names):
    normalized_row = {normalize(k): v for k, v in row.items() if k}
    for name in names:
        value = normalized_row.get(normalize(name))
        if value is not None:
            value = str(value).strip()
            if value:
                return value
    return "N/A"


# =====================================================
# 8. রিপোর্ট ফরম্যাটিং
# =====================================================

def make_report(row, seat_name, division, district):
    voter_no = get_value(row, ["voter_no", "voterno", "demo_id", "demoid", "id", "voter_id", "voterid", "ভোটার নম্বর", "আইডি", "sl", "slno", "voter"])
    serial = get_value(row, ["serial", "serialnumber", "সিরিয়াল"])
    name = get_value(row, ["name", "fullname", "नाम", "নাম", "votername"])
    father = get_value(row, ["father", "fathername", "father_name", "পিতা", "পিতার নাম", "fathersname"])
    mother = get_value(row, ["mother", "mothername", "mother_name", "মাতা", "মাতার নাম", "mothersname"])
    dob = get_value(row, ["dob", "dateofbirth", "birthdate", "birth_date", "জন্ম", "জন্মতারিখ", "birth"])
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


# Helper for Safe Edit Message
async def safe_edit_message(query, text, reply_markup=None, parse_mode=None):
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        else:
            raise e


# =====================================================
# 9. ডাইনামিক মেনু ফাংশনসমূহ
# =====================================================

async def show_division_menu(query_or_message):
    keyboard = []
    divisions = list(DIVISIONS_MAP.keys())

    if not divisions:
        text = "⚠️ কোনো voters_*.zip বা voters_*.7z ফাইল পাওয়া যায়নি!"
        if hasattr(query_or_message, 'edit_message_text'):
            await safe_edit_message(query_or_message, text)
        else:
            await query_or_message.reply_text(text)
        return

    for i in range(0, len(divisions), 2):
        row = [InlineKeyboardButton(f"🌍 {divisions[i]}", callback_data=f"div_{divisions[i]}")]
        if i + 1 < len(divisions):
            row.append(InlineKeyboardButton(f"🌍 {divisions[i+1]}", callback_data=f"div_{divisions[i+1]}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🏠 Demo Search Bot\n\n🌍 একটি বিভাগ নির্বাচন করুন:"

    if hasattr(query_or_message, 'edit_message_text'):
        await safe_edit_message(query_or_message, text, reply_markup=reply_markup)
    else:
        await query_or_message.reply_text(text, reply_markup=reply_markup)


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

    await safe_edit_message(
        query,
        f"🌍 বিভাগ: {division}\n\n🗺 এখন একটি জেলা নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


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

    await safe_edit_message(
        query,
        f"🌍 বিভাগ: {division}\n🗺 জেলা: {district}\n\n🏛 এখন একটি আসন নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


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
        await safe_edit_message(query_or_message, text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query_or_message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# =====================================================
# 10. Handlers
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    auto_load_zip_files()
    await show_division_menu(update.message)


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
            "জন্ম: [01/01/2000]"
        )
        await safe_edit_message(query, text, parse_mode="Markdown")
        return

    if data in search_types:
        info = search_types[data]
        context.user_data["search_type"] = info["type"]
        if info["type"] == "dob":
            text = "✅ 🎂 Demo জন্মতারিখ দিয়ে সার্চ নির্বাচন করা হয়েছে।\n\n✏️ এখন জন্মতারিখ লিখে পাঠান।\n\n📌 উদাহরণ: 01/01/2000"
        else:
            text = f"✅ {info['title']} দিয়ে সার্চ নির্বাচন করা হয়েছে।\n\n✏️ এখন আপনার {info['title']} লিখে পাঠান।"
        await safe_edit_message(query, text)


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

    await update.message.reply_text("🔍 Demo Data সার্চ করা হচ্ছে...\n\n⏳ একটু অপেক্ষা করুন।")

    results = search_archive(info["archive"], search_input, search_type)

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
# 11. Main Function
# =====================================================

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    print("🌐 Web Server चालू হয়েছে")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))

    print("🤖 Telegram Demo Search Bot চালু হয়েছে!")
    app.run_polling()


if __name__ == "__main__":
    main()
