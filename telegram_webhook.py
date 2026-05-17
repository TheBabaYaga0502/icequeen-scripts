import sys
import requests
from datetime import datetime
from variables import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PASTEBIN_API_KEY, PASTEBIN_USERNAME, PASTEBIN_PASSWORD


def format_size(size_bytes):
    """Format bytes into human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def send_telegram_message(text):
    """Send a message to Telegram via Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=data)
    return response.status_code == 200


def send_telegram_photo(photo_url, caption=None):
    """Send a photo to Telegram via Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": photo_url,
        "parse_mode": "HTML"
    }
    if caption:
        data["caption"] = caption
    response = requests.post(url, json=data)
    return response.status_code == 200


def get_pastebin_user_key():
    """Login to Pastebin and return a user session key."""
    data = {
        "api_dev_key": PASTEBIN_API_KEY,
        "api_user_name": PASTEBIN_USERNAME,
        "api_user_password": PASTEBIN_PASSWORD
    }
    response = requests.post("https://pastebin.com/api/api_login.php", data=data)
    if response.status_code == 200 and not response.text.startswith("Bad API request"):
        return response.text
    else:
        print(f"Pastebin login failed: {response.text}")
        return None


def create_pastebin(title, content):
    """Upload content to Pastebin under the authenticated account and return the paste URL."""
    user_key = get_pastebin_user_key()

    data = {
        "api_dev_key": PASTEBIN_API_KEY,
        "api_option": "paste",
        "api_paste_code": content,
        "api_paste_name": title,
        "api_paste_private": "1",  # unlisted
        "api_paste_expire_date": "N"  # never expire
    }
    if user_key:
        data["api_user_key"] = user_key

    response = requests.post("https://pastebin.com/api/api_post.php", data=data)
    if response.status_code == 200 and response.text.startswith("https://"):
        print(f"Pastebin created: {response.text}")
        return response.text
    else:
        print(f"Pastebin upload failed: {response.text}")
        return None


def build_pastebin_content(portable_folder_name, magnet_url, gofile_link, pixeldrain_link, onefichier_link, rootz_link):
    """Build a nicely formatted plaintext paste with all download links."""
    lines = []
    lines.append(f"{'=' * 60}")
    lines.append(f"  {portable_folder_name}")
    lines.append(f"{'=' * 60}")
    lines.append("")
    lines.append(f"Magnet:")
    lines.append(magnet_url)
    lines.append("")

    if gofile_link:
        lines.append(f"--- GoFile ---")
        lines.append(gofile_link)
        lines.append("")

    if pixeldrain_link:
        lines.append(f"--- PixelDrain ---")
        lines.append(pixeldrain_link)
        lines.append("")

    if onefichier_link:
        lines.append(f"--- 1fichier ---")
        lines.append(onefichier_link)
        lines.append("")

    if rootz_link:
        lines.append(f"--- Rootz ---")
        lines.append(rootz_link)
        lines.append("")

    return "\n".join(lines)


def post_to_telegram(portable_folder_name, magnet_url, gofile_link=None, pixeldrain_link=None, onefichier_link=None, rootz_link=None, image_url=None, store_url=None, original_size=0, compressed_size=0):

    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    # Upload all links to Pastebin
    paste_content = build_pastebin_content(portable_folder_name, magnet_url, gofile_link, pixeldrain_link, onefichier_link, rootz_link)
    paste_url = create_pastebin(portable_folder_name, paste_content)

    # Build the title line
    if store_url:
        title_line = f'<b><a href="{store_url}">{portable_folder_name}</a></b>'
    else:
        title_line = f"<b>{portable_folder_name}</b>"

    # Build size line
    size_line = ""
    if original_size > 0 and compressed_size > 0:
        compression_ratio = ((original_size - compressed_size) / original_size) * 100
        size_line = f"\n<b>Size:</b> {format_size(original_size)} \u2192 {format_size(compressed_size)} ({compression_ratio:.0f}% smaller)"

    # Build magnet line
    magnet_line = f"\n<b>Magnet:</b>\n<code>{magnet_url}</code>"

    # Build the download links line (single Pastebin URL or fallback to inline)
    if paste_url:
        links_line = f'\n\n<b>Download Links:</b> <a href="{paste_url}">{paste_url}</a>'
    else:
        # Fallback: show links inline if Pastebin fails
        links_parts = []
        if gofile_link:
            links_parts.append(f"<b>GoFile:</b>\n{gofile_link}")
        if pixeldrain_link:
            links_parts.append(f"<b>PixelDrain:</b>\n{pixeldrain_link}")
        if onefichier_link:
            links_parts.append(f"<b>1fichier:</b>\n{onefichier_link}")
        if rootz_link:
            links_parts.append(f"<b>Rootz:</b>\n{rootz_link}")
        links_line = "\n" + "\n".join(links_parts) if links_parts else ""

    # Build footer
    footer = f"\n\n<i>Uploaded at {dt_string}</i>"

    # Assemble the compact message
    full_message = title_line + size_line + magnet_line + links_line + footer

    # Send thumbnail as separate photo if available
    if image_url:
        send_telegram_photo(image_url, caption=title_line)

    # Send the single clean message
    success = send_telegram_message(full_message)
    if success:
        print("Successfully sent to Telegram.")
    else:
        print("Failed to send Telegram message.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python telegram_webhook.py <torrent_name> <magnet_url> [gofile_link] [pixeldrain_link] [onefichier_link] [rootz_link] [image_url] [store_url] [original_size] [compressed_size]")
        sys.exit(1)

    torrent_name = sys.argv[1]
    magnet_url = sys.argv[2]
    gofile_link = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
    pixeldrain_link = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None
    onefichier_link = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] else None
    rootz_link = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6] else None
    image_url = sys.argv[7] if len(sys.argv) > 7 and sys.argv[7] else None
    store_url = sys.argv[8] if len(sys.argv) > 8 and sys.argv[8] else None
    original_size = int(sys.argv[9]) if len(sys.argv) > 9 and sys.argv[9] else 0
    compressed_size = int(sys.argv[10]) if len(sys.argv) > 10 and sys.argv[10] else 0

    post_to_telegram(torrent_name, magnet_url, gofile_link, pixeldrain_link, onefichier_link, rootz_link, image_url, store_url, original_size, compressed_size)
