# pyOBD Improvement and Swift Rebuild Roadmap

This roadmap has two goals:

1. Make the current Python app dependable and easier to maintain.
2. Build a native Swift version without guessing at the ELM327 and OBD-II behavior.

The Python app should remain usable while the Swift app is developed. The Swift
version should reuse protocol knowledge and recorded adapter responses, not the
Python UI architecture.

## What to improve first in pyOBD

### 1. Protect the behavior with tests

There are currently no active automated tests. Before restructuring the app,
add tests for the parts most likely to cause incorrect vehicle data:

- ELM327 initialization and prompt handling
- supported-PID discovery
- Mode 01 live-data decoding
- Mode 02 freeze-frame decoding
- Mode 03 trouble-code decoding
- Mode 04 clear-code behavior
- unit conversion and formatting
- connection target parsing for serial, Wi-Fi, Bluetooth, custom URLs, and demo

Store sanitized ELM327 conversations as text fixtures. Include normal replies,
multi-ECU replies, `NO DATA`, `SEARCHING...`, malformed frames, timeouts, and
adapter disconnects. The demo connection is useful for the UI, but fixed
transcripts are better for repeatable protocol tests.

**Exit condition:** tests can run without a car or adapter and the CI workflow
actually executes them.

### 2. Split the 4,300-line application module

`pyobd.py` currently combines UI construction, configuration, threads,
connection state, polling, formatting, graphs, and event routing. Split it into
small modules with clear ownership:

```text
pyobd/
  app.py                 application startup
  models.py              readings, DTCs, connection state
  settings.py            loading, validation, and saving
  services/
    connection.py        connect, reconnect, disconnect
    polling.py           supported PID polling and scheduling
    diagnostics.py       DTC, freeze frame, readiness tests
  transports/
    base.py              transport interface
    serial.py
    tcp.py
    demo.py
  ui/
    main_window.py
    home.py
    status.py
    sensors.py
    diagnostics.py
    graphs.py
```

The UI should receive typed state and call service methods. It should not know
how an ELM command is framed or how a port is opened.

**Exit condition:** the main UI module contains screen assembly and event
handlers only; the protocol layer can run headlessly.

### 3. Replace fragile thread control

The current worker uses numeric control flags, broad exception handling, and an
immediate `os._exit(0)`. Replace those with:

- a stop event and an explicit connection state machine
- one owner for the active adapter connection
- bounded reads and cancellation
- clean worker shutdown before the window closes
- structured errors that can be shown to the user and written to a log
- reconnect backoff instead of tight repeated attempts

Suggested connection states are `disconnected`, `discovering`, `connecting`,
`initializingAdapter`, `discoveringVehicle`, `connected`, `reconnecting`, and
`failed`.

### 4. Improve the product experience

After the internals are stable:

- Add a first-run connection wizard with adapter-specific help.
- Show a useful reason when connection fails: port busy, permission denied,
  adapter found but ECU unavailable, unsupported BLE device, or network timeout.
- Remember recent adapters and allow one-click reconnect.
- Add searchable sensors, favorites, and configurable polling groups.
- Allow CSV and JSON recording with timestamps and units.
- Add graph pause, range selection, multiple scales, and export.
- Add DTC descriptions with a clear warning before Mode 04 clears codes and
  freeze-frame data.
- Add a diagnostic support bundle containing app version, platform, adapter
  identity, protocol, and sanitized logs.
- Use platform theme colors everywhere and verify light, dark, and high-contrast
  modes.

### 5. Make releases repeatable

- Define the supported Python and operating-system versions.
- Package the application rather than asking users to run a loose script.
- Run formatting, static checks, unit tests, and fixture tests in CI.
- Build release artifacts for Windows, macOS, and the chosen Linux targets.
- Add a changelog, semantic versions, and a short hardware compatibility list.
- Test releases with at least one USB adapter, one Wi-Fi adapter, demo mode, and
  each supported Bluetooth path.

## Native Swift rebuild

### Product scope

Build one Swift package containing the OBD engine and one SwiftUI app that can
target iPhone, iPad, and Mac. Start with iOS and macOS if both platforms matter,
but do not promise the same hardware transports on each platform.

| Transport | iPhone/iPad | Mac | Recommendation |
| --- | --- | --- | --- |
| Wi-Fi ELM327 over TCP | Yes | Yes | Support in the first release |
| BLE adapter with documented GATT service | Yes | Yes | Support selected tested adapters |
| Generic Bluetooth Classic SPP | No general-purpose API | Possible with platform-specific work | Do not make this an iOS launch requirement |
| MFi Bluetooth Classic/Lightning accessory | Only with supported accessory protocols | Limited use case | Add only for a specific partner/device |
| USB serial | Restricted/accessory-dependent | Yes | Add to the Mac target after Wi-Fi |
| Demo/replay | Yes | Yes | Build first |

