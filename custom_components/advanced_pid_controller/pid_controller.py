from simple_pid import PID


class PIDControllerWrapper:
    """Helper class to manage a simple-pid instance from HA entities."""

    def __init__(self) -> None:
        self._pid = PID(1.0, 0.0, 0.0)
        self._pid.output_limits = (-10.0, 10.0)
        self._pid.sample_time = 1.0
        self._setpoint = 20.0

    def update_parameters(self, values: dict) -> None:
        """Update all PID parameters based on HA entity values."""
        self._setpoint = values.get("setpoint", self._setpoint)
        self._pid.setpoint = self._setpoint
        self._pid.Kp = values.get("kp", self._pid.Kp)
        self._pid.Ki = values.get("ki", self._pid.Ki)
        self._pid.Kd = values.get("kd", self._pid.Kd)
        output_min = values.get("output_min", -10.0)
        output_max = values.get("output_max", 10.0)
        self._pid.output_limits = (output_min, output_max)
        self._pid.sample_time = values.get("sample_time", self._pid.sample_time)

    def compute(self, input_value: float) -> float:
        """Compute the PID output based on the current input."""
        return self._pid(input_value)

    @property
    def setpoint(self) -> float:
        return self._setpoint
