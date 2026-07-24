import csv
from datetime import datetime
import io
import os
import re
import threading
import zipfile

from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =====================================================
# 1. Telegram Bot Token
# =====================================================

TOKEN = "8757771538:AAF9jRDqSf044igszowCgAFq7ceaqbgNxQg"


# =====================================================
# 2. বাংলা ম্যাপিং (বিভাগ, জেলা, থানা ও ঠিকানার সাধারণ শব্দ)
# =====================================================

BANGLA_MAP = {
    # বিভাগসমূহ
    "rangpur": "রংপুর",
    "rajshahi": "রাজশাহী",
    "khulna": "খুলনা",
    "barishal": "বরিশাল",
    "dhaka": "ঢাকা",
    "mymensingh": "ময়মনসিংহ",
    "sylhet": "সিলেট",
    "chattogram": "চট্টগ্রাম",
    # জেলাসমূহ
    "panchagarh": "পঞ্চগড়",
    "thakurgaon": "ঠাকুরগাঁও",
    "dinajpur": "দিনাজপুর",
    "nilphamari": "নীলফামারী",
    "lalmonirhat": "লালমনিরহাট",
    "kurigram": "কুড়িগ্রাম",
    "gaibandha": "গাইবান্ধা",
    "joypurhat": "জয়পুরহাট",
    "bogura": "বগুড়া",
    "bogra": "বগুড়া",
    "chapainawabganj": "চাঁপাইনবাবগঞ্জ",
    "naogaon": "নওগাঁ",
    "natore": "নাটোর",
    "sirajganj": "সিরাজগঞ্জ",
    "pabna": "পাবনা",
    "meherpur": "মেহেরপুর",
    "kushtia": "কুষ্টিয়া",
    "chuadanga": "চুয়াডাঙ্গা",
    "jhenaidah": "ঝিনাইদহ",
    "jashore": "যশোর",
    "jessore": "যশোর",
    "magura": "মাগুরা",
    "narail": "নড়াইল",
    "bagerhat": "বাগেরহাট",
    "satkhira": "সাতক্ষীরা",
    "barguna": "বরগুনা",
    "patuakhali": "পটুয়াখালী",
    "bhola": "ভোলা",
    "jhalokati": "ঝালকাঠি",
    "pirojpur": "পিরোজপুর",
    "tangail": "টাঙ্গাইল",
    "kishoreganj": "কিশোরগঞ্জ",
    "manikganj": "মানিকগঞ্জ",
    "munshiganj": "মুন্সীগঞ্জ",
    "gazipur": "গাজীপুর",
    "narsingdi": "নরসিংদী",
    "narayanganj": "নারায়ণগঞ্জ",
    "rajbari": "রাজবাড়ী",
    "faridpur": "ফরিদপুর",
    "gopalganj": "গোপালগঞ্জ",
    "madaripur": "মাদারীপুর",
    "shariatpur": "শরীয়তপুর",
    "jamalpur": "জামালপুর",
    "sherpur": "শেরপুর",
    "netrokona": "নেত্রকোণা",
    "sunamganj": "সুনামগঞ্জ",
    "moulvibazar": "মৌলভীবাজার",
    "habiganj": "হবিগঞ্জ",
    "brahmanbaria": "ব্রাহ্মণবাড়িয়া",
    "cumilla": "কুমিল্লা",
    "comilla": "কুমিল্লা",
    "chandpur": "চাঁদপুর",
    "feni": "ফেনী",
    "noakhali": "নোয়াখালী",
    "lakshmipur": "লক্ষ্মীপুর",
    "coxsbazar": "কক্সবাজার",
    "khagrachhari": "খাগড়াছড়ি",
    "rangamati": "রাঙ্গামাটি",
    "bandarban": "বান্দরবান",
}

