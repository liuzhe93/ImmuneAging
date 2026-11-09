import json, math, csv, textwrap
from pathlib import Path
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Circle, Polygon
from reportlab.graphics import renderPDF, renderSVG
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase.pdfmetrics import stringWidth

import bootstrap

R = bootstrap.ROOT / "inputs" / "literature"
OUT = bootstrap.OUT / "figures" / "supplementary"
OUT.mkdir(exist_ok=True)
DATA = json.loads((R / "study_data.json").read_text(encoding="utf8"))
INK = "#172938"
MUTED = "#526475"
BLUE = "#296C93"
TEAL = "#24877E"
ORANGE = "#B66A32"
PURPLE = "#786496"
LIGHT = "#EEF3F5"
GRID = "#D6E0E5"


class Fig:
    def __init__(self, w, h, title, sub=""):
        self.w = w
        self.h = h
        self.d = Drawing(w, h)
        self.rect(0, 0, w, h, "#FFFFFF", None)
        self.text(22, h - 28, title, 20, INK, bold=True)
        if sub:
            self.text(22, h - 49, sub, 11.5, MUTED)

    def text(self, x, y, s, size=13, color=INK, bold=False, anchor="start"):
        self.d.add(
            String(
                x,
                y,
                s,
                fontName="Helvetica-Bold" if bold else "Helvetica",
                fontSize=size,
                fillColor=HexColor(color),
                textAnchor=anchor,
            )
        )

    def rect(self, x, y, w, h, fill=LIGHT, stroke=GRID, r=0):
        self.d.add(
            Rect(
                x,
                y,
                w,
                h,
                rx=r,
                ry=r,
                fillColor=HexColor(fill) if fill else None,
                strokeColor=HexColor(stroke) if stroke else None,
                strokeWidth=0.8,
            )
        )

    def line(self, x1, y1, x2, y2, col=GRID, width=1, dash=None):
        self.d.add(
            Line(
                x1,
                y1,
                x2,
                y2,
                strokeColor=HexColor(col),
                strokeWidth=width,
                strokeDashArray=dash,
            )
        )

    def dot(self, x, y, r=4, col=BLUE):
        self.d.add(Circle(x, y, r, fillColor=HexColor(col), strokeColor=None))

    def arrow(self, x1, y1, x2, y2, col=MUTED):
        self.line(x1, y1, x2, y2, col, 1.3)
        a = math.atan2(y2 - y1, x2 - x1)
        l = 6
        self.d.add(
            Polygon(
                [
                    x2,
                    y2,
                    x2 - l * math.cos(a - 0.4),
                    y2 - l * math.sin(a - 0.4),
                    x2 - l * math.cos(a + 0.4),
                    y2 - l * math.sin(a + 0.4),
                ],
                fillColor=HexColor(col),
                strokeColor=None,
            )
        )

    def para(self, x, y, s, width, size=12, color=INK, bold=False, leading=None):
        lead = leading or size * 1.35
        words = s.split()
        line = ""
        lines = []
        for word in words:
            cand = (line + " " + word).strip()
            if (
                stringWidth(cand, "Helvetica-Bold" if bold else "Helvetica", size)
                > width
                and line
            ):
                lines.append(line)
                line = word
            else:
                line = cand
        if line:
            lines.append(line)
        for i, t in enumerate(lines):
            self.text(x, y - i * lead, t, size, color, bold)
        return y - len(lines) * lead

    def save(self, name):
        renderPDF.drawToFile(self.d, str(OUT / f"{name}.pdf"))
        renderSVG.drawToFile(self.d, str(OUT / f"{name}.svg"))
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(OUT / f"{name}.pdf"))
        page = pdf[0]
        page.render(scale=2400 / page.get_width()).to_pil().save(OUT / f"{name}.png")
        page.close()
        pdf.close()
        p = OUT / f"{name}.svg"
        s = (
            p.read_text(encoding="utf8")
            .replace(
                "font-family: Helvetica-Bold;", "font-family: Arial; font-weight: bold;"
            )
            .replace("font-family: Helvetica;", "font-family: Arial;")
        )
        p.write_text(s, encoding="utf8")


