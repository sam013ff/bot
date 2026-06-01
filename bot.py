import telebot
from telebot import types
from datetime import datetime
import json
import os
from flask import Flask
from threading import Thread

# --- تنظیمات وب‌سرور برای زنده نگه داشتن ربات در رندر ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- تنظیمات اصلی ربات تلگرام ---
TOKEN = "8955790773:AAEHCFzwAk1yvNuaq_PnHJCYlf5AwVCgg94"
CARD_NUMBER = "5859831218221934"
CARD_NAME = "عظیمی✅❤️"
REQUIRED_CHANNEL = "@v2ray_letpix"
SUPPORT_USER = "@appmaker013"

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "bot_data.json"

if not os.path.exists(DATA_FILE):
    default_data = {
        "admin_id": None,
        "receipt_channel_id": None,
        "users": {},
        "products": {
            "1": {"name": "کانفیگ 10 گیگابایت ساده", "price": "230,000"}
        },
        "pending_orders": {}
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(default_data, f, ensure_ascii=False, indent=4)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def check_membership(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛍 لیست محصولات", "👤 حساب کاربری")
    markup.row("📞 پشتیبانی")
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔍 سرچ کاربر", "🚫 مسدود / رفع مسدود")
    markup.row("➕ افزودن محصول", "✏️ ویرایش محصول")
    markup.row("📢 پیام به همه", "📩 پیام شخصی")
    markup.row("🔙 خروج از پنل")
    return markup

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'document'])
def handle_all_messages_pre_check(message):
    data = load_data()
    user_id = str(message.from_user.id)
    
    if data["admin_id"] is None:
        data["admin_id"] = user_id
        save_data(data)
        bot.reply_to(message, "شما به عنوان مدیر اصلی ربات تعیین شدید!")
        return

    if user_id == data["admin_id"] and message.forward_from_chat:
        data["receipt_channel_id"] = message.forward_from_chat.id
        save_data(data)
        bot.reply_to(message, f"✅ کانال رسیدها با موفقیت متصل شد!\nآیدی کانال: {message.forward_from_chat.id}")
        return

    if user_id in data["users"] and data["users"][user_id].get("banned", False):
        bot.send_message(user_id, "❌ حساب کاربری شما به دلیل تخلف مسدود شده است.")
        return

    if not check_membership(message.from_user.id) and user_id != data["admin_id"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("ورود به کانال اصلی", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','') }"))
        bot.send_message(user_id, f"⚠️ برای استفاده از ربات باید ابتدا عضو کانال ما شوید:\n{REQUIRED_CHANNEL}", reply_markup=markup)
        return

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "username": message.from_user.username if message.from_user.username else "بدون آیدی",
            "banned": False,
            "step": ""
        }
        save_data(data)

    if user_id == data["admin_id"] and data["users"][user_id]["step"] != "":
        handle_admin_steps(message, data, user_id)
        return

    if data["users"][user_id]["step"] == "wait_receipt":
        if message.content_type == 'photo':
            handle_receipt_submission(message, data, user_id)
        else:
            bot.send_message(user_id, "❌ لطفاً فقط عکس رسید واریزی خود را ارسال کنید.")
        return

    if message.text == "/start" or message.text == "🔙 خروج از پنل":
        data["users"][user_id]["step"] = ""
        save_data(data)
        bot.send_message(user_id, "سلام به ربات فروش V2RAY خوش آمدید!", reply_markup=main_menu(user_id))
    
    elif message.text == "/admin" and user_id == data["admin_id"]:
        bot.send_message(user_id, "⚙️ به پنل مدیریت خوش آمدید:", reply_markup=admin_menu())

    elif message.text == "🛍 لیست محصولات":
        markup = types.InlineKeyboardMarkup()
        for prod_id, prod_info in data["products"].items():
            markup.add(types.InlineKeyboardButton(f"{prod_info['name']} - {prod_info['price']} تومان", callback_data=f"buy_{prod_id}"))
        bot.send_message(user_id, "👇 یکی از بسته‌های زیر را برای خرید انتخاب کنید:", reply_markup=markup)

    elif message.text == "👤 حساب کاربری":
        text = f"👤 مشخصات حساب شما:\n\n🆔 آیدی عددی شما: `{user_id}`\n🌐 آیدی تلگرام: @{message.from_user.username if message.from_user.username else 'ندارد'}"
        bot.send_message(user_id, text, parse_mode="Markdown")

    elif message.text == "📞 پشتیبانی":
        bot.send_message(user_id, f"🚀 جهت ارتباط با بخش پشتیبانی و ارسال سوالات خود به آیدی زیر پیام دهید:\n\n{SUPPORT_USER}")

    elif user_id == data["admin_id"]:
        if message.text == "🔍 سرچ کاربر":
            data["users"][user_id]["step"] = "search_user"
            save_data(data)
            bot.send_message(user_id, "🔍 آیدی عددی کاربر مورد نظر را بفرستید:")
        elif message.text == "🚫 مسدود / رفع مسدود":
            data["users"][user_id]["step"] = "ban_unban"
            save_data(data)
            bot.send_message(user_id, "🚫 آیدی عددی کاربر را جهت مسدود یا رفع مسدود کردن ارسال کنید:")
        elif message.text == "➕ افزودن محصول":
            data["users"][user_id]["step"] = "add_prod_name"
            save_data(data)
            bot.send_message(user_id, "📝 نام محصول جدید را وارد کنید:")
        elif message.text == "✏️ ویرایش محصول":
            markup = types.InlineKeyboardMarkup()
            for prod_id, prod_info in data["products"].items():
                markup.add(types.InlineKeyboardButton(prod_info['name'], callback_data=f"edit_{prod_id}"))
            bot.send_message(user_id, "✏️ کدام محصول را می‌خواهید ویرایش کنید؟", reply_markup=markup)
        elif message.text == "📢 پیام به همه":
            data["users"][user_id]["step"] = "broadcast"
            save_data(data)
            bot.send_message(user_id, "📢 متن پیام همگانی خود را بفرستید:")
        elif message.text == "📩 پیام شخصی":
            data["users"][user_id]["step"] = "private_msg_id"
            save_data(data)
            bot.send_message(user_id, "🆔 آیدی عددی کاربر هدف را ارسال کنید:")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    data = load_data()
    user_id = str(call.from_user.id)
    
    if call.data.startswith("buy_"):
        prod_id = call.data.split("_")[1]
        if prod_id in data["products"]:
            data["pending_orders"][user_id] = prod_id
            save_data(data)
            
            prod = data["products"][prod_id]
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ تایید و دریافت شماره کارت", callback_data="confirm_order"))
            markup.add(types.InlineKeyboardButton("❌ انصراف", callback_data="cancel_order"))
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🛒 شما محصول زیر را انتخاب کردید:\n\n📦 نام: {prod['name']}\n💰 قیمت: {prod['price']} تومان\n\nآیا سفارش را تایید می‌کنید؟",
                reply_markup=markup
            )

    elif call.data == "confirm_order":
        if user_id in data["pending_orders"]:
            prod_id = data["pending_orders"][user_id]
            prod = data["products"][prod_id]
            
            invoice_text = (
                f"💳 **دستورالعمل پرداخت کارت به کارت**\n\n"
                f"💵 مبلغ قابل پرداخت: **{prod['price']} تومان**\n"
                f"🔢 شماره کارت:\n`{CARD_NUMBER}`\n"
                f"👤 به نام: **{CARD_NAME}**\n\n"
                f"📸 لطفاً پس از واریز وجه، **فقط عکس رسید** خود را در پاسخ به همین پیام ارسال کنید.\n\n"
                f"⚠️ **نکته مهم:** ارسال هرگونه رسید فیک یا تکراری باعث مسدود شدن (بن دائم) حساب کاربری شما از ربات خواهد شد!"
            )
            data["users"][user_id]["step"] = "wait_receipt"
            save_data(data)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=invoice_text, parse_mode="Markdown")

    elif call.data == "cancel_order":
        if user_id in data["pending_orders"]:
            del data["pending_orders"][user_id]
        data["users"][user_id]["step"] = ""
        save_data(data)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="❌ سفارش شما لغو شد.")

    elif call.data.startswith("edit_") and user_id == data["admin_id"]:
        prod_id = call.data.split("_")[1]
        data["users"][user_id]["step"] = f"edit_prod_name_{prod_id}"
        save_data(data)
        bot.send_message(user_id, "✏️ نام جدید محصول را وارد کنید:")

