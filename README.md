# Simple PID Controller

> The Simple PID Controller is a Home Assistant integration for real-time PID control with UI-based tuning and diagnostics.

---

## 📚 Table of Contents
- [Features](#features)
- [Installation](#installation)
  - [HACS (Recommended)](#hacs-recommended)
  - [Manual Installation](#manual-installation)
  - [Removal Instructions](#removal-instructions) 
- [Configuration](#configuration)
- [Entities Overview](#entities-overview)
- [PID Tuning Guide](#pid-tuning-guide)
  - [Manual Tuning](#1-manual-trial--error)
  - [Ziegler–Nichols Method](#2-zieglernichols-method)
- [PID Calculation Frequency and Sample Time](#pid-calculation-frequency-and-sample-time)
- [Example PID Graph](#example-pid-graph)
- [Support & Development](#support--development)
- [Service Actions](#service-actions)


---

## ✨ Features

- **Live PID tuning** via Number entities.
- **Diagnostics** for P, I, and D terms (optional).
- **Switch** to toggle auto mode and proportional-on-measurement.
- **Configurable** output limits, setpoint, and sample time.

### Included Entities

| Platform | Entity                    | Purpose                                 |
|----------|---------------------------|-----------------------------------------|
| Sensor   | `PID Output`              | Current controller output as percentage |
| Sensor   | `PID P Contribution`      | Proportional term value (diagnostic)    |
| Sensor   | `PID I Contribution`      | Integral term value (diagnostic)        |
| Sensor   | `PID D Contribution`      | Derivative term value (diagnostic)      |
| Number   | `Kp`, `Ki`, `Kd`          | PID gain parameters                     |
| Number   | `Setpoint`                | Desired target value                    |
| Number   | `Output Min` / `Max`      | Controller output limits                |
| Number   | `Sample Time`             | PID evaluation interval                 |
| Switch   | `Auto Mode`               | Toggle automatic control                |
| Switch   | `Proportional on Measurement` | Change proportional mode         |
| Switch   | `Windup Protection`       | Toggle windup protection                |


> 💡 All entities are editable via the UI in **Settings > Devices & Services > [Your Controller] > Options**.

---

## 🔧 Installation

### HACS (Recommended)

1. In Home Assistant UI, navigate to **HACS > Integrations**
2. Click the three-dot menu (⋮) and select **Custom repositories**
3. Add:
   ```text
   https://github.com/bvweerd/simple_pid_controller
   ```
   Select **Integration** as type
4. Search for **Simple PID Controller** and install
5. Restart Home Assistant

### Manual Installation

1. Download or clone this repository
2. Copy `simple_pid_controller` to `/config/custom_components/`
3. Restart Home Assistant

### Removal Instructions 
To remove the Simple PID Controller, navigate to **Settings > Devices & Services**, select **Simple PID Controller**, and click **Delete**. If installed manually, delete the `custom_components/simple_pid_controller` directory and restart Home Assistant.

---

## ⚙️ Configuration
The controller is configured through the UI using the Config Flow {% term config_flow %}.

1. Go to **Settings > Devices & Services**
2. Click **Add Integration** and choose **Simple PID Controller**
3. Enter:
   - **Name**: e.g., "Heater Controller"
   - **Sensor Entity**: e.g., `sensor.living_room_temperature`
4. Submit and finish setup

**Default Range:**  
The controller’s setpoint range defaults to **0.0 – 100.0**. To customize this range, select the integration in **Settings > Devices & Services**, click **Options**, adjust **Range Min** and **Range Max**, and save.

---

## 📊 Entities Overview

| Platform | Entity Suffix                 | Description                                        |
|----------|-------------------------------|----------------------------------------------------|
| Sensor   | `PID Output`                  | Current controller output (%).                     |
| Sensor   | `PID P/I/D Contribution`      | Diagnostic terms. Disabled by default.             |
| Number   | `Kp`, `Ki`, `Kd`              | PID gains.                                         |
| Number   | `Setpoint`                    | Desired system target.                             |
| Number   | `Output Min` / `Output Max`   | Min/max control limits.                            |
| Number   | `Sample Time`                 | PID evaluation rate in seconds.                    |
| Switch   | `Auto Mode`                   | Enable/disable PID automation.                     |
| Switch   | `Proportional on Measurement` | Use measurement instead of error for P term.       |
| Switch   | `Windup Protection`           | Toggle windup protection                           |

---

## 🎯 PID Tuning Guide

A PID controller continuously corrects the difference between a **setpoint** and **measured value** using:

- **P (Proportional)**: reacts to present error
- **I (Integral)**: compensates for past error
- **D (Derivative)**: predicts future error trends

<details>
<summary><strong>1. Manual (Trial & Error)</strong></summary>

1. Set `Ki` and `Kd` to 0
2. Start with small `Kp` (e.g., 1.0)
3. Increase `Kp` until oscillations appear
4. Halve that `Kp` value
5. Increase `Ki` to reduce steady-state error
6. Add `Kd` to smooth out oscillations

</details>

<details>
<summary><strong>2. Ziegler–Nichols Method</strong></summary>

1. Set `Ki = 0`, `Kd = 0`, increase `Kp` until sustained oscillations
2. Measure:
   - **Ku** = critical gain
   - **Pu** = oscillation period
3. Apply:
   - `Kp = 0.6 × Ku`
   - `Ki = 1.2 × Ku / Pu`
   - `Kd = 0.075 × Ku × Pu`

</details>

---

## PID Calculation Frequency and Sample Time

This integration recalculates the PID output at a fixed, user-configurable interval to ensure timely and consistent control updates. Internally, both the PID loop and Home Assistant’s data coordinator use the same **Sample Time**, but they each maintain their own timer, so slight differences can occur.

- **Sample Time**  
  The minimum number of seconds between successive PID computations. For example, if you set `sample_time: 5`, both the PID controller and the update coordinator are scheduled to fire every 5 seconds.

### How it works in practice

1. **Initialization**  
   - On startup (or when options change), we set up a single `sample_time` value (in seconds).  
   - We register a periodic callback with Home Assistant’s scheduler (`async_track_time_interval` or `DataUpdateCoordinator`) using that same `sample_time`.  
   - We also configure the PID algorithm’s internal timer to the same `sample_time`.

2. **Coordinator Tick**  
   - Every `sample_time` seconds, Home Assistant’s scheduler invokes our update method.  
   - We immediately read the current process variable (e.g. temperature sensor) and pass it to the PID logic.

3. **PID Logic & Output**  
   - The PID algorithm checks whether at least `sample_time` seconds have elapsed since its own last computation.  
   - If so, it calculates the Proportional, Integral, and Derivative terms and writes the result to your target entity (e.g. a heater or set-point).  
   - If not (because the PID’s internal timer hasn’t quite reached the next tick), it skips the computation until its own timer allows it.

4. **Timer Drift & Overlap**  
   - Both the coordinator and the PID controller schedule their next run relative to when the current one started. Under heavy load, one callback may run a few milliseconds later than expected.  
   - Because each timer is independent, occasional “double-ticks” or small gaps can occur:  
     - If the scheduler drifts early but the PID timer hasn’t yet reached `sample_time`, no computation runs.  
     - If the PID timer elapses first and the scheduler callback is slightly late, the update happens immediately when the scheduler finally fires.  
   - Over time, these small variances average out, preserving an approximately consistent interval.

5. **Adjusting Sample Time**  
   - Changing `sample_time` in your integration options takes effect at the end of the current interval—no Home Assistant restart is required.  
   - On the next tick, both the coordinator and the PID logic will use the new interval.

By using a single **Sample Time** for both scheduling and calculation—and understanding that each component tracks its own clock—you get predictable, evenly-spaced control updates while allowing Home Assistant’s event loop to manage timing drifts gracefully.```


---

## 📈 Example PID Graph

Here's an example output showing the controller responding to a setpoint:

![Example PID Output](assets/pid_example_graph.png)

---

## 🛠️ Support & Development

- **GitHub Repository**: [https://github.com/bvweerd/simple_pid_controller](https://github.com/bvweerd/simple_pid_controller)
- **Issues & Bugs**: [Report here](https://github.com/bvweerd/simple_pid_controller/issues)

---

## 🔧 Service Actions 
This Integration does **not** expose any custom services. All interactions are performed via UI-based entities.


