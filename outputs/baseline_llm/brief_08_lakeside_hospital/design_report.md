# Direct-model design note - brief 08 lakeside hospital

**Verdict: PROCEED** (one-shot answer from gpt-5.5, no simulation)

- System: base_isolated
- Qd = 590 kN
- Kd = 4,500 kN/m
- Dy = 20 mm

Select lead-rubber base isolation for the hospital continuity target; the fixed-base three-storey frame would be relatively stiff near the site-period range and is unlikely to meet the 0.4 g floor-acceleration objective. Total seismic weight is about 14,715 kN. I have sized a soft, well-recentring isolation layer with characteristic lead strength about 4%W (590 kN), post-yield rubber stiffness 4,500 kN/m (post-yield period about 3.6 s), and yield displacement 20 mm. At a concept displacement in the 0.35–0.45 m range, the effective stiffness is roughly 5,800–6,200 kN/m, giving an effective isolated period about 3.1–3.2 s and equivalent damping of roughly 20–25%. The corresponding base shear coefficient is about Q/W + kdD/W = 0.15–0.18, comfortably below 0.3, with moat demand below the 0.55 m clearance. The rubber restoring force at design displacement substantially exceeds the lead force, so residual offset is expected to remain below the 0.12 m recentering limit while floor accelerations and interstorey drifts are reduced to the required hospital-operational range.

*No response-history verification was performed. Every number above is the model's judgment, not a simulation output.*
