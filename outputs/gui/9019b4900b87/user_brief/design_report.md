# SeismoForge prototype design report - user brief

**Verdict: NOT BUILDABLE WITHIN BRIEF**

> **Concept-stage prototype study - not for construction.** This report is produced by an automated design agent. It must be reviewed and signed off by a licensed structural engineer before it informs any design, procurement, or construction decision. The model class, acceptance limits, and synthetic ground motions are SeismoForge's own benchmark basis, not a substitute for code-compliant analysis of a project-specific hazard.

## Building and site

- Occupancy: office | stories: 9 | story height: 3.2 m
- Seismic floor weight: 700.0 t/floor (total seismic weight 61,803 kN)
- Story lateral stiffness: 610,000 kN/m
- Site: PGA 0.35 g, predominant period 1.2 s, duration 26.0 s
- Moat clearance available: 0.75 m | residual limit: 0.12 m

## Selected structural system

Lead-rubber base isolation layer under the full frame:

- Characteristic strength Qd = 5,253 kN (8.5% of seismic weight)
- Post-yield stiffness Kd = 12,282 kN/m (isolated period 4.50 s)
- Yield displacement Dy = 41 mm

## Verification basis

- Nonlinear response-history analysis in OpenSees (Newmark average acceleration, dt = 0.01 s, Newton iteration with ModifiedNewton retry).
- Record suite: 5 site-consistent synthetic accelerograms (soil-filtered, 120 harmonics, Clough-Penzien high-pass at 0.22 Hz), seeds [9759, 9760, 9761, 9762, 9763] - fully reproducible from this brief.
- Damping: 2% Rayleigh (alpha_m = 0.1154, beta_k = 0.001767; anchors 3.39 / 19.24 rad/s).

## Acceptance checks (suite envelope)

| Check | Demand | Limit | Utilization | Status |
|---|---|---|---|---|
| all records converged | yes | required | - | OK |
| peak_drift_ratio | 0.007444 | 0.012 | 0.62 | OK |
| peak_floor_accel_g | 0.5514 | 0.55 | 1.00 | **FAIL** |
| base_shear_coeff | 0.215 | 0.45 | 0.48 | OK |
| peak_isolator_disp_m | 0.6542 | 0.75 | 0.87 | OK |
| residual_disp_m | 0.1158 | 0.12 | 0.97 | OK |

Governing check: **peak_floor_accel_g** at utilization 1.00.

## Per-record results

| Record | Seed | Converged | Iso disp (m) | Drift | Floor acc (g) | V/W | Residual (m) |
|---|---|---|---|---|---|---|---|
| rec_01 | 9759 | yes | 0.6220 | 0.00744 | 0.5514 | 0.2086 | 0.0310 |
| rec_02 | 9760 | yes | 0.5178 | 0.00653 | 0.5069 | 0.1879 | 0.0094 |
| rec_03 | 9761 | yes | 0.2971 | 0.00558 | 0.5282 | 0.1440 | 0.0457 |
| rec_04 | 9762 | yes | 0.6457 | 0.00664 | 0.5176 | 0.2133 | 0.1158 |
| rec_05 | 9763 | yes | 0.6542 | 0.00658 | 0.4635 | 0.2150 | 0.0014 |

## Design search history

27 simulation-backed design evaluations:

| # | Stage | System | Qd (kN) | Kd (kN/m) | Dy (mm) | Result | Worst utilization |
|---|---|---|---|---|---|---|---|
| 1 | rule_of_thumb | base_isolated | 3,708 | 31,724 | 20 | fail | 1.33 |
| 2 | screen | base_isolated | 3,090 | 43,180 | 30 | fail | 1.52 |
| 3 | screen | base_isolated | 3,090 | 43,180 | 45 | fail | 1.52 |
| 4 | screen | base_isolated | 3,090 | 24,288 | 30 | fail | 1.36 |
| 5 | screen | base_isolated | 3,090 | 24,288 | 45 | fail | 1.38 |
| 6 | screen | base_isolated | 3,090 | 15,545 | 30 | fail | 1.23 |
| 7 | screen | base_isolated | 3,090 | 15,545 | 45 | fail | 1.29 |
| 8 | screen | base_isolated | 4,944 | 43,180 | 30 | fail | 1.67 |
| 9 | screen | base_isolated | 4,944 | 43,180 | 45 | fail | 1.62 |
| 10 | screen | base_isolated | 4,944 | 24,288 | 30 | fail | 1.39 |
| 11 | screen | base_isolated | 4,944 | 24,288 | 45 | fail | 1.38 |
| 12 | screen | base_isolated | 4,944 | 15,545 | 30 | fail | 1.11 |
| 13 | screen | base_isolated | 4,944 | 15,545 | 45 | fail | 1.18 |
| 14 | screen | base_isolated | 6,798 | 43,180 | 30 | fail | 1.86 |
| 15 | screen | base_isolated | 6,798 | 43,180 | 45 | fail | 1.83 |
| 16 | screen | base_isolated | 6,798 | 24,288 | 30 | fail | 1.49 |
| 17 | screen | base_isolated | 6,798 | 24,288 | 45 | fail | 1.33 |
| 18 | screen | base_isolated | 6,798 | 15,545 | 30 | fail | 1.33 |
| 19 | screen | base_isolated | 6,798 | 15,545 | 45 | fail | 1.20 |
| 20 | refine | base_isolated | 4,203 | 15,545 | 24 | fail | 1.03 |
| 21 | refine | base_isolated | 5,253 | 15,545 | 24 | fail | 1.17 |
| 22 | refine | base_isolated | 5,253 | 13,213 | 29 | fail | 1.10 |
| 23 | refine | base_isolated | 5,253 | 12,282 | 35 | fail | 1.04 |
| 24 | refine | base_isolated | 5,253 | 12,282 | 41 | fail | 1.00 |
| 25 | refine | base_isolated | 5,253 | 12,282 | 50 | fail | 1.27 |
| 26 | refine | base_isolated | 4,465 | 12,282 | 40 | fail | 1.51 |
| 27 | refine | base_isolated | 4,465 | 15,967 | 30 | fail | 1.01 |

## Why the brief is not buildable as posed

No design in the buildable isolation space met every acceptance target on this site; the table above shows the binding constraints. The recommendation is to revisit the brief itself (site, moat clearance, or supplemental damping outside the standard system) rather than to accept a design that fails verification.

## Engineering notes

Governing check: peak_floor_accel_g at utilization 1.00.

*Commentary written by the design agent. Unlike the tables above it is prose, not a simulation output, and carries no independent verification.*

---
*Generated by SeismoForge. Every number in the tables above comes from the simulation suite described in the verification basis; the suite is deterministic and reproducible from the project brief. Known modelling limitations of that basis are listed in the repository README - read them before acting on this report.*

> **Concept-stage prototype study - not for construction.** This report is produced by an automated design agent. It must be reviewed and signed off by a licensed structural engineer before it informs any design, procurement, or construction decision. The model class, acceptance limits, and synthetic ground motions are SeismoForge's own benchmark basis, not a substitute for code-compliant analysis of a project-specific hazard.
