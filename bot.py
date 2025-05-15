from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telebot.async_telebot import AsyncTeleBot


from async_backup import AsyncMySQLBackup
from helper import write_log_file, read_from_json, append_dict_to_json_file, normalize_font, delete_zip_files, table_data
import asyncio


mysql_backupper = AsyncMySQLBackup(table_data=table_data)
TOKEN = mysql_backupper.config["telegram_token"]
users_config_path = "users_config.json"

bot = AsyncTeleBot(TOKEN)

async def send_zip_file(user_id: int, zip_path: str, caption: str = None):
    try:
        with open(zip_path, "rb") as file:
            await bot.send_document(user_id, file, caption=caption)
    except Exception as e:
        write_log_file(f"Error sending ZIP file: {e}")

async def send_backup_info():
    users_info = read_from_json(users_config_path)
    if not users_info:
        write_log_file("There is no user was added.")

    backup_path = await mysql_backupper.check_and_update()
    if not backup_path: return
    for user_info in users_info:
        if user_info["is_active"]:
            await send_zip_file(user_id=user_info["user_id"], zip_path=backup_path, caption="Backup file")

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
            "first_name": normalize_font(user_first_name),
            "last_name": normalize_font(user_last_name),
            "user_id": user_id,
            "is_active": is_active
        }
        result = append_dict_to_json_file(data=user_config, filename=users_config_path)
        if result:
            await bot.send_message(user_id, "<b>Вы успешно зарегистрированы!</b>",
                                   parse_mode="HTML")
        else:
            await bot.send_message(user_id, "<b>Что то пошло не так, попробуйте позже!</b>",
                                   parse_mode="HTML")

async def main():
    scheduler = AsyncIOScheduler()
    write_log_file("Bot started...")
    delete_zip_files(folder_path=mysql_backupper.backup_dir)
    check_interval = mysql_backupper.config["check_interval"]
    scheduler.add_job(send_backup_info, 'interval', minutes=check_interval)
    scheduler.start()
    await bot.infinity_polling()

if __name__ == '__main__':
    asyncio.run(main())