# 🔹 থানার নাম বাংলা করার বর্ধিত ম্যাপিং ডিকশনারি
THANA_MAP = {
    # ঢাকা ও গাজীপুর
    "savar": "সাভার",
    "dhamrai": "ধামরাই",
    "keraniganj": "কেরানীগঞ্জ",
    "dohar": "দোহার",
    "nawabganj": "নবাবগঞ্জ",
    "mirpur": "মিরপুর",
    "uttara": "উত্তরা",
    "gulshan": "গুলশান",
    "dhanmondi": "ধানমন্ডি",
    "gazipur sadar": "গাজীপুর সদর",
    "kaliakair": "কালিয়াকৈর",
    "kapasia": "কাপাসিয়া",
    "sreepur": "শ্রীপুর",
    "kaliganj": "কালীগঞ্জ",
    "tejgaon": "তেজগাঁও",
    "ramna": "রমনা",
    "shahbagh": "শাহবাগ",
    "paltan": "পল্টন",
    "motijheel": "মতিঝিল",
    "jatrabari": "যাত্রাবাড়ী",
    "kadamtali": "কদমতলী",
    "badda": "বাড্ডা",
    "khilkhet": "খিলক্ষেত",
    "mohammadpur": "মোহাম্মদপুর",
    "adonbor": "আদাবর",
    "kafrul": "কাফরুল",
    "cantonment": "ক্যান্টনমেন্ট",
    # বগুড়া ও পাবনা
    "bogura sadar": "বগুড়া সদর",
    "bogra sadar": "বগুড়া সদর",
    "sathiya": "সাঁথিয়া",
    "santhia": "সাঁথিয়া",
    "ishwardi": "ঈশ্বরদী",
    "pabna sadar": "পাবনা সদর",
    "sherpur": "শেরপুর",
    "shibganj": "শিবগঞ্জ",
    "gabtali": "গাবতলী",
    "kahaloo": "কাহালু",
    "nandigram": "নন্দীগ্রাম",
    "dhopchanchia": "দুপচাঁচিয়া",
    "adamdighi": "আদমদীঘি",
    "sariakandi": "সারিয়াকান্দি",
    "dhunat": "ধুনট",
    "sonatala": "সোনাভোলা",
    # চট্টগ্রাম ও অন্যান্য
    "chattogram sadar": "চট্টগ্রাম সদর",
    "kotwali": "কোতোয়ালী",
    "panchlaish": "পাঁচলাইশ",
    "halishahar": "হালিশহর",
    "patenga": "পতেঙ্গা",
    "double mooring": "ডবলমুরিং",
    "sylhet sadar": "সিলেট সদর",
    "khulna sadar": "খুলনা সদর",
    "rajshahi sadar": "রাজশাহী সদর",
    "rangpur sadar": "রংপুর সদর",
    "barishal sadar": "বরিশাল সদর",
    "cumilla sadar": "কুমিল্লা সদর",
}

# 🔹 ঠিকানায় সাধারণ ইংরেজি শব্দগুলোর বাংলা অনুবাদ ডিকশনারি
ADDRESS_WORDS_MAP = {
    "village": "গ্রাম",
    "vill": "গ্রাম",
    "v/o": "গ্রাম",
    "v/p": "গ্রাম ও ডাক",
    "post": "ডাকঘর",
    "po": "ডাকঘর",
    "p.o": "ডাকঘর",
    "p/o": "ডাকঘর",
    "word": "ওয়ার্ড",
    "ward": "ওয়ার্ড",
    "no": "নং",
    "no.": "নং",
    "road": "রোড",
    "rd": "রোড",
    "house": "বাসা",
    "holding": "হোন্ডিং",
    "union": "ইউনিয়ন",
    "upazila": "উপজেলা",
    "thana": "থানা",
    "district": "জেলা",
    "para": "পাড়া",
    "mohalla": "মহল্লা",
    "mahalla": "মহল্লা",
    "bazar": "বাজার",
    "east": "পূর্ব",
    "west": "পশ্চিম",
    "north": "উত্তর",
    "south": "দক্ষিণ",
    "block": "ব্লক",
    "sector": "সেক্টর",
}


# =====================================================
# 3. অটোমেটিক ফাইল স্ক্যানার (ZIP & CSV Reader)
# =====================================================

SEAT_FILES = {}
DIVISIONS_MAP = {}


