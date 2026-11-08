# IoT Agriculture Device - IT Assignment

## Project Overview

The Smart Farming Dashboard is an IoT-based greenhouse monitoring and automation prototype designed to help monitor environmental conditions and manage watering and cooling.

The system uses a Raspberry Pi Pico W connected to sensors and electronic components to measure temperature, humidity and water tank levels. It can automatically activate cooling and irrigation indicators based on configurable thresholds.

A web-based dashboard allows users to monitor sensor readings, adjust settings and calibrate the water-level sensor.

## Features

- **Temperature monitoring:** Measures the greenhouse temperature using a DHT11 sensor.
- **Humidity monitoring:** Measures the surrounding humidity.
- **Water-level monitoring:** Uses an ultrasonic sensor to estimate the percentage of water remaining in a tank.
- **Automatic cooling:** Activates the cooling LED when the temperature exceeds the configured threshold.
- **Automatic irrigation:** Activates the irrigation LED when humidity falls below the configured threshold, provided there is sufficient water.
- **Manual controls:** Physical buttons allow the user to switch between automatic and manual modes and control the cooling and irrigation outputs.
- **Web dashboard:** Displays live sensor readings and the current status of the outputs.
- **Adjustable settings:** Allows the user to change temperature, humidity and water-level thresholds.
- **Potentiometer control:** Allows the temperature threshold to be adjusted using a physical potentiometer.
- **Buzzer alert:** Sounds when the temperature exceeds the active temperature threshold, if enabled.
- **Water sensor calibration:** Allows the user to set the empty and full distances for the water tank.
- **Data logging:** Saves sensor readings and output states to a local text file.
- **Settings storage:** Saves configuration settings in a JSON file so they can be loaded again when the program restarts.

## Hardware Components

| Component | GPIO Pin | Purpose |
|---|---|---|
| Raspberry Pi Pico W | — | Main microcontroller |
| DHT11 sensor | GP13 | Measures temperature and humidity |
| Cooling LED | GP0 | Indicates cooling activation |
| Irrigation LED | GP1 | Indicates irrigation activation |
| Ultrasonic sensor TRIG | GP14 | Sends ultrasonic pulses |
| Ultrasonic sensor ECHO | GP15 | Receives reflected pulses |
| Cooling button | GP12 | Manually controls cooling |
| Irrigation button | GP16 | Manually controls irrigation |
| Mode toggle button | GP8 | Switches between automatic and manual modes |
| Buzzer | GP11 | Provides temperature alerts |
| Potentiometer | GP26 | Adjusts the temperature threshold |

**Note:** The ultrasonic sensor's ECHO signal must be compatible with the Pico's 3.3V GPIO inputs. A suitable voltage divider or level shifter may be required for sensors with a 5V ECHO output.

## How It Works

### 1. Environmental Monitoring

The DHT11 sensor measures temperature and humidity. These readings are periodically collected and used by the system to determine whether cooling or irrigation should be activated.

### 2. Water-Level Monitoring

The ultrasonic sensor measures the distance between the sensor and the water surface. The measured distance is converted into a percentage using the calibrated empty and full distances.

The system also checks whether the water level is below the configured low-water threshold.

### 3. Automatic Mode

In automatic mode, the system controls the outputs using the configured thresholds:

- Cooling activates when the temperature exceeds the temperature threshold.
- Irrigation activates when humidity falls below the humidity threshold, provided the water level is sufficient.
- The buzzer sounds when the temperature exceeds the active temperature threshold and the buzzer is enabled.

### 4. Manual Mode

In manual mode, the physical buttons allow the user to control the cooling and irrigation outputs instead of relying on the automatic thresholds.

The system is designed to prevent irrigation when the water level is too low.

### 5. Web Dashboard

The Pico W hosts a small web server that can be accessed through a web browser on the same network.

The dashboard displays:
- Current temperature and humidity.
- Estimated water tank level.
- Cooling and irrigation status.
- Current operating mode.
- Active temperature threshold and its source.

Users can also change settings, enable or disable the buzzer and calibrate the water-level sensor.

## Software and Technologies

- **MicroPython:** Programming language used to control the Raspberry Pi Pico W.
- **Raspberry Pi Pico W:** Microcontroller with built-in Wi-Fi connectivity.
- **HTML, CSS and JavaScript:** Used to create the web-based dashboard.
- **JSON:** Used to store configuration settings.
- **Socket networking:** Used to host the dashboard through a local web server.

## Setup Instructions

1. Connect the hardware components to the Raspberry Pi Pico W using the GPIO pin connections listed above.
2. Install MicroPython on the Raspberry Pi Pico W.
3. Open `main.py` in a compatible editor, such as Visual Studio Code.
4. Update the Wi-Fi network name and password in the networking section of the code.
5. Upload `main.py` to the Pico W.
6. Run the program.
7. Once connected to Wi-Fi, the Pico W prints its IP address in the serial output.
8. Open that IP address in a web browser on a device connected to the same network.

**Important:** Wi-Fi credentials should be kept private. Replace any example credentials before sharing the project publicly.

## Project Files

| File | Description |
|---|---|
| `main.py` | Main MicroPython program containing the sensor readings, automation logic, web server and dashboard. |
| `settings.json` | Stores configuration settings such as thresholds, calibration values and preferences. Created when settings are saved. |
| `readings.txt` | Stores logged sensor readings and output states. Created when readings are recorded. |

## Testing and Limitations

The project was developed as a prototype to demonstrate how IoT technology can be used for greenhouse monitoring and automation.

The code includes functionality for sensor monitoring, automatic and manual controls, a web dashboard and data logging. However, any functionality that has not been physically tested with the final hardware setup should be treated as implemented but not fully verified.

The system also has some limitations:
- The DHT11 sensor has limited measurement accuracy.
- The water-level estimate depends on correct sensor calibration.
- The Pico W and dashboard require a working Wi-Fi connection.
- The system is a prototype and is not designed to control a real greenhouse without further testing and development.

## Future Improvements

Possible improvements include:
- Adding more accurate environmental sensors.
- Improving the dashboard with historical graphs and additional visualisations.
- Adding notifications when environmental conditions exceed certain thresholds.
- Improving error handling when sensors stop responding.
- Testing the complete system over longer periods.
- Developing a more permanent and reliable hardware enclosure.
