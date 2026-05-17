import os
import shutil
import sys
import subprocess
from variables import EXTRACTED_ISO, PORTABLES_FOLDER, DOWNLOADS_OF_TORRENTS
from nfo_image_extractor import extract_image_from_nfo

def copy_crack_files(game_folder_name, release_group):
    source_path = os.path.join(EXTRACTED_ISO, game_folder_name, release_group)
    destination_path = os.path.join(PORTABLES_FOLDER, f"{game_folder_name} [PORTABLE]")

    if not os.path.isdir(source_path):
        print(f"Error: Source path '{source_path}' does not exist.")
        return

    for root, _, files in os.walk(source_path):
        relative_path = os.path.relpath(root, source_path)
        dest_dir = os.path.join(destination_path, relative_path)

        os.makedirs(dest_dir, exist_ok=True)

        for file in files:
            source_file_path = os.path.join(root, file)
            destination_file_path = os.path.join(dest_dir, file)

            try:
                shutil.copy2(source_file_path, destination_file_path)
                print(f"Copied '{source_file_path}' to '{destination_file_path}'.")
            except Exception as e:
                print(f"Error copying '{source_file_path}' to '{destination_file_path}': {e}")

    # Extract image URL and store URL from NFO in the Downloads folder (where the ISO and NFO are)
    downloads_folder = os.path.join(DOWNLOADS_OF_TORRENTS, game_folder_name)
    image_url, store_url = extract_image_from_nfo(downloads_folder)

    # Delete the extracted folder
    extracted_folder = os.path.join(EXTRACTED_ISO, game_folder_name)
    shutil.rmtree(extracted_folder)
    call_generate_magnet_script(game_folder_name, image_url, store_url)

def call_generate_magnet_script(game_folder_name, image_url=None, store_url=None):
    destination_path = os.path.join(PORTABLES_FOLDER, f"{game_folder_name} [PORTABLE]")
    try:
        cmd = ["python", "generate_magnet.py", destination_path]
        cmd.append(image_url if image_url else "")
        cmd.append(store_url if store_url else "")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to execute generate_magnet.py. Details: {e}")

def main(game_folder_name, release_group):
    copy_crack_files(game_folder_name, release_group)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python copy_crack.py <game_folder_name> <release_group>")
    else:
        game_folder_name = sys.argv[1]
        release_group = sys.argv[2]
        main(game_folder_name, release_group)
