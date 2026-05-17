"""
Test script for Telegram + Pastebin notification flow.
Simulates a large upload with many parts to test the Pastebin integration.
"""

from telegram_webhook import post_to_telegram


def generate_mock_links(num_parts, service_name):
    """Generate mock upload links for testing with realistic URL lengths."""
    links = []
    for i in range(1, num_parts + 1):
        if service_name == "GoFile":
            links.append(f"Part {i}: https://gofile.io/d/aB3xK9mN2pQ5rT8w")
        elif service_name == "PixelDrain":
            links.append(f"Part {i}: https://pixeldrain.com/u/aB3xK9mN")
        elif service_name == "1fichier":
            links.append(f"Part {i}: https://1fichier.com/?abcdefghijk")
        elif service_name == "Rootz":
            links.append(f"Part {i}: https://rootz.io/d/aB3xK9mN2pQ5rT8w")
    return "\n".join(links)


def generate_mock_magnet():
    """Generate a mock magnet URL."""
    return "magnet:?xt=urn:btih:" + "a" * 40 + "&dn=Test.Game.v1.0-TESTGROUP"


if __name__ == "__main__":
    print("=== Telegram + Pastebin Test ===\n")

    NUM_PARTS = 25

    mock_gofile = generate_mock_links(NUM_PARTS, "GoFile")
    mock_pixeldrain = generate_mock_links(NUM_PARTS, "PixelDrain")
    mock_onefichier = generate_mock_links(NUM_PARTS, "1fichier")
    mock_rootz = generate_mock_links(NUM_PARTS, "Rootz")
    mock_magnet = generate_mock_magnet()

    print(f"Testing with {NUM_PARTS} parts per service (4 services)")
    print(f"This would have been {NUM_PARTS * 4} = {NUM_PARTS * 4} lines of links")
    print(f"Now it'll be 1 Pastebin URL instead\n")

    post_to_telegram(
        "Test.Game.v1.0-TESTGROUP [PORTABLE]",
        mock_magnet,
        mock_gofile,
        mock_pixeldrain,
        mock_onefichier,
        mock_rootz
    )

    print("\n=== Test Complete ===")
