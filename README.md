# fan-control-circuitpython
A controller for a fan for my fanless pc\

## Hardware
Microprocessor: I initially started with an Adafruit KB2040, but then I decided I wanted to use Adafruit IO datalogging, so I switched the microprocessor to a Seeed Studio XIAO ESP32-S3 which has wifi and a smaller footprint.
Fan: Noctua NF-P12 redux-1700 PWM, High Performance Cooling Fan, 4-Pin, 1700 RPM (120mm)
Boost Converter: Eiechip dc to dc Step up Converter USB Power Module Supply Module 2V-24V to 5V-28V 2A MT3608 Mico USB 
1N4001 diode

## Wiring

### Fan 4 wire Pin:
FAN COUNT: XAIO Pin 3 Input: D8 (GPIO7)
FAN PWM: XAIO Pin 4: Control: D9 (GPIO8)
Fan V+: Boost Converter Vout +
Fan V-: Ground Plane 

### Stemma I2C
Yellow: I2C SDA:  XAIO Pin 5
Blue I2C SCL: XAIO Pin 6
Black GND:  Ground Plane
Red 3.3V: XAIO Pin 12

### Boost Converter:
VIn +: to 1N4001 
3:57 PM 1/28/2024 Diode, then to +5V: Pin 14
Vin -: To Ground Plane
Vout +: To Fan +
Vout -: to Ground Plane 

### Ground Plane: 
Stemma I2C GND
Fan V-
Boost Vin-
Boost Vout -\
GND Pin 13
