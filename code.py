"""Code to monitor temperature, display it on an LED, then control a fan"""

import board
import countio
import digitalio
import pwmio
import time
from microcontroller import watchdog as w
from watchdog import WatchDogMode

import adafruit_pct2075  # Temperature sensor
from adafruit_ht16k33 import segments  # LED
from sampler import sampler

# This code is written for an Adafruit KB2040

# NUM_TEMP_SAMPLES: the number of temperature samples to keep. Should be
# an even number.
NUM_TEMP_SAMPLES = 10

# NUM_FAN_SAMPLES: the number of samples of the fan counter to keep.
NUM_FAN_SAMPLES = 3

# SAMPLE_LEN_SECONDS: # of seconds to delay before collecting a fan/temperature sample.
# Must be < WATCHDOG_TIMEOUT_SECS
SAMPLE_LEN_SECONDS = 3

# HYSTERESIS_SECONDS: # of seconds to wait before making a change to the fan output
HYSTERESIS_SECONDS = 60

# SET_POINT_DEGREES_C: Input to the PID algorithm
SET_POINT_DEGREES_C = 30

# WATCHDOG_TIMEOUT_SECS: The number of seconds to check to see if the controller is hung
WATCHDOG_TIMEOUT_SECS = 5

# Kp, Ki, Kd, Constant Values for PID control
# .0666 Roughly scales between .1 at 32 degrees and 1 at 45 degrees.
# .8 is intended to usethat for 80% of calculation
Kp = 0.8 * 0.0666

# .0666 / 100000 seems to scale down to between .1 and 1
# .2 is intended to account for rougly 20% of calculation of speed.
Ki = (0.2 * 0.0666) / 100000

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


def pid_fan_control(temperature, temp_samples):
    """Try to compute a percent on using a PID algorithm
    samples is a dictionary of {"ms":elapsed_ms, "temp":temperature, "error":error}
    """
    percent_on_pid = 0

    error = temperature - SET_POINT_DEGREES_C
    print("  >>>PID: Current temp=%f error=%f" % (temperature, error))

    # Compute the proportional output
    output_p = Kp * error

    accumulated_error = sum(temp_samples.by_key("error"))

    # Compute average sample time from history
    # Technically this skips the last sample, but
    # I think that's ok as we are just using it for the integral part.
    ms_list = temp_samples.by_key("elapsed_ms")
    elapsed_ms = sum(temp_samples.by_key("elapsed_ms"))
    average_sample_time_ms = elapsed_ms / len(ms_list)

    # Compute the integral output
    output_i = Ki * accumulated_error * average_sample_time_ms

    # Clamp the influence of output_i to 20% of total
    if output_i > 0.2:
        output_i = 0.2
    elif output_i < -0.2:
        output_i = 0.2
    percent_on_pid = output_p + output_i
    print(
        "  >>>PID: Proportional Output: %f  Integral Output: %f Total Output: %f"
        % (output_p, output_i, percent_on_pid)
    )

    # Limit the output to between .1 and 1
    if percent_on_pid < 0.1:
        return 0
    elif percent_on_pid > 1:
        return 1
    return percent_on_pid


def simple_fan_control(temperature):
    """Very naive algorithm to keep the CPU cool.

    Defines a ttep function based on current temperature.

    This works, but the fan turns on for a minute,
    then off for a minute. It's distracting. I wish the
    fan would just run slowly at a more or less constant speed.
    """
    percent_on = 0

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


# Turn on the hardware watchdog. This restarts the microcontroller if the code hangs.
#w.timeout = WATCHDOG_TIMEOUT_SECS
#w.mode = WatchDogMode.RAISE

# The LED and temp sensor run through i2C
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


loop_count = 0
while True:
    # Pet the nice watchdog.
    w.feed()

    loop_count = loop_count + 1

    fan_speed_samples.start()
    speed_pin.reset()
    time.sleep(SAMPLE_LEN_SECONDS)
    count = speed_pin.count
    fan_speed_samples.record({"fan_count": count})

    temperature = pct.temperature

    # The fan counts 2x per rotation, so instead of multiplying
    # by 60 for 60 seconds, multiply by 30
    rpm = count * (30 / SAMPLE_LEN_SECONDS)
    # print("Raw speed_pin count is %d or %d RPM" % (count, rpm))

    # Compute and save the error (temp off from desired temperature)
    # for this sample for PID control
    error = temperature - SET_POINT_DEGREES_C

    # Compute the output fan speed two different ways
    fan_output_simple = simple_fan_control(temperature)
    fan_output_pid = pid_fan_control(temperature, temp_samples)

    # Store away the samples to average over time
    temp_samples.record(
        {
            "temp": temperature,
            "error": error,
            "fan_output_simple": fan_output_simple,
            "fan_output_pid": fan_output_pid,
        }
    )

    print("DATA: ", temp_samples.last())

    # Alternate display between temp and RPM.
    print("Temperature: %.2f C RPM: %d" % (temperature, rpm))
    if loop_count % 2 == 0:
        display.fill(0)
        display.print("%d" % rpm)
    else:
        display.fill(0)
        display.print("%.0f C" % temperature)

    # This is quite lame control, but it keeps my cpu cool.
    if time.time() - last_fan_change_time > HYSTERESIS_SECONDS:
        # Use PID to attempt to control the fan
        print("Setting fan speed to %.0f" % (fan_output_pid))
        fan_pwm.duty_cycle = round(65536 * fan_output_pid)
        last_fan_change_time = time.time()