# Figure 1. A chronological selection, not a proportional time axis.
f = Fig(
    720,
    500,
    "Selected milestones in immune aging clocks",
    "A chronological map of measurement and inference; examples are not an exhaustive history",
)
events = [
    (
        "2013",
        "Molecular age",
        "Methylation clocks establish a reference for age prediction.",
        "Context",
        BLUE,
    ),
    (
        "2019",
        "Longitudinal immunity",
        "IMM-AGE maps coordinated cellular remodeling.",
        "Cell frequencies",
        TEAL,
    ),
    (
        "2021",
        "Inflammatory age",
        "iAge connects protein patterns with aging-related phenotypes.",
        "Plasma proteins",
        ORANGE,
    ),
    (
        "2022",
        "Clinical protein clocks",
        "ipAGE studies inflammatory profiles in kidney disease.",
        "Clinical context",
        ORANGE,
    ),
    (
        "2023",
        "Cell-type resolution",
        "PBMC and brain clocks link age estimates to defined populations.",
        "Single-cell RNA",
        BLUE,
    ),
    (
        "2024",
        "Cellular heterogeneity",
        "AIDA clocks resolve expression and cell proportions.",
        "Cells and aggregation",
        BLUE,
    ),
    (
        "2025",
        "Lineages and lifespan",
        "sc-ImmuAging, siAge and microglial featurization.",
        "Prediction and challenge",
        TEAL,
    ),
    (
        "2026",
        "Mechanism and transport",
        "Tictock, RUNX1, repertoire clocks, ensembles and outcome links.",
        "Multiple evidence types",
        PURPLE,
    ),
]
for i, (year, title, body, tag, col) in enumerate(events):
    row = i // 4
    colidx = i % 4
    x = 22 + colidx * 175
    y = 254 if row == 0 else 53
    f.rect(x, y, 159, 175, "#F7F9FA", GRID)
    f.rect(x, y + 169, 159, 6, col, None)
    f.text(x + 11, y + 144, year, 22, col, True)
    yy = f.para(x + 11, y + 120, title, 137, 13, INK, True)
    f.para(x + 11, yy - 11, body, 137, 12, INK, leading=16)
    f.para(x + 11, y + 10, tag, 137, 10.3, MUTED)
    if colidx < 3:
        f.arrow(x + 161, y + 90, x + 173, y + 90)
f.text(
    22,
    24,
    "Selected publication milestones. Microglial featurization: peer-reviewed study, 2025.",
    10.2,
    MUTED,
)
f.save("Figure_S1_milestones")

# Figure 2. Dot plots distinguish people and cells.
f = Fig(
    720,
    540,
    "People and cells answer different design questions",
    "Reported cohort roles are preserved; counts across rows must not be added",
)
f.text(181, 458, "A  Independent people", 15, INK, True)
f.text(463, 458, "B  Cellular coverage", 15, INK, True)
xa, xb = 187, 430
ya, yb = 89, 432


def px(n):
    return xa + (math.log10(n) - 2) / (math.log10(3000) - 2) * (xb - xa)


for n in [100, 300, 1000, 3000]:
    x = px(n)
    f.line(x, ya, x, yb, GRID, 0.7)
    f.text(x, ya - 19, f"{n:,}", 11, MUTED, anchor="middle")
xc, xd = 483, 682
for n in [0, 1, 2]:
    x = xc + n / 2.2 * (xd - xc)
    f.line(x, ya, x, yb, GRID, 0.7)
    f.text(x, ya - 19, str(n), 11, MUTED, anchor="middle")
for i, row in enumerate(DATA["scale"]):
    y = 418 - i * 37
    if i % 2 == 0:
        f.rect(20, y - 15, 680, 33, "#F7F9FA", None)
    f.text(25, y, row["label"], 12.3, INK, True)
    col = (
        ORANGE
        if "proteins" in row["modality"].lower()
        else TEAL if "Cell frequencies" == row["modality"] else BLUE
    )
    x = px(row["people"])
    f.dot(x, y + 3, 4.4, col)
    f.text(x + 8, y - 1, f"{row['people']:,}", 11.5, col, True)
    if row["cells_million"] is None:
        f.text((xc + xd) / 2, y - 1, "Not plotted", 11, MUTED, anchor="middle")
    else:
        n = row["cells_million"]
        xx = xc + n / 2.2 * (xd - xc)
        f.dot(xx, y + 3, 4.4, BLUE)
        txt = "1.059" if n == 1.058909 else f"~{n:.1f}"
        f.text(xx - 7, y - 1, txt, 11.5, BLUE, True, anchor="end")
