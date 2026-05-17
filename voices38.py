import os
import sys
import time
import ctypes
import subprocess
import pyautogui
try:
    import pygetwindow as gw
except ImportError:
    gw = None
from variables import EXTRACTED_ISO, PORTABLES_FOLDER


def execute_silent_install(game_folder_name, release_group):
    setup_path = os.path.join(EXTRACTED_ISO, game_folder_name, "Setup.exe")
    portable_output_path = os.path.join(PORTABLES_FOLDER, f"{game_folder_name} [PORTABLE]")

    if not os.path.isfile(setup_path):
        print(f"Error: Setup.exe not found at '{setup_path}'.")
        return False

    os.makedirs(PORTABLES_FOLDER, exist_ok=True)

    command = [
        setup_path,
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/NOICONS",
        f'/DIR={portable_output_path}',
    ]

    try:
        proc = subprocess.Popen(command)
    except OSError as e:
        print(f"Error: Failed to launch Setup.exe. Details: {e}")
        return False

    # Auto-dismiss the final "Finish" wizard page.
    # /VERYSILENT runs the install without UI, but this installer still pops a
    # Finish window at the end that blocks Setup.exe from exiting. Poll for it
    # (up to FINISH_TIMEOUT_S) and send Enter so the installer closes itself.
    FINISH_TIMEOUT_S = 600
    POLL_INTERVAL_S = 2
    elapsed = 0
    finish_window = None
    while elapsed < FINISH_TIMEOUT_S and proc.poll() is None:
        if gw is not None:
            for w in gw.getAllWindows():
                title = (w.title or "").lower()
                if "setup" in title and w.visible:
                    finish_window = w
                    break
        if finish_window is not None:
            break
        time.sleep(POLL_INTERVAL_S)
        elapsed += POLL_INTERVAL_S

    if finish_window is not None:
        # Send Enter directly to the window via Win32 PostMessage. This works
        # even if the window is minimized or behind other apps - no foreground
        # focus required, so we don't risk pressing Enter into the wrong app.
        hwnd = finish_window._hWnd
        user32 = ctypes.windll.user32
        SW_RESTORE = 9
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        VK_RETURN = 0x0D
        print(f"[voices38] Finish window detected ('{finish_window.title}', hwnd={hwnd}) - posting Enter to close it.")
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.PostMessageW(hwnd, WM_KEYDOWN, VK_RETURN, 0)
        user32.PostMessageW(hwnd, WM_KEYUP, VK_RETURN, 0)
    elif proc.poll() is None:
        print(f"[voices38] Warning: Finish window not detected within {FINISH_TIMEOUT_S}s - sending blind Enter as fallback.")
        pyautogui.press('enter')

    try:
        returncode = proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        print("[voices38] Error: Setup.exe still running 60s after Finish dismiss - killing it.")
        proc.kill()
        return False

    if returncode != 0:
        print(f"Error: Setup.exe failed with exit code {returncode}.")
        return False

    if not os.path.isdir(portable_output_path) or not os.listdir(portable_output_path):
        print(f"Error: Install directory '{portable_output_path}' is empty after silent install.")
        return False

    print(f"Silent install successful: '{portable_output_path}'.")
    return True


def call_copy_crack_script(game_folder_name, release_group):
    try:
        subprocess.run(["python", "copy_crack.py", game_folder_name, release_group], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to execute copy_crack.py. Details: {e}")


def main(game_folder_name, release_group):
    if execute_silent_install(game_folder_name, release_group):
        call_copy_crack_script(game_folder_name, release_group)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python voices38.py <game_folder_name> <release_group>")
    else:
        game_folder_name = sys.argv[1]
        release_group = sys.argv[2]
        main(game_folder_name, release_group)
