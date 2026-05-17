import subprocess
import os
import time
from datetime import datetime, timedelta, timezone
from variables import globaltime, LIST_FILE

def is_list_empty():
    if not os.path.exists(LIST_FILE):
        print(f"'{LIST_FILE}' does not exist. Treating as empty.")
        return True
    with open(LIST_FILE, "r") as file:
        lines = file.readlines()
    return len(lines) == 0

def get_utc_time_for_target():
    now = datetime.now(timezone.utc)
    target_offset = timedelta(seconds=globaltime) 
    today_target = datetime.combine(now.date(), datetime.min.time(), timezone.utc) + target_offset + timedelta(hours=8)
    if now >= today_target:
        today_target += timedelta(days=1)
    return today_target

def main():
    while True:
        if not is_list_empty():
            try:
                print("Running init.py as LIST.txt is not empty.")
                subprocess.run(["python", "init.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error: Failed to run init.py. Details: {e}")
        else:
            next_utc = get_utc_time_for_target()
            seconds_until_target = (next_utc - datetime.now(timezone.utc)).total_seconds()
            print(f"LIST.txt is empty. Idling until next target time zone ({next_utc}).")
            time.sleep(max(0, seconds_until_target))

if __name__ == "__main__":
    main()
