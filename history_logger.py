import os
import json
from datetime import datetime

# History file path (same directory as this script)
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")


def load_history():
    """Load history from JSON file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"games": []}
    return {"games": []}


def save_history(history):
    """Save history to JSON file."""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: Could not save history: {e}")


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


def log_processed_game(game_name, original_size=0, compressed_size=0, magnet_url=None,
                       gofile_link=None, pixeldrain_link=None, onefichier_link=None,
                       rootz_link=None, image_url=None, store_url=None, success=True,
                       error_message=None):
    """
    Log a processed game to history.json

    Args:
        game_name: Name of the portable folder
        original_size: Original folder size in bytes
        compressed_size: Compressed zip size in bytes
        magnet_url: Generated magnet link
        gofile_link: GoFile download link(s)
        pixeldrain_link: PixelDrain download link(s)
        onefichier_link: 1fichier download link(s)
        rootz_link: Rootz download link(s)
        image_url: Game image URL
        store_url: Store page URL
        success: Whether processing was successful
        error_message: Error message if failed
    """
    history = load_history()

    # Calculate compression ratio
    if original_size > 0 and compressed_size > 0:
        compression_ratio = ((original_size - compressed_size) / original_size) * 100
    else:
        compression_ratio = 0

    entry = {
        "game_name": game_name,
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "sizes": {
            "original": original_size,
            "original_formatted": format_size(original_size),
            "compressed": compressed_size,
            "compressed_formatted": format_size(compressed_size),
            "compression_ratio": round(compression_ratio, 1)
        },
        "links": {
            "magnet": magnet_url,
            "gofile": gofile_link,
            "pixeldrain": pixeldrain_link,
            "onefichier": onefichier_link,
            "rootz": rootz_link
        },
        "metadata": {
            "image_url": image_url,
            "store_url": store_url
        }
    }

    if error_message:
        entry["error"] = error_message

    history["games"].append(entry)
    save_history(history)

    print(f"Logged to history: {game_name} ({'success' if success else 'failed'})")


def get_history_stats():
    """Get summary statistics from history."""
    history = load_history()
    games = history.get("games", [])

    if not games:
        return None

    total_games = len(games)
    successful = sum(1 for g in games if g.get("success", False))
    failed = total_games - successful

    total_original = sum(g.get("sizes", {}).get("original", 0) for g in games)
    total_compressed = sum(g.get("sizes", {}).get("compressed", 0) for g in games)

    return {
        "total_games": total_games,
        "successful": successful,
        "failed": failed,
        "total_original_size": format_size(total_original),
        "total_compressed_size": format_size(total_compressed),
        "total_saved": format_size(total_original - total_compressed)
    }


if __name__ == "__main__":
    # Print history stats when run directly
    stats = get_history_stats()
    if stats:
        print("=== Processing History Stats ===")
        print(f"Total games processed: {stats['total_games']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Total original size: {stats['total_original_size']}")
        print(f"Total compressed size: {stats['total_compressed_size']}")
        print(f"Total space saved: {stats['total_saved']}")
    else:
        print("No history found.")
