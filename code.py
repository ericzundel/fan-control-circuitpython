"""Code to monitor temperature, display it on an LED, then control a fan"""

import board
import countio
import digitalio
import pwmio
import time

import adafruit_pct2075  # Temperature sensor
from adafruit_ht16k33 import segments  # LED
from sampler import sampler

# This code is written for an Adafruit KB2040

# NUM_TEMP_SAMPLES: the number of temperature samples to keep. Should be
# an even number.
NUM_TEMP_SAMPLES = 10

# NUM_FAN_SAMPLES: the number of samples of the fan counter to keep.
NUM_FAN_SAMPLES = 3

SAMPLE_LEN_SECONDS = 6
HYSTERESIS_SECONDS = 60
SET_POINT_DEGREES_C = 30

# Values for PID control
Kp = 0.8  # I have no idea what I'm doing
Ki = 0.2  # I have no idea what I'm doing

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


def pid_fan_control(temp_samples):
    """Try to compute a percent on using a PID algorithm
    samples is a dictionary of {"ms":elapsed_ms, "temp":temperature, "error":error}
    """
    percent_on_pid = 0
    last_sample = temp_samples.last()
    temperature = last_sample['temp']
    error = last_sample['error']
    print("  >>>PID: Current temp=%f error=%f" % (temperature, error))

    # Compute the proportional output
    output_p = Kp * error

    accumulated_error = sum([val['error'] if 'error' in val else 0 for val in samples])

    # Compute average sample time
    ms_list = temp_samples.by_key('elapsed_ms')
    elapsed_ms = sum(temp_samples.by_key('elapsed_ms'))
    average_sample_time_ms = elapsed_ms / len(ms_list)

    # Compute the integral output
    output_i = Ki * accumulated_error * average_sample_time_ms

    print("  >>>PID: Proportional Output: %d  Integral Output: %d" % (output_p, output_i))

    # I don't want the fan on at all below a certain temp.
    if error < -4:
        return 0
    return percent_on_pid


def naive_fan_control(temp_samples):
    """Very naive algorithm to keep the CPU cool.

    This works, but the fan turns on for a minute,
    then off for a minute. It's distracting. I wish the
    fan would just run slowly at a more or less constant speed.
    """
    percent_on = 0

    last_sample = temp_samples.last()
    temperature = last_sample['temp']

    # Control the fan in terms of percent of full speed
    if temperature < 32:
        percent_on = 0
    elif temperature < 35:
        percent_on = 0.1
    elif temperature < 38:
        percent_on = 0.25
    elif temperature < 41:
        percent_on = 0.75
    else:
        percent_on = 1
    return percent_on


def print_module_members(module):
    """Used to print out the members of a module for debugging"""
    public_attributes = [attr for attr in dir(module) if not attr.startswith("_")]
    attribute_values = {attr: getattr(board, attr) for attr in public_attributes}
    print(attribute_values)


def display_fan_sample_data(fan_count_samples):
    sampled_elapsed_ms = sum(fan_count_samples.by_key('elapsed_ms'))
    sampled_counts = sum([fan_count_samples.by_key('fan_count')])
    # the fan counts 2x per rotation
    sampled_rpm = round((float(sampled_counts) / float(sampled_elapsed_ms)) * 30000.0)
    print(
        "sampled counts=%d elapsed ms=%d avg rpm=%d"
        % (sampled_counts, sampled_elapsed_ms, sampled_rpm)
    )    
def display_temp_sample_data(temp_samples):
    sampled_elapsed_ms = sum(temp_samples.by_key('elapsed_ms'))
    temps = temp_samples.by_key('temp')

    # If we have a full set of samples, we can compute an average temperature.
    # Otherwise, we have just one point.
    if len(temps) is 0:
        average_temp = temperature
    else:
        average_temp = sum(temps) / float(len(temps))

    print(
        "elapsed ms=%d avg temp=%f"
        % (sampled_elapsed_ms, average_temp)
    )


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

temp_samples = sampler(NUM_TEMP_SAMPLES)
fan_speed_samples = sampler(3)

last_fan_change_time = 0

loop_count = 0;
while True:
    loop_count++

    fan_speed_samples.start()
    speed_pin.reset()
    time.sleep(SAMPLE_LEN_SECONDS)
    count = speed_pin.count
    fan_speed_samples.record({'fan_count' : count})


    temperature = pct.temperature

    # The fan counts 2x per rotation, so instead of multiplying
    # by 60 for 60 seconds, multiply by 30
    rpm = count * (30 / SAMPLE_LEN_SECONDS)
    # print("Raw speed_pin count is %d or %d RPM" % (count, rpm))

    # Compute and save the error (temp off from desired temperature)
    # for this sample for PID control
    error = temperature - SET_POINT_DEGREES_C

    # Store away the samples to average over time
    temp_samples.record({
        "ms": elapsed_ms,
        "temp": temperature,
        "error": error,
    }
    display_fan_sample_data(fan_speed_samples)               
    display_temp_sample_data(temp_samples)

    # Alternate display between temp and RPM.
    print("Temperature: %.2f C RPM: %d" % (temperature, rpm))
    if loop_count % 2 == 0:
        display.fill(0)
        display.print("%.0f C" % temperature)
    else:
        display.fill(0)
        display.print("%d" % rpm)

    # TODO: This is quite lame control, but it keeps my cpu cool.
    # Try something smarter like PID
    if time.time() - last_fan_change_time > HYSTERESIS_SECONDS:
        percent_on = naive_fan_control(temp_samples)
        print("Setting fan speed to %.0f" % percent_on)
        fan_pwm.duty_cycle = round(65536 * percent_on)
        last_fan_change_time = time.time()

    # Use PID to attempt to control the fan
    percent_on_pid = pid_fan_control(temp_samples)
    print("Computed PID percent on is %f" % percent_on_pid)

