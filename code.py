import time
import board
import busio
import adafruit_pct2075  # Temperature sensor
from adafruit_ht16k33 import segments  # LED


# Get all the attributes (values) of the module
module_attributes = dir(board)

# Filter out private attributes (those starting with '_')
public_attributes = [attr for attr in module_attributes if not attr.startswith('_')]

# Create a dictionary with attribute names and their corresponding values
attribute_values = {attr: getattr(board, attr) for attr in public_attributes}

# Pretty print the dictionary
print(attribute_values)

#i2c = busio.I2C(board.SCL, board.SDA)  # uses board.SCL and board.SDA
i2c = board.STEMMA_I2C()
pct = adafruit_pct2075.PCT2075(i2c)

# Create the LED segment class.
# This creates a 7 segment 4 character display:
display = segments.Seg7x4(i2c)

# Clear the display.
display.fill(0)

# Can just print a number
display.print(42)
time.sleep(2)

# Or, can print a hexadecimal value
display.print_hex(0xFF23)
time.sleep(2)

# Or, print the time
display.print("12:30")
time.sleep(2)


while True:
    print("Temperature: %.2f C" % pct.temperature)
    time.sleep(0.5)
    print("Hello World!")
