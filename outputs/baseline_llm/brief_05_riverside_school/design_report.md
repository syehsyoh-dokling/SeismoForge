# Direct-model design note - brief 05 riverside school

**Verdict: PROCEED** (one-shot answer from gpt-5.5, no simulation)

- System: base_isolated
- Qd = 1,200 kN
- Kd = 10,000 kN/m
- Dy = 20 mm

Use lead-rubber isolation rather than fixed base: the fixed-base four-storey shear building has a fundamental period around 0.7 s, too close to the 1 s soft-alluvium demand to be a good school solution for acceleration and base-shear limits. A moderate-strength, moderate-period LRB layer is selected: Qd/W about 6.4%, rubber stiffness 10,000 kN/m, and yield displacement 20 mm. At the governing moat displacement of about 0.45-0.50 m this gives effective stiffness roughly 12,400-12,700 kN/m, effective isolated period about 2.4-2.5 s, equivalent viscous damping about 12%, peak shear coefficient about (1200+10000D)/18835 = 0.30-0.33, and Qd/kd = 0.12 m for recentring. This should move the school safely away from the 1 s site pulse while retaining enough damping for the 0.6 m moat and keeping superstructure drift and floor accelerations within the stated concept targets.

*No response-history verification was performed. Every number above is the model's judgment, not a simulation output.*
