# Raspberry Pi pico CAN bus test with Joy-IT expansion board,
#    with or without interrupts.
# Also should work with Waveshare Pico-CAN-B board (but as yet untested)

# Import necessary libraries
import sys, time
from canbus import Can, CanError, CanMsg, CanMsgFlag
from machine import Pin, SPI

POLL = True                # True for polling, False for interrupt

_CANBOARD = const('JI')    # Board choice: 'JI' or 'WS'

if _CANBOARD == 'JI':
   # These pin assignments are appropriate for a RB-P-CAN-485 Joy-IT board
   INT_PIN = 20                  # Interrupt pin for CAN board
   SPI_CS = 17
   SPI_SCK = 18
   SPI_MOSI = 19
   SPI_MISO = 16
elif _CANBOARD == 'WS':
   # These pin assignments are appropriate for a Waveshare Pico-CAN-B board
   INT_PIN = 21                  # Interrupt pin for CAN board
   SPI_CS = 5
   SPI_SCK = 6
   SPI_MOSI = 7
   SPI_MISO = 4
else:
   raise RuntimeError('***%s is an unsupported CAN board***' % _CANBOARD)

prep = SPI(0,              # configure SPI to use correct pins
    sck=Pin(SPI_SCK), mosi=Pin(SPI_MOSI), miso=Pin(SPI_MISO)
)

pico_led = Pin("LED")
pico_led.off()

# Create an instance of the Can class to interface with the CAN bus
can = Can(spics=SPI_CS)

# Initialize the CAN interface.  Begin method initializes the CAN interface
#    and returns a status code
ret = can.begin()
if ret != CanError.ERROR_OK: # Check if the initialization was successful
    print("Error initializing CAN!")
    sys.exit(1)
print("Initialized successfully, %s mode." %
    ('polling' if POLL else 'interrupt')
)

ret = can.setLoopback()
if ret != CanError.ERROR_OK: # Check if the initialization was successful
    print("Error setting CAN loopback!")
    sys.exit(1)

def recv(can):
    # Receive data from the CAN bus; returns an error code and the message
    error, msg = can.recv()
    # Check if data was received without errors
    if error == CanError.ERROR_OK:
        # Print received message details
        # Print the CAN ID in hexadecimal format and whether RTR format
        data = ' '.join(           # put space between every octet
            map(''.join, zip(*[iter(msg.data.hex())]*2))
        )
        print("    CAN id: %#x%s%s (%d bytes): %s" % (
            msg.can_id,
            ' (RTR)' if msg.is_remote_frame else '',
            ' (EFF)' if msg.is_extended_id else '',
            msg.dlc,
            data if msg.dlc > 0 else ''
        ))
    return error

# Data to be sent over the CAN bus in bytes format
data = b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0"
n = 0

# Main loop to send data to the CAN bus
while POLL:
    n += 1
    print('---------------------------------')

    # Create a standard format frame CAN message
    # can_id is the identifier for the CAN message, data is the bytes to send
    msg = CanMsg(can_id=0x123, data=data)
    error = can.send(msg) # Send the CAN message and store the error status
    if error == CanError.ERROR_OK: # Check if the message was sent successfully
        print('{:3d} send normal------------------'.format(n))
    if can.checkReceive():
        if recv(can) != CanError.ERROR_OK:
            print('{:3d} -----------------receive FAIL'.format(n))

    # Create an extended format frame CAN message
    # EFF flag indicates an extended frame format
    msg = CanMsg(can_id=0x12345678, data=data, flags=CanMsgFlag.EFF)
    error = can.send(msg) # Send the CAN message and store the error status
    if error == CanError.ERROR_OK: # Check if the message was sent successfully
        print('{:3d} send EFF---------------------'.format(n))
    if can.checkReceive():
        if recv(can) != CanError.ERROR_OK:
            print('{:3d} -----------------receive FAIL'.format(n))

    pico_led.toggle()
    time.sleep(1) # Wait for 1 second before sending the next set of messages


# Falls through to here if interrupt driven

def trigger(pin):
    global can, POLL
    stat = can.getStatus()       # Order seems to matter here: status first ...
    intr = can.getInterrupts()   # ...then interrupt reg
    if POLL:
        print("Interrupt in polling mode?!  intr %02x stat %02x" % (intr,stat))
        can.clearInterrupts()
        return
    if intr & 0x03 == 0:
        # ignore interrupts except for reading
        print("    >>> Non-read interrupt:  intr %02x stat %02x" % (intr,stat))
        can.clearInterrupts()
        return
    while can.checkReceive():
        if recv(can) != CanError.ERROR_OK:
            print('{:3d} -----------------receive FAIL'.format(n))
    can.clearInterrupts()

print("Interrupt mask is %02x" % can.getInterruptMask())

pin = Pin(INT_PIN,Pin.IN,Pin.PULL_UP)
pin.irq(trigger=Pin.IRQ_FALLING,handler=trigger)

try:
    while not POLL:
        n += 1
        print('---------------------------------')

        # Create a standard format frame CAN message
        # can_id - identifier for the CAN message, data - bytes to send
        print('{:3d} send normal------------------'.format(n))
        msg = CanMsg(can_id=0x123, data=data[:n%9])
        error = can.send(msg) # Send the CAN message and store the error status
        if error != CanError.ERROR_OK:
            # Check if the message was sent successfully
            print('{:3d} -------------------------FAIL'.format(n))

        # Create an extended format frame CAN message
        # EFF flag indicates an extended frame format
        print('{:3d} send EFF---------------------'.format(n))
        msg = CanMsg(can_id=0x12345678, data=data[:n%9], flags=CanMsgFlag.EFF)
        error = can.send(msg) # Send the CAN message and store the error status
        if error != CanError.ERROR_OK:
            # Check if the message was sent successfully
            print('{:3d} -------------------------FAIL'.format(n))

        pico_led.toggle()
        time.sleep(1)

except KeyboardInterrupt:
    pass

pin.irq(handler=None)
