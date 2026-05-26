import os
import shutil
import requests
import subprocess
import string
import random
import sys
import time
import re
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from variables import PIXELDRAIN_API_KEY, GOFILE_API_TOKEN, ONEFICHIER_API_KEY, ROOTZ_API_KEY

def generate_random_name(length=12):
    """Generates a random string of letters and digits."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def get_folder_size(folder_path):
    """Calculate total size of a folder in bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(file_path)
            except (OSError, IOError):
                pass
    return total_size


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

def zip_folder(folder_path):
    """Zips the folder using 7z with password and random filename."""
    # Ensure we have an absolute path
    folder_path = os.path.abspath(folder_path)
    
    # Verify folder exists before proceeding
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist for zipping.")
        return None
    
    # Get the parent directory where we'll create the zip
    parent_dir = os.path.dirname(folder_path)
    
    # Generate random filename for the zip
    random_name = generate_random_name()
    zip_file_path = os.path.join(parent_dir, f"{random_name}.zip")
    
    # If zip already exists, delete it to ensure a fresh one
    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)
        
    print(f"Zipping folder: {folder_path} -> {zip_file_path} (Password: cs.rin.ru)...")
    
    # Try to find 7z in PATH first, then check common installation paths
    import shutil
    seven_zip = shutil.which("7z") or shutil.which("7z.exe")
    
    if not seven_zip:
        # Check common installation paths
        common_paths = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                seven_zip = path
                break
    
    if not seven_zip:
        print("Error: 7z.exe not found. Please ensure 7-Zip is installed and in your PATH.")
        return None
    
    # -p: password
    # -tzip: force zip format
    # -v2g: split into 2GB volumes
    # -bb: show progress with percentage
    # The folder inside will keep its original name automatically
    # Using list format ensures proper handling of paths with spaces/special chars
    command = [
        seven_zip, "a", 
        f"-pcs.rin.ru",
        "-tzip",
        "-v2g",  # Split into 2GB volumes
        "-bb1",  # Show progress: 0=off, 1=show names, 2=show names and sizes, 3=show progress bars
        zip_file_path, 
        folder_path
    ]
    
    try:
        # Don't capture output so 7z can show progress directly in terminal
        subprocess.run(command, check=True)
        
        # Find all created volume files (zip.001, zip.002, etc.) or the single zip file
        zip_files = []
        base_path = zip_file_path
        
        # Check if split volumes were created
        volume_num = 1
        while True:
            volume_path = f"{base_path}.{volume_num:03d}"  # .001, .002, etc.
            if os.path.exists(volume_path):
                zip_files.append(volume_path)
                volume_num += 1
            else:
                break
        
        # If no volumes found, check for single zip file
        if not zip_files:
            if os.path.exists(zip_file_path):
                zip_files.append(zip_file_path)
            else:
                print(f"\nError: Zip file was not created at {zip_file_path}")
                return []
        
        # Verify the first file is actually a ZIP file by checking magic bytes
        try:
            with open(zip_files[0], 'rb') as f:
                magic = f.read(4)
                # ZIP files start with PK\x03\x04 or PK\x05\x06 (empty zip) or PK\x07\x08
                if not (magic.startswith(b'PK\x03\x04') or magic.startswith(b'PK\x05\x06') or magic.startswith(b'PK\x07\x08')):
                    print(f"\nWarning: File does not appear to be a valid ZIP file (magic bytes: {magic.hex()})")
        except Exception as e:
            print(f"\nWarning: Could not verify ZIP file format: {e}")
        
        if len(zip_files) > 1:
            print(f"\nZipping complete: Created {len(zip_files)} volume(s) of 2GB each")
        else:
            print(f"\nZipping complete: {zip_files[0]}")
        
        return zip_files
    except subprocess.CalledProcessError as e:
        print(f"\nError during zipping: {e}")
        return None
    except Exception as e:
        print(f"\nUnexpected error during zipping: {e}")
        return None

def create_progress_callback(file_size):
    """Create a callback function for upload progress monitoring."""
    def callback(monitor):
        percent = (monitor.bytes_read / file_size) * 100
        bar_length = 50
        filled = int(percent / 2)
        bar = '#' * filled + '-' * (bar_length - filled)
        sys.stdout.write(f"\rUploading: [{bar}] {percent:.1f}%")
        sys.stdout.flush()
    return callback

