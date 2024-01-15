"""Code to monitor temperature, display it on an LED, then control a fan"""

import board
import countio
import digitalio
import pwmio
import time

import adafruit_pct2075  # Temperature sensor
from adafruit_ht16k33 import segments  # LED

# This code is written for an Adafruit KB2040
NUM_SAMPLES = 3
SAMPLE_LEN_SECONDS = 2
HYSTERESIS_SECONDS = 60

# Wiring
# LED and temperature sensor is on the Stemma I2C port
# The fan PWM and speed pins are connected to D8 and D9
#
# Power for the fan is 12V. This is provided by a boost converter.
# The boost converter is connected to a Micro USB port which also provides
# power to the KB2040 through a diode to the RAW pin. This allows you to
# also connect a USB port to the KB2040 for debugging while the fan
# is plugged in.

# GND pin 1
# 12V pin 2
# The green wire on my fan (pin 3) senses a rotation of the fan
# The blue wire on my fan (pin4) is PWM control
speed_pin = countio.Counter(board.D9, edge=countio.Edge.RISE, pull=digitalio.Pull.UP)

# I assume the blue wire is PWM control
# pwm_pin = digitalio.DigitalInOut(board.D9)
# pwm_pin.direction = digitalio.Direction.INPUT

fan_pwm = pwmio.PWMOut(board.D7, frequency=1000)

# freq=1000, duty_cycle 75% quiet, lots of air
# freq=1000, duty_cycle 16000/30% small air movement, little sound
# freq=1000, duty_cycle 8000/13% a little air movement, no sound
# freq=1000, duty_cycle 4000/8% fan spins very slowly

def print_module_members(module):
    """Used to print out the members of a module for debugging"""
    public_attributes = [attr for attr in dir(module) if not attr.startswith("_")]
    attribute_values = {attr: getattr(board, attr) for attr in public_attributes}
    print(attribute_values)

# What pins should I use for I2C? Depends on the board.
# print_module_members(board)
# i2c = busio.I2C(board.SCL, board.SDA)  # uses board.SCL and board.SDA
i2c = board.STEMMA_I2C()

# Create the LED segment class.
display = segments.Seg7x4(i2c)

# Clear the display.
display.fill(0)

# Init the temperature sensor
pct = adafruit_pct2075.PCT2075(i2c)

speed_pin.reset()

sample = 0
fan_sample_counts = [0 for i in range(NUM_SAMPLES)]
fan_sample_ms = [0 for i in range(NUM_SAMPLES)]

last_fan_change_time = 0

while True:
    sample = sample % NUM_SAMPLES

    speed_pin.reset()
    start_time = time.monotonic_ns()
    time.sleep(SAMPLE_LEN_SECONDS)
    count = speed_pin.count

    end_time = time.monotonic_ns()
    elapsed_ms = (end_time - start_time) / 1000000

    # Store away the samples to average over time
    fan_sample_ms[sample] = elapsed_ms
    fan_sample_counts[sample] = count

    # the fan counts 2x per rotation, so instead of multiplying
    # by 60 for 60 seconds, multiply by 30
    rpm = (count * (30/SAMPLE_LEN_SECONDS))

    print("Raw speed_pin count is %d or %d RPM" % (count, rpm))

    sampled_counts = sum(fan_sample_counts)
    sampled_elapsed_ms = sum(fan_sample_ms)
    # the fan counts 2x per rotation
    sampled_rpm = ((float(sampled_counts) / float(sampled_elapsed_ms)) * 30000.0)
    print(
        "sampled counts = %d elapsed_ms = %d averaged speed is %f"
        % (sampled_counts, sampled_elapsed_ms, sampled_rpm)
    )
    sample += 1

    temperature = pct.temperature

    # Display temperature
    print("Temperature: %.2f C" % temperature)
    display.print("%.0f C" % temperature)

    # TODO: This is quite lame control, but it keeps my cpu cool. Try something smarter like PID
    if (time.time() - last_fan_change_time > HYSTERESIS_SECONDS):
        # Control the fan
        if (temperature < 32):
            percent_on = 0
        elif(temperature <35):
            percent_on = .1
        elif(temperature <38):
            percent_on = .25
        elif(temperature <41):
            percent_on = .75
        else:
            percent_on = 1

        print("Setting fan speed to %02f" % percent_on)
        fan_pwm.duty_cycle = round(65536 * percent_on)
        last_fan_change_time = time.time()
