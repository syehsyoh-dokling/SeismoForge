# SeismoForge prototype design report - brief 10 cliffside clinic

**Verdict: NOT BUILDABLE WITHIN BRIEF**

> **Concept-stage prototype study - not for construction.** This report is produced by an automated design agent. It must be reviewed and signed off by a licensed structural engineer before it informs any design, procurement, or construction decision. The model class, acceptance limits, and synthetic ground motions are SeismoForge's own benchmark basis, not a substitute for code-compliant analysis of a project-specific hazard.

## Building and site

- Occupancy: hospital | stories: 6 | story height: 3.6 m
- Seismic floor weight: 700.0 t/floor (total seismic weight 41,202 kN)
- Story lateral stiffness: 400,000 kN/m
- Site: PGA 0.38 g, predominant period 1.3 s, duration 28.0 s
- Moat clearance available: 0.4 m | residual limit: 0.12 m

## Selected structural system

Lead-rubber base isolation layer under the full frame:

- Characteristic strength Qd = 4,532 kN (11.0% of seismic weight)
- Post-yield stiffness Kd = 16,192 kN/m (isolated period 3.20 s)
- Yield displacement Dy = 30 mm

## Verification basis

- Nonlinear response-history analysis in OpenSees (Newmark average acceleration, dt = 0.01 s, Newton iteration with ModifiedNewton retry).
- Record suite: 5 site-consistent synthetic accelerograms (soil-filtered, 120 harmonics, Clough-Penzien high-pass at 0.22 Hz), seeds [6325, 6326, 6327, 6328, 6329] - fully reproducible from this brief.
- Damping: 2% Rayleigh (alpha_m = 0.1426, beta_k = 0.001514; anchors 4.25 / 22.17 rad/s).

## Acceptance checks (suite envelope)

| Check | Demand | Limit | Utilization | Status |
|---|---|---|---|---|
| all records converged | yes | required | - | OK |
| peak_drift_ratio | 0.01181 | 0.007 | 1.69 | **FAIL** |
| peak_floor_accel_g | 0.8872 | 0.4 | 2.22 | **FAIL** |
| base_shear_coeff | 0.4499 | 0.3 | 1.50 | **FAIL** |
| peak_isolator_disp_m | 0.8648 | 0.4 | 2.16 | **FAIL** |
| residual_disp_m | 0.08313 | 0.12 | 0.69 | OK |

Governing check: **peak_floor_accel_g** at utilization 2.22.

## Per-record results

| Record | Seed | Converged | Iso disp (m) | Drift | Floor acc (g) | V/W | Residual (m) |
|---|---|---|---|---|---|---|---|
| rec_01 | 6325 | yes | 0.6995 | 0.00948 | 0.7425 | 0.3849 | 0.0389 |
| rec_02 | 6326 | yes | 0.5066 | 0.00840 | 0.6007 | 0.3091 | 0.0093 |
| rec_03 | 6327 | yes | 0.4479 | 0.00730 | 0.7424 | 0.2860 | 0.0112 |
| rec_04 | 6328 | yes | 0.8648 | 0.01181 | 0.7870 | 0.4499 | 0.0438 |
| rec_05 | 6329 | yes | 0.6291 | 0.01041 | 0.8872 | 0.3572 | 0.0831 |

## Design search history

25 simulation-backed design evaluations:

| # | Stage | System | Qd (kN) | Kd (kN/m) | Dy (mm) | Result | Worst utilization |
|---|---|---|---|---|---|---|---|
| 1 | agent | base_isolated | 2,472 | 21,149 | 20 | fail | 2.34 |
| 2 | agent | base_isolated | 2,060 | 28,786 | 30 | fail | 2.62 |
| 3 | agent | base_isolated | 2,060 | 28,786 | 45 | fail | 2.58 |
| 4 | agent | base_isolated | 2,060 | 16,192 | 30 | fail | 3.22 |
| 5 | agent | base_isolated | 2,060 | 16,192 | 45 | fail | 3.37 |
| 6 | agent | base_isolated | 2,060 | 10,363 | 30 | fail | 2.91 |
| 7 | agent | base_isolated | 2,060 | 10,363 | 45 | fail | 2.95 |
| 8 | agent | base_isolated | 3,296 | 28,786 | 30 | fail | 2.51 |
| 9 | agent | base_isolated | 3,296 | 28,786 | 45 | fail | 2.54 |
| 10 | agent | base_isolated | 3,296 | 16,192 | 30 | fail | 2.27 |
| 11 | agent | base_isolated | 3,296 | 16,192 | 45 | fail | 2.35 |
| 12 | agent | base_isolated | 3,296 | 10,363 | 30 | fail | 2.42 |
| 13 | agent | base_isolated | 3,296 | 10,363 | 45 | fail | 2.48 |
| 14 | agent | base_isolated | 4,532 | 28,786 | 30 | fail | 2.85 |
| 15 | agent | base_isolated | 4,532 | 28,786 | 45 | fail | 2.86 |
| 16 | agent | base_isolated | 4,532 | 16,192 | 30 | fail | 2.22 |
| 17 | agent | base_isolated | 4,532 | 16,192 | 45 | fail | 2.26 |
| 18 | agent | base_isolated | 4,532 | 10,363 | 30 | fail | 2.38 |
| 19 | agent | base_isolated | 4,532 | 10,363 | 45 | fail | 2.45 |
| 20 | agent | base_isolated | 4,985 | 13,763 | 36 | fail | 2.28 |
| 21 | agent | base_isolated | 5,484 | 11,699 | 43 | fail | 2.33 |
| 22 | agent | base_isolated | 5,768 | 9,944 | 50 | fail | 2.42 |
| 23 | agent | fixed_base | - | - | - | fail | 4.65 |
| 24 | agent | base_isolated | 5,768 | 8,452 | 50 | fail | 2.48 |
| 25 | agent | base_isolated | 4,903 | 8,452 | 40 | fail | 2.48 |

## Why the brief is not buildable as posed

No design in the buildable isolation space met every acceptance target on this site; the table above shows the binding constraints. The recommendation is to revisit the brief itself (site, moat clearance, or supplemental damping outside the standard system) rather than to accept a design that fails verification.

## Engineering notes

Screening of the buildable isolation space and follow-up refinements did not find a compliant solution. The best simulated candidate remains governed by floor acceleration, with isolator displacement also far beyond the 0.4 m moat; increasing characteristic strength reduces travel only modestly and drives accelerations up, while lengthening/softening the isolation period worsens moat demand. Fixed-base response is substantially worse, so the governing feasibility issue is the combination of near-fault soft-ground input, acute-care limits, and the 0.4 m parcel moat.

*Commentary written by the design agent. Unlike the tables above it is prose, not a simulation output, and carries no independent verification.*

---
*Generated by SeismoForge. Every number in the tables above comes from the simulation suite described in the verification basis; the suite is deterministic and reproducible from the project brief. Known modelling limitations of that basis are listed in the repository README - read them before acting on this report.*

> **Concept-stage prototype study - not for construction.** This report is produced by an automated design agent. It must be reviewed and signed off by a licensed structural engineer before it informs any design, procurement, or construction decision. The model class, acceptance limits, and synthetic ground motions are SeismoForge's own benchmark basis, not a substitute for code-compliant analysis of a project-specific hazard.
