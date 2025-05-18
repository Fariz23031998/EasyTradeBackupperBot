from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telebot.async_telebot import AsyncTeleBot
import time

from async_backup import AsyncMySQLBackup
from helper import (write_log_file, read_from_json,
                    configure_settings, table_data, keep_last_three_files)
import asyncio

# pyinstaller command: pyinstaller --onefile --name=EasyTradeBackupperBot bot.py


mysql_backupper = AsyncMySQLBackup(table_data=table_data)
TOKEN = mysql_backupper.config["telegram_token"]
config_file_path = "config.json"
bot = AsyncTeleBot(TOKEN)

async def send_zip_file(chat_id: int, zip_path: str, caption: str = None):
    try:
        with open(zip_path, "rb") as file:
            await bot.send_document(chat_id, file, caption=caption)
    except Exception as e:
        write_log_file(f"Error sending ZIP file: {e}")
        await bot.send_message(chat_id, f"Error sending ZIP file: {e}")

async def send_backup_info(force=False):
    if force:
        backup_path = await mysql_backupper.create_backup()
        if backup_path: mysql_backupper.last_update_timestamp = time.time()
    else:
        backup_path = await mysql_backupper.check_and_update()
    if not backup_path: return
    chat_id = mysql_backupper.group_chat_id
    if chat_id == 0:
        write_log_file("Bot wasn't added to the group.")
        return
    await send_zip_file(chat_id=chat_id, zip_path=backup_path, caption=f"Файл backup - {backup_path}")

    keep_last_three_files(mysql_backupper.backup_dir)

@bot.message_handler(commands=['start'])
async def start(message):
    await bot.send_message(message.from_user.id,
"<b>Вам нужно добавить этот бот в группу чтобы он отправил в эту нужную группу Backup EasyTrade!</b>", parse_mode="html")

@bot.my_chat_member_handler()
async def on_bot_added_to_group(message):
    chat = message.chat
    new_status = message.new_chat_member.status
    old_status = message.old_chat_member.status

    # Check if the bot was added (e.g. was "kicked" or "left", now "member" or "administrator")
    if message.new_chat_member.user.id == (await bot.get_me()).id:
        if old_status in ["left", "kicked"] and new_status in ["member", "administrator"]:
            settings = read_from_json(config_file_path)
            settings["group_chat_id"] = chat.id
            mysql_backupper.group_chat_id = chat.id
            configure_settings(data_dict=settings, filename=config_file_path, update=True)
            write_log_file(f"Bot added to group: {chat.title} ({chat.id})")

async def main():
    scheduler = AsyncIOScheduler()
    write_log_file("Bot started...")
    await send_backup_info(force=True)
    check_interval = mysql_backupper.config["check_interval"]
    scheduler.add_job(send_backup_info, 'interval', minutes=check_interval)

    hours = [f"{i:02}" for i in range(24)]
    for hour in hours:
        scheduler.add_job(
            send_backup_info,
            CronTrigger(hour=hour, minute="00"),
            args=[True],
        )
    scheduler.start()
    await bot.infinity_polling()

if __name__ == '__main__':
    asyncio.run(main())



