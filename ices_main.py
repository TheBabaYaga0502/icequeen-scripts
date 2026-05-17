import os
import shutil
import requests
import base64
import hashlib
from variables import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Folder A: All downloads come here. Check for .iso files.
# Folder B: Copy .iso files to this folder. Create torrent and magnet here.
# Folder C: Move .iso and .torrent files here after creating torrent and magnet. Used for uploading and for qBittorrent to grab .torrent files.

folderA = "D:\\project\\iso_automation_releases\\Downloads"
folderB = "D:\\project\\iso_automation_releases\\Processing"
folderC = "D:\\project\\iso_automation_releases\\Finished"
logFile = "D:\\project\\iso_automation_releases\\completed_torrents.txt"
trackers = [
    "udp://tracker.opentrackr.org:1337",
	"udp://explodie.org:6969/announce",
	"udp://tracker.torrent.eu.org:451/announce",
	"http://open.acgnxtracker.com:80/announce",
	"udp://tracker.theoks.net:6969/announce",
	"http://tracker.bt4g.com:2095/announce",
	"udp://tracker.dump.cl:6969/announce",
	"https://tracker.tamersunion.org:443/announce",
	"udp://ec2-18-191-163-220.us-east-2.compute.amazonaws.com:6969/announce",
	"https://trackers.mlsub.net:443/announce",
	"udp://opentracker.io:6969/announce",
	"udp://leet-tracker.moe:1337/announce",
	"https://tracker.yemekyedim.com:443/announce",
	"http://bt.okmp3.ru:2710/announce",
	"udp://run.publictracker.xyz:6969/announce"
]

# Functie: Controleer of een torrent al is verwerkt
def is_torrent_processed(torrent_name):
    if os.path.exists(logFile):
        with open(logFile, 'r') as log:
            return torrent_name in log.read()
    return False

# Functie: Voeg een torrent toe aan het logbestand
def add_to_log(torrent_name):
    with open(logFile, 'a') as log:
        log.write(torrent_name + '\n')

# Functie: Stuur bericht naar Telegram
def send_to_telegram(title, magnet_url):
    base64_encoded = base64.b64encode(magnet_url.encode()).decode()
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    text = f"<b>{title}</b>\nMagnet (Base64): <code>{base64_encoded}</code>\nDecoded Magnet: https://www.base64decode.org/"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=data)
    response.raise_for_status()

# Functie: Bereken de info-hash van een torrentbestand
def calculate_info_hash(torrent_file_path):
    with open(torrent_file_path, "rb") as torrent_file:
        torrent_data = torrent_file.read()
        info_start = torrent_data.find(b"4:info") + 6
        info_end = torrent_data.rfind(b"ee")
        info_hash = hashlib.sha1(torrent_data[info_start:info_end]).hexdigest()
        return info_hash

# Functie: Genereer een magnet-link
def generate_magnet_link(info_hash, torrent_name, trackers):
    base_magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={torrent_name}"
    for tracker in trackers:
        base_magnet += f"&tr={tracker}"
    return base_magnet

# Functie: Maak een torrent met py3createtorrent
def create_torrent(source_path):
    torrent_file_name = os.path.splitext(os.path.basename(source_path))[0] + ".torrent"
    torrent_file_path = os.path.join(folderB, torrent_file_name)
    tracker_args = " ".join([f"-t {tracker}" for tracker in trackers])
    command = f"py3createtorrent {source_path} {tracker_args} -o {torrent_file_path}"
    os.system(command)
    return torrent_file_path

# Functie: Verplaats een bestand, verwijder het bestaande indien nodig
def safe_move(src, dst):
    if os.path.exists(dst):
        os.remove(dst)  # Verwijder het bestaande bestand
    shutil.move(src, dst)

# Hoofdscript
for root, _, files in os.walk(folderA):
    for file in files:
        if file.endswith(".iso"):
            iso_path = os.path.join(root, file)
            torrent_name = os.path.splitext(file)[0]

            if not is_torrent_processed(torrent_name):
                # 1. Kopieer .iso naar Folder B
                processing_iso_path = os.path.join(folderB, file)
                shutil.copy(iso_path, processing_iso_path)

                # 2. Maak een torrent en magnet-link
                new_torrent_path = create_torrent(processing_iso_path)
                info_hash = calculate_info_hash(new_torrent_path)
                magnet_url = generate_magnet_link(info_hash, torrent_name, trackers)
                print(f"Magnet URL gegenereerd: {magnet_url}")

                # 3. Stuur de gegevens naar Telegram
                send_to_telegram(torrent_name, magnet_url)

                # 4. Voeg toe aan het logbestand
                add_to_log(torrent_name)

                # 5. Verplaats .iso en .torrent naar Folder C
                finished_iso_path = os.path.join(folderC, file)
                finished_torrent_path = os.path.join(folderC, os.path.basename(new_torrent_path))
                safe_move(processing_iso_path, finished_iso_path)
                safe_move(new_torrent_path, finished_torrent_path)
