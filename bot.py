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
from telegram.error import BadRequest


# =====================================================
# 1. Telegram Bot Token
# =====================================================

TOKEN = "8757771538:AAFhe_TDcM1Ffg5MJ2bsCGyJUXOr5QlNH-8"


# =====================================================
# 2. ইংরেজি ফাইল নেম থেকে বাংলা নাম ম্যাপিং
# =====================================================

BANGLA_MAP = {
    "rangpur": "রংপুর বিভাগ", "rajshahi": "রাজশাহী বিভাগ", "khulna": "খুলনা বিভাগ",
    "barishal": "বরিশাল বিভাগ", "dhaka": "ঢাকা বিভাগ", "mymensingh": "ময়মনসিংহ বিভাগ",
    "sylhet": "সিলেট বিভাগ", "chattogram": "চট্টগ্রাম বিভাগ",
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
    "chandpur": "চাঁদপুর", "feni": "ফেনী", "noakhali": "নোয়াখালী",
    "lakshmipur": "লক্ষ্মীপুর", "coxsbazar": "কক্সবাজার", "khagrachhari": "খাগড়াছড়ি",
    "rangamati": "রাঙ্গামাটি", "bandarban": "বান্দরবান"
}


# =====================================================
# 3. অটোমেটিক ফাইল স্ক্যানার ও ডিটেক্টর (ZIP Only)
# =====================================================

SEAT_FILES = {}
DIVISIONS_MAP = {}

def auto_load_zip_files():
    global SEAT_FILES, DIVISIONS_MAP
    SEAT_FILES.clear()
    DIVISIONS_MAP.clear()
    zip_files = [f for f in os.listdir(".") if f.startswith("voters_") and f.endswith(".zip")]
    for index, zip_name in enumerate(sorted(zip_files), start=1):
        seat_key = f"auto_seat_{index}"
        raw_name = zip_name.replace("voters_", "").replace(".zip", "")
        parts = raw_name.split("_")
        division_raw = parts[0].lower() if len(parts) > 0 else "other"
        district_raw = parts[1].lower() if len(parts) > 1 else "general"
        seat_raw = parts[2] if len(parts) > 2 else f"{index}"
        division = BANGLA_MAP.get(division_raw, division_raw.capitalize())
        district = BANGLA_MAP.get(district_raw, district_raw.capitalize())
        seat_name = f"আসন-{seat_raw.replace('seat', '')}"
        SEAT_FILES[seat_key] = {"name": seat_name, "division": division, "district": district, "zip": zip_name}
        if division not in DIVISIONS_MAP: DIVISIONS_MAP[division] = {}
        if district not in DIVISIONS_MAP[division]: DIVISIONS_MAP[division][district] = []
        DIVISIONS_MAP[division][district].append(seat_key)

auto_load_zip_files()

web_app = Flask(__name__)
@web_app.route("/")
def home(): return "Telegram Demo Search Bot is running!"
def run_web_server(): web_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def normalize(text): return str(text).strip().lower().replace(" ", "").replace("_", "").replace("-", "")

def search_zip(zip_path, search_input, search_type):
    if not os.path.exists(zip_path): return []
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
            all_files = z.namelist()
            csv_file_name = next((f for f in all_files if f.lower().endswith(".csv")), None)
            if not csv_file_name: return []
            with z.open(csv_file_name) as file:
                text_file = io.TextIOWrapper(file, encoding="utf-8-sig", errors="replace", newline="")
                reader = csv.DictReader(text_file)
                for row in reader:
                    normalized_row = {normalize(k): str(v or "") for k, v in row.items()}
                    if search_type == "multi":
                        is_match = True
                        for field, search_val in search_input.items():
                            if not search_val: continue
                            possible_cols = column_mappings.get(field, [])
                            found_value = next((normalized_row[normalize(col)] for col in possible_cols if normalize(col) in normalized_row), "")
                            s_val, f_val = str(search_val).strip().lower(), str(found_value).strip().lower()
                            if field == "dob": s_val, f_val = s_val.replace("-", "/").replace(".", "/"), f_val.replace("-", "/").replace(".", "/")
                            if s_val not in f_val:
                                is_match = False
                                break
                        if is_match: results.append(dict(row))
                    else:
                        search_columns = column_mappings.get(search_type, [])
                        found_value = next((normalized_row[normalize(column)] for column in search_columns if normalize(column) in normalized_row), "")
                        search_value = str(search_input).strip().lower()
                        f_val = str(found_value).strip().lower()
                        if search_type == "dob": search_value, f_val = search_value.replace("-", "/").replace(".", "/"), f_val.replace("-", "/").replace(".", "/")
                        if search_value in f_val: results.append(dict(row))
    except Exception as e: print("Zip Search Error:", e)
    return results

def get_value(row, names):
    normalized_row = {normalize(k): v for k, v in row.items()}
    for name in names:
        value = normalized_row.get(normalize(name))
        if value: return str(value).strip()
    return "N/A"

# =====================================================
# 8. রিপোর্ট ফরম্যাটিং (আপডেটেড)
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

    return (
        f"🪪 *ভোটার রিপোর্ট*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢 ID: {voter_no} | 🔖 সিরিয়াল: {serial}\n"
        f"👤 নাম: *{name}*\n"
        f"👨 পিতা: {father} | 👩 মাতা: {mother}\n"
        f"🎂 জন্ম: {dob} | ⚧ লিঙ্গ: {gender}\n"
        f"💼 পেশা: {occupation}\n"
        f"🏠 ঠিকানা: {address}\n"
        f"📍 এলাকা: {area} | 🏛 {district}"
    )

async def safe_edit_message(query, text, reply_markup=None, parse_mode="Markdown"):
    try: await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest as e: pass