f.text((xa + xb) / 2, 44, "People, logarithmic scale", 11.5, MUTED, anchor="middle")
f.text(
    (xc + xd) / 2, 44, "Cells in millions, linear scale", 11.5, MUTED, anchor="middle"
)
f.text(
    22,
    23,
    "ipAGE: total clinical cohort. IDEAL-Age: initial training split. Terekhova atlas is reused by Tictock.",
    10.2,
    MUTED,
)
f.save("Figure_S3_cohort_scale")

# Figure 3. Methods and representations.
f = Fig(
    720,
    540,
    "From biological measurements to model outputs",
    "The independent age label belongs to the donor, even when predictions are cell resolved",
)
f.text(22, 454, "A  Observation hierarchy", 14, INK, True)
for i, (title, sub) in enumerate(
    [
        ("Donor", "Independent unit"),
        ("Visit or sample", "Repeated measures"),
        ("Library", "Technical unit"),
        ("Cell", "Nested observation"),
    ]
):
    x = 22 + i * 177
    f.rect(x, 387, 156, 50, "#F3F7F8", GRID)
    f.text(x + 78, 417, title, 13, INK, True, "middle")
    f.text(x + 78, 399, sub, 10.7, MUTED, anchor="middle")
    if i < 3:
        f.arrow(x + 159, 412, x + 173, 412)
f.text(
    22,
    355,
    "B  Measurement and representation determine the modeling question",
    14,
    INK,
    True,
)
for x, t in [
    (22, "Measurement"),
    (204, "Representation"),
    (399, "Model families"),
    (579, "Output"),
]:
    f.text(x, 326, t, 12, MUTED, True)
lanes = [
    (
        "Cell frequencies",
        "Fractions and ratios",
        "Regression and trees",
        "Composition age",
        TEAL,
    ),
    (
        "Plasma proteins",
        "Targeted panel",
        "Elastic net; guided AE",
        "Inflammatory score",
        ORANGE,
    ),
    (
        "Single-cell RNA",
        "Pseudobulk or cell sets",
        "Regularized models; RF; PointNet; DeepSets",
        "Lineage or donor age",
        BLUE,
    ),
    (
        "TCR and BCR",
        "Gene usage and clones",
        "Boosting or fusion",
        "Repertoire age",
        PURPLE,
    ),
]
for i, (a, b, c, d, col) in enumerate(lanes):
    y = 259 - i * 64
    for x, w, t in [(22, 157, a), (204, 170, b), (399, 155, c), (579, 119, d)]:
        f.rect(x, y, w, 48, "#F7F9FA", GRID)
        f.para(x + 8, y + 29, t, w - 16, 11.6, INK, leading=14)
    f.rect(22, y, 4, 48, col, None)
    for x1, x2 in [(181, 200), (376, 395), (556, 575)]:
        f.arrow(x1, y + 24, x2, y + 24)
f.text(
    22,
    38,
    "Compare composition-only, within-lineage and combined models on identical donor splits.",
    12,
    INK,
    True,
)
f.text(
    22,
    19,
    "Model families are examples; architecture alone does not determine biological meaning. AE, autoencoder; RF, random forest.",
    10.3,
    MUTED,
)
f.save("Figure_S2_representations_models")

