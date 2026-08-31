# Direct-model design note - brief 04 metro datacenter

**Verdict: PROCEED** (one-shot answer from gpt-5.5, no simulation)

- System: base_isolated
- Qd = 1,413 kN
- Kd = 9,000 kN/m
- Dy = 15 mm

Use lead-rubber base isolation because the fixed-base frame is very stiff and would transmit near-short-period ground acceleration into the data floors, making the 0.3 g equipment acceleration limit the controlling criterion. Total seismic weight is 23,544 kN; the selected lead strength is about 6.0%W and the rubber stiffness gives an isolated elastic period about 3.2 s on the post-yield branch, well away from the 0.9 s site period. At an expected design displacement of roughly 0.35-0.40 m, the secant stiffness is about 12,500-13,000 kN/m, giving an effective period about 2.7-2.8 s and an equivalent viscous damping near 18-20%, so displacement should remain below the 0.6 m moat. The corresponding base shear coefficient is approximately (1413+9000D)/23544 = 0.19-0.21, comfortably below 0.35 and consistent with floor accelerations below 0.3 g; the very stiff superstructure should then keep interstorey drift far under 0.008. The 15 mm yield displacement and moderate lead strength provide stable hysteretic damping while keeping the expected residual displacement within the 0.12 m recentering limit.

*No response-history verification was performed. Every number above is the model's judgment, not a simulation output.*
