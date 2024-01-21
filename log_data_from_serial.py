"""Run this on the Host and read from the serial port"""

import serial
import sys
import time

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(32)]
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

port_names=serial_ports()
com_port=port_names[-1]

print("Chose port: ", com_port, " from ", port_names, file=sys.stderr)

serial_obj = serial.Serial(com_port) # COMxx  format on Windows
                  # ttyUSBx format on Linux
serial_obj.baudrate = 115200  # set Baud rate to 9600
serial_obj.bytesize = 8   # Number of data bits = 8
serial_obj.parity  ='N'   # No parity
serial_obj.stopbits = 1   # Number of Stop bits = 1

# Read from the serial port and echo to stdout
while True:
    buffer = serial_obj.read_until()
    line = buffer.decode('utf-8')
    if line.startswith("DATA: "):
        print(line[7:], end="")
