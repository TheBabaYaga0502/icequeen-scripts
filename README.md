# Portables Pipeline

An end-to-end automation tool that turns a downloaded scene release (an `.iso`
torrent of a cracked game) into a "portable" zip, distributes it across
multiple file hosts, generates a magnet link, and posts everything to a
Telegram channel. Built around a simple queue file (`LIST.txt`) so you can
drop release names in and let the rest run unattended.

> All credentials in `variables.py` are placeholders — fill in your own before
> running. See **Configuration** below.

---

## What it does

For each release name you queue, the pipeline:

1. **Extracts the ISO** from your downloads folder using 7-Zip.
2. **Installs / unpacks** the game using a release-group-specific handler
   (silent install for groups that support it, GUI automation for the ones that
   don't).
3. **Copies the crack** files from the release into the installed game folder.
4. **Reads the NFO** to grab the Steam/GOG/Epic store URL and a header image.
5. **Creates a `.torrent`** + magnet link (with a preset tracker list).
6. **Zips the portable folder** with 7-Zip, password-protected
   (`cs.rin.ru`), split into 5 GB volumes.
7. **Uploads every volume** to PixelDrain, GoFile, 1fichier, and Rootz in
   parallel-ish sequence.
8. **Builds a Pastebin** of all download links.
9. **Posts the release** (title, magnet, size info, Pastebin link, image) to
   a Telegram channel via the Bot API.
10. **Logs the result** to `history.json`.

---

## How it's wired together

```
run.py        always-on scheduler; watches LIST.txt
   |
   v
init.py       pops one game off LIST.txt and runs main.py for it
   |
   v
main.py       1) 7z-extracts the ISO
              2) dispatches to one of:
                   - DARKSiDERS_skidrow_HOODLUM_tinyiso.py
                   - FAiRLIGHT_DOGE.py
                   - RUNE_VREX.py
                   - TENOKE.py            (pyautogui GUI clicks)
                   - voices38.py          (Inno silent + auto-Finish dismiss)
   |
   v
copy_crack.py   copies release-group crack into the portable folder,
                pulls store URL + image from the NFO,
                deletes the extracted ISO folder
   |
   v
generate_magnet.py    creates the .torrent, computes the magnet,
                      then calls upload_folder_to_all (upload_utils.py)
                      which zips + uploads everywhere
   |
   v
telegram_webhook.py   posts the whole package to Telegram
   |
   v
history_logger.py     appends an entry to history.json
```

### Dispatch by release group

`main.py` looks at the last `-suffix` in the release name to pick a handler:

| Release group (suffix)                            | Handler                                |
|---------------------------------------------------|----------------------------------------|
| `darksiders`, `skidrow`, `HOODLUM`, `tinyiso`     | `DARKSiDERS_skidrow_HOODLUM_tinyiso.py` |
| `flt`, `doge`                                     | `FAiRLIGHT_DOGE.py`                    |
| `rune`, `vrex`                                    | `RUNE_VREX.py`                         |
| `tenoke`                                          | `TENOKE.py`                            |
| `voices38`                                        | `voices38.py`                          |

If the suffix doesn't match any of the above, the release is logged and
skipped.

### Folder layout the pipeline expects

`copy_crack.py` expects the extracted ISO to contain a release-group
subfolder so the crack files can be found:

```
<EXTRACTED_ISO>\<release_name>\<release_group>\...crack files...
```

After install + crack copy, the finished portable lives at:

```
<PORTABLES_FOLDER>\<release_name> [PORTABLE]\
```

---

## Prerequisites

* **Python 3.11+** on Windows.
* **7-Zip** installed and on `PATH` (used both for ISO extraction and for
  password-protected archive creation).
* **`py3createtorrent`** on `PATH` (used to make the `.torrent` file).
* A **Telegram bot** (create via `@BotFather`) and the chat/channel ID where
  it should post.
* Accounts / API keys for any of the hosts you want to use:
  PixelDrain, GoFile (optional — guest upload if no token), 1fichier, Rootz.
* A **Pastebin** account with API access.

### Python dependencies

From `PY_INSTALL THIS FIRST.txt`:

```
pip install pyautogui psutil py7zr requests requests-toolbelt pillow py3createtorrent
```

(`pygetwindow` is pulled in automatically by `pyautogui` on Windows and is
required by `voices38.py`.)

---

## Configuration

All configuration lives in **`variables.py`**.

### Paths

```python
DOWNLOADS_OF_TORRENTS = r"D:\Downloads"       # where qBittorrent saves new releases
EXTRACTED_ISO         = r"D:\Processing"      # working dir for ISO extracts
PORTABLES_FOLDER      = r"D:\Finished"        # output dir for portable folders
LIST_FILE             = r"D:\A\LIST.txt"      # the release queue file
TORRENT_PATH          = r"D:\Torrents"        # where new .torrent files are written
```

Edit these to match your machine.

### Credentials (placeholders — fill in your own)

```python
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'
TELEGRAM_CHAT_ID   = 'YOUR_TELEGRAM_CHAT_ID_HERE'

PASTEBIN_API_KEY   = 'YOUR_PASTEBIN_API_KEY_HERE'
PASTEBIN_USERNAME  = 'YOUR_PASTEBIN_USERNAME_HERE'
PASTEBIN_PASSWORD  = 'YOUR_PASTEBIN_PASSWORD_HERE'

PIXELDRAIN_API_KEY  = 'YOUR_PIXELDRAIN_API_KEY_HERE'
GOFILE_API_TOKEN    = None  # Guest upload if None
ONEFICHIER_API_KEY  = 'YOUR_1FICHIER_API_KEY_HERE'
ROOTZ_API_KEY       = 'YOUR_ROOTZ_API_KEY_HERE'
```

Set a host's key to `None` (or remove its call from `upload_utils.py`) to
skip uploading there.

### Trackers

`variables.py` ships with a default tracker list (`TRACKERS`) used for both
the `.torrent` file and the magnet URL. Edit if you want to add/remove
trackers.

### TENOKE click coordinates

`TENOKE.py` automates the official TENOKE setup wizard via `pyautogui`
click coordinates. Two coordinate sets are included in `variables.py` for
different screen sizes — the active set is at the top, the alternate set
is commented out at the bottom. Adjust to your resolution if the clicks
miss.

---

## Usage

### One-shot

Add a single release name to the queue, then run it:

```powershell
python add_torrent_to_list.py "Some.Game.Name-RELEASEGROUP"
python init.py
```

### Always-on (scheduler mode)

`run.py` will sit idle until `LIST.txt` has entries, then process them in
order. When the queue empties, it sleeps until a fixed daily target time
(controlled by `globaltime` in `variables.py`) and checks again.

```powershell
python run.py
```

### Skip the queue and process one release directly

```powershell
python main.py "Some.Game.Name-RELEASEGROUP"
```

### Just package + upload a folder that's already built

```powershell
python generate_magnet.py "D:\Finished\Some.Game.Name-RELEASEGROUP [PORTABLE]"
```

---

## Files at a glance

| File                                       | Purpose                                                                                  |
|--------------------------------------------|------------------------------------------------------------------------------------------|
| `run.py`                                   | Always-on scheduler. Polls `LIST.txt` and idles when empty.                              |
| `init.py`                                  | Drains `LIST.txt` one release at a time through `main.py`.                               |
| `main.py`                                  | ISO extract + dispatch to the release-group handler.                                     |
| `add_torrent_to_list.py`                   | Appends a release name to `LIST.txt`.                                                    |
| `DARKSiDERS_skidrow_HOODLUM_tinyiso.py`    | Handler for scene groups that ship a ready-to-play folder inside the ISO.                |
| `FAiRLIGHT_DOGE.py`                        | Handler for FAiRLIGHT / DOGE releases.                                                   |
| `RUNE_VREX.py`                             | Handler for RUNE / VREX releases (uses `arc.exe` / `unarc.dll` / `unpack.exe`).          |
| `TENOKE.py`                                | Handler for TENOKE releases (drives the GUI installer with `pyautogui`).                 |
| `voices38.py`                              | Handler for Inno-style `voices38` installers (silent install + auto-close Finish window).|
| `copy_crack.py`                            | Copies release-group crack into the portable folder + triggers downstream pipeline.      |
| `nfo_image_extractor.py`                   | Parses the release NFO for Steam/GOG/Epic store URL and Steam header image.              |
| `generate_magnet.py`                       | Creates the `.torrent`, computes the magnet, then triggers zipping + uploading + post.   |
| `upload_utils.py`                          | 7z-zips the portable folder (split 2 GB, password-protected) and uploads to all hosts.   |
| `telegram_webhook.py`                      | Posts the release card to Telegram (title, magnet, size, Pastebin link, store image).   |
| `history_logger.py`                        | Appends every processed release to `history.json` for stats / audit.                     |
| `variables.py`                             | All paths, credentials, trackers, and TENOKE click coordinates.                          |
| `config.ini` / `config_o.ini`              | Templates passed to `arc.exe` / `unarc.dll` for RUNE/VREX-style unpacking.               |
| `arc.exe`, `unarc.dll`, `unpack.exe`       | Native helpers for unpacking certain release formats.                                    |
| `arc.ini`                                  | Per-archive config consumed by `arc.exe`.                                                |
| `LIST.txt`                                 | The release queue. One release name per line.                                            |
| `PY_INSTALL THIS FIRST.txt`                | The pip install line for first-time setup.                                               |
| `ices_main.py`, `test_split_discord.py`    | Older / experimental helpers, not part of the main pipeline.                             |

---

## Notes

* The 7-Zip archives produced by `upload_utils.py` are password-protected
  with the literal password **`cs.rin.ru`** and split into **5 GB** volumes
  (`.zip.001`, `.zip.002`, ...). All volumes are uploaded to every enabled
  host and the Telegram post / Pastebin lists each part separately.
* The `voices38.py` handler runs Inno Setup with `/VERYSILENT`. Even with
  silent mode the installer leaves a Finish window up at the end, so the
  script polls (up to 10 minutes) for that window via `pygetwindow`, then
  posts a `WM_KEYDOWN`/`WM_KEYUP` for `Enter` straight to the window's
  handle via Win32 `PostMessage` — this works whether the window is
  minimized, in the background, or in the foreground.
* `TENOKE.py` automates the official TENOKE GUI installer using fixed
  click coordinates from `variables.py` — if you change resolution or DPI
  the clicks will miss. Adjust the coordinates accordingly.
* `history.json` is not shipped in this copy. It will be created on first
  run.
