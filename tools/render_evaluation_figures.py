"""Render the evaluation deck figures from a versioned aggregate input file."""

import argparse
from datetime import date
from collections.abc import Callable
from typing import Any
from matplotlib.figure import Figure
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import re
from tempfile import TemporaryDirectory

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import Formatter, PercentFormatter, StrMethodFormatter

CONTRACT = Path(__file__).resolve().parents[1] / "contracts/reporting/evaluation-deck.json"
COLORS = ("#174467", "#526579", "#AB551F", "#725387")
SCENARIOS = {
    "reference": "ED-weighted reference",
    "longer_stays": "Longer ICU stays",
    "longer_flat_weight": "Longer stays, flat base QWAU",
    "higher_care_cost": "Higher costs outside ICU",
}


def keys(row: object, expected: str) -> None:
    if not isinstance(row, dict) or set(row) != set(expected.split()):
        raise ValueError(f"Expected aggregate fields: {expected}")


def number(value: object, *, count: bool=False, minimum: float=0, maximum: float=float("inf")) -> None:
    if (not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value)
            or not minimum <= value <= maximum or (count and type(value) is not int)):
        raise ValueError("Invalid aggregate number")


def validate(data: dict[str, Any]) -> None:
    keys(data, "input_class period_months activity pathways funding")
    if data["input_class"] not in ("synthetic_only", "private_aggregate"):
        raise ValueError("Unknown aggregate input class")
    number(data["period_months"], count=True, minimum=1)
    if not isinstance(data["activity"], list) or len(data["activity"]) != data["period_months"]:
        raise ValueError("Monthly activity does not cover the reporting period")
    previous = None
    for row in data["activity"]:
        keys(row, "month admissions icu1_pct icu2_pct")
        if not isinstance(row["month"], str) or not re.fullmatch(r"\d{4}-\d{2}", row["month"]):
            raise ValueError("Month must be YYYY-MM")
        month = date.fromisoformat(row["month"] + "-01")
        index = 12 * month.year + month.month
        if previous is not None and index != previous + 1:
            raise ValueError("Expected consecutive activity months")
        previous = index
        number(row["admissions"], count=True)
        for field in ("icu1_pct", "icu2_pct"):
            if row[field] is not None:
                number(row[field], maximum=100)

    pathway = data["pathways"]
    keys(pathway, "screen_months adult_icu_destinations labelled chart_review avoided reused_hours added")
    for name in ("screen_months", "adult_icu_destinations", "labelled", "chart_review"):
        number(pathway[name], count=True)
    if not 0 < pathway["screen_months"] <= data["period_months"]:
        raise ValueError("Screening period is outside the reporting period")
    if not pathway["adult_icu_destinations"] >= pathway["labelled"] >= pathway["chart_review"]:
        raise ValueError("Observed screening counts do not reconcile")
    for name in ("avoided", "reused_hours", "added"):
        number(pathway[name])

    if not isinstance(data["funding"], dict) or set(data["funding"]) != set(SCENARIOS):
        raise ValueError("Funding comparison must include each specified scenario")
    for case in data["funding"].values():
        keys(case, "full_net_payment incremental_spending")
        for value in case.values():
            number(value, minimum=-float("inf"))