def auto_load_csv_files():
  global SEAT_FILES, DIVISIONS_MAP
  SEAT_FILES.clear()
  DIVISIONS_MAP.clear()

  data_files = [
      f
      for f in os.listdir(".")
      if f.startswith("voters_") and (f.endswith(".zip") or f.endswith(".csv"))
  ]

  for index, file_name in enumerate(sorted(data_files), start=1):
    seat_key = f"auto_seat_{index}"

    raw_name = (
        file_name.replace("voters_", "").replace(".zip", "").replace(".csv", "")
    )
    parts = raw_name.split("_")

    division_raw = parts[0].lower() if len(parts) > 0 else "other"
    district_raw = parts[1].lower() if len(parts) > 1 else "general"
    seat_raw = parts[2] if len(parts) > 2 else f"{index}"

    division = BANGLA_MAP.get(division_raw, division_raw.capitalize())
    district = BANGLA_MAP.get(district_raw, district_raw.capitalize())
    seat_name = f"{district}-{seat_raw.replace('seat', '')}"

    SEAT_FILES[seat_key] = {
        "name": seat_name,
        "division": division,
        "district": district,
        "file": file_name,
    }

    if division not in DIVISIONS_MAP:
      DIVISIONS_MAP[division] = {}
    if district not in DIVISIONS_MAP[division]:
      DIVISIONS_MAP[division][district] = []

    DIVISIONS_MAP[division][district].append(seat_key)

  print(f"✅ মোট {len(SEAT_FILES)} টি ফাইল (ZIP/CSV) লোড হয়েছে!")


auto_load_csv_files()


# =====================================================
# 4. Web Server
# =====================================================

web_app = Flask(__name__)


@web_app.route("/")
def home():
  return "Bot is running!"


def run_web_server():
  port = int(os.environ.get("PORT", 10000))
  web_app.run(host="0.0.0.0", port=port)


# =====================================================
# 5. Helper & Fast Search Function
# =====================================================


def normalize(text):
  return (
      str(text).strip().lower().replace(" ", "").replace("_", "").replace("-", "")
  )


def get_thana_from_raw(raw_thana):
  if not raw_thana or raw_thana == "N/A":
    return "N/A"
  clean = raw_thana.lower().strip()

  if clean in THANA_MAP:
    return THANA_MAP[clean]

  for k, v in THANA_MAP.items():
    if k in clean:
      return v

  return raw_thana.title()


def get_translated_address(raw_address):
  if not raw_address or raw_address == "N/A":
    return "N/A"

  translated = raw_address

  for eng_word, bng_word in ADDRESS_WORDS_MAP.items():
    pattern = re.compile(rf"\b{re.escape(eng_word)}\b", re.IGNORECASE)
    translated = pattern.sub(bng_word, translated)

  return translated


def search_in_files(file_list, search_input, search_type, target_thana=None):
  results = []
  column_mappings = {
      "demo_id": ["voter_no", "voterno", "demo_id", "demoid", "id", "nid"],
      "name": ["name", "fullname", "নাম"],
      "father": ["father", "fathername", "পিতা"],
      "mother": ["mother", "mothername", "মাতা"],
      "dob": ["dob", "dateofbirth", "birthdate", "জন্ম"],
  }

  for file_info in file_list:
    file_path = file_info["file"]
    seat_name = file_info["name"]
    division = file_info["division"]
    district = file_info["district"]

    if not os.path.exists(file_path):
      continue

    try:
      if file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, "r") as z:
          csv_files_in_zip = [f for f in z.namelist() if f.endswith(".csv")]
          if not csv_files_in_zip:
            continue
          with z.open(csv_files_in_zip[0]) as f:
            content = io.TextIOWrapper(
                f, encoding="utf-8-sig", errors="replace"
            )
            reader = csv.DictReader(content)
            res = process_rows(
                reader,
                search_input,
                search_type,
                column_mappings,
                seat_name,
                division,
                district,
                target_thana,
            )
            results.extend(res)
      else:
        with open(
            file_path, mode="r", encoding="utf-8-sig", errors="replace"
        ) as file:
          reader = csv.DictReader(file)
          res = process_rows(
              reader,
              search_input,
              search_type,
              column_mappings,
              seat_name,
              division,
              district,
              target_thana,
          )
          results.extend(res)

    except Exception as e:
      print("CSV Search Error:", e)

  return results


def process_rows(
    reader,
    search_input,
    search_type,
    column_mappings,
    seat_name,
    division,
    district,
    target_thana=None,
):
  results = []
  for row in reader:
    if target_thana:
      row_thana = get_value(
          row, ["upazila", "উপজেলা", "thana", "policestation", "থানা"]
      )
      translated_thana = get_thana_from_raw(row_thana)
      if (
          target_thana.lower() not in translated_thana.lower()
          and target_thana.lower() not in row_thana.lower()
      ):
        continue

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
        item = dict(row)
        item["_meta_seat"] = seat_name
        item["_meta_division"] = division
        item["_meta_district"] = district
        results.append(item)

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
        found_value_normalized = found_value_normalized.replace(
            "-", "/"
        ).replace(".", "/")

      if search_value in found_value_normalized:
        item = dict(row)
        item["_meta_seat"] = seat_name
        item["_meta_division"] = division
        item["_meta_district"] = district
        results.append(item)

  return results


