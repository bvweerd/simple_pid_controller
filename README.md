# Simple PID Controller

This Home Assistant custom component provides a PID controller whose parameters can be adjusted in the UI:
- **Number entities**: Kp, Ki, Kd, Setpoint, Output Min, Output Max, Sample Time  
- **Switch entities**: Auto Mode, P on Measurement  
- **Sensor entities**: PID Output, P Contribution, I Contribution, D Contribution (diagnostic)  

All entities are grouped under a device named during configuration. Changes to any parameter or switch trigger an immediate PID computation.
