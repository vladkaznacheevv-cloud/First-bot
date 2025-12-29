import logging
import os
import settings
from openai import AsyncOpenAI
from collections import defaultdict
from telegram import Update, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

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

client = AsyncOpenAI(
    api_key=settings.MIMO_API_KEY,
    base_url="https://api.xiaomimimo.com/v1"
    )

user_conversations = defaultdict(lambda: [
    {"role": "system", "content": (
        "Ты - ГремБот, харизматичный и дружелюбный бот-компаньон Кожаного повелителя."
        "Твоя задача — убедить собеседника записаться на прибухнуть. /drink "
    )}
])

async def ask_ai(messages: list) -> str:
    try:
        logging.info("Отправляю запрос к MiMo API...")

        completion = await client.chat.completions.create(
            model="mimo-v2-flash",
            messages=messages,
            max_completion_tokens=1024,
            temperature=0.3,
            top_p=0.95,
            stream=False,
            frequency_penalty=0,
            presence_penalty=0,
            extra_body={
                "thinking": {"type": "disabled"}
            }
        )

        return completion.choices[0].message.content.strip()
    
    except Exception as e:
        logging.error(f"Ошибка ИИ: {e}")
        return "Кожаный повелитель уже в пути! 🏍️"

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if len(user_conversations[user_id]) > 1:
        user_message = update.message.text.strip()
        if not user_message:
            return

        user_conversations[user_id].append({"role": "user", "content": user_message})

        await update.message.chat.send_action(action="typing")
        ai_response = await ask_ai(user_conversations[user_id])
        user_conversations[user_id].append({"role": "assistant", "content": ai_response})

        await update.message.reply_text(ai_response)
        logging.info(f"Диалог с {user.id}: '{user_message[:30]}...'")

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()