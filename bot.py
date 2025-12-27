import logging
import os
import httpx
import settings
from collections import defaultdict
from telegram import Update, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

log_file = os.path.join(os.path.dirname(__file__),'bot.log')

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
    )

user_conversations = defaultdict(lambda: [
    {"role": "system", "content": (
        "Ты - ГремБот,харизматичный и дружелюбный бот-компаньон Кожаного повелителя."
        "Твоя задача — убедить собеседника записаться на прибухнуть. "
    )}
])

async def ask_ai(messages: list) -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url= "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemma-2-2b-it:free",
                    "messages": messages,
                    "max_tokens": 250,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                logging.error(f"OpenRouter error: {response.status_code} - {response.text}")
                return "Извини, я бухой. Попробуй позже."
    except Exception as e:
        logging.error(f"Ошибка ИИ: {e}")
        return "Кожаный повелитель уже бежит!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f'Запрос /start от пользователя: {user.full_name} (ID: {user.id})')
    logging.info(f'Пользователь {user.full_name} (ID: {user.id})нажал /start')
    
    welcome_text = (
        f"👋Привет, <b>{user.first_name}</b>!\n\n"
        "🤖 Я — <b>бот помошник</b>, 'Кожанного повелителя'.\n"
        "🍺 Готов записать тебя на прибухнуть или просто поболтать.\n\n"
        "Выбери команду из меню — и погнали!"
    )
    await update.message.reply_text(welcome_text, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sticker_path = os.path.join(os.path.dirname(__file__),'sticker.webp')

    await update.message.reply_sticker(sticker=open(sticker_path,'rb'))

    await update.message.reply_text("🆘Я сам не ебу что происходит!!!")

async def drink_command(update: Update,context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    await update.message.reply_text(
        "🍻Отлично! Ты записан на прибухнуть!\n\n"
        "Кожаный повелитель скоро свяжется с тобой для уточнения деталей."
    )

    admin_message = (
        f"🔔 <b>Новая запись на прибухнуть!</b>\n\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🕒 Время: {update.message.date.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    try:
        await context.bot.send_message(
            chat_id=settings.ADMIN_TELEGRAM_ID,
            text=admin_message,
            parse_mode='HTML'
        )
        logging.info(f"Уведомление отправлено админу о льзователе {user.id}")
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление админу: {e}")

async def talk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    text = update.message.text
    if text.startswith("/talk"):
        user_message = text[6:].strip()
    else:
        user_message = text

    if not user_message:
        user_message = "Ну, базарь"
    
    user_conversations[user_id].append({"role": "user", "content": user_message})
    
    await update.message.chat.send_action(action="typing")
    ai_response = await ask_ai(user_conversations[user_id])

    user_conversations[user_id].append({"role": "assistant", "content": ai_response})

    keyboard = [[InlineKeyboardButton("🔄 Обнулиться", callback_data="reset_dialog")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(ai_response, reply_markup=reply_markup)
    logging.info(f"Пользователь {user.id} в диалоге: {user_message[:30]}...")

async def reset_dialog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_conversations[user_id] = [user_conversations[user_id][0]]
    await query.edit_message_text("✅ Обнулились как Путин!")

async def post_init(application):
    await application.bot.set_my_commands([
    BotCommand("start","Запустить бота🚀"),
    BotCommand("help","Помощьℹ️"),
    BotCommand("drink","Записать на прибухнуть🍻"), 
    BotCommand("talk", "Побазарим с ИИ 🤖"),
    BotCommand("reset", "Обнулимся? 🔄")   
    ])
    logging.info("Меню команд установлено")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_conversations[user_id] = [user_conversations[user_id][0]]
        await update.message.reply_text("✅ Диалог обнулён! Но я всё ещё хочу прибухнуть! 🍻")

if __name__ == "__main__":
    logging.info('Bot Let drink!')
    app = (
    Application.builder()
        .token(settings.API_KEY)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("drink", drink_command))
    app.add_handler(CommandHandler("talk", talk_command) )
    app.add_handler(CallbackQueryHandler(reset_dialog_callback, pattern="^reset_dialog$"))
    app.add_handler(CommandHandler("reset", reset_command))
    app.run_polling()