import os
import sys
import subprocess
from variables import EXTRACTED_ISO, PORTABLES_FOLDER

def execute_unpack(game_folder_name, release_group):
    input_file = os.path.join(EXTRACTED_ISO, game_folder_name, "setup-1.bin")
    output_path = os.path.join(PORTABLES_FOLDER, f"{game_folder_name} [PORTABLE]")
    config_path = os.path.abspath("config.ini")

    with open(config_path, "w") as config_file:
        config_file.write(fr"""\
InputFile={input_file}
OutputPath={output_path}
Password=ABC
CfgFile=.\arc.ini
WorkPath=.\temp
""")

    print(f"Generated config.ini at {config_path}")

    try:
        command = ["unpack", config_path]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, text=True)
        process.communicate(input="\n") 
        process.wait()
        if process.returncode == 0:
            print("Unpack completed successfully.")
            call_copy_crack_script(game_folder_name, release_group)
        else:
            print(f"Unpack failed with return code {process.returncode}.")
    except Exception as e:
        print(f"Error: Failed to execute unpack. Details: {e}")

def call_copy_crack_script(game_folder_name, release_group):
    try:
        subprocess.run(["python", "copy_crack.py", game_folder_name, release_group], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to execute copy_crack.py. Details: {e}")

def main(game_folder_name, release_group):
    execute_unpack(game_folder_name, release_group)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python RUNE_VREX.py <game_folder_name> <release_group>")
    else:
        game_folder_name = sys.argv[1]
        release_group = sys.argv[2]
        main(game_folder_name, release_group)