def extract_thanas_from_district(seat_keys):
  thanas = set()
  for key in seat_keys:
    file_info = SEAT_FILES.get(key)
    if not file_info:
      continue
    file_path = file_info["file"]

    try:
      if file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, "r") as z:
          csv_files = [f for f in z.namelist() if f.endswith(".csv")]
          if csv_files:
            with z.open(csv_files[0]) as f:
              content = io.TextIOWrapper(
                  f, encoding="utf-8-sig", errors="replace"
              )
              reader = csv.DictReader(content)
              count = 0
              for r in reader:
                th = get_value(
                    r, ["upazila", "উপজেলা", "thana", "policestation", "থানা"]
                )
                if th and th != "N/A":
                  thanas.add(get_thana_from_raw(th))
                count += 1
                if count > 2000 and len(thanas) >= 10:
                  break
      else:
        with open(
            file_path, mode="r", encoding="utf-8-sig", errors="replace"
        ) as file:
          reader = csv.DictReader(file)
          count = 0
          for r in reader:
            th = get_value(
                r, ["upazila", "উপজেলা", "thana", "policestation", "থানা"]
            )
            if th and th != "N/A":
              thanas.add(get_thana_from_raw(th))
            count += 1
            if count > 2000 and len(thanas) >= 10:
              break
    except Exception as e:
      print(f"Error reading thana: {e}")

  return sorted(list(thanas))


def get_value(row, names):
  normalized_row = {normalize(k): v for k, v in row.items()}
  for name in names:
    value = normalized_row.get(normalize(name))
    if value is not None:
      value = str(value).strip()
      if value:
        return value
  return "N/A"


def calculate_age(dob_str):
  if not dob_str or dob_str == "N/A":
    return ""
  try:
    clean_dob = dob_str.replace(".", "/").replace("-", "/")
    parts = clean_dob.split("/")
    if len(parts) == 3:
      day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
      birth_date = datetime(year, month, day)
      today = datetime.today()
      age = (
          today.year
          - birth_date.year
          - ((today.month, today.day) < (birth_date.month, birth_date.day))
      )
      return f" · {age} বছর"
  except Exception:
    pass
  return ""


def make_report(row):
  voter_no = get_value(
      row, ["voter_no", "voterno", "demo_id", "demoid", "id", "nid"]
  )
  serial = get_value(row, ["serial", "serialnumber", "সিরিয়াল"])
  name = get_value(row, ["name", "fullname", "নাম"])
  father = get_value(row, ["father", "fathername", "পিতা"])
  mother = get_value(row, ["mother", "mothername", "মাতা"])
  dob = get_value(row, ["dob", "dateofbirth", "birthdate", "জন্ম"])
  gender = get_value(row, ["gender", "sex", "লিঙ্গ"])
  occupation = get_value(row, ["occupation", "profession", "পেশা"])

  raw_address = get_value(row, ["address", "ঠিকানা"])
  address = get_translated_address(raw_address)

  raw_upazila = get_value(
      row, ["upazila", "উপজেলা", "thana", "policestation", "থানা"]
  )
  upazila = get_thana_from_raw(raw_upazila)

  area_code = get_value(row, ["code", "areacode", "আসনকোড", "কোড"])
  raw_age = get_value(row, ["age", "বয়স"])

  seat_name = row.get("_meta_seat", "N/A")
  division = row.get("_meta_division", "N/A")
  district = row.get("_meta_district", "N/A")

  if raw_age != "N/A" and raw_age != "":
    age_str = f" · {raw_age} বছর" if "বছর" not in raw_age else f" · {raw_age}"
  else:
    age_str = calculate_age(dob)

  return f"""🪪 {name}
────────────────────
🔢 NID  {voter_no}
🔖 সিরিয়াল  {serial}
👨 পিতা  {father}
👩 মাতা  {mother}
🎂 জন্ম  {dob}{age_str}
⚧ লিঙ্গ  {gender}
💼 পেশা  {occupation}
🏠 ঠিকানা  {address}
📍 থানা  {upazila}
🗺 জেলা  {district}  ·  বিভাগ  {division}
🏛 আসন  {seat_name}  ·  কোড  {area_code}"""


