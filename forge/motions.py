"""Synthetic ground-motion suite generation.

Site-consistent accelerograms built as filtered, enveloped random processes:
white-noise phases shaped by a single-mode soil transfer function (peaked at
the site's predominant period), a trapezoidal-plus-exponential intensity
envelope, and amplitude scaling to the design PGA. Fully deterministic for a
given (site, seed): the same brief always yields the same test suite.

This is a compact engineering-grade screen suite, not a hazard analysis; the
point is that every design is tested against the same physically reasonable
records and can be re-tested by anyone from the brief alone.
"""

from __future__ import annotations

import math

import numpy as np

from .building import G, Site

DT = 0.01  # s, analysis and synthesis time step
N_HARMONICS = 120
SOIL_DAMPING = 0.55  # broadband soil-filter damping
HIGHPASS_CORNER_HZ = 0.22  # Clough-Penzien high-pass corner


def synthesize(site: Site, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (time [s], ground acceleration [m/s^2]) for one realization."""
    duration = float(site.duration_sec)
    count = int(round(duration / DT)) + 1
    time = np.arange(count) * DT

    omega_soil = 2.0 * math.pi / float(site.soil_period_sec)
    # Harmonic grid spanning the frequencies buildings in the model class see.
    freqs = np.linspace(0.15, 12.0, N_HARMONICS)
    omega = 2.0 * math.pi * freqs
    # Kanai-Tajimi-style soil amplitude shape, tempered at high frequency,
    # with a Clough-Penzien-style high-pass so the process does not carry
    # unphysical displacement energy at very long periods.
    num = omega_soil**4 + (2.0 * SOIL_DAMPING * omega_soil * omega) ** 2
    den = (omega_soil**2 - omega**2) ** 2 + (2.0 * SOIL_DAMPING * omega_soil * omega) ** 2
    amplitude = np.sqrt(num / den) / np.sqrt(1.0 + 0.35 * omega)
    omega_c = 2.0 * math.pi * HIGHPASS_CORNER_HZ
    zeta_c = 0.7
    highpass = omega**2 / np.sqrt(
        (omega_c**2 - omega**2) ** 2 + (2.0 * zeta_c * omega_c * omega) ** 2
    )
    amplitude *= highpass

    rng = np.random.default_rng(seed)
    phases = rng.uniform(0.0, 2.0 * math.pi, size=freqs.shape)
    signal = np.zeros(count)
    for a, w, p in zip(amplitude, omega, phases):
        signal += a * np.sin(w * time + p)

    # Intensity envelope: parabolic rise, hold, exponential decay.
    rise_end = 0.15 * duration
    hold_end = 0.55 * duration
    envelope = np.ones(count)
    rising = time < rise_end
    envelope[rising] = (time[rising] / rise_end) ** 2
    decaying = time > hold_end
    envelope[decaying] = np.exp(-0.4 * (time[decaying] - hold_end))
    signal *= envelope

    peak = float(np.max(np.abs(signal)))
    if peak > 0.0:
        signal *= float(site.pga_g) * G / peak
    return time, signal


def suite(site: Site) -> list[dict]:
    """The deterministic record suite for one site."""
    return [
        {
            "record_id": f"rec_{index + 1:02d}",
            "seed": site.seed_base + index,
        }
        for index in range(int(site.records))
    ]
