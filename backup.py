import mysql.connector
import os
import time
import hashlib
import subprocess
from datetime import datetime
import zipfile
import hashlib


from helper import configure_settings, write_log_file

class MySQLBackup:
    def __init__(self):
        self.config = configure_settings()
        self.host = self.config["host"]
        self.user = self.config["user"]
        self.password = self.config["password"]
        self.database = self.config["database"]
        self.backup_dir = self.config["backup_dir"]
        self.mysqldump_path = self.config["mysqldump_path"]
        self.last_change_signature = None
        os.makedirs(self.backup_dir, exist_ok=True)

    def database_signature(self):
        """
        Creates a fingerprint (hash) of all row counts in the database to detect structural or data changes.
        """
        try:
            conn = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                database=self.database
            )
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]

            signature_data = ""
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                count = cursor.fetchone()[0]
                signature_data += f"{table}:{count};"

            cursor.close()
            conn.close()

            # Generate a hash of the signature string
            return hashlib.md5(signature_data.encode()).hexdigest()

        except Exception as e:
            write_log_file(f"Error: {e}")
            return None

    def check_db(self):
        db_signature = self.database_signature()
        if db_signature != self.last_change_signature:
            self.last_change_signature = db_signature
            write_log_file("Database signature changed")
            return True
        else:
            write_log_file("Database signature did not change")
            return False

    def check_and_update(self):
        if self.check_db():
            self.create_backup()

    def create_backup(self):
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

            with open(output_file, "w") as f:
                result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True)

            if result.returncode != 0:
                raise RuntimeError(f"mysqldump failed: {result.stderr}")

            write_log_file(f"Backup successful: {output_file}")

            with zipfile.ZipFile(zip_output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(output_file, arcname=os.path.basename(output_file))

            os.remove(output_file)

        except Exception as e:
            write_log_file(f"Backup failed: {e}")
            return False
        else:
            return zip_output_file

