# Direct-model design note - brief 02 valley office

**Verdict: PROCEED** (one-shot answer from gpt-5.5, no simulation)

- System: base_isolated
- Qd = 2,800 kN
- Kd = 15,000 kN/m
- Dy = 25 mm

Use lead-rubber isolation rather than relying on the fixed-base frame: the fixed-base period is likely around 1.3-1.4 s for the eight-storey shear building, close enough to the valley deposit amplification range that floor accelerations are not a comfortable pass against the 0.55 g limit. For the isolated option I would set the rubber stiffness at about 15,000 kN/m, giving an isolation period of about 3.5 s on post-yield stiffness, and use a lead characteristic strength of 2,800 kN, about 6% of seismic weight, with a 25 mm yield displacement. At the 0.55 m moat limit the secant stiffness is about 20,100 kN/m and the base-shear coefficient is about (15,000*0.55+2,800)/47,100 = 0.235, comfortably below 0.45; at more probable peak displacement around 0.35-0.45 m it gives an effective period about 3.0-3.2 s and equivalent viscous damping on the order of 20%, which should keep isolator displacement inside the moat and transmitted floor accelerations well below 0.55 g. The restoring ratio Kd*D/Qd at the displacement limit is about 3, so recentring should satisfy the 0.12 m residual limit.

*No response-history verification was performed. Every number above is the model's judgment, not a simulation output.*
