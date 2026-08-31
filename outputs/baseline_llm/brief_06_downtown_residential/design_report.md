# Direct-model design note - brief 06 downtown residential

**Verdict: PROCEED** (one-shot answer from gpt-5.5, no simulation)

- System: base_isolated
- Qd = 4,590 kN
- Kd = 18,000 kN/m
- Dy = 25 mm

Use lead-rubber base isolation rather than a fixed-base frame, because the fixed-base fundamental period is close enough to the site band to risk floor accelerations and drift concentration in a 12-storey residential tower, while isolation can decouple the superstructure. The building seismic weight is about 76,500 kN; I have selected lead strength Qd about 4,590 kN, i.e. 6% W, post-yield rubber stiffness 18,000 kN/m, and yield displacement 25 mm. At a concept displacement of roughly 0.25–0.30 m, the effective isolation stiffness is about 33,000–36,000 kN/m, giving an effective isolated period of about 2.9–3.1 s and equivalent damping in the order of 20%, which should keep displacement comfortably below the 0.5 m moat, limit base shear to around 0.18–0.20 W, and keep superstructure drifts and floor accelerations below the stated 0.012 and 0.55 g limits. The rubber stiffness provides a recentering ratio comfortably above the lead offset at the expected peak displacement, so residual displacement should remain below 0.12 m; the moat is therefore not expected to be the binding constraint for this concept.

*No response-history verification was performed. Every number above is the model's judgment, not a simulation output.*