async def safe_edit_message(query, text, reply_markup=None, parse_mode=None):
  try:
    await query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode=parse_mode
    )
  except BadRequest as e:
    if "Message is not modified" in str(e):
      pass
    else:
      raise e


# =====================================================
# 6. Menus & Handlers
# =====================================================


async def show_division_menu(query_or_message):
  keyboard = []
  divisions = list(DIVISIONS_MAP.keys())

  if not divisions:
    text = "⚠️ কোনো voters_*.zip বা voters_*.csv ফাইল পাওয়া যায়নি!"
    if hasattr(query_or_message, "edit_message_text"):
      await safe_edit_message(query_or_message, text)
    else:
      await query_or_message.reply_text(text)
    return

  for i in range(0, len(divisions), 2):
    row = [
        InlineKeyboardButton(
            f"🌍 {divisions[i]}", callback_data=f"div_{divisions[i]}"
        )
    ]
    if i + 1 < len(divisions):
      row.append(
          InlineKeyboardButton(
              f"🌍 {divisions[i+1]}", callback_data=f"div_{divisions[i+1]}"
          )
      )
    keyboard.append(row)

  reply_markup = InlineKeyboardMarkup(keyboard)
  text = "🏠 Demo Search Bot\n\n🌍 একটি বিভাগ নির্বাচন করুন:"

  if hasattr(query_or_message, "edit_message_text"):
    await safe_edit_message(query_or_message, text, reply_markup=reply_markup)
  else:
    await query_or_message.reply_text(text, reply_markup=reply_markup)


async def show_district_menu(query, context):
  division = context.user_data.get("division")
  districts = list(DIVISIONS_MAP.get(division, {}).keys())

  keyboard = []
  for i in range(0, len(districts), 2):
    row = [
        InlineKeyboardButton(
            f"🗺 {districts[i]}", callback_data=f"dis_{districts[i]}"
        )
    ]
    if i + 1 < len(districts):
      row.append(
          InlineKeyboardButton(
              f"🗺 {districts[i+1]}", callback_data=f"dis_{districts[i+1]}"
          )
      )
    keyboard.append(row)

  keyboard.append(
      [InlineKeyboardButton("🔙 পূর্বের মেনু", callback_data="back_division")]
  )

  await safe_edit_message(
      query,
      f"🌍 বিভাগ: {division}\n\n🗺 এখন একটি জেলা নির্বাচন করুন:",
      reply_markup=InlineKeyboardMarkup(keyboard),
  )


async def show_district_options_menu(query, context):
  division = context.user_data.get("division")
  district = context.user_data.get("district")

  keyboard = [
      [
          InlineKeyboardButton(
              f"🎯 পুরো {district} জেলায় সার্চ করুন",
              callback_data="mode_district",
          )
      ],
      [
          InlineKeyboardButton(
              "📍 থানা অনুযায়ী সার্চ করুন", callback_data="mode_thana"
          )
      ],
      [
          InlineKeyboardButton(
              "🏛 আসন অনুযায়ী সার্চ করুন", callback_data="mode_seat"
          )
      ],
      [
          InlineKeyboardButton(
              "🔙 জেলা পরিবর্তন", callback_data="back_district"
          )
      ],
  ]

  await safe_edit_message(
      query,
      f"🌍 বিভাগ: {division}\n🗺 জেলা: {district}\n\nআপনি কীভাবে সার্চ করতে চান?",
      reply_markup=InlineKeyboardMarkup(keyboard),
  )


