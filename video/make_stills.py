#!/usr/bin/env python3
"""Generate the non-GUI stills the video needs for sections 5 and 6.

Section 5 is the changelog: two of its entries are claims about experiments
that were removed, so the repository as it stands cannot show them running.
This script reconstructs both from the shipped code rather than illustrating
them, and says on each still exactly what was changed to get back to the old
behaviour:

  * Iteration 1, "the verifier was wrong": the shipped motion generator is run
    against a copy of itself with the Clough-Penzien high-pass stage removed -
    which is what "plain Kanai-Tajimi synthesis" means in that changelog row -
    and the same 50-candidate grid is swept under each.
  * Iteration 2, "pure failure-driven refinement": ``forge.designer.refine`` is
    called with only the governing failed check visible to it. That is the
    removed strategy, expressed against the current code: fix the worst check,
    rerun. The shipped loop, which sees every failed check at once, is run on
    the same brief for comparison.

Section 6 needs no reconstruction. Its numbers are read out of the committed
result and trajectory files and printed with their file and line, so a viewer
can check them.

Everything lands in ``video/stills/``. Run it from a machine with openseespy:

    python3 video/make_stills.py

The two sweeps are the slow part - 500 nonlinear analyses, about a minute.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from agent.tools import ForgeTools
from forge import motions, simulate
from forge.brief_parser import parse_brief_file
from forge.building import Design, IsolationDesign
from forge.checks import acceptance_report
from forge.designer import clamp, kd_for_period, refine, rule_of_thumb
from forge.motions import DT, G, N_HARMONICS, SOIL_DAMPING
from forge.simulate import assess

STILLS = REPO / "video" / "stills"
HOSPITAL = REPO / "briefs" / "brief_01_coastal_hospital.md"

# --------------------------------------------------------------------------
# PNG rendering. The stills are written as text as well, because the text is
# what a reader can check, but the video needs images it can cut to.
# --------------------------------------------------------------------------

FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

INK = {
    "bg": "#0f1115",
    "text": "#e8ecf4",
    "dim": "#7d8698",
    "rule": "#2b3241",
    "title": "#cfe0ff",
    "good": "#4ade80",
    "bad": "#ff6b6b",
    "warn": "#f5c451",
    "accent": "#8fa4d0",
}

FONT_PX = 30
PAD = 56


def _fonts():
    from PIL import ImageFont
    return (ImageFont.truetype(FONT_MONO, FONT_PX),
            ImageFont.truetype(FONT_MONO_BOLD, FONT_PX),
            ImageFont.truetype(FONT_SANS_BOLD, int(FONT_PX * 1.25)))


def _line_ink(line: str) -> tuple[str, bool]:
    """Colour and weight for one line of a text still."""
    stripped = line.strip()
    if not stripped:
        return INK["text"], False
    if set(stripped) <= {"-"}:
        return INK["rule"], False
    if stripped.startswith("NOTE:"):
        return INK["warn"], False
    if stripped.startswith("Reproduce:") or stripped.startswith("Sources"):
        return INK["dim"], False
    # " -> " marks a governing-check flip. Guard against source lines: a
    # return annotation is an arrow too.
    if "PASS" in line or (" -> " in line and not {"(", ":"} & set(line)):
        return INK["good"], False
    if stripped.endswith("fail") or '"error"' in line:
        return INK["bad"], False
    if stripped.startswith(("brief ", "grid ", "records ", "design ", "verdict ",
                            "  brief", "  design", "  verdict")):
        return INK["accent"], False
    return INK["text"], False


def write_still(stem: str, lines: list[str], title: str | None = None) -> None:
    """Write one still as text and as a PNG the video can cut to."""
    (STILLS / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print(f"  {stem}.txt written; install pillow for the PNG")
        return

    mono, mono_bold, sans = _fonts()
    head = title if title is not None else lines[0]
    body = lines[1:] if title is None else lines

    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    cw = dummy.textlength("M", font=mono)
    lh = int(FONT_PX * 1.46)
    head_h = int(FONT_PX * 1.25 * 1.7)

    width = int(max(
        dummy.textlength(head, font=sans),
        max((dummy.textlength(line, font=mono) for line in body), default=0),
    ) + 2 * PAD)
    height = PAD + head_h + 18 + lh * len(body) + PAD

    image = Image.new("RGB", (width, height), INK["bg"])
    draw = ImageDraw.Draw(image)
    draw.text((PAD, PAD), head, font=sans, fill=INK["title"])
    y = PAD + head_h
    draw.line([(PAD, y), (width - PAD, y)], fill=INK["rule"], width=2)
    y += 18
    for line in body:
        colour, bold = _line_ink(line)
        draw.text((PAD, y), line, font=mono_bold if bold else mono, fill=colour)
        y += lh
    image.save(STILLS / f"{stem}.png")
    print(f"  {stem}.png  {width} x {height}")

# The sweep grid. 5 x 5 x 2 = 50 candidates, the "50-point sweep" of the
# changelog's iteration 1.
QD_FRACTIONS = (0.04, 0.07, 0.10, 0.13, 0.16)
PERIODS_S = (2.0, 2.5, 3.0, 3.5, 4.0)
DY_M = (0.015, 0.03)


# --------------------------------------------------------------------------
# Iteration 1: the generator before the high-pass was added
# --------------------------------------------------------------------------

def synthesize_unfiltered(site, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """``forge.motions.synthesize`` without the Clough-Penzien stage.

    Line for line the shipped generator, minus ``amplitude *= highpass``. That
    single missing stage is what let the process carry displacement energy at
    periods no real record has, which is what made every isolated candidate
    fail.
    """
    duration = float(site.duration_sec)
    count = int(round(duration / DT)) + 1
    time = np.arange(count) * DT

    omega_soil = 2.0 * math.pi / float(site.soil_period_sec)
    freqs = np.linspace(0.15, 12.0, N_HARMONICS)
    omega = 2.0 * math.pi * freqs
    num = omega_soil**4 + (2.0 * SOIL_DAMPING * omega_soil * omega) ** 2
    den = (omega_soil**2 - omega**2) ** 2 + (2.0 * SOIL_DAMPING * omega_soil * omega) ** 2
    amplitude = np.sqrt(num / den) / np.sqrt(1.0 + 0.35 * omega)
    # (the high-pass stage belongs here)

    rng = np.random.default_rng(seed)
    phases = rng.uniform(0.0, 2.0 * math.pi, size=freqs.shape)
    signal = np.zeros(count)
    for a, w, p in zip(amplitude, omega, phases):
        signal += a * np.sin(w * time + p)

    rise_end = 0.15 * duration
    hold_end = 0.55 * duration
    envelope = np.ones(count)
    rising = time < rise_end
    envelope[rising] = (time[rising] / rise_end) ** 2
    decaying = time > hold_end
    envelope[decaying] = np.exp(-0.4 * (time[decaying] - hold_end))
    signal *= envelope

    peak = float(np.max(np.abs(signal)))
    if peak > 0.0:
        signal *= float(site.pga_g) * G / peak
    return time, signal


def grid(spec) -> list[Design]:
    weight = spec.seismic_weight_kn
    return [
        Design("base_isolated", IsolationDesign(
            qd_kn=frac * weight, kd_kn_m=kd_for_period(spec, period), dy_m=dy))
        for frac in QD_FRACTIONS
        for period in PERIODS_S
        for dy in DY_M
    ]


def sweep(spec, designs: list[Design]) -> dict:
    """Pass count and the closest miss, for one motion generator."""
    passing, worst = 0, []
    for design in designs:
        report = acceptance_report(spec, design, assess(spec, design))
        util = report["governing_utilization"]
        if report["passed"]:
            passing += 1
        worst.append((util if util is not None else float("inf"),
                      report["governing_check"]))
    best = min(worst)
    return {"passing": passing, "total": len(designs),
            "closest_utilization": best[0], "closest_check": best[1]}


def still_verifier_sweep(spec) -> None:
    designs = grid(spec)
    shipped = simulate.synthesize

    simulate.synthesize = synthesize_unfiltered
    try:
        before = sweep(spec, designs)
    finally:
        simulate.synthesize = shipped
    after = sweep(spec, designs)

    lines = [
        "ITERATION 1  -  the verifier was wrong, not the design space",
        "",
        f"brief    {spec.name}",
        f"grid     {len(QD_FRACTIONS)} x {len(PERIODS_S)} x {len(DY_M)}"
        f" = {len(designs)} candidates",
        f"         Qd/W {QD_FRACTIONS[0]:.2f}-{QD_FRACTIONS[-1]:.2f}"
        f"   T_iso {PERIODS_S[0]:.1f}-{PERIODS_S[-1]:.1f} s"
        f"   Dy {DY_M[0]:.3f}-{DY_M[-1]:.3f} m",
        f"records  {spec.site.records} per candidate,"
        f" {len(designs) * spec.site.records} nonlinear analyses per column",
        "",
        "                                    passing    closest miss",
        "-" * 68,
        f"  plain Kanai-Tajimi synthesis      {before['passing']:>3} / {before['total']}"
        f"      {before['closest_check']} at {before['closest_utilization']:.2f}",
        f"  + Clough-Penzien high-pass        {after['passing']:>3} / {after['total']}"
        f"      {after['closest_check']} at {after['closest_utilization']:.2f}",
        "-" * 68,
        "",
        "The design space did not change between these two rows. Only the test",
        "did. Every candidate failed because the ground motions carried",
        "displacement energy at periods no real record has - exactly the band a",
        "base-isolated building lives in.",
        "",
        "Reproduce: video/make_stills.py, synthesize_unfiltered() is",
        "forge/motions.py:synthesize with the line 'amplitude *= highpass'",
        "removed.",
    ]
    write_still("05b_verifier_sweep", lines)
    return before, after


# --------------------------------------------------------------------------
# Iteration 1, the picture: what the two generators do to long periods
# --------------------------------------------------------------------------

def displacement_spectrum(accel: np.ndarray, periods: np.ndarray,
                          damping: float = 0.05) -> np.ndarray:
    """Peak SDOF displacement per period. Newmark linear acceleration."""
    out = np.empty_like(periods)
    for index, period in enumerate(periods):
        w = 2.0 * math.pi / period
        k, c, m = w * w, 2.0 * damping * w, 1.0
        a0, a1 = 1.0 / (0.25 * DT * DT), 0.5 / (0.25 * DT)
        keff = k + a0 * m + a1 * c
        u = v = a = 0.0
        peak = 0.0
        for ag in accel:
            rhs = (-m * ag + m * (a0 * u + a1 * v + a)
                   + c * (a1 * u + v + 0.25 * DT * a))
            u_new = rhs / keff
            v_new = v + DT * (0.5 * a + 0.5 * (a0 * (u_new - u) - a1 * v - a))
            a = a0 * (u_new - u) - a1 * v - a
            u, v = u_new, v_new
            peak = max(peak, abs(u))
        out[index] = peak
    return out


def still_spectrum(spec) -> None:
    seed = spec.site.seed_base
    _, unfiltered = synthesize_unfiltered(spec.site, seed)
    _, shipped = motions.synthesize(spec.site, seed)
    periods = np.linspace(0.2, 6.0, 60)
    sd_before = displacement_spectrum(unfiltered, periods)
    sd_after = displacement_spectrum(shipped, periods)

    top = float(max(sd_before.max(), sd_after.max())) * 1.08
    W, H = 900, 470
    L, R, T, B = 78, 26, 54, 56
    px = lambda t: L + (t - periods[0]) / (periods[-1] - periods[0]) * (W - L - R)
    py = lambda d: H - B - d / top * (H - T - B)

    def path(values):
        return " ".join(f"{px(t):.1f},{py(d):.1f}" for t, d in zip(periods, values))

    ticks_x = [1, 2, 3, 4, 5, 6]
    step = 10 ** math.floor(math.log10(top))
    ticks_y = [v for v in np.arange(0, top, step / 2) if v > 0][:8]

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'font-family="ui-sans-serif,Segoe UI,Helvetica,sans-serif">',
        f'<rect width="{W}" height="{H}" fill="#0f1115"/>',
        f'<rect x="{px(1.8):.0f}" y="{T}" width="{px(4.5) - px(1.8):.0f}" '
        f'height="{H - T - B}" fill="#2b3550" opacity="0.55"/>',
        f'<text x="{(px(1.8) + px(4.5)) / 2:.0f}" y="{T + 20}" fill="#8fa4d0" '
        f'font-size="13" text-anchor="middle">isolation period band</text>',
        f'<line x1="{L}" y1="{H - B}" x2="{W - R}" y2="{H - B}" stroke="#4a5163"/>',
        f'<line x1="{L}" y1="{T}" x2="{L}" y2="{H - B}" stroke="#4a5163"/>',
    ]
    for t in ticks_x:
        svg.append(f'<line x1="{px(t):.0f}" y1="{H - B}" x2="{px(t):.0f}" '
                   f'y2="{H - B + 5}" stroke="#4a5163"/>')
        svg.append(f'<text x="{px(t):.0f}" y="{H - B + 22}" fill="#9aa3b5" '
                   f'font-size="13" text-anchor="middle">{t}</text>')
    for d in ticks_y:
        svg.append(f'<line x1="{L - 5}" y1="{py(d):.0f}" x2="{W - R}" '
                   f'y2="{py(d):.0f}" stroke="#242a35"/>')
        svg.append(f'<text x="{L - 10}" y="{py(d) + 4:.0f}" fill="#9aa3b5" '
                   f'font-size="12" text-anchor="end">{d:.2f}</text>')
    svg += [
        f'<polyline fill="none" stroke="#ff6b6b" stroke-width="2.6" '
        f'points="{path(sd_before)}"/>',
        f'<polyline fill="none" stroke="#4ade80" stroke-width="2.6" '
        f'points="{path(sd_after)}"/>',
        f'<text x="{L}" y="30" fill="#e8ecf4" font-size="17" '
        f'font-weight="600">Displacement response spectrum, 5% damped '
        f'- one record, same seed</text>',
        f'<text x="{W - R}" y="{H - 14}" fill="#9aa3b5" font-size="12" '
        f'text-anchor="end">period T (s)</text>',
        f'<text x="{L}" y="{H - 14}" fill="#9aa3b5" font-size="12">'
        f'Sd (m)</text>',
        f'<rect x="{W - R - 268}" y="{T + 14}" width="256" height="52" '
        f'fill="#161a22" stroke="#2b3241" rx="6"/>',
        f'<line x1="{W - R - 254}" y1="{T + 32}" x2="{W - R - 226}" '
        f'y2="{T + 32}" stroke="#ff6b6b" stroke-width="2.6"/>',
        f'<text x="{W - R - 218}" y="{T + 37}" fill="#e8ecf4" font-size="13">'
        f'plain Kanai-Tajimi</text>',
        f'<line x1="{W - R - 254}" y1="{T + 52}" x2="{W - R - 226}" '
        f'y2="{T + 52}" stroke="#4ade80" stroke-width="2.6"/>',
        f'<text x="{W - R - 218}" y="{T + 57}" fill="#e8ecf4" font-size="13">'
        f'+ Clough-Penzien high-pass</text>',
        "</svg>",
    ]
    (STILLS / "05c_spectrum.svg").write_text("\n".join(svg) + "\n",
                                             encoding="utf-8")
    band = (periods >= 1.8) & (periods <= 4.5)
    ratio = float(np.max(sd_before[band] / sd_after[band]))
    render_spectrum_png(periods, sd_before, sd_after, ratio)
    print(f"  across the 1.8-4.5 s isolation band the unfiltered process "
          f"demands up to {ratio:.2f}x the displacement")


def render_spectrum_png(periods, sd_before, sd_after, ratio: float) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  05c_spectrum.svg written; install pillow for the PNG")
        return

    W, H = 1780, 940
    L, R, T, B = 168, 60, 132, 118
    top = float(max(sd_before.max(), sd_after.max())) * 1.15
    px = lambda t: L + (t - periods[0]) / (periods[-1] - periods[0]) * (W - L - R)
    py = lambda d: H - B - d / top * (H - T - B)

    image = Image.new("RGB", (W, H), INK["bg"])
    draw = ImageDraw.Draw(image)
    body = ImageFont.truetype(FONT_MONO, 27)
    head = ImageFont.truetype(FONT_SANS_BOLD, 38)
    small = ImageFont.truetype(FONT_MONO, 24)

    draw.rectangle([px(1.8), T, px(4.5), H - B], fill="#232c42")
    draw.text(((px(1.8) + px(4.5)) / 2, T + 14), "isolation period band",
              font=small, fill=INK["accent"], anchor="ma")

    step = 10 ** math.floor(math.log10(top))
    for value in np.arange(step / 2, top, step / 2):
        draw.line([(L, py(value)), (W - R, py(value))], fill="#1c222c", width=2)
        draw.text((L - 18, py(value)), f"{value:.2f}", font=small,
                  fill=INK["dim"], anchor="rm")
    for tick in (1, 2, 3, 4, 5, 6):
        draw.line([(px(tick), H - B), (px(tick), H - B + 10)],
                  fill=INK["rule"], width=2)
        draw.text((px(tick), H - B + 20), str(tick), font=small,
                  fill=INK["dim"], anchor="ma")
    draw.line([(L, H - B), (W - R, H - B)], fill=INK["rule"], width=3)
    draw.line([(L, T), (L, H - B)], fill=INK["rule"], width=3)

    for values, colour in ((sd_before, INK["bad"]), (sd_after, INK["good"])):
        draw.line([(px(t), py(d)) for t, d in zip(periods, values)],
                  fill=colour, width=5, joint="curve")

    draw.text((L, 44), "Displacement response spectrum, 5% damped "
                       "- one record, same seed", font=head, fill=INK["title"])
    draw.text((L, 92), f"across the isolation band the unfiltered process "
                       f"demands up to {ratio:.2f}x the displacement",
              font=small, fill=INK["dim"])
    draw.text((W - R, H - 36), "period T (s)", font=small, fill=INK["dim"],
              anchor="ra")
    draw.text((L - 18, T - 16), "Sd (m)", font=small, fill=INK["dim"],
              anchor="rb")

    # Upper left: the only corner both curves stay out of, since displacement
    # demand is small at short period.
    lx, ly = L + 34, T + 30
    draw.rectangle([lx, ly, lx + 500, ly + 108], fill="#161a22",
                   outline=INK["rule"], width=2)
    for index, (colour, label) in enumerate((
            (INK["bad"], "plain Kanai-Tajimi"),
            (INK["good"], "+ Clough-Penzien high-pass"))):
        y = ly + 32 + index * 46
        draw.line([(lx + 26, y), (lx + 82, y)], fill=colour, width=5)
        draw.text((lx + 100, y), label, font=body, fill=INK["text"], anchor="lm")

    image.save(STILLS / "05c_spectrum.png")
    print(f"  05c_spectrum.png  {W} x {H}")


# --------------------------------------------------------------------------
# Iteration 2: the refinement strategy that was removed
# --------------------------------------------------------------------------

def trace(spec, max_iters: int = 15) -> tuple[list[str], list[str]]:
    """Refinement alone, from the rule-of-thumb start. Lines and check order."""
    design = clamp(rule_of_thumb(spec), spec)
    lines, governing = [], []
    for iteration in range(max_iters):
        report = acceptance_report(spec, design, assess(spec, design))
        iso = design.isolation
        util = report["governing_utilization"]
        governing.append(report["governing_check"])
        lines.append(
            f"  {iteration:>2}   Qd {iso.qd_kn:>7.0f} kN   Kd {iso.kd_kn_m:>7.0f} kN/m"
            f"   Dy {iso.dy_m:.3f} m   {report['governing_check']:<20}"
            f" {util:.2f}   {'PASS' if report['passed'] else 'fail'}")
        if report["passed"]:
            lines.append(f"       converged after {iteration} refinement steps")
            return lines, governing
        nxt = refine(spec, design, report)
        if nxt is None:
            lines.append("       no move available")
            return lines, governing
        design = nxt
    lines.append(f"       still failing after {max_iters} iterations")
    return lines, governing


def still_refinement(spec) -> None:
    """Why single-failure refinement was removed: the constraints are coupled.

    The changelog's iteration 2 records fifteen non-converging iterations. That
    result belongs to the refinement moves as they were then; those moves were
    retuned when the strategy was replaced, so it is not reproducible against
    the code in this repository and this still does not claim to reproduce it.
    What is reproducible, and is the reason the strategy was removed, is the
    coupling itself: the check that governs keeps moving between limits that
    want opposite changes.
    """
    lines_out, governing = trace(spec)
    flips = [f"{a} -> {b}" for a, b in zip(governing, governing[1:]) if a != b]
    lines = [
        "ITERATION 2  -  why the local refinement strategy was removed",
        "",
        f"brief    {spec.name}",
        "         refinement alone, from the rule-of-thumb start, without the",
        "         coarse screening stage that precedes it in the shipped policy",
        "",
        "  it    design                                     governing check",
        "-" * 92,
        *lines_out,
        "-" * 92,
        "",
        "The governing check moves:",
        *[f"    {flip}" for flip in flips],
        "",
        "That is the coupling. Lowering transmitted force wants a softer",
        "rubber; holding travel inside the moat and recentring want a stiffer",
        "one. A strategy that fixes only the worst failed check chases the",
        "constraints around instead of reconciling them, which is why it was",
        "removed in favour of coarse screening followed by refinement.",
        "",
        "NOTE: the fifteen non-converging iterations recorded in the changelog",
        "belong to the refinement moves as they were at that time. Those moves",
        "were retuned when the strategy was replaced, so that run is not",
        "reproducible against this code and is not reproduced here. The",
        "changelog entry is the record of it.",
        "",
        "Reproduce: video/make_stills.py",
    ]
    write_still("05d_coupling", lines)


# --------------------------------------------------------------------------
# Iteration 4: the change that mattered most, as code
# --------------------------------------------------------------------------

def still_veto(spec) -> None:
    """The veto as code, and then the veto actually firing.

    The demonstration submits the rule-of-thumb design - the one the baseline
    submits unverified, and the one the run in section 3 opens with - together
    with a 'proceed' verdict, and prints what write_report returns.
    """
    source = (REPO / "agent" / "tools.py").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(source)
                 if line.strip().startswith("def write_report("))
    end = next(i for i in range(start, len(source))
               if "paths = write_outputs(" in source[i])
    body = [f"  {n + 1:>4} | {source[n]}" for n in range(start, end)]

    tools = ForgeTools(out_root=REPO / "outputs" / "still_demo")
    design = clamp(rule_of_thumb(spec), spec)
    answer = tools.write_report(brief=spec.name, design=design.as_dict(),
                                verdict="proceed")

    lines = [
        "ITERATION 4  -  the change that contributed most",
        "",
        "The report writer re-simulates the design it was asked to recommend,",
        "and refuses the verdict if the physics disagrees.",
        "",
        "agent/tools.py",
        "-" * 78,
        *body,
        "-" * 78,
        "",
        "",
        "THE VETO FIRING",
        "",
        f"  brief    {spec.name}",
        f"  design   {json.dumps(design.as_dict()['isolation'])}",
        "  verdict  proceed",
        "",
        "  write_report returns:",
        "",
        *[f"    {line}" for line in json.dumps(answer, indent=2).splitlines()],
        "",
        "No report was written. The deliverable cannot disagree with the",
        "physics, because the physics is re-run to render it.",
    ]
    write_still("05e_report_veto", lines)


# --------------------------------------------------------------------------
# Section 6: the agency experiment, read out of the committed files
# --------------------------------------------------------------------------

def usage_line(name: str) -> tuple[int, dict]:
    path = REPO / "trajectories" / f"trajectory_{name}.jsonl"
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        event = json.loads(raw)
        if event.get("kind") == "usage":
            return number, event
    raise LookupError(f"no usage event in {path}")


def still_agency() -> None:
    results = json.loads((REPO / "evaluation" / "results.json").read_text(
        encoding="utf-8"))
    a_line, a_use = usage_line("assisted")
    g_line, g_use = usage_line("agent")
    ratio = g_use["input_tokens"] / a_use["input_tokens"]

    lines = [
        "THE AGENCY EXPERIMENT  -  same ten briefs, same judge",
        "",
        "                     correct   wall time    input tokens   output",
        "-" * 74,
    ]
    for mode, label in (("offline", "deterministic"), ("assisted", "assisted"),
                        ("agent", "full agent")):
        row = results[mode]
        use = {"assisted": a_use, "agent": g_use}.get(mode)
        tok = f"{use['input_tokens']:>12,}   {use['output_tokens']:>6,}" if use \
            else f"{'no model':>12}   {'-':>6}"
        lines.append(f"  {label:<18} {row['correct']:>2}/{row['total']}"
                     f"   {row['wall_time_sec']:>8.1f} s   {tok}")
    lines += [
        "-" * 74,
        "",
        f"  {g_use['input_tokens']:,} / {a_use['input_tokens']:,} = {ratio:.1f}x"
        f" the input, for the same score.",
        "",
        "Sources, verbatim:",
        f"  evaluation/results.json          correct, total, wall_time_sec",
        f"  trajectories/trajectory_assisted.jsonl:{a_line}",
        f"    {json.dumps(a_use)}",
        f"  trajectories/trajectory_agent.jsonl:{g_line}",
        f"    {json.dumps(g_use)}",
        "",
        "The deterministic column needs no API key. It is the one a judge can",
        "reproduce from a clean checkout.",
    ]
    write_still("06a_agency", lines)


CHANGELOG_ROWS = ("Baseline", "Iteration 1", "Iteration 2", "Iteration 4",
                  "Final deterministic path")


def still_changelog() -> None:
    """The changelog rows the narration walks, lifted out of the README.

    Read from README.md rather than retyped, so the still cannot drift away
    from the deliverable it is quoting.
    """
    table = [line for line in (REPO / "README.md").read_text(
        encoding="utf-8").splitlines() if line.startswith("| **")]
    picked = [row for row in table
              if any(row.startswith(f"| **{name}") for name in CHANGELOG_ROWS)]
    if len(picked) != len(CHANGELOG_ROWS):
        raise LookupError(f"expected {len(CHANGELOG_ROWS)} changelog rows, "
                          f"found {len(picked)}")
    lines = [
        "# Improvement Changelog - the entries the video walks",
        "",
        "Quoted from README.md. The evaluator and the ten briefs are fixed",
        "throughout; the metric is briefs resolved correctly.",
        "",
        "| Stage | What we tried and why | Evidence | Decision / learning |",
        "|---|---|---|---|",
        *picked,
    ]
    (STILLS / "05a_changelog.md").write_text("\n".join(lines) + "\n",
                                             encoding="utf-8")

    # The table is far too wide to read on screen, so the PNG is a card per
    # row: stage, then the three columns wrapped and labelled.
    cells = [[c.strip() for c in row.strip("|").split("|")] for row in picked]
    render_changelog_png(cells)


def render_changelog_png(cells: list[list[str]]) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  05a_changelog.md written; install pillow for the PNG")
        return
    import re
    import textwrap

    size = 27
    mono = ImageFont.truetype(FONT_MONO, size)
    stage_font = ImageFont.truetype(FONT_SANS_BOLD, int(size * 1.3))
    head_font = ImageFont.truetype(FONT_SANS_BOLD, int(size * 1.6))
    label_font = ImageFont.truetype(FONT_MONO_BOLD, size)

    strip = lambda s: re.sub(r"\*\*|`", "", s)
    wrap = lambda s: textwrap.wrap(strip(s), width=86) or [""]
    labels = ("tried", "evidence", "learned")

    blocks = []
    for stage, *rest in cells:
        blocks.append((strip(stage), [(labels[i], wrap(rest[i]))
                                      for i in range(3)]))

    lh = int(size * 1.42)
    width, y = 1780, PAD
    height = PAD + int(size * 1.6 * 1.8) + 18
    for _, fields in blocks:
        height += int(size * 1.3 * 1.6)
        height += sum(lh * len(text) for _, text in fields) + 26
    height += PAD

    image = Image.new("RGB", (width, height), INK["bg"])
    draw = ImageDraw.Draw(image)
    draw.text((PAD, y), "Improvement Changelog - the entries the video walks",
              font=head_font, fill=INK["title"])
    y += int(size * 1.6 * 1.8)
    draw.line([(PAD, y), (width - PAD, y)], fill=INK["rule"], width=2)
    y += 18

    for stage, fields in blocks:
        draw.text((PAD, y), stage, font=stage_font, fill=INK["accent"])
        y += int(size * 1.3 * 1.6)
        for label, text in fields:
            draw.text((PAD + 24, y), f"{label:>8}", font=label_font,
                      fill=INK["dim"])
            for index, piece in enumerate(text):
                draw.text((PAD + 24 + 11 * size * 0.602, y + index * lh), piece,
                          font=mono,
                          fill=INK["good"] if "10/10" in piece else INK["text"])
            y += lh * len(text)
        y += 26
    image.save(STILLS / "05a_changelog.png")
    print(f"  05a_changelog.png  {width} x {height}")


def still_tree() -> None:
    """Where the evidence lives - the answer to 'can a judge check this'."""
    lines = [
        "WHERE THE EVIDENCE LIVES",
        "",
        "  forge/            the physics. simulate.py drives OpenSees;",
        "                    motions.py synthesizes the record suite",
        "  agent/            the tool surface and the model layer.",
        "                    tools.py holds the write_report veto",
        "  briefs/           the ten benchmark briefs, strict format",
        "  briefs_prose/     the same ten as ordinary prose",
        "  baselines/        rule-of-thumb sizing, and the model asked directly",
        "  evaluation/       results.json, results.md, and the ground-truth",
        "                    sweep that re-derives the feasibility map",
        "  trajectories/     one full trajectory per mode, jsonl and markdown",
        "  outputs/          every deliverable, one directory per mode",
        "  video/            this script, and the stills it generates",
        "",
        "  No API key is needed for forge/, briefs/, evaluation/ or the",
        "  deterministic path. That is the column a judge reproduces.",
    ]
    write_still("06b_tree", lines)


def main() -> int:
    STILLS.mkdir(parents=True, exist_ok=True)
    spec = parse_brief_file(HOSPITAL)
    still_changelog()
    still_tree()
    still_veto(spec)
    still_agency()
    still_spectrum(spec)
    still_refinement(spec)
    if "--skip-sweep" not in sys.argv:
        still_verifier_sweep(spec)  # 500 nonlinear analyses, about a minute
    print(f"\nstills written to {STILLS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
