from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand, \
    ReplyKeyboardRemove
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import ApiTelegramException

from backup import MySQLBackup
from helper import write_log_file, read_from_json, append_dict_to_json_file, normalize_font, delete_zip_files


mysql_backupper = MySQLBackup()
TOKEN = mysql_backupper.config["telegram_token"]
users_config_path = "users_config."

bot = AsyncTeleBot(TOKEN)

@bot.message_handler(commands=['start'])
async def register_user(message):
    user_id = message.from_user.id
    str_user_id = str(user_id)
    users_config_data = read_from_json(users_config_path)
    if users_config_data and str_user_id in users_config_data:
        if users_config_data[str_user_id]["is_active"]:
            await bot.send_message(user_id, "<b>Вы уже зарегистрированы и активный!</b>", parse_mode="HTML")
        else:
            await bot.send_message(user_id, "<b>Вы уже зарегистрированы, но вас не активировали!</b>", parse_mode="HTML")
    else:
        user_first_name = message.from_user.first_name
        user_last_name = message.from_user.last_name
        is_active = False
        user_config = {
            user_id: {
                "first_name": normalize_font(user_first_name),
                "last_name": normalize_font(user_last_name),
                "is_active": is_active
            }
        }
        result = append_dict_to_json_file(data=user_config, filename=users_config_path)
        if result:
            await bot.send_message(user_id, "<b>Вы успешно зарегистрированы!</b>",
                                   parse_mode="HTML")
        else:
            await bot.send_message(user_id, "<b>Что то пошло не так, попробуйте позже!</b>",
                                   parse_mode="HTML")

async def main():
    delete_zip_files(folder_path=mysql_backupper.backup_dir)
    hour_list = ["{:02d}".format(h) for h in range(24)]

    scheduler = AsyncIOScheduler()
    check_interval = mysql_backupper.config["check_interval"]
    scheduler.add_job(mysql_backupper.check_and_update, 'interval', seconds=check_interval)


