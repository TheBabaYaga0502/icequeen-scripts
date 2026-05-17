import os
import sys
import subprocess
from variables import EXTRACTED_ISO, PORTABLES_FOLDER

def execute_arc_command(game_folder_name, release_group):
    portable_output_path = os.path.join(PORTABLES_FOLDER, f"{game_folder_name} [PORTABLE]")

    bin_file_path = os.path.join(EXTRACTED_ISO, game_folder_name, f"{release_group}.BIN")

    os.makedirs(PORTABLES_FOLDER, exist_ok=True)

    command = [
        "arc", "x",
        f"-dp{portable_output_path}",
        bin_file_path
    ]

    try:
        subprocess.run(command, check=True)
        print(f"ARC extraction successful! Files extracted to '{portable_output_path}'.")
        call_copy_crack_script(game_folder_name, release_group)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to execute ARC command for '{bin_file_path}'. Details: {e}")

def call_copy_crack_script(game_folder_name, release_group):
    try:
        subprocess.run(["python", "copy_crack.py", game_folder_name, release_group], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to execute copy_crack.py. Details: {e}")

def main(game_folder_name, release_group):
    execute_arc_command(game_folder_name, release_group)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python DARKSiDERS_skidrow_HOODLUM_TiNYiSO.py <game_folder_name> <release_group>")
    else:
        game_folder_name = sys.argv[1]
        release_group = sys.argv[2]
        main(game_folder_name, release_group)
