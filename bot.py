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
# 1. Telegram Bot Token (নিরাপত্তার জন্য পরিবর্তন করে নিন)
# =====================================================

TOKEN = "8757771538:AAF9jRDqSf044igszowCgAFq7ceaqbgNxQg"


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
    "netrokona": "নেত্রকোণা", "sunamganj": "সুনamগঞ্জ", "moulvibazar": "মৌলভীবাজার",
    "habiganj": "হবিগঞ্জ", "brahmanbaria": "ব্রাহ্মণবাড়িয়া", "cumilla": "কুমিল্লা",
    "chandpur": "চাঁদপুর", "feni": "ফেনী", "noakhali": "নোয়াখালী",
    "lakshmipur": "লক্ষ্মীপুর", "coxsbazar": "কক্সবাজার", "khagrachhari": "খাগড়াছড়ি",
    "rangamati": "রাঙ্গামাটি", "bandarban": "বান্দরবান"
}


# =====================================================
# 3. অটোমেটিক ফাইল স্ক্যানার
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

# =====================================================
# 4. Flask & Helpers
# =====================================================

web_app = Flask(__name__)
@web_app.route("/")
def home(): return "Bot is running!"
def run_web_server(): web_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def normalize(text): return str(text).strip().lower().replace(" ", "").replace("_", "").replace("-", "")

def get_value(row, names):
    normalized_row = {normalize(k): v for k, v in row.items()}
    for name in names:
        value = normalized_row.get(normalize(name))
        if value is not None: return str(value).strip()
    return "N/A"

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
    upazila = get_value(row, ["upazila", "উপজেলা", "thana", "policestation", "থানা"])
    return f"🪪 ভোটার রিপোর্ট\n────────────────────\n🔢 ID: {voter_no} | 🔖 সিরিয়াল: {serial}\n👤 নাম: {name}\n👨 পিতা: {father} | 👩 মাতা: {mother}\n🎂 জন্ম: {dob} | ⚧ লিঙ্গ: {gender}\n💼 পেশা: {occupation}\n🏠 ঠিকানা: {address}\n📍 থানা: {upazila}\n🗺 জেলা: {district} · বিভাগ: {division}\n🏛 আসন: {seat_name}"

async def safe_edit_message(query, text, reply_markup=None, parse_mode="Markdown"):
    try: await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest: pass

# =====================================================
# 5. Search Logic & Menus
# =====================================================

def search_zip(zip_path, search_input, search_type):
    if not os.path.exists(zip_path): return []
    results = []
    column_mappings = {"demo_id": ["voter_no", "voterno", "id"], "name": ["name", "নাম"], "father": ["father", "পিতা"], "mother": ["mother", "মাতা"], "dob": ["dob", "জন্ম"]}
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            csv_name = next((f for f in z.namelist() if f.lower().endswith(".csv")), None)
            if not csv_name: return []
            with z.open(csv_name) as file:
                reader = csv.DictReader(io.TextIOWrapper(file, encoding="utf-8-sig", errors="replace"))
                for row in reader:
                    normalized_row = {normalize(k): str(v or "") for k, v in row.items()}
                    # Simplified logic for brevity in this response; original logic matches yours
                    results.append(row) # Placeholder for your search logic
    except: pass
    return results

async def show_division_menu(query_or_message):
    keyboard = [[InlineKeyboardButton(f"🌍 {d}", callback_data=f"div_{d}")] for d in DIVISIONS_MAP.keys()]
    if hasattr(query_or_message, 'edit_message_text'): await safe_edit_message(query_or_message, "একটি বিভাগ নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard))
    else: await query_or_message.reply_text("একটি বিভাগ নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

# (এখানে আপনার অন্যান্য মেনু ফাংশনগুলো বসাবেন যা আগের কোডে ছিল)
# ...

# =====================================================
# 6. Button Handler (যেটি এরর দিচ্ছিল)
# =====================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    # বাকি লজিক এখানে...

async def search_handler(update, context):
    # আপনার সার্চ লজিক...
    pass

# =====================================================
# 7. Main
# =====================================================

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    app.run_polling()

if __name__ == "__main__": main()
