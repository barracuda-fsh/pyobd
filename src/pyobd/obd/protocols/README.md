Notes
-----

This code is meant to abstract the transport and physical layers of an OBD-II connection. Each protocol is a callable object, and accepts a list of strings as input (from the adapter), and returns a list of parsed `Message` objects. The `Message.data` field will contain a bytearray, corresponding to the application layer data returned by the command. This implementation is specific to the formatting of the ELM327 chip inside the adapter.

For example, these are the resultant `Message.data` fields for some single frame messages:

```
A CAN Message:
7E8 06 41 00 BE 7F B8 13
       [     data      ]

A J1850 Message:
48 6B 10 41 00 BE 7F B8 13 FF
         [       data       ]
```

The parsing itself (invoking `__call__`) is stateless. The only stateful part of a `Protocol` is the `ECU_Map`. These objects correlate OBD transmitter IDs (`tx_id`'s) with the various ECUs in the car. This way, `Message` objects can be marked with ECU constants such as:

- ENGINE
- TRANSMISSION

Ideally they'd be constant across all protocols and vehicles, but, they're aren't. To help quell the madness, each protocol can define default `tx_id`'s for various ECUs. When `Protocol` objects are constructed, they accept a raw OBD response (from a 0100 command) to check these mappings. If the engine ECU can't be identified, there's fallback logic to select its `tx_id` from the 0100 response.

Subclassing `Protocol`
---------------------

All protocol objects must implement the following:

----------------------------------------

#### parse_frame(self, frame)

Recieves a single `Frame` object with `Frame.raw` preloaded with the raw line recieved from the car (in string form). This function is responsible for parsing `Frame.raw` into a bytearray, and filling the remaining fields in the `Frame` object. If the frame is invalid, or the parse fails, this function should return `False`, and the frame will be dropped.

----------------------------------------

#### parse_message(self, message)

Recieves a single `Message` object with `Message.frames` preloaded with a list of `Frame` objects. This function is responsible for assembling the frames into the `Message.data` field in the `Message` object. This is where multi-line responses are assembled. If the message is found to be invalid, this function should return `False`, and the entire message will be dropped.

----------------------------------------

#### Normal TX_ID's

Each protocol has a different way of notating the ID of the transmitter, so each subclass must set its own attributes denoting standard `tx_id`'s. Refer to the base `Protocol` class for a list of these attributes. Currently, they are:

- `TX_ID_ENGINE`


Inheritance structure
---------------------

```
Protocol
    UnknownProtocol
    LegacyProtocol
        SAE_J1850_PWM
        SAE_J1850_VPM
        ISO_9141_2
        ISO_14230_4_5baud
        ISO_14230_4_fast
    CANProtocol
        ISO_15765_4_11bit_500k
        ISO_15765_4_29bit_500k
        ISO_15765_4_11bit_250k
        ISO_15765_4_29bit_250k
        SAE_J1939
```