# Figure 4. Evaluation workflow.
f = Fig(
    720,
    540,
    "Keep development and external evaluation separate",
    "Proposed workflow for a new-person prediction task",
)
f.rect(22, 390, 676, 76, "#F3F7F8", GRID)
f.text(37, 442, "1  Declare the target and resolve provenance", 15, INK, True)
f.para(
    37,
    419,
    "Define age, function or risk; map donors, visits and libraries; identify cohort overlap and freeze the evaluation unit.",
    640,
    13,
)
f.arrow(360, 386, 360, 368)
f.rect(22, 164, 413, 201, "#EEF5F8", GRID)
f.rect(462, 164, 236, 201, "#F3F7F4", GRID)
f.text(37, 340, "2  Development donors", 15, BLUE, True)
f.para(
    37,
    314,
    "Inner folds: feature selection, scaling, tuning and age calibration.",
    375,
    13,
)
f.para(
    37,
    264,
    "Outer donor-disjoint folds: estimate internal error and compare matched baselines.",
    375,
    13,
)
f.para(
    37,
    209,
    "Refit the selected pipeline; freeze all transformations and model parameters.",
    375,
    13,
)
f.text(476, 340, "3  Untouched external data", 14, TEAL, True)
f.para(
    476,
    313,
    "Apply the frozen pipeline. Report coverage, error, calibration and subgroup limits.",
    207,
    13,
)
f.para(
    476,
    240,
    "If these data guide tuning or recalibration, reserve another independent evaluation.",
    207,
    12,
    INK,
)
f.arrow(438, 280, 459, 280, TEAL)
f.arrow(360, 160, 360, 139)
f.rect(22, 53, 676, 82, "#F7F5F1", GRID)
f.text(37, 109, "4  Test the biological claim", 15, ORANGE, True)
f.para(
    37,
    84,
    "Estimate repeatability; assess composition sensitivity; add orthogonal function, prospective outcomes or controlled perturbation as required by the intended use.",
    640,
    13,
)
f.text(
    22,
    23,
    "All visits and cells from one donor stay together. External data used for model selection are no longer an untouched test.",
    10.8,
    MUTED,
)
f.save("Figure_S4_validation_workflow")

# Figure 5. Evidence map, not study ratings.
f = Fig(
    720,
    510,
    "What a change in immune age can support",
    "Proposed evidence map; these are distinct tests, not a validated scoring system",
)
rows = [
    (
        "1",
        "Repeatable measurement",
        "Does the assay and pipeline return a stable result?",
        "Technical replicates and repeated baselines",
        BLUE,
    ),
    (
        "2",
        "Transportable prediction",
        "Does the frozen model work in new donors and cohorts?",
        "Independent evaluation and calibration",
        TEAL,
    ),
    (
        "3",
        "Functional relevance",
        "Does the score relate to a defined immune capability?",
        "Orthogonal challenge or prospective outcome",
        ORANGE,
    ),
    (
        "4",
        "Mechanistic response",
        "Does perturbing a candidate alter the relevant biology?",
        "Controlled experiments with functional readouts",
        PURPLE,
    ),
    (
        "5",
        "Clinical benefit and surrogacy",
        "Does changing the score reliably track treatment benefit?",
        "Randomized evidence and endpoint validation",
        BLUE,
    ),
]
for i, (n, title, q, test, col) in enumerate(rows):
    y = 354 - i * 69
    f.dot(39, y + 30, 15, col)
    f.text(39, y + 25, n, 15, "#FFFFFF", True, "middle")
    f.text(69, y + 42, title, 14.5, col, True)
    f.text(69, y + 23, q, 12.6, INK)
    f.text(69, y + 5, test, 11.2, MUTED)
    if i < 4:
        f.line(39, y + 11, 39, y - 22, GRID, 2)
f.line(22, 54, 698, 54, GRID, 1)
f.text(
    22,
    32,
    "Prediction error does not establish mechanism. Score movement does not by itself establish rejuvenation.",
    12,
    INK,
    True,
)
f.save("Figure_S8_evidence_map")

refs = json.loads((R / "references_verified.json").read_text(encoding="utf8"))
with (bootstrap.RESULTS / "literature_figure_source_data.csv").open(
    "w", newline="", encoding="utf-8-sig"
) as h:
    cols = [
        "label",
        "people",
        "cells_million",
        "role",
        "note",
        "modality",
        "doi",
        "source_locator",
    ]
    w = csv.DictWriter(h, fieldnames=cols)
    w.writeheader()
    for row in DATA["scale"]:
        r = {k: row[k] for k in cols if k in row}
        r["doi"] = refs[row["key"]]["record"]["doi"]
        r["source_locator"] = (
            "Original report abstract/results; IDEAL-Age Results Overview; Terekhova original atlas and author-associated data description"
        )
        w.writerow(r)
print("Wrote 5 vector figures and figure_source_data.csv")
