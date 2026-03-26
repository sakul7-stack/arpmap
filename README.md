# ARPMap

ARPMap is a Python utility to scan your local network using the ARP table, list devices, and allow you to assign human-readable names to each device. The device information is stored locally in a JSON database for future reference.

---

## Working

- Scan local network devices using ARP (`arp -a`).
- Automatically filter local IP addresses (`192.168.x.x`, `10.x.x.x`, `172.x.x.x`).
- Assign custom names to devices (by MAC address).
- Save device mapping in a JSON file (`arpmap_db.json`).
- View all devices and their assigned names in a neat table.

---


## Installation

1. Clone or download the repository:

```bash
git clone <repository-url>
cd arpmap