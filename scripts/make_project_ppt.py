"""
Generate a portfolio PowerPoint deck for the cover glass MQE project.

All metrics come from README.md and existing report outputs.
Dataset is synthetic only — not real supplier or customer data.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# --- Design constants ---
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)
ACCENT = RGBColor(0x00, 0x71, 0xBC)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)
LIGHT_GRAY = RGBColor(0x66, 0x66, 0x66)
BORDER_GRAY = RGBColor(0xCC, 0xCC, 0xCC)
TAKEAWAY_BG = RGBColor(0xE8, 0xF4, 0xFC)
FOOTER_TEXT = "Synthetic data only | Portfolio project"

included_figures: list[str] = []
included_screenshots: list[str] = []
missing_files: list[str] = []


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def output_path() -> Path:
    return project_root() / "outputs" / "presentation" / "cover_glass_quality_portfolio.pptx"


def new_presentation() -> Presentation:
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    return prs


def _blank_slide(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _set_slide_bg_white(slide) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)


def _add_footer(slide, text: str = FOOTER_TEXT) -> None:
    box = slide.shapes.add_textbox(Inches(0.5), Inches(7.05), Inches(12.3), Inches(0.35))
    tf = box.text_frame
    tf.text = text
    p = tf.paragraphs[0]
    p.font.size = Pt(9)
    p.font.color.rgb = LIGHT_GRAY
    p.alignment = PP_ALIGN.RIGHT


def _style_title(text_frame, size: int = 32) -> None:
    text_frame.paragraphs[0].font.size = Pt(size)
    text_frame.paragraphs[0].font.bold = True
    text_frame.paragraphs[0].font.color.rgb = ACCENT


def _add_bullets(text_frame, bullets: list[str], size: int = 18) -> None:
    for i, bullet in enumerate(bullets):
        p = text_frame.paragraphs[0] if i == 0 else text_frame.add_paragraph()
        p.text = bullet
        p.level = 0
        p.font.size = Pt(size)
        p.font.color.rgb = DARK_GRAY
        p.space_after = Pt(6)


def _add_notes(slide, notes: str) -> None:
    if notes.strip():
        slide.notes_slide.notes_text_frame.text = notes


def _inches(value) -> float:
    """Return numeric inches from an Inches/Length object or plain float."""
    return value.inches if hasattr(value, "inches") else float(value)


def _track_asset(path: Path, is_screenshot: bool) -> None:
    rel = str(path.relative_to(project_root()))
    if is_screenshot:
        if rel not in included_screenshots:
            included_screenshots.append(rel)
    elif rel not in included_figures:
        included_figures.append(rel)


def _add_placeholder(slide, left, top, box_w, box_h, label: str) -> None:
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, box_w, box_h)
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0xF5, 0xF5, 0xF5)
    box.line.color.rgb = BORDER_GRAY
    tf = box.text_frame
    tf.text = f"[Missing: {label}]"
    tf.paragraphs[0].font.size = Pt(12)
    tf.paragraphs[0].font.color.rgb = LIGHT_GRAY
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.vertical_anchor = 1  # middle


def _add_image_border(slide, left, top, width, height) -> None:
    border = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    border.fill.background()
    border.line.color.rgb = BORDER_GRAY
    border.line.width = Pt(0.75)


def _add_caption(slide, text: str, left, top, width) -> None:
    cap = slide.shapes.add_textbox(left, top, width, Inches(0.35))
    tf = cap.text_frame
    tf.text = text
    p = tf.paragraphs[0]
    p.font.size = Pt(10)
    p.font.color.rgb = LIGHT_GRAY
    p.alignment = PP_ALIGN.CENTER


def add_image_fit(
    slide,
    image_path: Path,
    left,
    top,
    box_w,
    box_h,
    caption: str | None = None,
    is_screenshot: bool = False,
) -> bool:
    """Insert image preserving aspect ratio, centered inside the box."""
    rel = str(image_path.relative_to(project_root()))
    if not image_path.is_file():
        if rel not in missing_files:
            missing_files.append(rel)
        _add_placeholder(slide, left, top, box_w, box_h, image_path.name)
        return False

    with Image.open(image_path) as img:
        img_w, img_h = img.size

    img_aspect = img_w / img_h
    box_w_in = _inches(box_w)
    box_h_in = _inches(box_h)
    box_aspect = box_w_in / box_h_in

    if img_aspect > box_aspect:
        fit_w = Inches(box_w_in)
        fit_h = Inches(box_w_in / img_aspect)
    else:
        fit_h = Inches(box_h_in)
        fit_w = Inches(box_h_in * img_aspect)

    x_off = left + (box_w - fit_w) / 2
    y_off = top + (box_h - fit_h) / 2

    _add_image_border(slide, x_off, y_off, fit_w, fit_h)
    slide.shapes.add_picture(str(image_path), x_off, y_off, width=fit_w, height=fit_h)
    _track_asset(image_path, is_screenshot)

    if caption:
        cap_top = top + box_h + Inches(0.05)
        _add_caption(slide, caption, left, cap_top, box_w)

    return True


def _add_takeaway_box(slide, text: str, left, top, width, height) -> None:
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = TAKEAWAY_BG
    shape.line.color.rgb = ACCENT
    shape.line.width = Pt(1)

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Pt(8)
    tf.margin_right = Pt(8)
    tf.margin_top = Pt(6)
    tf.margin_bottom = Pt(6)

    label = tf.paragraphs[0]
    label.text = "Takeaway"
    label.font.size = Pt(11)
    label.font.bold = True
    label.font.color.rgb = ACCENT

    body = tf.add_paragraph()
    body.text = text
    body.font.size = Pt(13)
    body.font.color.rgb = DARK_GRAY
    body.space_before = Pt(2)


def add_title_slide(
    prs: Presentation,
    title: str,
    subtitle_lines: list[str],
    author_lines: list[str] | None = None,
    notes: str = "",
) -> None:
    slide = _blank_slide(prs)
    _set_slide_bg_white(slide)

    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(11.5), Inches(1.2))
    tf = title_box.text_frame
    tf.text = title
    _style_title(tf, size=36)

    sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(3.3), Inches(11.5), Inches(1.4))
    _add_bullets(sub_box.text_frame, subtitle_lines, size=22)

    if author_lines:
        author_box = slide.shapes.add_textbox(Inches(0.8), Inches(4.85), Inches(11.5), Inches(1.0))
        atf = author_box.text_frame
        for i, line in enumerate(author_lines):
            p = atf.paragraphs[0] if i == 0 else atf.add_paragraph()
            p.text = line
            p.font.size = Pt(18 if i == 0 else 16)
            p.font.bold = i == 0
            p.font.color.rgb = DARK_GRAY if i == 0 else LIGHT_GRAY
            p.space_after = Pt(4)

    _add_footer(slide)
    _add_notes(slide, notes)


def add_thank_you_slide(
    prs: Presentation,
    name: str,
    github_url: str,
    notes: str = "",
) -> None:
    slide = _blank_slide(prs)
    _set_slide_bg_white(slide)

    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(2.4), Inches(11.5), Inches(1.0))
    ttf = title_box.text_frame
    ttf.text = "Thank You"
    _style_title(ttf, size=40)
    ttf.paragraphs[0].alignment = PP_ALIGN.CENTER

    name_box = slide.shapes.add_textbox(Inches(0.8), Inches(3.55), Inches(11.5), Inches(0.6))
    ntf = name_box.text_frame
    ntf.text = name
    ntf.paragraphs[0].font.size = Pt(22)
    ntf.paragraphs[0].font.bold = True
    ntf.paragraphs[0].font.color.rgb = DARK_GRAY
    ntf.paragraphs[0].alignment = PP_ALIGN.CENTER

    link_box = slide.shapes.add_textbox(Inches(0.8), Inches(4.35), Inches(11.5), Inches(0.6))
    ltf = link_box.text_frame
    ltf.text = f"GitHub: {github_url}"
    ltf.paragraphs[0].font.size = Pt(16)
    ltf.paragraphs[0].font.color.rgb = ACCENT
    ltf.paragraphs[0].alignment = PP_ALIGN.CENTER

    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(5.15), Inches(11.5), Inches(0.45))
    gtf = tag_box.text_frame
    gtf.text = FOOTER_TEXT
    gtf.paragraphs[0].font.size = Pt(12)
    gtf.paragraphs[0].font.color.rgb = LIGHT_GRAY
    gtf.paragraphs[0].alignment = PP_ALIGN.CENTER

    _add_notes(slide, notes)


def add_bullet_slide(
    prs: Presentation,
    title: str,
    bullets: list[str],
    notes: str = "",
    takeaway: str | None = None,
) -> None:
    slide = _blank_slide(prs)
    _set_slide_bg_white(slide)

    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.45), Inches(12.0), Inches(0.8))
    ttf = title_box.text_frame
    ttf.text = title
    _style_title(ttf, size=28)

    body_h = Inches(4.8) if takeaway else Inches(5.4)
    body_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.35), Inches(11.8), body_h)
    _add_bullets(body_box.text_frame, bullets[:5], size=19)

    if takeaway:
        _add_takeaway_box(slide, takeaway, Inches(0.8), Inches(5.85), Inches(11.8), Inches(0.95))

    _add_footer(slide)
    _add_notes(slide, notes)


def add_figure_slide(
    prs: Presentation,
    title: str,
    bullets: list[str],
    takeaway: str,
    image_path: Path,
    caption: str | None = None,
    notes: str = "",
) -> None:
    """Two-column slide: bullets + takeaway left, fitted figure right."""
    slide = _blank_slide(prs)
    _set_slide_bg_white(slide)

    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.45), Inches(12.0), Inches(0.75))
    ttf = title_box.text_frame
    ttf.text = title
    _style_title(ttf, size=28)

    left_x = Inches(0.55)
    left_w = Inches(5.0)
    body_box = slide.shapes.add_textbox(left_x, Inches(1.25), left_w, Inches(3.1))
    body_box.text_frame.word_wrap = True
    _add_bullets(body_box.text_frame, bullets[:5], size=17)

    _add_takeaway_box(slide, takeaway, left_x, Inches(4.55), left_w, Inches(1.35))

    img_x = Inches(5.85)
    img_y = Inches(1.25)
    img_w = Inches(7.0)
    img_h = Inches(4.65)
    add_image_fit(slide, image_path, img_x, img_y, img_w, img_h, caption=caption)

    _add_footer(slide)
    _add_notes(slide, notes)


def add_two_figure_slide(
    prs: Presentation,
    title: str,
    bullets: list[str],
    takeaway: str,
    image_left: Path,
    image_right: Path,
    caption_left: str | None = None,
    caption_right: str | None = None,
    notes: str = "",
) -> None:
    slide = _blank_slide(prs)
    _set_slide_bg_white(slide)

    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.45), Inches(12.0), Inches(0.75))
    ttf = title_box.text_frame
    ttf.text = title
    _style_title(ttf, size=28)

    body_box = slide.shapes.add_textbox(Inches(0.55), Inches(1.2), Inches(12.2), Inches(0.95))
    body_box.text_frame.word_wrap = True
    _add_bullets(body_box.text_frame, bullets[:3], size=16)

    _add_takeaway_box(slide, takeaway, Inches(0.55), Inches(2.25), Inches(12.2), Inches(0.75))

    img_y = Inches(3.15)
    img_h = Inches(3.55)
    add_image_fit(slide, image_left, Inches(0.55), img_y, Inches(6.0), img_h, caption_left)
    add_image_fit(slide, image_right, Inches(6.75), img_y, Inches(6.0), img_h, caption_right)

    _add_footer(slide)
    _add_notes(slide, notes)


def add_implementation_evidence_slide(
    prs: Presentation,
    screenshot_cursor: Path,
    screenshot_data: Path,
    notes: str = "",
) -> None:
    slide = _blank_slide(prs)
    _set_slide_bg_white(slide)

    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.45), Inches(12.0), Inches(0.75))
    ttf = title_box.text_frame
    ttf.text = "Implementation Evidence"
    _style_title(ttf, size=28)

    left_x = Inches(0.55)
    left_w = Inches(4.8)
    body_box = slide.shapes.add_textbox(left_x, Inches(1.25), left_w, Inches(3.5))
    body_box.text_frame.word_wrap = True
    _add_bullets(
        body_box.text_frame,
        [
            "What I built: reproducible Python pipeline (`main.py` + `src/`)",
            "50,000-row synthetic dataset in `data/raw/`",
            "JMP import table + project for interactive review",
            "GitHub portfolio with reports, figures, and this deck",
        ],
        size=17,
    )

    _add_takeaway_box(
        slide,
        "This is a working project — not just a slide outline.",
        left_x,
        Inches(4.95),
        left_w,
        Inches(0.95),
    )

    add_image_fit(
        slide,
        screenshot_cursor,
        Inches(5.55),
        Inches(1.25),
        Inches(3.55),
        Inches(4.65),
        caption="Cursor agent workflow",
        is_screenshot=True,
    )
    add_image_fit(
        slide,
        screenshot_data,
        Inches(9.25),
        Inches(1.25),
        Inches(3.55),
        Inches(4.65),
        caption="50k synthetic raw data",
        is_screenshot=True,
    )

    _add_footer(slide)
    _add_notes(slide, notes)


def add_ai_workflow_slide(
    prs: Presentation,
    screenshot_cursor: Path,
    screenshot_claude: Path,
    screenshot_data: Path,
    notes: str = "",
) -> None:
    slide = _blank_slide(prs)
    _set_slide_bg_white(slide)

    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.45), Inches(12.0), Inches(0.75))
    ttf = title_box.text_frame
    ttf.text = "AI-Assisted Engineering Workflow"
    _style_title(ttf, size=28)

    intro = slide.shapes.add_textbox(Inches(0.55), Inches(1.15), Inches(12.2), Inches(0.55))
    intro_tf = intro.text_frame
    intro_tf.text = (
        "I used AI tools to move faster, but I still owned the MQE logic, validation, and conclusions."
    )
    intro_tf.paragraphs[0].font.size = Pt(16)
    intro_tf.paragraphs[0].font.color.rgb = DARK_GRAY

    card_y = Inches(1.85)
    card_h = Inches(3.85)
    card_img_h = Inches(3.30)
    card_w = Inches(3.85)
    gap = Inches(0.35)
    cards = [
        (screenshot_cursor, "Cursor", "Python code, debugging, PPT script"),
        (screenshot_claude, "Claude Code", "Multi-file edits and docs"),
        (screenshot_data, "Python / JMP", "Reproducible analytics + review"),
    ]
    for i, (path, label, desc) in enumerate(cards):
        x = Inches(0.55 + i * (_inches(card_w) + _inches(gap)))
        add_image_fit(slide, path, x, card_y, card_w, card_img_h, is_screenshot=True)
        label_box = slide.shapes.add_textbox(x, Inches(5.15), card_w, Inches(0.55))
        ltf = label_box.text_frame
        ltf.text = f"{label}: {desc}"
        ltf.paragraphs[0].font.size = Pt(11)
        ltf.paragraphs[0].font.bold = True
        ltf.paragraphs[0].font.color.rgb = ACCENT
        ltf.paragraphs[0].alignment = PP_ALIGN.CENTER

    tool_box = slide.shapes.add_textbox(Inches(0.55), Inches(5.85), Inches(12.2), Inches(0.55))
    ttf2 = tool_box.text_frame
    ttf2.text = (
        "ChatGPT: planning, MQE storyline, stats review, interview prep  |  "
        "Cursor: implementation  |  Claude Code: larger refactors  |  "
        "Python + JMP: analytics source of truth + interactive review"
    )
    ttf2.paragraphs[0].font.size = Pt(11)
    ttf2.paragraphs[0].font.color.rgb = LIGHT_GRAY

    note_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(6.45), Inches(12.2), Inches(0.45)
    )
    note_shape.fill.solid()
    note_shape.fill.fore_color.rgb = TAKEAWAY_BG
    note_shape.line.color.rgb = ACCENT
    note_tf = note_shape.text_frame
    note_tf.text = (
        "AI tools accelerated implementation, but engineering assumptions, validation, "
        "leakage control, and MQE interpretation were manually reviewed."
    )
    note_tf.paragraphs[0].font.size = Pt(11)
    note_tf.paragraphs[0].font.color.rgb = DARK_GRAY

    _add_footer(slide)
    _add_notes(slide, notes)


def build_deck() -> Presentation:
    root = project_root()
    fig = root / "outputs" / "figures"
    jmp_fig = root / "outputs" / "jmp" / "figures"
    shots = root / "assets" / "screenshots"

    prs = new_presentation()

    add_title_slide(
        prs,
        "Cover Glass Manufacturing Quality Analytics",
        [
            "Simulated MQE / Brittles portfolio project",
            "Synthetic data only",
        ],
        author_lines=[
            "Hexing Yin",
            "Ph.D. in Materials Science and Engineering, UCLA",
        ],
        notes=(
            "I'm walking through a simulated cover-glass yield excursion. "
            "All data is synthetic — this is not Apple or supplier confidential data."
        ),
    )

    add_bullet_slide(
        prs,
        "Project Motivation",
        [
            "Why it matters: high-volume cover glass, brittle edge defects",
            "What I saw: CNC edge chipping and chamfer width drift",
            "MQE goal: find high-risk process windows and preventive controls",
        ],
        notes=(
            "Start with the business problem — yield dropped after CNC contouring. "
            "My job as MQE is to localize the issue and recommend containment and fixes."
        ),
    )

    add_bullet_slide(
        prs,
        "Manufacturing Problem",
        [
            "AOI yield drop after CNC contouring / chamfering",
            "Edge-initiated defects can feed downstream reliability risk",
            "Phase 1 focus: CNC-related Edge_Chipping",
        ],
        notes=(
            "I'm not trying to solve every defect mode in v1. "
            "Edge chipping is the dominant signature, so that's where I focused."
        ),
    )

    add_bullet_slide(
        prs,
        "Synthetic Data Design",
        [
            "What I built: 50,000 synthetic unit-level records",
            "Traceability: machine, fixture, shift, tool life, coolant stability",
            "CTQs, defect mode, defect location, final disposition",
            "Embedded special cause: tool wear × coolant instability",
        ],
        notes=(
            "I designed the dataset to mirror real traceability fields. "
            "There's a planted interaction — high tool life plus unstable coolant — "
            "so I can show whether analysis finds it without cheating."
        ),
    )

    add_bullet_slide(
        prs,
        "End-to-End Workflow",
        [
            "Generate → validate → Pareto → stratification",
            "SPC → capability → defect-location heatmap",
            "ML risk screening (supporting, not controlling)",
            "JMP interactive review → MQE containment / corrective / preventive actions",
        ],
        notes=(
            "Python runs the reproducible pipeline. "
            "JMP is for live filtering and visual confirmation in a cross-functional review."
        ),
    )

    add_implementation_evidence_slide(
        prs,
        shots / "cursor_agent.png",
        shots / "generated_50k_raw_data.png",
        notes=(
            "If they ask 'did you actually build this?' — yes. "
            "Here's the repo structure, the raw CSV, and the scripts that regenerate every chart."
        ),
    )

    add_ai_workflow_slide(
        prs,
        shots / "cursor_agent.png",
        shots / "claude_code_cli.png",
        shots / "generated_50k_raw_data.png",
        notes=(
            "I used AI to speed up coding and documentation. "
            "But I manually checked stats assumptions, ML leakage rules, and every MQE conclusion. "
            "Don't oversell AI — it's an accelerator, not the engineer."
        ),
    )

    add_figure_slide(
        prs,
        "Defect Pareto",
        [
            "What I tested: overall NG defect mix",
            "What the data showed: 3.85% NG rate",
            "Edge_Chipping = 80.95% of NG parts",
            "Why it matters: confirms where to spend root-cause time",
        ],
        "Edge chipping dominates — start there before chasing minor modes.",
        fig / "defect_pareto.png",
        caption="NG defect Pareto (Python)",
        notes=(
            "First step in any excursion: confirm the defect signature. "
            "Three-point-eight-five percent NG, and edge chipping is ~81% of that. "
            "That's my Phase 1 scope."
        ),
    )

    add_bullet_slide(
        prs,
        "Traceability & Stratification",
        [
            "What I tested: machine, fixture, shift, tool life, coolant stability",
            "What the data showed: concentration on CNC-04 / CNC-06, FIX-B2 / FIX-C1",
            "Why it matters: narrows from fleet yield to suspect windows",
        ],
        notes=(
            "This is classic traceability work — stratify before you jump to a root cause. "
            "A few machines and fixtures light up; that's where I drill deeper."
        ),
    )

    add_figure_slide(
        prs,
        "Key Finding: Tool Life × Coolant Stability",
        [
            "What I tested: tool-life band × coolant stability",
            "Critical_90_100 + Unstable: 61.52% Edge_Chipping rate",
            "Found through stratification — not assumed upfront",
            "Why it matters: points to tooling + coolant interaction",
        ],
        "Edge chipping is not random — it clusters in high tool-life and unstable coolant windows.",
        jmp_fig / "jmp_tool_life_coolant_stratification.png",
        caption="Tool life × coolant (JMP review)",
        notes=(
            "This is the money slide. "
            "When tool life is critical and coolant is unstable, chipping jumps to 61.5%. "
            "I didn't bake this into the headline — stratification rediscovered it."
        ),
    )

    add_figure_slide(
        prs,
        "SPC Monitoring",
        [
            "What I tested: chamfer width (X-bar/R) and chipping rate (p-chart)",
            "Chamfer is a continuous CTQ; chipping is an attribute rate",
            "I-MR on chipping size kept exploratory (zero-inflated)",
            "Why it matters: separates special cause from normal variation",
        ],
        "Use p-chart for chipping rate; control limits are process-derived, not spec limits.",
        fig / "spc_chipping_p_chart.png",
        caption="Edge chipping p-chart on CNC-04",
        notes=(
            "SPC answers: is this a special cause or just noisy? "
            "For chipping I prefer the p-chart over I-MR on size because most units are zero."
        ),
    )

    add_figure_slide(
        prs,
        "Process Capability",
        [
            "What I tested: chamfer width vs spec (LSL 0.25 / USL 0.35 mm)",
            "Cp/Cpk: within-subgroup sigma (Rbar/d2)",
            "Pp/Ppk: overall sigma",
            "Low-risk Cpk ≈ 1.404 | High wear + unstable Cpk ≈ 1.181",
        ],
        "High-risk window shifts mean toward USL — capability drops even if spread looks OK.",
        fig / "chamfer_capability_distribution.png",
        caption="Chamfer capability by process window",
        notes=(
            "Capability tells me spec margin, not just pass/fail. "
            "Baseline Cpk is ~1.4; the bad window drops to ~1.18 with a mean shift up."
        ),
    )

    add_figure_slide(
        prs,
        "Defect Location Heatmap",
        [
            "What I tested: where Edge_Chipping shows up on the part",
            "What the data showed: edge location dominates",
            "Corners and feature cutouts are secondary clusters",
            "Why it matters: supports CNC edge / contour root cause",
        ],
        "Defects cluster on edges and corners — consistent with CNC contouring, not random handling.",
        fig / "chipping_location_heatmap.png",
        caption="Machine × defect location heatmap",
        notes=(
            "Location pattern is another sanity check. "
            "If chipping were random contamination you'd expect a different map."
        ),
    )

    add_figure_slide(
        prs,
        "ML Risk Screening",
        [
            "What I tested: can process inputs rank chipping risk before inspection?",
            "No CTQ leakage — process + traceability inputs only",
            "ROC-AUC ~0.95 | PR-AUC ~0.40",
            "Top features: Tool_Life_Pct, Coolant_Pressure_Stability, Coolant_Pressure_bar",
        ],
        "ML is a screening aid — rank high-risk windows, not automatic process control.",
        fig / "ml_feature_importance.png",
        caption="Random Forest feature importance",
        notes=(
            "ML supports the same story as stratification. "
            "I deliberately excluded chamfer and chipping size from inputs. "
            "Use predicted probability for ranking — 0.5 threshold is wrong for a 4% defect rate."
        ),
    )

    add_two_figure_slide(
        prs,
        "JMP Interactive Review Layer",
        [
            "Full 50,000-row dataset imported into JMP",
            "Python = reproducible batch analytics",
            "JMP = interactive filtering, CTQ review, OOC subgroup check",
        ],
        "JMP supports live engineering review — Python stays the source of truth for calculations.",
        jmp_fig / "jmp_chamfer_distribution.png",
        jmp_fig / "jmp_edge_chipping_ooc_highlight.png",
        "Chamfer CTQ distribution",
        "OOC subgroup highlight",
        notes=(
            "In a real review I'd open the JMP project and filter live. "
            "Python generated the numbers; JMP lets the team explore together."
        ),
    )

    add_bullet_slide(
        prs,
        "MQE Recommendations",
        [
            "Containment: hold / sort high-risk lots on CNC-04, CNC-06",
            "Corrective: inspect tooling, coolant system, FIX-B2 / FIX-C1",
            "Preventive: tool-life stop (~75%), coolant interlock, SPC alerts, capability review",
        ],
        takeaway="MQE action: contain now, fix tooling/coolant/fixtures, then lock in preventive controls.",
        notes=(
            "Close the loop — containment first so bad material doesn't ship, "
            "then corrective on the machines and fixtures that stratified hot, "
            "then preventive so it doesn't come back."
        ),
    )

    add_bullet_slide(
        prs,
        "Limitations & Future Work",
        [
            "Synthetic data only — no real AOI images or supplier data",
            "No real DOE or line validation in Phase 1",
            "Future: Streamlit dashboard, DOE simulation, reliability linkage, SHAP",
        ],
        notes=(
            "Be honest about limits. "
            "This demonstrates MQE methodology on simulated data — next step would be real line validation."
        ),
    )

    add_bullet_slide(
        prs,
        "Interview Takeaway",
        [
            "Structured MQE path: signature → traceability → SPC → capability → action",
            "Connects materials / reliability background to manufacturing quality",
            "Python for reproducible analytics; JMP for interactive review",
            "AI-assisted workflow — with manual engineering review",
        ],
        notes=(
            "If I had 30 seconds: I confirmed the defect, traced it to tool life and coolant, "
            "proved it with SPC and capability, and wrote containment plus preventive controls. "
            "All reproducible in Python, reviewable in JMP."
        ),
    )

    add_thank_you_slide(
        prs,
        name="Hexing Yin",
        github_url="https://github.com/hexing-yin/mqe-glass-quality-demo",
        notes="Pause for questions. Point them to the GitHub repo if they want to dig into the code.",
    )

    return prs


def main() -> None:
    global included_figures, included_screenshots, missing_files
    included_figures = []
    included_screenshots = []
    missing_files = []

    out = output_path()
    out.parent.mkdir(parents=True, exist_ok=True)

    prs = build_deck()
    prs.save(out)

    print("--- Portfolio PowerPoint Generated ---")
    print(f"Output: {out}")
    print(f"Slides: {len(prs.slides)}")
    print("Screenshots included:")
    for path in included_screenshots:
        print(f"  - {path}")
    if not included_screenshots:
        print("  (none)")
    print("Figures included:")
    for path in included_figures:
        print(f"  - {path}")
    if not included_figures:
        print("  (none)")
    print("Missing files:")
    for path in missing_files:
        print(f"  - {path}")
    if not missing_files:
        print("  (none)")


if __name__ == "__main__":
    main()
