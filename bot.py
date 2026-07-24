import os
import csv
import zipfile
import io
import re
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
from telegram.error import BadRequest

# =====================================================
# 1. Telegram Bot Token
# =====================================================
TOKEN = "8908728538:AAEMB6huV4-n-LpmcW8KXaYmKU5c0zKxiHM"

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
# 3. ফাইল স্ক্যানার ও সার্চ ইঞ্জিন
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

def normalize(text): return str(text).strip().lower().replace(" ", "").replace("_", "").replace("-", "")

def get_value(row, names):
    normalized_row = {normalize(k): v for k, v in row.items()}
    for name in names:
        value = normalized_row.get(normalize(name))
        if value: return str(value).strip()
    return "N/A"

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
            csv_file_name = next((f for f in z.namelist() if f.lower().endswith(".csv")), None)
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
                            if str(search_val).strip().lower() not in str(found_value).strip().lower():
                                is_match = False
                                break
                        if is_match: results.append(dict(row))
                    else:
                        search_columns = column_mappings.get(search_type, [])
                        found_value = next((normalized_row[normalize(col)] for col in search_columns if normalize(col) in normalized_row), "")
                        if str(search_input).strip().lower() in str(found_value).strip().lower(): results.append(dict(row))
    except Exception as e: print("Error:", e)
    return results

# =====================================================
# 4. রিপোর্ট ফরম্যাট (আপনার চাহিদা অনুযায়ী)
# =====================================================
def make_report(row, seat_name, division, district):
    name = get_value(row, ["name", "fullname", "নাম"])
    voter_no = get_value(row, ["voter_no", "voterno", "demo_id", "demoid", "id"])
    serial = get_value(row, ["serial", "serialnumber", "সিরিয়াল"])
    father = get_value(row, ["father", "fathername", "পিতা"])
    mother = get_value(row, ["mother", "mothername", "মাতা"])
    dob = get_value(row, ["dob", "dateofbirth", "birthdate", "জন্ম"])
    gender = get_value(row, ["gender", "sex", "লিঙ্গ"])
    occupation = get_value(row, ["occupation", "profession", "পেশা"])
    address = get_value(row, ["address", "ঠিকানা"])
    upazila = get_value(row, ["upazila", "উপজেলা", "thana", "policestation", "থানা"])
    return (
        f"🪪 *{name}*\n"
        f"────────────────────\n"
        f"🔢 NID: {voter_no}\n"
        f"🔖 সিরিয়াল: {serial}\n"
        f"👨 পিতা: {father}\n"
        f"👩 মাতা: {mother}\n"
        f"🎂 জন্ম: {dob}\n"
        f"⚧ লিঙ্গ: {gender}\n"
        f"💼 পেশা: {occupation}\n"
        f"🏠 ঠিকানা: {address}\n"
        f"📍 থানা: {upazila}\n"
        f"🗺 জেলা: {district} · বিভাগ: {division}\n"
        f"🏛 আসন: {seat_name}"
    )

# =====================================================
# 5. বটের অন্যান্য মেনু ও হ্যান্ডলার
# =====================================================
async def safe_edit_message(query, text, reply_markup=None):
    try: await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")
    except BadRequest: pass

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("div_"):
        context.user_data["division"] = data.split("_")[1]
        await show_district_menu(query, context)
    elif data.startswith("dis_"):
        context.user_data["district"] = data.split("_")[1]
        await show_seat_menu(query, context)
    elif data.startswith("auto_seat_"):
        context.user_data["seat"] = data
        await show_search_menu(query, context)
    elif data.startswith("search_"):
        context.user_data["search_type"] = data.split("_")[1]
        await query.edit_message_text(f"আপনার {data.split('_')[1].upper()} তথ্য লিখুন:")
    elif data == "back_division": await show_division_menu(query)
    elif data == "back_district": await show_district_menu(query, context)
    elif data == "back_seat": await show_seat_menu(query, context)

async def show_division_menu(query):
    keyboard = [[InlineKeyboardButton(f"🌍 {d}", callback_data=f"div_{d}")] for d in DIVISIONS_MAP.keys()]
    await safe_edit_message(query, "🌍 বিভাগ নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_district_menu(query, context):
    districts = list(DIVISIONS_MAP.get(context.user_data["division"], {}).keys())
    keyboard = [[InlineKeyboardButton(f"🗺 {d}", callback_data=f"dis_{d}")] for d in districts]
    keyboard.append([InlineKeyboardButton("🔙", callback_data="back_division")])
    await safe_edit_message(query, "🗺 জেলা নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_seat_menu(query, context):
    seat_keys = DIVISIONS_MAP.get(context.user_data["division"], {}).get(context.user_data["district"], [])
    keyboard = [[InlineKeyboardButton(f"🏛 {SEAT_FILES[s]['name']}", callback_data=s)] for s in seat_keys]
    keyboard.append([InlineKeyboardButton("🔙", callback_data="back_district")])
    await safe_edit_message(query, "🏛 আসন নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_search_menu(query, context):
    keyboard = [[InlineKeyboardButton("🆔 ID", callback_data="search_demo_id"), InlineKeyboardButton("👤 নাম", callback_data="search_name")]]
    await safe_edit_message(query, "🔎 সার্চ টাইপ সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

async def search_handler(update, context):
    if "seat" not in context.user_data or "search_type" not in context.user_data: return
    info = SEAT_FILES.get(context.user_data["seat"])
    raw_results = search_zip(info["zip"], update.message.text, context.user_data["search_type"])
    
    seen, unique_results = set(), []
    for item in raw_results:
        uid = get_value(item, ["voter_no", "id"])
        if uid not in seen:
            seen.add(uid)
            unique_results.append(item)
    
    if not unique_results: await update.message.reply_text("❌ তথ্য পাওয়া যায়নি।")
    else:
        for row in unique_results[:5]:
            await update.message.reply_text(make_report(row, info['name'], info['division'], info['district']), parse_mode="Markdown")

async def start(update, context): await show_division_menu(update.message)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    app.run_polling()

if __name__ == "__main__": main()
