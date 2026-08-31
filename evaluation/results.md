# SeismoForge - measured comparison

Primary metric: briefs resolved correctly out of 10 (a 'proceed' must
survive independent re-simulation of the submitted design; an
infeasible brief must be flagged, not forced).

| System | Correct briefs | Wall time (s) |
|---|---|---|
| baseline | **3/10** | 0.4 |
| llm_direct | **6/10** | - |
| offline | **10/10** | 38.6 |
| assisted | **10/10** | 71.3 |
| agent | **10/10** | 337.8 |

## Per-brief outcomes

| Brief | baseline | llm_direct | offline | assisted | agent |
|---|---|---|---|---|---|
| brief_01_coastal_hospital | wrong - claimed proceed but fails ['peak_floor_accel_g', 'base_shear_coeff'] | wrong - claimed proceed but fails ['peak_isolator_disp_m'] | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design |
| brief_02_valley_office | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design |
| brief_03_hillside_warehouse | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design |
| brief_04_metro_datacenter | wrong - claimed proceed but fails ['peak_floor_accel_g'] | wrong - claimed proceed but fails ['peak_floor_accel_g'] | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design |
| brief_05_riverside_school | wrong - claimed proceed but fails ['peak_floor_accel_g'] | wrong - claimed proceed but fails ['peak_floor_accel_g'] | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design |
| brief_06_downtown_residential | wrong - claimed proceed but fails ['peak_floor_accel_g'] | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design |
| brief_07_plains_office | wrong - claimed proceed but fails ['peak_floor_accel_g'] | wrong - claimed proceed but fails ['peak_floor_accel_g'] | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design |
| brief_08_lakeside_hospital | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design |
| brief_09_port_warehouse | wrong - claimed proceed but fails ['peak_floor_accel_g', 'base_shear_coeff'] | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design | CORRECT - verified design |
| brief_10_cliffside_clinic | wrong - claimed proceed but fails ['peak_drift_ratio', 'peak_floor_accel_g', 'base_shear_coeff', 'peak_isolator_disp_m'] | CORRECT - correctly flagged infeasible brief | CORRECT - correctly flagged infeasible brief | CORRECT - correctly flagged infeasible brief | CORRECT - correctly flagged infeasible brief |