def upload_to_pixeldrain(file_path, max_retries=3):
    """Uploads a file to PixelDrain with progress bar and retry logic."""
    print(f"\nUploading to PixelDrain: {file_path}...")
    url = "https://pixeldrain.com/api/file"
    auth = ("", PIXELDRAIN_API_KEY)
    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)

    for attempt in range(1, max_retries + 1):
        try:
            with open(file_path, "rb") as f:
                encoder = MultipartEncoder(
                    fields={"file": (filename, f, "application/zip")}
                )
                monitor = MultipartEncoderMonitor(encoder, create_progress_callback(file_size))

                response = requests.post(
                    url,
                    auth=auth,
                    data=monitor,
                    headers={"Content-Type": monitor.content_type},
                    timeout=3600  # 1 hour for large files
                )

            print("")  # New line after progress bar

            if response.status_code in [200, 201]:
                data = response.json()
                file_id = data.get("id")
                link = f"https://pixeldrain.com/u/{file_id}"
                print(f"PixelDrain upload successful: {link}")
                return link
            else:
                if attempt < max_retries:
                    wait_time = attempt * 2
                    print(f"PixelDrain upload failed with status {response.status_code} (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"PixelDrain upload failed: {response.status_code}")
                    return None
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                wait_time = attempt * 2
                print(f"\nPixelDrain upload timeout (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"\nPixelDrain upload timeout after {max_retries} attempts")
                return None
        except Exception as e:
            if attempt < max_retries:
                wait_time = attempt * 2
                print(f"\nPixelDrain error: {e} (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"\nPixelDrain error after {max_retries} attempts: {e}")
                return None

    return None

def upload_to_gofile(file_path, max_retries=3):
    """Uploads a file to GoFile with progress bar and retry logic using global upload endpoint."""
    print(f"\nUploading to GoFile: {file_path}...")

    url = "https://upload.gofile.io/uploadfile"
    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)

    for attempt in range(1, max_retries + 1):
        try:
            with open(file_path, "rb") as f:
                fields = {"file": (filename, f, "application/zip")}
                if GOFILE_API_TOKEN:
                    fields["token"] = GOFILE_API_TOKEN

                encoder = MultipartEncoder(fields=fields)
                monitor = MultipartEncoderMonitor(encoder, create_progress_callback(file_size))

                response = requests.post(
                    url,
                    data=monitor,
                    headers={"Content-Type": monitor.content_type},
                    timeout=3600  # 1 hour for large files
                )

            print("")  # New line after progress bar

            if response.status_code == 200:
                data = response.json()
                if data["status"] == "ok":
                    link = data["data"]["downloadPage"]
                    print(f"GoFile upload successful: {link}")
                    return link
                else:
                    error_msg = data.get("status", "unknown")
                    if attempt < max_retries and ("rate limit" in str(data).lower() or "server" in str(data).lower()):
                        wait_time = attempt * 2
                        print(f"GoFile upload failed: {error_msg} (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"GoFile upload failed: {data}")
                        return None
            else:
                if attempt < max_retries:
                    wait_time = attempt * 2
                    print(f"GoFile upload failed with status {response.status_code} (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"GoFile upload failed with status code: {response.status_code}")
                    return None
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                wait_time = attempt * 2
                print(f"\nGoFile upload timeout (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"\nGoFile upload timeout after {max_retries} attempts")
                return None
        except Exception as e:
            if attempt < max_retries:
                wait_time = attempt * 2
                print(f"\nGoFile error: {e} (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"\nGoFile error after {max_retries} attempts: {e}")
                return None

    return None

def upload_to_1fichier(file_path, max_retries=3):
    """Uploads a file to 1fichier with progress bar and retry logic."""
    print(f"\nUploading to 1fichier: {file_path}...")

    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)

    for attempt in range(1, max_retries + 1):
        try:
            # Step 1: Get upload server
            server_response = requests.post(
                "https://api.1fichier.com/v1/upload/get_upload_server.cgi",
                json={"api_key": ONEFICHIER_API_KEY},
                timeout=30
            )

            if server_response.status_code != 200:
                if attempt < max_retries:
                    wait_time = attempt * 2
                    print(f"1fichier server request failed (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"1fichier: Failed to get upload server: {server_response.status_code}")
                    return None

            server_data = server_response.json()
            if "url" not in server_data:
                if attempt < max_retries:
                    wait_time = attempt * 2
                    print(f"1fichier no upload URL (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"1fichier: No upload URL in response: {server_data}")
                    return None

            base_url = server_data["url"]
            if not base_url.startswith("http"):
                base_url = "https://" + base_url
            upload_id = server_data.get("id", "")
            upload_url = f"{base_url}/upload.cgi?id={upload_id}"

            # Step 2: Upload file to the server
            with open(file_path, "rb") as f:
                encoder = MultipartEncoder(
                    fields={
                        "file[]": (filename, f, "application/octet-stream")
                    }
                )
                monitor = MultipartEncoderMonitor(encoder, create_progress_callback(file_size))

                upload_response = requests.post(
                    upload_url,
                    data=monitor,
                    headers={"Content-Type": monitor.content_type},
                    timeout=3600  # 1 hour for large files
                )

            print("")  # New line after progress bar

            if upload_response.status_code == 200:
                response_text = upload_response.text

                # 1fichier returns HTML with the download link embedded
                # Look for the link pattern: https://1fichier.com/?{code}
                link_match = re.search(r'https?://1fichier\.com/\?[a-zA-Z0-9]+', response_text)
                if link_match:
                    link = link_match.group(0)
                    print(f"1fichier upload successful: {link}")
                    return link

                # Fallback: try plain text format (URL;control_code or just URL)
                if "1fichier.com" in response_text and "http" in response_text:
                    lines = response_text.strip().split("\n")
                    for line in lines:
                        if "1fichier.com" in line:
                            link = line.split(";")[0].strip()
                            if link.startswith("http"):
                                print(f"1fichier upload successful: {link}")
                                return link

                # Try JSON format as last resort
                try:
                    data = upload_response.json()
                    if "links" in data and len(data["links"]) > 0:
                        link = data["links"][0].get("download", data["links"][0].get("url"))
                        if link:
                            print(f"1fichier upload successful: {link}")
                            return link
                except:
                    pass

                if attempt < max_retries:
                    wait_time = attempt * 2
                    print(f"1fichier unexpected response (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"1fichier: Could not find download link in response")
                    return None
            else:
                if attempt < max_retries:
                    wait_time = attempt * 2
                    print(f"1fichier upload failed with status {upload_response.status_code} (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"1fichier upload failed: {upload_response.status_code}")
                    return None

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                wait_time = attempt * 2
                print(f"\n1fichier upload timeout (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"\n1fichier upload timeout after {max_retries} attempts")
                return None
        except Exception as e:
            if attempt < max_retries:
                wait_time = attempt * 2
                print(f"\n1fichier error: {e} (attempt {attempt}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"\n1fichier error after {max_retries} attempts: {e}")
                return None

    return None


def upload_to_rootz(file_path, max_retries=3):
    """Uploads a file to Rootz using their S3-style multipart protocol.

    Rootz stores files on Cloudflare R2 and routes single-shot POSTs through
    the Cloudflare edge, which caps request bodies at ~100 MB. The multipart
    API hands the client per-part presigned R2 URLs so chunks bypass that
    edge limit entirely. See /api/files/multipart/{init,part-url,complete,abort}.
    """
    print(f"\nUploading to Rootz: {file_path}...")
    base = "https://rootz.so/api/files/multipart"
    headers = {"Authorization": f"Bearer {ROOTZ_API_KEY}"}
    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)

    # 1. Init session
    try:
        r = requests.post(
            f"{base}/init",
            json={"fileName": filename, "fileSize": file_size, "mimeType": "application/zip"},
            headers=headers,
            timeout=60,
        )
    except Exception as e:
        print(f"Rootz init error: {e}")
        return None
    if r.status_code != 200:
        print(f"Rootz init failed: HTTP {r.status_code} {r.text[:300]}")
        return None
    init = r.json()
    if not init.get("success"):
        print(f"Rootz init failed: {init}")
        return None

    upload_id = init["uploadId"]
    key = init["key"]
    chunk_size = init["chunkSize"]
    total_parts = init["totalParts"]
    print(f"Rootz multipart: {total_parts} part(s) x {format_size(chunk_size)}")

    parts = []
    bytes_uploaded = 0

    def _draw_progress():
        percent = (bytes_uploaded / file_size) * 100 if file_size else 100.0
        bar_length = 50
        filled = int(percent / 2)
        bar = '#' * filled + '-' * (bar_length - filled)
        sys.stdout.write(
            f"\rUploading: [{bar}] {percent:.1f}% "
            f"({format_size(bytes_uploaded)}/{format_size(file_size)})"
        )
        sys.stdout.flush()

    try:
        with open(file_path, "rb") as f:
            for part_number in range(1, total_parts + 1):
                # 2a. Presigned URL for this part (with retry)
                part_url = None
                for attempt in range(1, max_retries + 1):
                    try:
                        rurl = requests.post(
                            f"{base}/part-url",
                            json={"uploadId": upload_id, "key": key, "partNumber": part_number},
                            headers=headers,
                            timeout=60,
                        )
                        if rurl.status_code == 200 and rurl.json().get("success"):
                            part_url = rurl.json()["url"]
                            break
                        raise RuntimeError(f"HTTP {rurl.status_code} {rurl.text[:200]}")
                    except Exception as e:
                        if attempt < max_retries:
                            time.sleep(attempt * 2)
                            continue
                        raise RuntimeError(f"could not get URL for part {part_number}: {e}")

                # Read chunk from disk
                chunk = f.read(chunk_size)
                if not chunk:
                    raise RuntimeError(f"unexpected EOF at part {part_number}")

                # 2b. PUT chunk to R2 (with retry)
                etag = None
                for attempt in range(1, max_retries + 1):
                    try:
                        rput = requests.put(
                            part_url,
                            data=chunk,
                            headers={
                                "Content-Type": "application/octet-stream",
                                "Content-Length": str(len(chunk)),
                            },
                            timeout=1800,
                        )
                        if rput.status_code == 200:
                            etag_raw = rput.headers.get("ETag", "").strip().strip('"')
                            if etag_raw:
                                etag = etag_raw
                                break
                            raise RuntimeError("missing ETag in PUT response")
                        raise RuntimeError(f"HTTP {rput.status_code} {rput.text[:200]}")
                    except Exception as e:
                        if attempt < max_retries:
                            time.sleep(attempt * 2)
                            continue
                        raise RuntimeError(f"PUT failed for part {part_number}: {e}")

                parts.append({"partNumber": part_number, "etag": etag})
                bytes_uploaded += len(chunk)
                _draw_progress()

        print("")  # Newline after progress bar

        # 3. Complete (with retry)
        for attempt in range(1, max_retries + 1):
            try:
                rcomp = requests.post(
                    f"{base}/complete",
                    json={
                        "uploadId": upload_id,
                        "key": key,
                        "parts": parts,
                        "fileName": filename,
                        "fileSize": file_size,
                        "mimeType": "application/zip",
                    },
                    headers=headers,
                    timeout=300,
                )
                if rcomp.status_code == 200 and rcomp.json().get("success"):
                    info = rcomp.json().get("file", {})
                    short_id = info.get("shortId") or info.get("id", "")
                    link = f"https://rootz.so/d/{short_id}"
                    print(f"Rootz upload successful: {link}")
                    return link
                raise RuntimeError(f"HTTP {rcomp.status_code} {rcomp.text[:300]}")
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(attempt * 2)
                    continue
                raise RuntimeError(f"complete failed: {e}")

        return None
    except Exception as e:
        print(f"\nRootz multipart upload error: {e}")
        # Free server-side state so the orphaned upload doesn't linger.
        try:
            requests.post(
                f"{base}/abort",
                json={"uploadId": upload_id, "key": key},
                headers=headers,
                timeout=30,
            )
        except Exception:
            pass
        return None


def upload_folder_to_all(folder_path):
    """Zips the folder (with password and random name, split into 2GB volumes) and uploads with progress.

    Returns dict with:
        - PixelDrain, GoFile, 1fichier: upload links
        - original_size: original folder size in bytes
        - compressed_size: compressed zip size in bytes
        - compression_ratio: percentage saved
    """
    # Calculate original folder size
    original_size = get_folder_size(folder_path)
    print(f"Original folder size: {format_size(original_size)}")

    zip_files = zip_folder(folder_path)
    if not zip_files:
        return {"original_size": original_size, "compressed_size": 0}

    # Calculate compressed size
    compressed_size = sum(os.path.getsize(f) for f in zip_files)
    if original_size > 0:
        compression_ratio = ((original_size - compressed_size) / original_size) * 100
        print(f"Compressed size: {format_size(compressed_size)} ({compression_ratio:.1f}% smaller)")
    else:
        compression_ratio = 0

    links = {"PixelDrain": [], "GoFile": [], "1fichier": [], "Rootz": []}

    # Upload all parts
    total_parts = len(zip_files)
    if total_parts > 1:
        print(f"\nNote: Archive split into {total_parts} parts (2GB each). Uploading all parts...")

    for i, part_file in enumerate(zip_files, start=1):
        if total_parts > 1:
            print(f"\n--- Uploading Part {i}/{total_parts} ---")

        # PixelDrain
        pd_link = upload_to_pixeldrain(part_file)
        if pd_link:
            links["PixelDrain"].append(pd_link)

        # GoFile
        gf_link = upload_to_gofile(part_file)
        if gf_link:
            links["GoFile"].append(gf_link)

        # 1fichier
        of_link = upload_to_1fichier(part_file)
        if of_link:
            links["1fichier"].append(of_link)

        # Rootz
        rz_link = upload_to_rootz(part_file)
        if rz_link:
            links["Rootz"].append(rz_link)

    # Format links for returning
    final_links = {}
    for service in ["PixelDrain", "GoFile", "1fichier", "Rootz"]:
        if links[service]:
            if total_parts > 1:
                # Create a formatted list of links
                formatted_links = []
                for idx, link in enumerate(links[service], start=1):
                    formatted_links.append(f"Part {idx}: {link}")
                final_links[service] = "\n".join(formatted_links)
            else:
                final_links[service] = links[service][0]

    # Cleanup all zip files after upload
    for zip_file in zip_files:
        try:
            os.remove(zip_file)
            print(f"Cleaned up: {zip_file}")
        except Exception as e:
            print(f"Failed to cleanup zip file {zip_file}: {e}")

    # Add size info to return dict
    final_links["original_size"] = original_size
    final_links["compressed_size"] = compressed_size

    return final_links