Apple's Core Bluetooth framework is for BLE peripherals. Bluetooth Classic
accessories exposed through External Accessory require supported MFi protocols.
This makes a documented BLE adapter or a Wi-Fi adapter the practical choice for
an App Store iPhone app.

### Proposed Swift architecture

```text
PyOBDKit (Swift package)
  Models/
    Measurement, PID, DTC, ECU, VehicleStatus
  Transport/
    OBDTransport protocol
    TCPTransport
    BLETransport
    ReplayTransport
    MacSerialTransport
  ELM327/
    ELM327Session actor
    CommandFramer
    ResponseTokenizer
    AdapterCapabilities
  OBDII/
    PIDCatalog
    PIDDecoder
    DTCDecoder
    SupportedPIDDiscovery
  Services/
    VehicleSession actor
    PollScheduler
    RecordingService

PyOBDApp (SwiftUI)
  Connection/
  Dashboard/
  Sensors/
  Diagnostics/
  FreezeFrame/
  Graphs/
  Settings/
```

Use a transport protocol so the OBD engine sees only an asynchronous byte
stream. Keep all command sequencing inside an actor; an ELM327 adapter should
never receive overlapping commands. Expose typed readings to SwiftUI using an
observable app model. Use Swift Charts for live graphs and store recordings in
a documented, exportable format.

### Delivery phases

#### Phase 0 — Compatibility specification (1–2 weeks)

- Inventory every feature and PID currently used by the Python app.
- Select the minimum supported Apple OS versions.
- Choose the first two physical adapters: one Wi-Fi and one documented BLE.
- Capture sanitized sessions from demo mode and real adapters.
- Write expected decoded values for those sessions.

**Gate:** a written compatibility matrix and reusable protocol fixtures exist.

#### Phase 1 — Swift protocol engine (2–4 weeks)

- Create `PyOBDKit` as a standalone Swift package.
- Implement replay transport, response tokenization, ELM initialization, PID
  support discovery, Mode 01 decoding, DTC decoding, and units.
- Run the Python fixtures through Swift tests and compare expected results.

**Gate:** the Swift package passes fixture tests without UI or hardware.

#### Phase 2 — Wi-Fi MVP (2–3 weeks)

- Implement the TCP transport with Apple's Network framework.
- Build SwiftUI connection, status, sensor list, DTC, and basic graph screens.
- Add cancellation, timeouts, disconnect handling, and useful error messages.
- Test on iPhone, iPad, Mac, and at least one real vehicle or bench simulator.

**Gate:** connect, identify the protocol, display stable live data, read DTCs,
and disconnect cleanly.

#### Phase 3 — BLE and polished diagnostics (3–5 weeks)

- Implement BLE discovery and transport for explicitly supported adapters.
- Add readiness tests, freeze-frame data, favorites, recordings, export, and
  richer graphs.
- Add clear-code confirmation and explain its effects.
- Validate background/foreground transitions and reconnection behavior.

**Gate:** each advertised adapter passes a repeatable hardware test checklist.

#### Phase 4 — Mac USB and release preparation (2–4 weeks)

- Add a macOS serial transport if Mac USB support is required.
- Add privacy strings, accessibility labels, localization-ready text, app
  logging, support bundle export, and a privacy policy.
- Run TestFlight, crash testing, App Store review preparation, and final vehicle
  testing.

**Gate:** no known data-decoding errors, no UI hangs during disconnects, and all
supported hardware paths have release test evidence.

### What to reuse and what to rewrite

Reuse:

- OBD command definitions and formulas after verifying them against fixtures
- DTC descriptions and protocol knowledge, subject to license attribution
- demo scenarios and sanitized adapter transcripts
- product behavior that users already understand

Rewrite:

- the UI and navigation
- threading and connection lifecycle
- transport implementations
- configuration storage
- graphing and recording
- error handling

Do not translate `pyobd.py` line by line. That would preserve its coupling and
make Swift concurrency harder to reason about.

## Recommended order

Start with the Python fixture suite and module split. In parallel with normal
Python maintenance, create `PyOBDKit` and make replay mode its first transport.
Do not begin BLE work until a specific adapter and its GATT characteristics are
documented and available for testing. Ship the Swift MVP with Wi-Fi and demo
mode, then add BLE adapters individually as verified compatibility targets.