async def show_thana_menu(query, context):
  division = context.user_data.get("division")
  district = context.user_data.get("district")
  seat_keys = DIVISIONS_MAP.get(division, {}).get(district, [])

  try:
    await safe_edit_message(query, "⏳ থানার তালিকা লোড হচ্ছে, অপেক্ষা করুন...")
  except Exception:
    pass

  try:
    thanas = extract_thanas_from_district(seat_keys)
  except Exception as e:
    print("Thana reading exception:", e)
    thanas = []

  keyboard = []
  if thanas:
    for i in range(0, len(thanas), 2):
      row = [
          InlineKeyboardButton(
              f"📍 {thanas[i]}", callback_data=f"thana_{thanas[i]}"
          )
      ]
      if i + 1 < len(thanas):
        row.append(
            InlineKeyboardButton(
                f"📍 {thanas[i+1]}", callback_data=f"thana_{thanas[i+1]}"
            )
        )
      keyboard.append(row)
  else:
    keyboard.append([
        InlineKeyboardButton(
            "❌ কোনো থানা চিহ্নিত করা যায়নি (জেলাজুড়ে সার্চ করুন)",
            callback_data="mode_district",
        )
    ])

  keyboard.append([
      InlineKeyboardButton(
          "🔙 অপশন মেনু", callback_data="back_district_options"
      )
  ])

  await safe_edit_message(
      query,
      f"🌍 বিভাগ: {division}\n🗺 জেলা: {district}\n\n📍 এখন একটি থানা নির্বাচন করুন:",
      reply_markup=InlineKeyboardMarkup(keyboard),
  )


async def show_seat_menu(query, context):
  division = context.user_data.get("division")
  district = context.user_data.get("district")

  seat_keys = DIVISIONS_MAP.get(division, {}).get(district, [])

  keyboard = []
  for i in range(0, len(seat_keys), 2):
    seat_1 = SEAT_FILES[seat_keys[i]]
    row = [
        InlineKeyboardButton(
            f"🏛 {seat_1['name']}", callback_data=seat_keys[i]
        )
    ]

    if i + 1 < len(seat_keys):
      seat_2 = SEAT_FILES[seat_keys[i + 1]]
      row.append(
          InlineKeyboardButton(
              f"🏛 {seat_2['name']}", callback_data=seat_keys[i + 1]
          )
      )

    keyboard.append(row)

  keyboard.append([
      InlineKeyboardButton(
          "🔙 অপশন মেনু", callback_data="back_district_options"
      )
  ])

  await safe_edit_message(
      query,
      f"🌍 বিভাগ: {division}\n🗺 জেলা: {district}\n\n🏛 এখন একটি আসন নির্বাচন করুন:",
      reply_markup=InlineKeyboardMarkup(keyboard),
  )


async def show_search_menu(query_or_message, context):
  division = context.user_data.get("division", "N/A")
  district = context.user_data.get("district", "N/A")
  thana = context.user_data.get("thana")
  seat = context.user_data.get("seat")

  target_text = f"🌍 বিভাগ: {division}\n🗺 জেলা: {district}\n"
  if thana:
    target_text += f"📍 থানা: {thana}\n"
  elif seat:
    info = SEAT_FILES.get(seat, {})
    target_text += f"🏛 আসন: {info.get('name', 'N/A')}\n"
  else:
    target_text += "🎯 মোড: পুরো জেলা ফিল্টার\n"

  keyboard = [
      [
          InlineKeyboardButton(
              "⚡ Multi Search (AND Search)", callback_data="search_multi"
          )
      ],
      [
          InlineKeyboardButton(
              "🆔 Demo ID", callback_data="search_demo_id"
          ),
          InlineKeyboardButton("👤 Demo নাম", callback_data="search_name"),
      ],
      [
          InlineKeyboardButton(
              "👨 Demo পিতার নাম", callback_data="search_father"
          ),
          InlineKeyboardButton(
              "👩 Demo মাতার নাম", callback_data="search_mother"
          ),
      ],
      [
          InlineKeyboardButton(
              "🎂 Demo জন্মতারিখ", callback_data="search_dob"
          )
      ],
      [
          InlineKeyboardButton(
              "🔙 ফিল্টার পরিবর্তন", callback_data="back_district_options"
          )
      ],
  ]

  text = f"{target_text}\n🔎 কোন তথ্য দিয়ে সার্চ করতে চান?"

  if hasattr(query_or_message, "edit_message_text"):
    await safe_edit_message(
        query_or_message, text, reply_markup=InlineKeyboardMarkup(keyboard)
    )
  else:
    await query_or_message.reply_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard)
    )


# 🌟 নতুন যুক্ত করা /start ফাংশন (যেখানে বট চালু হলেই কিবোর্ড নিচে যুক্ত হবে)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data.clear()
  auto_load_csv_files()

  # 📌 আপনার দেওয়া ছবির মতো কাস্টম নিচের কিবোর্ড বাটনগুলো তৈরি করা হলো
  keyboard_buttons = [
      ["🔍 নতুন সার্চ", "📁 ফিল্টার"],
      ["📊 স্ট্যাটাস", "🏠 মেনু", "❌ রিসেট"],
  ]
  reply_keyboard = ReplyKeyboardMarkup(
      keyboard_buttons, resize_keyboard=True, persistent=True
  )

  await update.message.reply_text(
      "🤖 **Demo Search Bot-এ স্বাগতম!**", reply_markup=reply_keyboard
  )
  await show_division_menu(update.message)


