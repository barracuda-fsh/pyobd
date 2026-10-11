# pyOBD

An open-source OBD-II diagnostic app for viewing engine sensors, readiness tests,
trouble codes, freeze-frame data, and live graphs. Includes a demo mode without
an adapter. Modified by FareBrothers, based on
[pyOBD by barracuda-fsh](https://github.com/barracuda-fsh/pyobd) and the original
project by Donour Sizemore. Licensed under GPL-2.0; see [COPYING](COPYING).

## About FareBrothers

Operating since 2023, FareBrothers, LLC develops iOS and Android applications
and maintains automotive software projects including pyOBD, DodgeOBD, and
NissanOBD. Through Great Lakes IT Services, the company also provides website
hosting and game server hosting.

### More from us

Visit [Farebros.com](https://farebros.com) or explore the
[FareBrothers divisions](https://farebros.com/divisions.php). Our mobile apps
are available through the
[Apple App Store](https://apps.apple.com/us/developer/fare-brothers/id1869971574)
and [Google Play](https://play.google.com/store/apps/developer?id=FareBrothers).

## Ubuntu setup

Use Ubuntu's wxPython package to avoid compiling the GUI toolkit. Run these
commands in a terminal:

```bash
sudo apt update
sudo apt install git python3 python3-venv python3-pip python3-wxgtk4.0

git clone https://github.com/alexfare/pyobd.git
cd pyobd
/usr/bin/python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -r requirements/requirements-ubuntu.txt
python pyobd.py
```

If you already downloaded the project, open a terminal in its folder and start
with the virtual environment command. Use `/usr/bin/python3` so the environment
can access Ubuntu's wxPython package. If `.venv` already exists without access
to system packages, use a fresh environment folder instead.

To launch again later, run these commands from the project folder:

```bash
source .venv/bin/activate
python pyobd.py
```

### Optional adapter setup

No new user account is needed. If a USB serial adapter reports **Permission
denied**, give your existing account serial-port access:

```bash
sudo usermod -aG dialout "$USER"
```

Log out and back in for that change to take effect. Do not run the app with sudo.

For Bluetooth adapters, install the pairing tools if needed:

```bash
sudo apt install bluez blueman
```

Pair the adapter before connecting. Bluetooth connections require a serial
profile (SPP/RFCOMM); BLE-only adapters are not supported by this connection mode.

## Windows and macOS

Install Python 3.8 or newer and any driver required by your adapter. From the
project folder, create and activate an environment:

Windows:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python pyobd.py
```

macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python pyobd.py
```

The Python dependencies are wxPython, NumPy, Pint, and pyserial. Ubuntu gets
wxPython through apt; the other setup uses pip. The bundled `obd` module is
included in this repository.

## Connect

Connect an ELM327-compatible adapter to the car and computer, then turn the
ignition on. Open **Configure**, choose a connection type, and click **Connect**:

| Type | Target |
| --- | --- |
| DEMO | Simulated vehicle; no hardware needed |
| SERIAL | Serial port and baud rate, or AUTO |
| WIFI | Adapter host and port, such as `192.168.0.10:35000` |
| BLUETOOTH | Windows COM port or `MAC:channel` for an SPP adapter |
| CUSTOM | pyserial URL, such as `socket://192.168.0.10:35000` |

On Home, **Scan DTC** reads trouble codes, **Services** opens vehicle status,
and **Graphs** opens live plots. Available readings depend on the vehicle;
some require the engine to be running.

### Graph views

Add or remove PIDs before or during playback. Click a PID to select it and click
it again to unselect it; several rows can stay selected for removal. Right-click
a PID to delete selected rows, isolate that PID on the graph, show all PIDs, or
clear the selection. The symbol at the right side of the toolbar switches
between the combined graph and individual scrolling graphs.

This app supports engine OBD-II data. It does not provide manufacturer-specific
ABS, airbag, or body-module diagnostics. Recording and replay are not implemented.
