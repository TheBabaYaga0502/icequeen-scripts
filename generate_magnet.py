import os
import hashlib
import sys
import subprocess
from variables import TRACKERS, TORRENT_PATH
from upload_utils import upload_folder_to_all
from history_logger import log_processed_game

def calculate_info_hash(torrent_file_path):
    with open(torrent_file_path, "rb") as torrent_file:
        torrent_data = torrent_file.read()
        info_start = torrent_data.find(b"4:info") + 6
        info_end = torrent_data.rfind(b"ee")
        info_hash = hashlib.sha1(torrent_data[info_start:info_end]).hexdigest()
        return info_hash

def generate_magnet_link(info_hash, torrent_name, trackers):
    base_magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={torrent_name}"
    for tracker in trackers:
        base_magnet += f"&tr={tracker}"
    return base_magnet

def create_torrent(source_path):
    torrent_file_name = os.path.splitext(os.path.basename(source_path))[0] + ".torrent"
    torrent_file_path = os.path.join(TORRENT_PATH, torrent_file_name) 

    tracker_args = " ".join([f"-t {tracker}" for tracker in TRACKERS])
    
    command = f"py3createtorrent \"{source_path}\" {tracker_args} -o \"{torrent_file_path}\""
    os.system(command)

    return torrent_file_path

def call_telegram_webhook(torrent_name, magnet_url, gofile_link=None, pixeldrain_link=None, onefichier_link=None, rootz_link=None, image_url=None, store_url=None, original_size=0, compressed_size=0):
    cmd = ["python", "telegram_webhook.py", torrent_name, magnet_url]
    cmd.append(gofile_link if gofile_link else "")
    cmd.append(pixeldrain_link if pixeldrain_link else "")
    cmd.append(onefichier_link if onefichier_link else "")
    cmd.append(rootz_link if rootz_link else "")
    cmd.append(image_url if image_url else "")
    cmd.append(store_url if store_url else "")
    cmd.append(str(original_size))
    cmd.append(str(compressed_size))
    subprocess.run(cmd)

def process_and_generate_magnet(folder_path, image_url=None, store_url=None):
    # Ensure we have an absolute path
    folder_path = os.path.abspath(folder_path)

    if not os.path.isdir(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return

    # 1. Generate Magnet FIRST (before any zipping/uploading)
    print(f"Generating torrent for: {folder_path}...")
    torrent_file_path = create_torrent(folder_path)

    if not os.path.exists(torrent_file_path):
        print(f"Error: Failed to create torrent file at {torrent_file_path}")
        return

    info_hash = calculate_info_hash(torrent_file_path)
    magnet_url = generate_magnet_link(info_hash, os.path.basename(folder_path), TRACKERS)
    print(f"Magnet URL generated: {magnet_url}")

    # 2. Now handle the zipping and uploads
    upload_links = upload_folder_to_all(folder_path)
    gofile_link = upload_links.get("GoFile")
    pixeldrain_link = upload_links.get("PixelDrain")
    onefichier_link = upload_links.get("1fichier")
    rootz_link = upload_links.get("Rootz")
    original_size = upload_links.get("original_size", 0)
    compressed_size = upload_links.get("compressed_size", 0)

    # 3. Send everything to Telegram
    call_telegram_webhook(os.path.basename(folder_path), magnet_url, gofile_link, pixeldrain_link, onefichier_link, rootz_link, image_url, store_url, original_size, compressed_size)

    # 4. Log to history
    log_processed_game(
        game_name=os.path.basename(folder_path),
        original_size=original_size,
        compressed_size=compressed_size,
        magnet_url=magnet_url,
        gofile_link=gofile_link,
        pixeldrain_link=pixeldrain_link,
        onefichier_link=onefichier_link,
        rootz_link=rootz_link,
        image_url=image_url,
        store_url=store_url,
        success=True
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_magnet.py <folder_path> [image_url] [store_url]")
        sys.exit(1)

    folder_path = sys.argv[1]
    image_url = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
    store_url = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
    process_and_generate_magnet(folder_path, image_url, store_url)
