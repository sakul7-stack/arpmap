# ARPMap

Scan your local network, name your devices, and track them over time — using the
system ARP table. Works on Windows, Linux, and macOS. No dependencies.

## Install

```bash
git clone https://github.com/sakul7-stack/arpmap.git
cd arpmap
python -m arpmap --help        # run from source
pip install -e .               # or install the `arpmap` command
```

Requires Python 3.9+.

## Commands

```bash
arpmap scan                    # list devices on your network
arpmap scan --sweep            # ping the subnet first to find more
arpmap scan --resolve          # also look up hostnames (reverse DNS)
arpmap list                    # show saved devices (no scan)
arpmap name 192.168.1.10 nas   # give a device a name
arpmap ports 192.168.1.10      # scan a device's TCP ports
arpmap stats                   # summary: counts and top vendors
arpmap watch                   # alert when devices join or leave
arpmap watch --log events.jsonl   # ...and record every event to a file
arpmap export --format csv -o devices.csv
```

Run `arpmap` with no command to scan. Add `--json` to `scan`, `list`, `ports`, or
`stats` for machine-readable output. Add `--help` to any command for options.

## Example

```
#   IP             MAC                Name    Hostname   Vendor
--  -------------  -----------------  ------  ---------  ------------------------
0   192.168.1.1    d8:4a:2b:3e:16:f0  router  router     Zyxel Communications
1   192.168.1.10   b8:27:eb:fd:de:48  nas     nas.lan    Raspberry Pi Foundation
```

```
$ arpmap ports 192.168.1.10
Open ports on 192.168.1.10:
      22  ssh
     445  smb
    5000  upnp/http
```

## How it works

`arp -a` is read and parsed into IP/MAC pairs, filtered to your local network,
populated with a vendor name and any name you've set, then saved to
`arpmap_db.json`. `--sweep` pings the subnet first so more devices show up.

ARP only sees devices on your own subnet, and firewalled hosts may not respond to
pings.

## Options

| Option | Description |
| --- | --- |
| `--sweep` | Ping the subnet before scanning (`scan`, `watch`, `export --scan`). |
| `--resolve` | Reverse-DNS resolve hostnames (`scan`, `watch`). |
| `--online` | Look up unknown vendors online. |
| `--all` | Include public / non-private IPs. |
| `--json` | Machine-readable output (`scan`, `list`, `ports`, `stats`). |
| `--log FILE` | Append watch events to a JSON-lines file (`watch`). |
| `--db PATH` | Use a different database file. |
| `--plain` | Plain text tables (no colors). |

## Data

Devices are stored in `arpmap_db.json` by MAC address, with the name, vendor, last
IP, and first/last-seen time. Old `{"mac": "name"}` files are upgraded
automatically.

## Develop

```bash
pip install -e ".[dev]"
pytest -q
```

## License

MIT
