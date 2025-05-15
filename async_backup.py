import aiomysql
import aiofiles
import asyncio
import os
import hashlib
from datetime import datetime
import zipfile
from helper import configure_settings, write_log_file
import time


class AsyncMySQLBackup:
    def __init__(self, table_data):
        self.config = configure_settings()
        self.host = self.config["host"]
        self.user = self.config["user"]
        self.password = self.config["password"]
        self.database = self.config["database"]
        self.backup_dir = self.config["backup_dir"]
        self.mysqldump_path = self.config["mysqldump_path"]
        self.last_change_signature = None
        self.last_update_timestamp = 0
        self.table_data = table_data
        os.makedirs(self.backup_dir, exist_ok=True)

    async def database_signature(self):
        try:
            conn = await aiomysql.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                db=self.database
            )
            async with conn.cursor() as cursor:
                await cursor.execute("SHOW TABLES")
                tables = [row[0] for row in await cursor.fetchall()]

                signature_data = ""
                for table in tables:
                    await cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                    count = (await cursor.fetchone())[0]
                    signature_data += f"{table}:{count};"

            conn.close()
            return hashlib.md5(signature_data.encode()).hexdigest()

        except Exception as e:
            write_log_file(f"Error: {e}")
            return None

    async def is_data_updated(self, table_d):
        """
        Checks whether any of the given tables has a last update timestamp newer than self.last_update_timestamp.
        Returns True if any such update is found, otherwise False.
        """
        try:
            conn = await aiomysql.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                db=self.database
            )
            async with conn.cursor() as cursor:
                for entry in table_d:
                    table = entry["table_name"]
                    column = entry["last_update_column"]
                    query = f"SELECT MAX(`{column}`) FROM `{table}`"
                    try:
                        await cursor.execute(query)
                        result = await cursor.fetchone()
                        latest_update = result[0].timestamp()

                        if latest_update > self.last_update_timestamp:
                            await conn.ensure_closed()
                            return True
                    except Exception as table_err:
                        write_log_file(f"Error checking {table}.{column}: {table_err}")

            await conn.ensure_closed()
            return False
        except Exception as e:
            write_log_file(f"Database check failed: {e}")
            return False

    async def check_db(self):
        is_data_updated = await self.is_data_updated(self.table_data)
        if is_data_updated:
            return True

        db_signature = await self.database_signature()
        if db_signature != self.last_change_signature:
            self.last_change_signature = db_signature
            write_log_file("Database signature changed")
            return True
        else:
            write_log_file("Database signature did not change")
            return False

    async def check_and_update(self):
        write_log_file("Checking database...")
        if await self.check_db():
            write_log_file("Backup creation started...")
            backup_result = await self.create_backup()
            if backup_result:
                self.last_update_timestamp = time.time()
                write_log_file("Backup creation finished")
                return backup_result
            else:
                write_log_file("Backup creation failed")
                return False

    async def async_zip_file(self, input_path, output_zip_path):
        """
        Asynchronously zips a file by offloading the task to a background thread.
        """
        def zip_task():
            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(input_path, arcname=os.path.basename(input_path))

        try:
            await asyncio.to_thread(zip_task)
        except Exception as e:
            write_log_file(f"Zipping failed: {e}")
            raise

    async def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{self.backup_dir}/{self.database}_{timestamp}.sql"
        zip_output_file = output_file + ".zip"
        try:
            command = [
                self.mysqldump_path,
                f"--user={self.user}",
                f"--password={self.password}",
                f"--host={self.host}",
                self.database
            ]

            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                raise RuntimeError(f"mysqldump failed: {stderr.decode()}")

            async with aiofiles.open(output_file, "w") as f:
                await f.write(stdout.decode())

            write_log_file(f"Backup successful: {output_file}")

            await self.async_zip_file(input_path=output_file, output_zip_path=zip_output_file)

            os.remove(output_file)

        except Exception as e:
            write_log_file(f"Backup failed: {e}")
            return False
        else:
            return zip_output_file
