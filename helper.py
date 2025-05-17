import os
from datetime import datetime
import json
import unicodedata
import glob
import pathlib

_today = datetime.now().strftime("%d-%m-%Y")
log_file = f"logs/log-{_today}.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)

DEFAULT_CONFIG = {
    "host": "localhost",
    "user": "easytrade",
    "password": "<PASSWORD>",
    "database": "easytrade_db",
    "check_interval": 60,
    "backup_dir": "backups",
    "mysqldump_path": "C:\\MySQL\\bin\\mysqldump",
    "telegram_token": "<TELEGRAM TOKEN>"
}

table_data = [
    {
        "table_name": "dir_avg_cost",
        "last_update_column": "avgc_last_update"
    },
    {
        "table_name": "dir_customers",
        "last_update_column": "cstm_last_update"
    },
    {
        "table_name": "dir_good_remainders",
        "last_update_column": "objbl_last_update"
    },
    {
        "table_name": "dir_goods",
        "last_update_column": "gd_last_update"
    },
    {
        "table_name": "dir_groups",
        "last_update_column": "grp_last_update"
    },
    {
        "table_name": "dir_objects",
        "last_update_column": "obj_last_update"
    },
    {
        "table_name": "dir_prices",
        "last_update_column": "prc_last_update"
    },
    {
        "table_name": "dir_prices_types",
        "last_update_column": "prct_last_update"
    },
    {
        "table_name": "dir_prices_types",
        "last_update_column": "prct_last_update"
    },
    {
        "table_name": "dir_scans",
        "last_update_column": "scn_last_update"
    },
    {
        "table_name": "doc_payments",
        "last_update_column": "pmt_last_update"
    },
    {
        "table_name": "doc_sales",
        "last_update_column": "sls_last_update"
    },
    {
        "table_name": "operations",
        "last_update_column": "opr_last_update"
    },
]

def get_date():
    now = datetime.now()
    return now.strftime("%m/%d/%Y %H:%M:%S")

def write_log_file(text):
    with open(log_file, "a", encoding='utf-8') as file:
        formatted_text = f"{get_date()} - {text}\n"
        file.write(formatted_text)
        print(formatted_text)


def configure_settings(data_dict=DEFAULT_CONFIG, filename="config.json"):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as json_file:
                data_dict = json.load(json_file)
            return data_dict
        except FileNotFoundError:
            write_log_file(f"Error: File '{filename}' not found")

        except json.JSONDecodeError:
            write_log_file(f"Error: File '{filename}' contains invalid JSON")
            os.remove(filename)

        except Exception as e:
            write_log_file(f"Error reading JSON file: {e}")
            os.remove(filename)


    try:
        with open(filename, 'w', encoding='utf-8', errors="replace") as json_file:
            json.dump(data_dict, json_file, indent=4, ensure_ascii=False)
    except Exception as e:
        write_log_file(f"Error writing to JSON file: {e}")
    else:
        return data_dict

def normalize_font(text):
    return ''.join(
        unicodedata.normalize('NFKD', char)[0]
        for char in text
    )

def append_dict_to_json_file(data: dict, filename: str):
    # Check if the file exists
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
            # Ensure it's a list
            if not isinstance(existing_data, list):
                raise ValueError("JSON file does not contain a list.")
        except (json.JSONDecodeError, FileNotFoundError):
            existing_data = []
    else:
        existing_data = []

    # Append new data and write back
    existing_data.append(data)
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, indent=4)

        return True
    except Exception as e:
        write_log_file(f"Error writing to JSON file: {e}")
        return False

def read_from_json(filename):
    """
    Reads data from a JSON file and returns it as a Python object.

    Args:
        filename (str): Path to the JSON file.

    Returns:
        dict or list: The parsed JSON content.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        write_log_file(f"Error reading from JSON: {e}")
        return None

def keep_last_three_files(folder_path):
    # Convert to Path object
    folder = pathlib.Path(folder_path)

    if not folder.is_dir():
        write_log_file(f"The path '{folder_path}' is not a valid directory.")

    # Get all files in the directory
    files = [f for f in folder.iterdir() if f.is_file()]

    # Sort files by creation time (oldest first)
    files.sort(key=lambda f: f.stat().st_ctime)

    # Keep only the last 3 created files
    files_to_delete = files[:-3]

    for file in files_to_delete:
        try:
            file.unlink()  # Delete the file
            write_log_file(f"Deleted: {file}")
        except Exception as e:
            write_log_file(f"Failed to delete {file}: {e}")