# ... (Menu functions remain same) ...

async def show_division_menu(query_or_message):
    keyboard = []
    divisions = list(DIVISIONS_MAP.keys())
    for i in range(0, len(divisions), 2):
        row = [InlineKeyboardButton(f"🌍 {divisions[i]}", callback_data=f"div_{divisions[i]}")]
        if i + 1 < len(divisions): row.append(InlineKeyboardButton(f"🌍 {divisions[i+1]}", callback_data=f"div_{divisions[i+1]}"))
        keyboard.append(row)
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🏠 Demo Search Bot\n\n🌍 একটি বিভাগ নির্বাচন করুন:"
    if hasattr(query_or_message, 'edit_message_text'): await safe_edit_message(query_or_message, text, reply_markup=reply_markup)
    else: await query_or_message.reply_text(text, reply_markup=reply_markup)

async def show_district_menu(query, context):
    division = context.user_data.get("division")
    districts = list(DIVISIONS_MAP.get(division, {}).keys())
    keyboard = []
    for i in range(0, len(districts), 2):
        row = [InlineKeyboardButton(f"🗺 {districts[i]}", callback_data=f"dis_{districts[i]}")]
        if i + 1 < len(districts): row.append(InlineKeyboardButton(f"🗺 {districts[i+1]}", callback_data=f"dis_{districts[i+1]}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 পূর্বের মেনু", callback_data="back_division")])
    await safe_edit_message(query, f"🌍 বিভাগ: {division}\n\n🗺 এখন একটি জেলা নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_seat_menu(query, context):
    division, district = context.user_data.get("division"), context.user_data.get("district")
    seat_keys = DIVISIONS_MAP.get(division, {}).get(district, [])
    keyboard = []
    for i in range(0, len(seat_keys), 2):
        row = [InlineKeyboardButton(f"🏛 {SEAT_FILES[seat_keys[i]]['name']}", callback_data=seat_keys[i])]
        if i + 1 < len(seat_keys): row.append(InlineKeyboardButton(f"🏛 {SEAT_FILES[seat_keys[i+1]]['name']}", callback_data=seat_keys[i+1]))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 পূর্বের মেনু", callback_data="back_district")])
    await safe_edit_message(query, f"🌍 বিভাগ: {division}\n🗺 জেলা: {district}\n\n🏛 এখন একটি আসন নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_search_menu(query_or_message, context):
    seat = context.user_data.get("seat")
    info = SEAT_FILES.get(seat, {})
    keyboard = [
        [InlineKeyboardButton("⚡ Multi Search", callback_data="search_multi")],
        [InlineKeyboardButton("🆔 ID", callback_data="search_demo_id"), InlineKeyboardButton("👤 নাম", callback_data="search_name")],
        [InlineKeyboardButton("👨 পিতার নাম", callback_data="search_father"), InlineKeyboardButton("👩 মাতার নাম", callback_data="search_mother")],
        [InlineKeyboardButton("🎂 জন্মতারিখ", callback_data="search_dob")],
        [InlineKeyboardButton("🔙 আসন পরিবর্তন", callback_data="back_seat")]
    ]
    text = f"🌍 বিভাগ: {info.get('division', 'N/A')}\n🗺 জেলা: {info.get('district', 'N/A')}\n🏛 আসন: {info.get('name', 'N/A')}\n\n🔎 সার্চ অপশন:"
    if hasattr(query_or_message, 'edit_message_text'): await safe_edit_message(query_or_message, text, reply_markup=InlineKeyboardMarkup(keyboard))
    else: await query_or_message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update, context): context.user_data.clear(); auto_load_zip_files(); await show_division_menu(update.message)

# =====================================================
# 10. Handler (আপডেটেড ডুপ্লিকেট ফিল্টারিং সহ)
# =====================================================

async def search_handler(update, context):
    if "seat" not in context.user_data or "search_type" not in context.user_data: return
    raw_text = update.message.text.strip()
    search_type, seat = context.user_data["search_type"], context.user_data["seat"]
    info = SEAT_FILES.get(seat, {})
    
    # [আপনার আগের লজিক এখানে...]
    if search_type == "multi":
        parsed = {"name": "", "father": "", "mother": "", "dob": ""}
        lines = raw_text.split("\n")
        for line in lines:
            if ":" in line: key, val = line.split(":", 1)
            elif "：" in line: key, val = line.split("：", 1)
            else: continue
            key, val = key.strip().lower(), val.strip()
            if key in ["নাম", "name"]: parsed["name"] = val
            elif key in ["পিতা", "পিতার নাম", "father", "fathername"]: parsed["father"] = val
            elif key in ["মাতা", "মাতার নাম", "mother", "mothername"]: parsed["mother"] = val
            elif key in ["জন্ম", "জন্মতারিখ", "dob", "dateofbirth"]: parsed["dob"] = val
        search_input = parsed
    else: search_input = raw_text

    await update.message.reply_text("🔍 সার্চ করা হচ্ছে...")
    raw_results = search_zip(info["zip"], search_input, search_type)

    # ডুপ্লিকেট ফিল্টার
    unique_results, seen = [], set()
    for item in raw_results:
        v_id = get_value(item, ["voter_no", "id"])
        v_name = get_value(item, ["name", "নাম"])
        unique_key = f"{v_id}_{v_name}"
        if unique_key not in seen:
            seen.add(unique_key)
            unique_results.append(item)

    if not unique_results:
        await update.message.reply_text("❌ কোনো তথ্য পাওয়া যায়নি।")
        return

    for row in unique_results[:10]:
        await update.message.reply_text(make_report(row, info['name'], info['division'], info['district']), parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    app.run_polling()

if __name__ == "__main__": main()
