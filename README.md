# Simple PID Controller

A Home Assistant integration that provides a simple, live-tunable PID (Proportional-Integral-Derivative) controller. It allows:

* **Real-time tuning** of PID parameters via Number entities.
* **Diagnostic sensors** for P, I, and D contributions (disabled by default).
* **Automatic control** toggling through a Switch entity.
* **Configurable output limits**, sample time, and setpoint.

## Features

* **PID Output Sensor**: Reports the current controller output as a percentage.
* **Diagnostic Sensors**: Separate sensors for the P, I, and D contributions (disabled by default).
* **Number Entities** for:

  * **Kp** (Proportional gain)
  * **Ki** (Integral gain)
  * **Kd** (Derivative gain)
  * **Setpoint** (Desired target value)
  * **Output Min** (Minimum controller output)
  * **Output Max** (Maximum controller output)
  * **Sample Time** (Interval between PID calculations)
* **Switch Entities** for:

  * **Auto Mode**: Enable/disable automatic PID control.
  * **Proportional on Measurement**: Toggle whether the proportional term acts on measurement rather than error.

## Installation

### HACS (Recommended)

1. In Home Assistant UI, navigate to **HACS > Integrations**.
2. Click the three-dot menu (⋮) in the top right and choose **Custom repositories**.
3. Add the repository URL:

   ```text
   https://github.com/bvweerd/simple_pid_controller
   ```

   and select **Integration** as the category.
4. Once added, search for **Simple PID Controller** in HACS and install it.
5. Restart Home Assistant.

### Manual Installation

1. Download or clone this repository.
2. Copy the `simple_pid_controller` folder into your `/config/custom_components/` directory.
3. Ensure the folder structure is:

   ```text
   config/
   └── custom_components/
       └── simple_pid_controller/
           ├── __init__.py
           ├── manifest.json
           ├── sensor.py
           ├── number.py
           ├── switch.py
           └── ...
   ```
4. Restart Home Assistant.

## Configuration

1. In Home Assistant UI, go to **Settings > Devices & Services**.
2. Click **Add Integration** and search for **Simple PID Controller**.
3. Enter the following:

   * **Name**: A friendly name for your controller (e.g., "Heater Controller").
   * **Sensor Entity**: The entity ID of the input sensor (e.g., `sensor.living_room_temperature`).
4. Click **Submit** and finish the setup.

### Entity Overview

After setup, the following entities are created under the device named after your controller:

| Platform | Entity Suffix                 | Purpose                                              |
| -------- | ----------------------------- | ---------------------------------------------------- |
| Sensor   | `PID Output`                  | Current controller output (as a percentage).         |
| Sensor   | `PID P Contribution`          | Proportional term value (diagnostic).                |
| Sensor   | `PID I Contribution`          | Integral term value (diagnostic).                    |
| Sensor   | `PID D Contribution`          | Derivative term value (diagnostic).                  |
| Number   | `Kp`                          | Proportional gain parameter.                         |
| Number   | `Ki`                          | Integral gain parameter.                             |
| Number   | `Kd`                          | Derivative gain parameter.                           |
| Number   | `Setpoint`                    | Desired target value for the controller.             |
| Number   | `Output Min`                  | Minimum output limit.                                |
| Number   | `Output Max`                  | Maximum output limit.                                |
| Number   | `Sample Time`                 | Time interval (in seconds) between PID calculations. |
| Switch   | `Auto Mode`                   | Toggle automatic PID control on/off.                 |
| Switch   | `Proportional on Measurement` | Switch proportional term to measurement mode.        |

> **Tip:** All Number and Switch entities are editable in the UI (Settings > Devices & Services > \[Your Controller] > Options).

## PID Tuning Guide

A PID controller continuously calculates an error value as the difference between a desired **setpoint** and a measured **input**. It applies corrections based on three terms:

* **Proportional (P)**: Reacts to the current error.
* **Integral (I)**: Accumulates past errors to eliminate steady-state offset.
* **Derivative (D)**: Predicts future error based on its rate of change.

Proper tuning of **Kp**, **Ki**, and **Kd** is crucial for stable and responsive control. Below are two common methods:

### 1. Manual (Trial & Error)

1. Set `Ki` and `Kd` to **0**.
2. Start with a small `Kp` (e.g., **1.0**).
3. Gradually increase `Kp` until the system begins to oscillate around the setpoint.
4. Reduce `Kp` to about **half** of that oscillation-inducing value for stability.
5. Increase `Ki` slowly to eliminate any remaining steady-state error. Watch for slow oscillations and back off if they appear.
6. Increase `Kd` to dampen oscillations and improve settling time.
7. Adjust **Setpoint**, **Output Min**, **Output Max**, and **Sample Time** as needed.

### 2. Ziegler–Nichols Method

1. With `Ki = 0` and `Kd = 0`, increase `Kp` until sustained oscillations occur. Call this critical gain **Ku** and oscillation period **Pu**.
2. Apply the following tuned values:

   * **Kp** = `0.6 × Ku`
   * **Ki** = `1.2 × Ku / Pu`  (or integral time `Ti = Pu / 2`)
   * **Kd** = `0.075 × Ku × Pu`
3. Fine-tune by making small adjustments based on system response.

## Support & Development

* **Documentation**: [https://github.com/bvweerd/simple\_pid\_controller](https://github.com/bvweerd/simple_pid_controller)
* **Issue Tracker**: [https://github.com/bvweerd/simple\_pid\_controller/issues](https://github.com/bvweerd/simple_pid_controller/issues)
