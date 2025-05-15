import os
from datetime import datetime
import json
import unicodedata
import glob

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
    "mysqldump_path": "mysqldump",
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

def delete_zip_files(folder_path="notifications"):
    """
    Delete all .xlsx files from the specified folder.

    Args:
        folder_path (str): The path to the folder containing .txt files

    Returns:
        int: Number of files deleted
    """
    # Create a pattern to match all .txt files in the folder
    pattern = os.path.join(folder_path, "*.zip")

    # Find all .txt files
    txt_files = glob.glob(pattern)

    # Count how many files we'll delete
    count = len(txt_files)

    # Delete each file
    for file_path in txt_files:
        try:
            os.remove(file_path)
            write_log_file(f"Deleted: {file_path}")
        except Exception as e:
            write_log_file(f"Error deleting {file_path}: {e}")

    write_log_file(f"Total .txt files deleted: {count}")
    return count
