# Brute Forcing SSH Login

## Objective
Learn how SSH authentication brute-forcing works by building a tool that
tests username/password combinations against a target SSH server, and
understand the real-world compatibility challenges of connecting to older
SSH implementations with modern tooling.

## Tools Used
- Python 3 (`subprocess`, `argparse`)
- `sshpass` — enables non-interactive password authentication with the
  system SSH client
- OpenSSH client (`ssh`)

## ⚠️ Legal & Ethical Notice
Only run this against systems you own or are explicitly authorized to test
(e.g. your own lab VM, such as Metasploitable). Brute-forcing SSH logins
against systems without permission is illegal in most jurisdictions.

## Setup

### 1. Install dependencies
```bash
sudo apt install sshpass -y
```

### 2. Prepare wordlists
Create a username list and a password list in the project directory:

```bash
cat > usernames.txt << 'EOF'
root
admin
administrator
manas
user
ubuntu
kali
msfadmin
test
guest
EOF

cat > wordlist.txt << 'EOF'
123456
password
admin
root
toor
letmein
qwerty
msfadmin
1234
EOF
```

## Usage
```bash
python3 ssh-brute-force.py <target-ip> --userlist usernames.txt --wordlist wordlist.txt --delay 2
```

Example:
```bash
python3 ssh-brute-force.py 192.168.10.7 --userlist usernames.txt --wordlist wordlist.txt --delay 2
```

## How It Works
1. Loads username and password wordlists from file.
2. Iterates through every username/password combination.
3. For each pair, attempts an SSH login using the **system SSH client**
   (via `sshpass`) rather than a pure-Python SSH library, with legacy
   algorithm support explicitly re-enabled:
   - `KexAlgorithms=+diffie-hellman-group1-sha1,diffie-hellman-group14-sha1`
   - `Ciphers=+aes128-cbc,3des-cbc,aes256-cbc`
   - `HostKeyAlgorithms=+ssh-rsa`
4. A successful connection (exit code 0) means valid credentials were found;
   the script stops and reports them.
5. A configurable `--delay` between attempts avoids hammering the target.

## Key Technical Finding
Initial attempts used **Paramiko** (a pure-Python SSH library), which failed
against the lab target with `unknown cipher` / `IncompatiblePeer` errors.
Investigation revealed that modern Paramiko has **fully removed** legacy
algorithms like `diffie-hellman-group1-sha1` — not just disabled them, but
no longer implements the code for them at all, due to their cryptographic
weaknesses.

The system's OpenSSH client, by contrast, still ships with these legacy
algorithms implemented (just disabled by default) and allows re-enabling
them per-connection via `-o` flags with a `+` prefix. Switching from
Paramiko to a `subprocess`-driven `sshpass`/`ssh` approach was required to
successfully authenticate against this older target at all.

This is a legitimate, reportable finding in its own right: **a target
requiring legacy/deprecated SSH algorithms to connect is itself a security
weakness**, independent of whatever credentials are ultimately found.

## Sample Output
```
Target: 192.168.10.7:22
Usernames: 10  |  Passwords: 9  |  Total combinations: 90

[13:00:01] (1/90) Trying root:123456
[13:00:03] (2/90) Trying root:password
...
[13:00:45] (34/90) Trying manas:1234

[+] SUCCESS! Username: manas  Password: 1234
```

## Project Structure
```
ssh-bruteforce/
├── README.md
├── ssh-brute-forcer.py
├── usernames.txt
├── wordlist.txt
```

## What I Learned
- How SSH authentication brute-forcing works mechanically, including the
  combinatorial cost of testing both usernames and passwords
- Why rate-limiting/fail2ban-style protections make brute-forcing
  impractical against properly hardened targets — observed firsthand when
  the target began refusing connections after repeated failed attempts
- That modern SSH libraries (Paramiko) have dropped support for legacy
  cryptographic algorithms (DH group1/14-sha1, 3DES, DSA host keys)
  entirely, while the system OpenSSH client retains — but disables by
  default — support for backward compatibility
- How to debug SSH algorithm negotiation failures using `ssh -vvv` and by
  reading server-advertised algorithm lists directly
- Why using `subprocess` + the system `ssh` binary can be more practical
  than a pure-Python SSH library when targeting legacy systems
