import sys

def append_to_list_file(torrent_name):
    file_name = "LIST.txt"
    try:
        with open(file_name, "a") as file:
            file.write(torrent_name + "\n")
        print(f"'{torrent_name}' has been added to {file_name}.")
    except Exception as e:
        print(f"An error occurred while writing to {file_name}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_torrent_to_list.py <torrent_name>")
    else:
        torrent_name = sys.argv[1]
        append_to_list_file(torrent_name)
