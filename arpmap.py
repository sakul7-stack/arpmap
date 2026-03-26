import subprocess
import json
import os

DB_FILE = "arpmap_db.json"


def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)


def get_arp():
    output = subprocess.check_output("arp -a", shell=True).decode()
    lines = output.split("\n")

    devices = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 2 and "-" in parts[1]:
            ip = parts[0]
            mac = parts[1].lower()

            # filter only local network IPs
            if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
                devices.append((ip, mac))

    return devices


def show_devices(devices, db):
    print("\nNetwork Devices:\n")
    for i, (ip, mac) in enumerate(devices):
        name = db.get(mac, "Unknown")
        print(f"[{i}] {ip:15} {mac:20} {name}")
    print()


def add_names(devices, db):
    while True:
        nums = input("Enter device number(s) (comma separated): ").strip()
        if not nums:
            return

        nums = nums.split(",")

        for n in nums:
            try:
                idx = int(n.strip())
                ip, mac = devices[idx]
                name = input(f"Enter name for {ip} ({mac}): ").strip()
                if name:
                    db[mac] = name
                    print(f"Saved: {name}")
            except:
                print(f"Invalid selection: {n}")

        more = input("Add another device? (Y/n): ").strip().lower()
        if more == "n":
            break


def main():
    db = load_db()
    devices = get_arp()

    show_devices(devices, db)

    choice = input("Do you want to name devices? (Y/n): ").strip().lower()

    if choice == "" or choice == "y":
        add_names(devices, db)
        save_db(db)
        print("All changes saved.")

    print("\nFinal Mapping:\n")
    show_devices(devices, db)


if __name__ == "__main__":
    main()