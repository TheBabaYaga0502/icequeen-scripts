import os
import sys
import subprocess
from variables import EXTRACTED_ISO, PORTABLES_FOLDER

# Resolve arc.exe next to this script. Python's subprocess on Windows does not
# search the current working directory for executables, so a bare "arc" call
# fails if the caller's PATH doesn't include this folder.
ARC_EXE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arc.exe")


def execute_arc_extraction(game_folder_name, release_group):
    # voices38 releases ship a custom GUI installer (Setup.exe + Setup.dll) that
    # wraps a FreeArc archive (Setup-1.bin, with optional Setup-2.bin, ... as
    # continuation parts). The GUI rejects any silent-install switches, so we
    # skip Setup.exe entirely and extract the FreeArc payload directly with the
    # bundled arc.exe. FreeArc auto-follows multi-part .bin continuations when
    # pointed at Setup-1.bin.
    extracted_folder = os.path.join(EXTRACTED_ISO, game_folder_name)
    bin_file_path = os.path.join(extracted_folder, "Setup-1.bin")
    portable_output_path = os.path.join(PORTABLES_FOLDER, f"{game_folder_name} [PORTABLE]")

    if not os.path.isfile(bin_file_path):
        print(f"Error: FreeArc payload not found at '{bin_file_path}'.")
        return False

    os.makedirs(PORTABLES_FOLDER, exist_ok=True)

    command = [
        ARC_EXE, "x", "-y",
        f"-dp{portable_output_path}",
        bin_file_path,
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: arc.exe extraction failed. Details: {e}")
        return False
    except OSError as e:
        print(f"Error: Failed to launch arc.exe. Details: {e}")
        return False

    if not os.path.isdir(portable_output_path) or not os.listdir(portable_output_path):
        print(f"Error: Install directory '{portable_output_path}' is empty after extraction.")
        return False

    print(f"FreeArc extraction successful: '{portable_output_path}'.")
    return True


def call_copy_crack_script(game_folder_name, release_group):
    try:
        subprocess.run(["python", "copy_crack.py", game_folder_name, release_group], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to execute copy_crack.py. Details: {e}")


def main(game_folder_name, release_group):
    if execute_arc_extraction(game_folder_name, release_group):
        call_copy_crack_script(game_folder_name, release_group)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python voices38.py <game_folder_name> <release_group>")
    else:
        game_folder_name = sys.argv[1]
        release_group = sys.argv[2]
        main(game_folder_name, release_group)
