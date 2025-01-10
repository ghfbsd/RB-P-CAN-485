# Using the RB-P-CAN-485 Raspberry Pi expansion board with MicroPython

The board is an expansion board for the Raspberry Pi pico (RPP).
It contains a CAN bus interface and an RS485 interface that the RPP can drive
to interact with peripherals.
The CAN bus is the main focus of this repository.

The documentation for this board is incomplete.
This describes how I was able to set one up and get it to work with a CAN bus.

Driving the CAN and RS485 interfaces with MicroPython requires a Python library.
The board's documentation reports that it is available from Longlan Labs, and
gives examples of its use; the RS485 example works immediately.
The CAN bus use example does not work because the code makes assumptions about
which RPP GPIO pins drive the board that conflict with the board's wiring
layout (see below).
I extended the code to expand its diagnostic and operation capabilities.
You can get the updated code from the
[MicroPython_CAN_BUS_MCP2515](https://github.com/ghfbsd/MicroPython_CAN_BUS_MCP2515) repository, which is imported under the *canbus* name in Python.
(For reference, the original Longlan Labs version is
[here](https://github.com/Longan-Labs/MicroPython_CAN_BUS_MCP2515).)

## Connections

The board's documentation tells you how to use the external connections for
USB, power, CAN and 485 I/O.  Refer to that material for details.
USB power to either the board or to the RPP will run both.
However, only the RPP USB connection will talk to your computer's
development platform/IDE, so use that one.

Note that there are two further connections that are not documented but visible
on the board (see map below):  CS and INT.  These are both crucial to effective
use of the CAN bus.

```
Exp. board                         Exp. board
header--+   +-Raspberry PI pico-+   +--header
        |   |                   |   |
        |   |                   |   |
        V   V      --USB--      V   V
                   connect
        O   1 GP0          VBUS 40  O
        O   2 GP1          VSYS 39  O
        O   3 gnd           gnd 38  O
        O   4 GP2        3V3_EN 37  O
        O   5 GP3      3V3(OUT) 36  O
        O   6 GP4       ADC_REF 35  O
        O   7 GP5          GP28 34  O
        O   8 gnd    analog gnd 33  O
        O   9 GP6          GP27 32  O
        O  10 GP7          GP26 31  O
        O  11 GP8           RUN 30  O
        O  12 GP9          GP22 29  O
        O  13 gnd           gnd 28  O
        O  14 GP10         GP21 27  O
        O  15 GP11         GP20 26  O
        O  16 GP12         GP19 25  O
        O  17 GP13         GP18 24  O
        O  18 gnd           gnd 23  O
        O  19 GP14         GP17 22  O
        O  20 GP15         GP16 21  O

                         O INT
                         O CS
```

This board is based on the [MCP2515 CAN controller](https://ww1.microchip.com/downloads/en/DeviceDoc/MCP2515-Stand-Alone-CAN-Controller-with-SPI-20001801J.pdf).
The MCP2515 uses an SPI bus to interact with the RPP.
The relevant SPI bus connections are the CS line, the SCK line, the SI line and the SO line.
These must be routed to the correct GPIO pins on the RPP for proper operation.

The board exposes the SPI lines as follows:

- SCK on pin 24 (GP18)
- SI on pin 25 (GP19)
- SO on pin 21 (GP16)
- CS on the board hole labeled "CS"

Due to there being no connection of the CS line to any header/socket on the RPP,
the board is unusable as a CAN interface as delivered.
With a few short wire jumpers installed, it *will* work, however.
Connect them as follows:

- pin 24 (GP18) -> pin 4 (GP2): SCK line
- pin 25 (GP19) -> pin 5 (GP3): SI line
- pin 21 (GP16) -> pin 6 (GP4): SO line
- CS hole -> pin 11 (GP9): CS line
- INT hole -> pin 20 (GP15): interrupt line

These jumper the SPI bus lines to the GPIO pins expected by the *canbus*
library.
*canbus* is agnostic about interrupt-driven MC2515 use, so the interrupt
pin's jumper connection is your choice; 15 is used here (see the `INT_PIN`
value in `can_test_int.py` for its definition).
Now the board is ready for use with the RPP.

## Preparation

* Plug a RPP into the sockets/headers on the board.

* Connect to your RPP with the USB cable.

* Get your favorite RPP development platform/IDE running (
[rshell](https://forum.micropython.org/viewtopic.php?t=708) and
[Thonny](https://thonny.org/) seem to be popular choices).

* Download *canbus* to the RPP (with _rshell_, use `rsync canbus /pyboard` after
`cd MicroPython_CAN_BUS_MCP2515`; with _Thonny_, use
the `Tools -> Manage Packages menu`, search for "MicroPython_CAN_BUS_MCP2515" and install it to the target board).

* Download the *picozero* Python package to your RPP.
You can get *picozero* [here](https://projects.raspberrypi.org/en/projects/introduction-to-the-pico/4).

* Look at the `can_test_intr.py` source code.
There are two ways of running the CAN bus:
synchronously/polling or interrupt-driven.
The simplest is by synchronous polling.
Look at the source code and make sure the `POLL` variable has the value `True`.
If not, change it and save the updated code.

* Download `can_test_intr.py` to the RPP (with _rshell_ use `cp`;
not sure what to do for _Thonny_).

* Run `can_test_intr.py`.
Compare your output with the sample output below.
The program will flash the LED on the RPP once a second.
It also runs forever, and you must interrupt it to stop it.

### Sample output in synchronous/polling mode.
```

Initialized successfully, polling mode.
CAN status reg: 00 (***should be 40 [loopback mode]; ignoring***)
---------------------------------
  1 send normal------------------
  1 send EFF---------------------
---------------------------------
  2 send normal------------------
  2 send EFF---------------------
---------------------------------
  3 send normal------------------
  3 send EFF---------------------
---------------------------------
  4 send normal------------------
  4 send EFF---------------------
---------------------------------
  5 send normal------------------
  5 send EFF---------------------
---------------------------------
  ...
```
### Sample output in interrupt mode.
```

Initialized successfully, interrupt mode.
CAN status reg: 00 (***should be 40 [loopback mode]; ignoring***)
Interrupt mask is a3
---------------------------------
  1 send normal------------------
    CAN id: 0x123 (1 bytes): 12
  1 send EFF---------------------
    CAN id: 0x12345678 (EFF) (1 bytes): 12
---------------------------------
  2 send normal------------------
    CAN id: 0x123 (2 bytes): 12 34
  2 send EFF---------------------
    CAN id: 0x12345678 (EFF) (2 bytes): 12 34
---------------------------------
  3 send normal------------------
    CAN id: 0x123 (3 bytes): 12 34 56
  3 send EFF---------------------
    CAN id: 0x12345678 (EFF) (3 bytes): 12 34 56
---------------------------------
  4 send normal------------------
    CAN id: 0x123 (4 bytes): 12 34 56 78
  4 send EFF---------------------
    CAN id: 0x12345678 (EFF) (4 bytes): 12 34 56 78
---------------------------------
  5 send normal------------------
    CAN id: 0x123 (5 bytes): 12 34 56 78 9a
  5 send EFF---------------------
    CAN id: 0x12345678 (EFF) (5 bytes): 12 34 56 78 9a
---------------------------------
  6 send normal------------------
    CAN id: 0x123 (6 bytes): 12 34 56 78 9a bc
  6 send EFF---------------------
    CAN id: 0x12345678 (EFF) (6 bytes): 12 34 56 78 9a bc
---------------------------------
  7 send normal------------------
    CAN id: 0x123 (7 bytes): 12 34 56 78 9a bc de
  7 send EFF---------------------
    CAN id: 0x12345678 (EFF) (7 bytes): 12 34 56 78 9a bc de
---------------------------------
  8 send normal------------------
    CAN id: 0x123 (8 bytes): 12 34 56 78 9a bc de f0
  8 send EFF---------------------
    CAN id: 0x12345678 (EFF) (8 bytes): 12 34 56 78 9a bc de f0
---------------------------------
  9 send normal------------------
    CAN id: 0x123 (0 bytes):
  9 send EFF---------------------
    CAN id: 0x12345678 (EFF) (0 bytes):
---------------------------------
 10 send normal------------------
    CAN id: 0x123 (1 bytes): 12
 10 send EFF---------------------
    CAN id: 0x12345678 (EFF) (1 bytes): 12
 ...
```

## Notes

- Some MCP2515 clones apparently do not report the interface status
correctly (see the message `***should be 40 [loopback mode]; ignoring***`).
For the test program, this is harmless.

- The program runs forever; you must interrupt it to stop it.

# How it works

Firstly, the test program configures the CAN interface by putting it into
_loopback mode_.  This essentially connects the output of the bus to its
own input, and therefore you don't need to have a running CAN bus to hook
into to test out the board.

In synchronous/polling mode, the program creates a CAN message and sends it.
It pays no attention to the result except to check that it was transmitted
without an error.

The program's operation in interrupt mode is more interesting.
First, it defines a Python function called `trigger` to be called whenever
there is new data received on the CAN bus.
Then the program makes CAN messages of various lengths ranging from 0 to 8
bytes, sending them out and listening for the result.
When a message is available to be read, the interrupt causes `trigger` to
be called, which dumps the content of the message.
The program shows the received message and its payload after each
interrupt.
Due to the loopback interface, it actually *receives* the message before it
knows whether it was *sent* properly.
(If it isn't sent properly, the program will complain and you probably
won't see the message either.)