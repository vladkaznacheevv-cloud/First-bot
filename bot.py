import logging
import os
import settings

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

log_file = os.path.join(os.path.dirname(__file__),'bot.log')
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8')

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f'Запрос /start от пользователя: {user.full_name} (ID: {user.id})')
    logging.info(f'Пользователь {user.full_name} (ID: {user.id})нажал /start')
    
    welcome_text = (
        f"👋Привет, <b>{user.first_name}</b>!\n\n"
        "🤖 Я — <b>Грем</b>, бот помошник 'Кожанного повелителя'.\n"
        "🍺 Готов записать тебя на прибухнуть или просто поболтать.\n\n"
        "Выбери команду из меню — и погнали!"
    )
    await update.message.reply_text(welcome_text, parse_mode='HTML')

async def post_init(application):
    await application.bot.set_my_commands([
    BotCommand("start","Запустить бота🚀"),
    BotCommand("help","Помощьℹ️"),
    BotCommand("drink","Записать на прибухнуть🍻"),    
    ])
    logging.info("Меню команд установлено")

logging.info('Bot Let drink!')

app = (
Application.builder()
    .token(settings.API_KEY)
    .post_init(post_init)
    .build()
)

app.add_handler(CommandHandler("start", start))
app.run_polling()