async def send_page(query, context):
  results = context.user_data.get("results", [])
  page = context.user_data.get("page", 0)

  per_page = 10
  start_index = page * per_page
  end_index = start_index + per_page
  page_results = results[start_index:end_index]

  for row in page_results:
    report = make_report(row)
    await query.message.reply_text(report)

  keyboard = []
  if end_index < len(results):
    keyboard.append(
        [InlineKeyboardButton("➡️ আরো দেখুন", callback_data="next_page")]
    )

  keyboard.append([
      InlineKeyboardButton(
          "🔎 নতুন সার্চ (পূর্বের মেনু)", callback_data="new_search"
      )
  ])
  keyboard.append([
      InlineKeyboardButton(
          "🏠 মূল মেনু (Start)", callback_data="show_division"
      )
  ])

  await query.message.reply_text(
      f"📄 মোট ফলাফল: {len(results)} টি\n📑 দেখানো হয়েছে:"
      f" {start_index + 1} - {min(end_index, len(results))}",
      reply_markup=InlineKeyboardMarkup(keyboard),
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
    await show_district_options_menu(query, context)
    return

  if data == "back_division":
    await show_division_menu(query)
    return

  if data == "back_district":
    await show_district_menu(query, context)
    return

  if data == "back_district_options":
    context.user_data.pop("thana", None)
    context.user_data.pop("seat", None)
    await show_district_options_menu(query, context)
    return

  if data == "mode_district":
    context.user_data.pop("thana", None)
    context.user_data.pop("seat", None)
    await show_search_menu(query, context)
    return

  if data == "mode_thana":
    await show_thana_menu(query, context)
    return

  if data == "mode_seat":
    await show_seat_menu(query, context)
    return

  if data.startswith("thana_"):
    thana_name = data.replace("thana_", "")
    context.user_data["thana"] = thana_name
    context.user_data.pop("seat", None)
    await show_search_menu(query, context)
    return

  if data in SEAT_FILES:
    context.user_data["seat"] = data
    context.user_data.pop("thana", None)
    context.user_data.pop("search_type", None)
    await show_search_menu(query, context)
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
      "search_dob": {"type": "dob", "title": "🎂 Demo জন্মতারিখ"},
  }

  if data == "search_multi":
    context.user_data["search_type"] = "multi"
    text = (
        "⚡ **Multi Search (AND Search)**\n\n"
        "আপনি চাইলে নাম, পিতার নাম, মাতার নাম এবং জন্মতারিখ যেকোনো"
        " কম্বিনেশনে লিখে পাঠাতে পারেন।\n\n"
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
      text = (
          "✅ 🎂 Demo জন্মতারিখ দিয়ে সার্চ নির্বাচন করা হয়েছে।\n\n✏️ এখন"
          " জন্মতারিখ লিখে পাঠান।\n\n📌 উদাহরণ: 01/01/2000"
      )
    else:
      text = (
          f"✅ {info['title']} দিয়ে সার্চ নির্বাচন করা হয়েছে।\n\n✏️ এখন আপনার"
          f" {info['title']} লিখে পাঠান।"
      )
    await safe_edit_message(query, text)


# 🌟 নতুন যুক্ত করা কাস্টম বাটন হ্যান্ডলার (নিচের বাটনে ক্লিক করলে যা ঘটবে)
async def bottom_keyboard_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  text = update.message.text.strip()

  if text == "🏠 মেনু" or text == "❌ রিসেট":
    context.user_data.clear()
    await show_division_menu(update.message)

  elif text == "🔍 নতুন সার্চ":
    if "district" in context.user_data:
      await show_search_menu(update.message, context)
    else:
      await show_division_menu(update.message)

  elif text == "📁 ফিল্টার":
    if "division" in context.user_data and "district" in context.user_data:
      await show_district_options_menu(update.message, context)
    else:
      await update.message.reply_text(
          "⚠️ প্রথমে /start চাপুন এবং একটি বিভাগ ও জেলা সিলেক্ট করুন।"
      )

  elif text == "📊 স্ট্যাটাস":
    total_files = len(SEAT_FILES)
    total_divisions = len(DIVISIONS_MAP)
    status_text = (
        f"📊 **বট স্ট্যাটাস রিপোর্ট**\n\n"
        f"✅ বট স্ট্যাটাস: অনলাইন\n"
        f"📁 মোট লোড হওয়া ফাইল: {total_files} টি\n"
        f"🌍 নিবন্ধিত বিভাগ: {total_divisions} টি"
    )
    await update.message.reply_text(status_text, parse_mode="Markdown")

  else:
    # যদি বাটন ছাড়া সাধারণ সার্চের টেক্সট পাঠায় তবে সার্চ হ্যান্ডলারে রিডাইরেক্ট করবে
    await search_handler(update, context)


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if "district" not in context.user_data:
    await update.message.reply_text(
        "⚠️ প্রথমে /start দিয়ে বিভাগ ও জেলা নির্বাচন করুন।"
    )
    return

  if "search_type" not in context.user_data:
    await update.message.reply_text(
        "⚠️ প্রথমে সার্চের ধরন নির্বাচন করুন।"
    )
    return

  raw_text = update.message.text.strip()
  search_type = context.user_data["search_type"]

  division = context.user_data["division"]
  district = context.user_data["district"]
  thana = context.user_data.get("thana")
  seat = context.user_data.get("seat")

  target_files = []
  if seat:
    if seat in SEAT_FILES:
      target_files.append(SEAT_FILES[seat])
  else:
    seat_keys = DIVISIONS_MAP.get(division, {}).get(district, [])
    for k in seat_keys:
      if k in SEAT_FILES:
        target_files.append(SEAT_FILES[k])

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
        await update.message.reply_text(
            "⚠️ জন্মতারিখ সঠিক ফরম্যাটে লিখুন। (যেমন: 01/01/2000)"
        )
        return

  await update.message.reply_text(
      "🔍 Demo Data সার্চ করা হচ্ছে...\n\n⏳ একটু অপেক্ষা করুন।"
  )

  results = search_in_files(
      target_files, search_input, search_type, target_thana=thana
  )

  if not results:
    keyboard = [
        [
            InlineKeyboardButton(
                "🔎 নতুন সার্চ (পূর্বের মেনু)", callback_data="new_search"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 মূল মেনু (Start)", callback_data="show_division"
            )
        ],
    ]
    await update.message.reply_text(
        "❌ কোনো Demo Data পাওয়া যায়নি।\n\n🔎 অন্য তথ্য দিয়ে আবার চেষ্টা"
        " করুন।",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return

  context.user_data["results"] = results
  context.user_data["page"] = 0

  first_results = results[:10]

  for row in first_results:
    report = make_report(row)
    await update.message.reply_text(report)

  keyboard = []
  if len(results) > 10:
    keyboard.append(
        [InlineKeyboardButton("➡️ আরো দেখুন", callback_data="next_page")]
    )

  keyboard.append([
      InlineKeyboardButton(
          "🔎 নতুন সার্চ (পূর্বের মেনু)", callback_data="new_search"
      )
  ])
  keyboard.append([
      InlineKeyboardButton(
          "🏠 মূল মেনু (Start)", callback_data="show_division"
      )
  ])

  summary_text = (
      f"📄 মোট ফলাফল: {len(results)} টি\n\n📑 প্রথম {min(10, len(results))} টি"
      " রিপোর্ট দেখানো হয়েছে।"
  )
  await update.message.reply_text(
      summary_text, reply_markup=InlineKeyboardMarkup(keyboard)
  )


# =====================================================
# 7. Main Function
# =====================================================


def main():
  threading.Thread(target=run_web_server, daemon=True).start()
  print("🌐 Web Server চালু হয়েছে")

  app = Application.builder().token(TOKEN).build()

  app.add_handler(CommandHandler("start", start))
  app.add_handler(CallbackQueryHandler(button_handler))

  # 🌟 নতুন কিবোর্ডের জন্য হ্যান্ডলার ফিল্টার যুক্ত করা হলো
  app.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, bottom_keyboard_handler)
  )

  print("🤖 Telegram Demo Search Bot চালু হয়েছে!")
  app.run_polling()


if __name__ == "__main__":
  main()
