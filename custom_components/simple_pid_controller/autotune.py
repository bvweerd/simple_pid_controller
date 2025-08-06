"""Relay based auto-tuning for PID parameters."""

from __future__ import annotations

import math
from typing import Sequence


class RelayAutoTuner:
    """Perform PID autotuning using the relay (Åström–Hägglund) method.

    The implementation analyses oscillations obtained by exciting the
    process with a relay (on/off) controller.  From the sustained
    oscillations the ultimate gain and period are derived and translated
    to PID parameters using the classic Ziegler–Nichols rules.
    """

    @staticmethod
    def tune(
        data: Sequence[float],
        sample_time: float,
        relay_amplitude: float,
    ) -> tuple[float, float, float]:
        """Return ``(kp, ki, kd)`` for the given oscillation data.

        ``data`` should contain process values around the setpoint for at
        least two complete oscillation cycles. ``sample_time`` is the time
        between data points in seconds. ``relay_amplitude`` is the output
        step (absolute value) used during the relay test.
        """

        if len(data) < 3:
            raise ValueError("Not enough data for autotune")

        maxima: list[tuple[int, float]] = []
        minima: list[tuple[int, float]] = []
        for i in range(1, len(data) - 1):
            prev_, cur, next_ = data[i - 1], data[i], data[i + 1]
            if cur > prev_ and cur > next_:
                maxima.append((i, cur))
            if cur < prev_ and cur < next_:
                minima.append((i, cur))

        # Need at least two maxima and one minima to determine amplitude and period
        if len(maxima) < 2 or len(minima) < 1:
            raise ValueError("Could not determine oscillation characteristics")

        # Determine oscillation period using last two maxima
        last_idx, prev_idx = maxima[-1][0], maxima[-2][0]
        pu = (last_idx - prev_idx) * sample_time

        max_avg = sum(v for _, v in maxima) / len(maxima)
        min_avg = sum(v for _, v in minima) / len(minima)
        a = (max_avg - min_avg) / 2.0
        if a <= 0:
            raise ValueError("Invalid oscillation amplitude")

        ku = 4.0 * relay_amplitude / (math.pi * a)
        kp = 0.6 * ku
        ki = 1.2 * ku / pu
        kd = 0.075 * ku * pu
        return kp, ki, kd