def activity(data: dict[str, Any], _spec: dict[str, Any]) -> Figure:
    rows = data["activity"]
    dates = [date.fromisoformat(row["month"] + "-01") for row in rows]
    fig, (counts, occupancy) = plt.subplots(2, 1, figsize=(12, 4.35), sharex=True, layout="constrained")
    counts.set_title("ICU admissions per month", loc="left", fontweight="bold")
    counts.plot(dates, [row["admissions"] for row in rows], marker="o", color=COLORS[0])
    counts.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    occupancy.set_title("Funded-bed occupancy by unit", loc="left", fontweight="bold")
    for index, field in enumerate(("icu1_pct", "icu2_pct")):
        occupancy.plot(
            dates, [float("nan") if row[field] is None else row[field] for row in rows],
            marker=("o", "s")[index], linestyle=("-", "--")[index], color=COLORS[index],
            label=f"ICU{index + 1}",
        )
    occupancy.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    occupancy.legend(loc="lower left", ncols=2, frameon=False)
    step = max(1, len(dates) // 7)
    tick_dates = dates[::step]
    if (dates[-1] - tick_dates[-1]).days >= 30 * max(1, step - 1):
        tick_dates.append(dates[-1])
    occupancy.set_xticks(tick_dates)
    date_formatter: Callable[[str], Formatter] = mdates.DateFormatter
    occupancy.xaxis.set_major_formatter(date_formatter("%b %Y"))
    for axis in (counts, occupancy):
        axis.grid(axis="y", color="#D8DFE4", linewidth=.75)
        axis.set_axisbelow(True)
    return fig


def pathways(data: dict[str, Any], _spec: dict[str, Any]) -> Figure:
    row = data["pathways"]
    fig, panels = plt.subplots(2, 1, figsize=(12, 4.15), layout="constrained")
    panels_data = (
        (f"Observed ED screening ({row['screen_months']} months)",
         ((row["adult_icu_destinations"], "Adult ED cases with\nan ICU destination"),
          (row["labelled"], "Sepsis or DKA\nrecorded in ED"),
          (row["chart_review"], "Cases for\nchart review"))),
        (f"Modelled higher-effect pathway scenario ({data['period_months']} months)",
         ((row["avoided"], "ICU admissions\nassumed avoided"),
          (row["reused_hours"], "ICU hours released\nand reused"),
          (row["added"], "Additional acute\nadmissions"))),
    )
    for panel, (title, stages) in zip(panels, panels_data, strict=True):
        panel.set_axis_off()
        panel.text(.01, .94, title, size=17, weight="bold", va="top", transform=panel.transAxes)
        for index, (value, label) in enumerate(stages):
            x = (.16, .50, .84)[index]
            panel.text(x, .53, f"{value:,.0f}", ha="center", size=28, weight="bold",
                       color=COLORS[0], transform=panel.transAxes)
            panel.text(x, .38, label, ha="center", va="top", size=15, transform=panel.transAxes)
        for start, stop in ((.28, .37), (.62, .71)):
            panel.annotate("", xy=(stop, .53), xytext=(start, .53), xycoords="axes fraction",
                           arrowprops={"arrowstyle": "->", "color": "#68747C", "lw": 1.4})
    return fig


def funding(data: dict[str, Any], spec: dict[str, Any]) -> Figure:
    first, last = spec["payment_range_percent"]
    fig, axis = plt.subplots(figsize=(12, 4.32), layout="constrained")
    for index, (key, label) in enumerate(SCENARIOS.items()):
        case = data["funding"][key]
        dollars = [(case["full_net_payment"] * x / 100 - case["incremental_spending"]) / 1000
                   for x in (first, last)]
        axis.plot((first, last), dollars, color=COLORS[index], linewidth=2.2, label=label,
                  linestyle=("-", "--", "-.", ":")[index], marker="o", markevery=[1])
    axis.axhline(0, color="#52616C", linewidth=1.1)
    axis.grid(axis="y", color="#D8DFE4", linewidth=.75)
    axis.set_axisbelow(True)
    axis.set(xlabel="Share of net additional QWAU paid", ylabel="Budget change (A$000)")
    axis.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    axis.set_xticks(range(first, last + 1, 5))
    axis.legend(loc="lower left", bbox_to_anchor=(0, 1), ncols=2, frameon=False, borderaxespad=0)
    return fig


RENDER = {"activity": activity, "pathways": pathways, "funding": funding}


def build(inputs: Path, destination: Path, contract_path: Path = CONTRACT) -> dict[str, Any]:
    raw = inputs.read_bytes()
    contract_raw = contract_path.read_bytes()
    data = json.loads(raw)
    validate(data)
    contract = json.loads(contract_raw)
    if [row["input_section"] for row in contract["figures"]] != list(RENDER):
        raise ValueError("Deck contract and figure renderers differ")
    if data["input_class"] not in contract["input_classes"]:
        raise ValueError("Input class isn't admitted by the deck figure contract")
    if data["input_class"] == "private_aggregate":
        for path in (inputs.resolve(), destination.resolve()):
            if any((directory / ".git").exists() for directory in path.parents):
                raise ValueError("Private figure inputs and outputs must be outside Git worktrees")
    if destination.exists():
        raise FileExistsError("Choose a new destination for the figure bundle")
    report = {
        "input_class": data["input_class"], "input_sha256": sha256(raw).hexdigest(),
        "contract_sha256": sha256(contract_raw).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "matplotlib": matplotlib.__version__, "figures": [],
    }
    with TemporaryDirectory(prefix=".evaluation-figures-", dir=destination.parent) as temp:
        staging = Path(temp) / "figures"
        staging.mkdir(mode=0o700)
        with plt.rc_context({
            "font.family": "DejaVu Sans", "font.size": 13, "lines.markersize": 4.5,
            "axes.spines.top": False, "axes.spines.right": False,
            "axes.labelcolor": "#15191F", "svg.hashsalt": "icu-evaluation-deck-v1",
        }):
            for spec in contract["figures"]:
                fig = RENDER[spec["input_section"]](data, spec)
                if data["input_class"] == "synthetic_only":
                    fig.text(.99, .99, "FICTIONAL", ha="right", va="top", color="#536171", size=9)
                record = {"id": spec["id"], "alt_text": spec["alt_text"], "files": {}}
                try:
                    for extension in ("png", "svg"):
                        name = f"{spec['artifact_stem']}.{extension}"
                        artifact = staging / name
                        fig.savefig(artifact, dpi=155, metadata={"Date": None} if extension == "svg" else None)
                        artifact.chmod(0o600)
                        record["files"][name] = sha256(artifact.read_bytes()).hexdigest()
                finally:
                    plt.close(fig)
                report["figures"].append(record)
        manifest = staging / "manifest.json"
        manifest.write_text(json.dumps(report, indent=2) + "\n")
        manifest.chmod(0o600)
        if destination.exists():
            raise FileExistsError("Figure destination appeared during generation")
        staging.rename(destination)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.inputs, args.output)


if __name__ == "__main__":
    main()
