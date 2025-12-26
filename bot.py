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

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.info('Bot Let drink!')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f'Запрос /start от пользователя: {user.full_name} (ID: {user.id})')
    logging.info(f'Пользователь {user.full_name} (ID: {user.id})нажал /start')
    await update.message.reply_text("Привет! Хочешь прибухнуть с Гремом?")

app = Application.builder().token(settings.API_KEY).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()