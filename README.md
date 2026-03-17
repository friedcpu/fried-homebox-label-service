# fried-homebox-label-service
> [!WARNING]
> This project was coded with AI assistance. Mainly because I haven't coded much in 20 years and it saved a lot of time.

An external label service for [Homebox](https://homebox.software) inventory management, with optional instructions on how to make homebox use brother-ql-web print server.

Everything shoudl be able to be modified to fit whatever labels you have.

![Label example](example.png)

## Features

- Generates labels at any size Homebox requests
- QR code encodes the full public Homebox URL for the location
- Title auto-shrinks to fit if the name is long
- Fixes relative URLs sent by Homebox (no need to configure `HBOX_BASE_URL`)
- Minimal dependencies — Flask, Pillow, qrcode

## Requirements

- Python 3.11+
- DejaVu Sans fonts (`sudo apt install fonts-dejavu-core`)
- A Brother QL label printer (tested with QL-700)

## Optional
- [FriedrichFroebel/brother_ql_web](https://github.com/FriedrichFroebel/brother_ql_web) for print server

## Installation

```bash
git clone https://github.com/friedcpu/fried-homebox-label-service
cd fried-homebox-label-service
pip install flask pillow qrcode --break-system-packages
sudo apt install fonts-dejavu-core
```

## Configuration

Edit the configuration block at the top of `label_service.py`:

```python
HOMEBOX_PUBLIC_URL = "https://box.example.com"  # Your public Homebox URL
DOMAIN             = "box.example.com"          # Domain shown on label
PORT               = 8099                       # Port to listen on

FONT_SIZE_TITLE    = 160   # Title font size, auto-shrinks if too wide
FONT_SIZE_DOMAIN   = 40    # Domain font size
QR_BORDER          = 3     # Border around QR code in pixels
```

## Running

```bash
python3 label_service.py
```

### Running as a systemd service

Create `/etc/systemd/system/fried-homebox-label-service.service`:

```ini
[Unit]
Description=FRiEd Homebox Label Service
After=network.target

[Service]
User=root
WorkingDirectory=/root/fried-homebox-label-service
ExecStart=/usr/bin/python3 /root/fried-homebox-label-service/label_service.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable fried-homebox-label-service
systemctl start fried-homebox-label-service
```

## Homebox Configuration

Add the following to your Homebox `.env`:

```
HBOX_LABEL_MAKER_LABEL_SERVICE_URL=http://<this-machine-ip>:8099
HBOX_LABEL_MAKER_WIDTH=991
HBOX_LABEL_MAKER_HEIGHT=306
```

Optional, if you are using the brother-ql-web print server:
```
HBOX_LABEL_MAKER_PRINT_COMMAND=curl -s -X POST http://<ip-of-print-server>:8013/api/print/image -F image=@{{.FileName}} -F label_size=29x90
```

Then restart Homebox

## Label Dimensions

Tested with Brother DK-11201 (29mm x 90mm) die-cut labels:

| Parameter | Value |
|-----------|-------|
| Width     | 991px |
| Height    | 306px |
| Label size (brother_ql) | `29x90` |

## Why `HOMEBOX_PUBLIC_URL`?

Homebox sends a relative URL (`/location/uuid`) in the label service request rather than a full URL, because it builds the QR code URL client-side in the browser. This service prepends `HOMEBOX_PUBLIC_URL` to fix the URL before encoding it into the QR code, ensuring the QR code always points to your public Homebox instance regardless of how Homebox was accessed when the label was printed.

## Fonts

- Title: DejaVu Sans Bold
- Domain: DejaVu Sans Oblique

## License

MIT
