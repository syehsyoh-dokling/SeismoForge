# Direct-model design note - brief 09 port warehouse

**Verdict: PROCEED** (one-shot answer from gpt-5.5, no simulation)

- System: base_isolated
- Qd = 600 kN
- Kd = 5,000 kN/m
- Dy = 20 mm

The fixed-base frame is borderline/not preferred: its first-mode period is about 0.67 s for the 3-storey 200 MN/m shear frame, close enough to the 0.9 s reclaimed-fill site pulse that floor accelerations and base shear would likely govern. I would isolate it with a moderately soft lead-rubber layer. With W = 3 x 450 t x 9.81 = 13,244 kN, Qd = 600 kN is 4.5%W and kd = 5,000 kN/m gives an isolation period on rubber stiffness of about 3.24 s, away from the site period but not so soft that moat demand is excessive. At the 0.45 m moat displacement the isolator shear is Qd + kdD = 2,850 kN, V/W = 0.22, well below 0.55; the effective stiffness is about 6,333 kN/m and the effective period is about 2.9 s. Qd/kd = 0.12 m, so the recentring limit is just satisfied, and dy = 0.02 m is within the practical LRB range. Superstructure drift and floor acceleration should be comfortably below the stated limits at these force levels.

*No response-history verification was performed. Every number above is the model's judgment, not a simulation output.*
