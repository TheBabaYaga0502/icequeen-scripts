import os
import re
import requests

def find_nfo_files(folder_path):
    """Find all .nfo files in a folder (non-recursive)."""
    nfo_files = []
    try:
        for file in os.listdir(folder_path):
            if file.lower().endswith('.nfo'):
                nfo_files.append(os.path.join(folder_path, file))
    except Exception:
        pass
    return nfo_files

def extract_store_url_from_nfo(nfo_path):
    """Extract store URL from an NFO file. Returns (store_url, app_id) tuple."""
    try:
        # Try multiple encodings as NFO files vary
        content = None
        for encoding in ['utf-8', 'latin-1', 'cp437', 'cp850']:
            try:
                with open(nfo_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()
                break
            except Exception:
                continue

        if not content:
            return None, None

        # Try to find Steam URL first
        steam_pattern = r'(https?://)?store\.steampowered\.com/app/(\d+)(/[^\s]*)?'
        steam_match = re.search(steam_pattern, content, re.IGNORECASE)
        if steam_match:
            app_id = steam_match.group(2)
            store_url = f"https://store.steampowered.com/app/{app_id}"
            return store_url, app_id

        # Try GOG
        gog_pattern = r'(https?://)?www\.gog\.com/[^\s]+'
        gog_match = re.search(gog_pattern, content, re.IGNORECASE)
        if gog_match:
            url = gog_match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url, None

        # Try Epic Games Store
        epic_pattern = r'(https?://)?store\.epicgames\.com/[^\s]+'
        epic_match = re.search(epic_pattern, content, re.IGNORECASE)
        if epic_match:
            url = epic_match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url, None

        return None, None
    except Exception:
        return None, None

def get_steam_image_from_store(app_id, timeout=10):
    """
    Fetch the actual header image URL from Steam store page.
    Steam now uses dynamic URLs with hashes for newer games.
    """
    try:
        store_url = f"https://store.steampowered.com/app/{app_id}"
        response = requests.get(store_url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        if response.status_code != 200:
            return None

        # Look for og:image meta tag (most reliable)
        og_match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', response.text)
        if og_match:
            return og_match.group(1)

        # Fallback: look for header image in page
        header_match = re.search(r'(https://[^"\']+/header\.jpg[^"\']*)', response.text)
        if header_match:
            return header_match.group(1)

        return None
    except Exception:
        return None

def get_steam_image_urls(app_id):
    """
    Get list of possible Steam CDN image URLs for an app ID.
    Returns multiple formats as fallbacks (for older games).
    """
    return [
        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/header.jpg",
        f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg",
        f"https://steamcdn-a.akamaihd.net/steam/apps/{app_id}/header.jpg",
        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/capsule_616x353.jpg",
        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/library_600x900.jpg",
    ]

def verify_image_exists(url, timeout=5):
    """Verify the image URL is accessible (HEAD request)."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except Exception:
        return False

def extract_image_from_nfo(extracted_folder_path, verify=True):
    """
    Main function: Extract game image URL and store URL from NFO file.

    Args:
        extracted_folder_path: Path to the extracted ISO folder
        verify: Whether to verify the image URL is accessible

    Returns:
        Tuple of (image_url, store_url) - either can be None
    """
    try:
        # Find NFO files
        nfo_files = find_nfo_files(extracted_folder_path)

        if not nfo_files:
            print("No NFO files found in extracted folder.")
            return None, None

        # Try each NFO file until we find a store URL
        for nfo_path in nfo_files:
            store_url, app_id = extract_store_url_from_nfo(nfo_path)

            if store_url:
                print(f"Found store URL: {store_url}")

                # If it's a Steam game, try to get the image
                if app_id:
                    print(f"Steam app ID: {app_id}")

                    if verify:
                        # First try to get image directly from Steam store page
                        print("Fetching image from Steam store page...")
                        store_image = get_steam_image_from_store(app_id)
                        if store_image:
                            print(f"Image URL from store: {store_image}")
                            return store_image, store_url

                        # Fallback: try legacy CDN URLs
                        print("Trying legacy CDN URLs...")
                        for image_url in get_steam_image_urls(app_id):
                            if verify_image_exists(image_url):
                                print(f"Image URL verified: {image_url}")
                                return image_url, store_url

                        print(f"No accessible image found for app ID: {app_id}")
                        # Still return store_url even if image fails
                        return None, store_url
                    else:
                        return get_steam_image_urls(app_id)[0], store_url
                else:
                    # Non-Steam store (GOG, Epic, etc.) - no image extraction
                    return None, store_url

        print("No valid store URL found in NFO files.")
        return None, None

    except Exception as e:
        print(f"Error extracting from NFO: {e}")
        return None, None


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python nfo_image_extractor.py <extracted_folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    image_url, store_url = extract_image_from_nfo(folder_path)

    print(f"\nResults:")
    print(f"  Image URL: {image_url}")
    print(f"  Store URL: {store_url}")