def handle_receipt_submission(message, data, user_id):
    prod_id = data["pending_orders"].get(user_id, "1")
    prod = data["products"].get(prod_id, {"name": "نامشخص", "price": "نامشخص"})
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = f"@{message.from_user.username}" if message.from_user.username else "بدون آیدی"
    
    channel_id = data["receipt_channel_id"]
    if channel_id:
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📩 ورود به پیوی خریدار", url=f"tg://user?id={user_id}"))
            
            caption = (
                f"💰 **رسید جدید پرداخت واصل شد!**\n\n"
                f"👤 خریدار: {username}\n"
                f"🆔 آیدی عددی: `{user_id}`\n"
                f"📦 محصول: {prod['name']}\n"
                f"💵 مبلغ مندرج: {prod['price']} تومان\n"
                f"⏰ زمان ارسال: {now}"
            )
            
            bot.send_photo(channel_id, message.photo[-1].file_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
            bot.send_message(user_id, "✅ رسید شما با موفقیت برای مدیریت ارسال شد. پس از بررسی و تایید، کانفیگ شما ارسال خواهد شد.")
        except Exception:
            bot.send_message(user_id, "❌ خطایی در سیستم ارسال فیش رخ داد. لطفا به پشتیبانی پیام دهید.")
    else:
        bot.send_message(user_id, "❌ کانال ثبت رسیدها توسط ادمین ست نشده است.")
    
    data["users"][user_id]["step"] = ""
    if user_id in data["pending_orders"]:
        del data["pending_orders"][user_id]
    save_data(data)

def handle_admin_steps(message, data, user_id):
    step = data["users"][user_id]["step"]
    
    if step == "search_user":
        target_id = message.text.strip()
        if target_id in data["users"]:
            u = data["users"][target_id]
            bot.send_message(user_id, f"👤 اطلاعات کاربر:\n\n🆔 آیدی: `{target_id}`\n🌐 آیدی تلگرام: @{u['username']}\n🚫 وضعیت مسدودیت: {'بله' if u['banned'] else 'خیر'}", parse_mode="Markdown")
        else:
            bot.send_message(user_id, "❌ کاربر یافت نشد.")
        data["users"][user_id]["step"] = ""
        save_data(data)

    elif step == "ban_unban":
        target_id = message.text.strip()
        if target_id in data["users"]:
            data["users"][target_id]["banned"] = not data["users"][target_id]["banned"]
            status = "مسدود" if data["users"][target_id]["banned"] else "رفع مسدود"
            bot.send_message(user_id, f"✅ کاربر `{target_id}` با موفقیت {status} شد.", parse_mode="Markdown")
        else:
            bot.send_message(user_id, "❌ کاربر در دیتابیس یافت نشد.")
        data["users"][user_id]["step"] = ""
        save_data(data)

    elif step == "add_prod_name":
        data["users"][user_id]["step"] = f"add_prod_price_{message.text}"
        save_data(data)
        bot.send_message(user_id, "💰 قیمت محصول را به تومان وارد کنید:")

    elif step.startswith("add_prod_price_"):
        prod_name = step.replace("add_prod_price_", "")
        new_id = str(len(data["products"]) + 1)
        data["products"][new_id] = {"name": prod_name, "price": message.text}
        data["users"][user_id]["step"] = ""
        save_data(data)
        bot.send_message(user_id, "✅ محصول جدید با موفقیت اضافه شد.")

    elif step.startswith("edit_prod_name_"):
        prod_id = step.replace("edit_prod_name_", "")
        data["users"][user_id]["step"] = f"edit_prod_price_{prod_id}_{message.text}"
        save_data(data)
        bot.send_message(user_id, "💰 قیمت جدید محصول را به تومان وارد کنید:")

    elif step.startswith("edit_prod_price_"):
        parts = step.replace("edit_prod_price_", "").split("_")
        prod_id = parts[0]
        prod_name = parts[1]
        if prod_id in data["products"]:
            data["products"][prod_id] = {"name": prod_name, "price": message.text}
            bot.send_message(user_id, "✅ محصول با موفقیت ویرایش شد.")
        data["users"][user_id]["step"] = ""
        save_data(data)

    elif step == "broadcast":
        count = 0
        for uid in data["users"].keys():
            try:
                bot.send_message(uid, f"📢 پیام از طرف مدیریت:\n\n{message.text}")
                count += 1
            except Exception:
                continue
        bot.send_message(user_id, f"✅ پیام شما با موفقیت به {count} کاربر ارسال شد.")
        data["users"][user_id]["step"] = ""
        save_data(data)

    elif step == "private_msg_id":
        data["users"][user_id]["step"] = f"private_msg_send_{message.text.strip()}"
        save_data(data)
        bot.send_message(user_id, "📩 متن پیام خود را برای کاربر بفرستید:")

    elif step.startswith("private_msg_send_"):
        target_id = step.replace("private_msg_send_", "")
        try:
            bot.send_message(target_id, f"📩 پیام خصوصی از طرف مدیریت:\n\n{message.text}")
            bot.send_message(user_id, "✅ پیام شما با موفقیت به کاربر ارسال شد.")
        except Exception:
            bot.send_message(user_id, "❌ ارسال پیام ناموفق بود.")
        data["users"][user_id]["step"] = ""
        save_data(data)

if __name__ == '__main__':
    # روشن کردن وب‌سرور دایمی
    keep_alive()
    # شروع به کار ربات تلگرام
    bot.infinity_polling()
