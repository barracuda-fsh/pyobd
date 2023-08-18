```
           API
┌───────────────────────┐
│   obd.py / async.py   │
└───┰───────────────────┘
    ┃               ▲
    ┃               ┃
┌───╂───────────────╂───┐      ┌─────────────────┐         ┌────────────────────┐
│   ┃               ┗━━━┿━━━━━━┥                 │◀ ━━━━━━━┥                    │
│   ┃ OBDCommand.py     │      │   decoders.py   │ (maybe) │ UnitsAndScaling.py │
│   ┃               ┏━━━┿━━━━ ▶│                 ┝━━━━━━━ ▶│                    │
└───╂───────────────╂───┘      └─────────────────┘         └────────────────────┘
    ┃               ┃
    ┃               ┃
┌───╂───────────────╂───┐      ┌─────────────────┐
│   ┃               ┗━━━┿━━━━━━┥                 │
│   ┃   elm327.py       │      │    protocol/    │
│   ┃               ┏━━━┿━━━━ ▶│                 │
└───╂───────────────╂───┘      └─────────────────┘
    ┃               ┃
    ▼               ┃
┌───────────────────┸───┐
│        pyserial       │
└───────────────────────┘
       Serial Port
```

Not pictured:

- `commands.py` : defines the various OBD commands, and which decoder they use
- `codes.py` : stores tables of standardized values needed by `decoders.py` (mostly check-engine codes)
- `OBDResponse.py` : defines structures/objects returned by the API in response to a query.
