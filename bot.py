import os
import zipfile
import gdown

# ==========================================
# 📥 ১. GOOGLE DRIVE থেকে ফাইল ডাউনলোড করার অংশ
# ==========================================
# এখানে আপনার গুগল ড্রাইভের ফাইল ID গুলোর লিস্ট
DRIVE_FILES = [
    {"id": "1CfbqdJP_T7XPG0-Va0J3eLZLma6qFohQ", "filename": "file1.zip"},
    {"id": "1KBPfUexBd5zBqcrrgSRXfb6DED5ExVqM", "filename": "file2.zip"}
]

def download_drive_files():
    for item in DRIVE_FILES:
        file_id = item["id"]
        output_name = item["filename"]
        
        # ফাইলটি আগে থেকে নামানো না থাকলে ডাউনলোড করবে
        if not os.path.exists(output_name):
            print(f"⏳ Downloading {output_name} from Google Drive...")
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, output_name, quiet=False)
            
            # যদি জিপ ফাইল হয়, তবে আনজিপ করবে
            if output_name.endswith(".zip") and os.path.exists(output_name):
                print(f"📦 Extracting {output_name}...")
                try:
                    with zipfile.ZipFile(output_name, 'r') as zip_ref:
                        zip_ref.extractall(".")
                    print(f"✅ Extracted {output_name} successfully!")
                except Exception as e:
                    print(f"⚠️ Extraction error for {output_name}: {e}")

# অ্যাপ চালুর শুরুতেই ডাউনলোড ফাংশন রান হবে
download_drive_files()


# ==========================================
# 🤖 ২. আপনার টেলিগ্রাম বটের মূল কোড (নিচে থাকবে)
# ==========================================
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ⚠️ এখানে আপনার আসল বটের TOKEN বসান
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 বোট চালু হয়েছে! ডাটা সার্চ করতে তথ্য দিন।")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
