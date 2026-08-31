# Direct-model design note - brief 01 coastal hospital

**Verdict: PROCEED** (one-shot answer from gpt-5.5, no simulation)

- System: base_isolated
- Qd = 590 kN
- Kd = 5,362 kN/m
- Dy = 10 mm

Recommend lead-rubber base isolation rather than a fixed-base shear-wall hospital: the fixed-base fundamental period is around 0.75–0.8 s, close enough to the 1.1 s soft-soil pulse that accelerations and base shear are unlikely to meet an immediate-occupancy brief. I have therefore selected the softest practical rubber stiffness, Kd = 5,362 kN/m, giving a post-yield isolated period of about 4.5 s and an effective period of about 4.0 s at design displacement, well separated from the site period. The lead strength Qd = 590 kN is about 2.2% of seismic weight, enough for roughly 10–14% equivalent damping over the expected 0.4–0.7 m displacement range while keeping the recentering index Qd/Kd = 0.11 m below the 0.12 m residual displacement limit. With Dy = 0.01 m the isolators yield early. Even at the full 0.9 m moat displacement the isolation shear would be only (590 + 5,362 x 0.9) / 26,980 = about 0.20 W, below the 0.30 limit, so superstructure drift in the very stiff wall block should remain well below 0.007 and floor accelerations should be in the operational range.

*No response-history verification was performed. Every number above is the model's judgment, not a simulation output.*
