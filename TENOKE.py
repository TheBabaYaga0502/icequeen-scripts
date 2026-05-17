import os
import subprocess
import time
import pyautogui
import psutil
import shutil
import sys
from variables import (PORTABLES_FOLDER, EXTRACTED_ISO, DOWNLOADS_OF_TORRENTS,
                       TENOKE_OK_BTN_X, TENOKE_OK_BTN_Y,
                       TENOKE_INSTALL_BTN_X, TENOKE_INSTALL_BTN_Y,
                       TENOKE_UNINSTALL_BTN_X, TENOKE_UNINSTALL_BTN_Y,
                       TENOKE_SHORTCUT_BTN_X, TENOKE_SHORTCUT_BTN_Y,
                       TENOKE_FIRST_CLICK_X, TENOKE_FIRST_CLICK_Y,
                       TENOKE_INSTALL_TO_FIELD_X, TENOKE_INSTALL_TO_FIELD_Y)
from nfo_image_extractor import extract_image_from_nfo

def tenoke_unpack(game_folder_name, release_group):

    OUTPUT_FOLDER = os.path.join(PORTABLES_FOLDER,f"{game_folder_name} [PORTABLE]")
    setup_path = fr"{EXTRACTED_ISO}\{game_folder_name}\SETUP.exe"
    set_install_path = fr"{PORTABLES_FOLDER}\{game_folder_name} [PORTABLE]"

    print(OUTPUT_FOLDER)

    subprocess.Popen([setup_path])

    time.sleep(5) 

    tenoke_started = False
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == "SETUP.exe":
            tenoke_started = True
            break
    if tenoke_started:
      pyautogui.click(TENOKE_FIRST_CLICK_X, TENOKE_FIRST_CLICK_Y)
      time.sleep(1)

      pyautogui.click(TENOKE_INSTALL_TO_FIELD_X, TENOKE_INSTALL_TO_FIELD_Y)
      pyautogui.press('tab')
      pyautogui.press('delete')
      pyautogui.typewrite(set_install_path)

      pyautogui.click(TENOKE_SHORTCUT_BTN_X, TENOKE_SHORTCUT_BTN_Y)
      pyautogui.click(TENOKE_UNINSTALL_BTN_X, TENOKE_UNINSTALL_BTN_Y)
      pyautogui.click(TENOKE_INSTALL_BTN_X, TENOKE_INSTALL_BTN_Y)   

    while tenoke_started:
        #pyautogui.click(TENOKE_OK_BTN_X, TENOKE_OK_BTN_Y)
        pyautogui.press('enter')
        
        time.sleep(5) 

        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == "SETUP.exe":
                tenoke_started = True
                break
            else:
                tenoke_started = False

    print("im done")

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
    tenoke_unpack(game_folder_name, release_group)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python TENOKE.py <game_folder_name> <release_group>")
    else:
        game_folder_name = sys.argv[1]
        release_group = sys.argv[2]
        main(game_folder_name, release_group)

    
