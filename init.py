import subprocess
import os
from variables import LIST_FILE

def process_list():
    if not os.path.exists(LIST_FILE):
        print(f"Error: '{LIST_FILE}' does not exist.")
        return

    while True:
        with open(LIST_FILE, "r") as file:
            lines = file.readlines()

        if not lines:
            print("LIST.txt is empty. Exiting.")
            break

        first_line = lines[0].strip()

        try:
            print(f"Running main.py with argument: {first_line}")
            subprocess.run(["python", "main.py", first_line], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to run main.py with argument '{first_line}'. Details: {e}")
            break

        with open(LIST_FILE, "w") as file:
            file.writelines(lines[1:])

if __name__ == "__main__":
    process_list()
