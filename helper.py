import os
from datetime import datetime
import json
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
    "telegram_token": "<TELEGRAM TOKEN>",
    "group_chat_id": 0,
    "prefix": "EasyTrade"
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


def configure_settings(data_dict=DEFAULT_CONFIG, filename="config.json", update: bool = False):
    if not update and os.path.exists(filename):
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


def get_c_drive_serial():
    """
    Returns the serial number of the C drive in the format 'E8D0-04CC'.

    Returns:
        str: The formatted serial number of the C drive
    """
    try:
        # Method 1: Using the Windows API via ctypes
        import ctypes

        # Define needed Windows API constants
        DRIVE_FIXED = 3

        # Get the volume information
        volume_name_buffer = ctypes.create_unicode_buffer(1024)
        file_system_name_buffer = ctypes.create_unicode_buffer(1024)
        volume_serial_number = ctypes.c_ulong(0)
        max_component_length = ctypes.c_ulong(0)
        file_system_flags = ctypes.c_ulong(0)

        # Call GetVolumeInformation Windows API function
        ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p("C:\\"),
            volume_name_buffer,
            ctypes.sizeof(volume_name_buffer),
            ctypes.byref(volume_serial_number),
            ctypes.byref(max_component_length),
            ctypes.byref(file_system_flags),
            file_system_name_buffer,
            ctypes.sizeof(file_system_name_buffer)
        )

        # Convert the serial number to the desired format
        serial_number = volume_serial_number.value
        formatted_serial = f"{(serial_number >> 16) & 0xFFFF:04X}-{serial_number & 0xFFFF:04X}"

        return formatted_serial

    except Exception as e:
        # If the first method fails, try the fallback method using subprocess
        try:
            import subprocess
            import re

            # Run the 'vol' command to get volume information
            result = subprocess.run(['cmd', '/c', 'vol', 'C:'],
                                    capture_output=True,
                                    text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)

            # Use regex to find the serial number in the output
            # Example output: "Volume in drive C is Windows\nVolume Serial Number is E8D0-04CC"
            serial_match = re.search(r'Serial Number is ([0-9A-F]{4}-[0-9A-F]{4})', result.stdout)

            if serial_match:
                return serial_match.group(1)
            else:
                write_log_file(f"Error: Could not find serial number '{serial_match}'")
                return "OOOO-OOOO"

        except Exception as inner_e:
            write_log_file(f"Failed to retrieve serial number: {str(inner_e)}")
            return "OOOO-OOOO"

