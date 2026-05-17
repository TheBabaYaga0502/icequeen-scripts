import os
import sys
import time
import subprocess
from variables import DOWNLOADS_OF_TORRENTS, EXTRACTED_ISO

def extract_iso(game_folder_name):
    torrent_path = os.path.join(DOWNLOADS_OF_TORRENTS, game_folder_name)

    if not os.path.isdir(torrent_path):
        print(f"Error: Directory '{torrent_path}' does not exist.")
        return

    iso_files = [file for file in os.listdir(torrent_path) if file.endswith('.iso')]

    if len(iso_files) != 1:
        print(f"Error: Expected exactly one .iso file in '{torrent_path}', but found {len(iso_files)}.")
        return

    iso_file = iso_files[0]
    iso_file_path = os.path.join(torrent_path, iso_file)

    os.makedirs(EXTRACTED_ISO, exist_ok=True)

    command = [
        "7z", "x", 
        iso_file_path,  
        f"-o{os.path.join(EXTRACTED_ISO, game_folder_name)}"  
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Extraction successful! Files extracted to '{os.path.join(EXTRACTED_ISO, game_folder_name)}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to extract '{iso_file_path}'. Details: {e}")

def check_release_group(game_folder_name):
    release_group = game_folder_name.split("-")[-1]

    target_groups_1 = {"darksiders", "skidrow", "HOODLUM", "tinyiso"}
    target_groups_2 = {"flt", "doge"}
    target_groups_3 = {"rune", "vrex"}
    target_groups_4 = {"voices38"}
    if release_group.lower() in target_groups_1:
        try:
            subprocess.run(["python", "DARKSiDERS_skidrow_HOODLUM_tinyiso.py", game_folder_name, release_group], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to execute script for release group '{release_group}'. Details: {e}")
    elif release_group.lower() in target_groups_2:
        try:
            subprocess.run(["python", "FAiRLIGHT_DOGE.py", game_folder_name, release_group], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to execute script for release group '{release_group}'. Details: {e}")
    elif release_group.lower() in target_groups_3:
        try:
            subprocess.run(["python", "RUNE_VREX.py", game_folder_name, release_group], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to execute script for release group '{release_group}'. Details: {e}")
    elif release_group.lower() == "tenoke":
        try:
            subprocess.run(["python", "TENOKE.py", game_folder_name, release_group], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to execute script for release group '{release_group}'. Details: {e}")
    elif release_group.lower() in target_groups_4:
        try:
            subprocess.run(["python", "voices38.py", game_folder_name, release_group], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to execute script for release group '{release_group}'. Details: {e}")
    else:
        print(f"Release group '{release_group}' does not match the target groups.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <game_folder_name>")
    else:
        game_folder_name = sys.argv[1]
        extract_iso(game_folder_name)
        time.sleep(10) #for tenoke so i get time to logout
        check_release_group(game_folder_name)
