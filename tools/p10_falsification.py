"""Adversarial synthetic P4 scenarios; no clinical or financial acceptance."""
from __future__ import annotations
from typing import Any

import json
from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike

from icu_liaison.p4_model import EconomicScenario, evaluate_scenarios
from tools.evaluate_safety_decision import evaluate_decision

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "contracts/reporting/falsification-matrix.json"


def _fixed(prior: dict[str, Any], value: float) -> None:
    prior["family"] = "fixed"
    prior["params"] = {"value": value}


def _variant(raw: dict[str, Any], case: str) -> EconomicScenario:
    data = json.loads(json.dumps(raw))
    if case == "no_effect":
        for arm in data["strategies"]:
            if arm["role"] == "proposed":
                _fixed(arm["delay_success_fraction"], 0)
                _fixed(arm["relative_return_effect"], 0)
        data["dependence_groups"] = [
            x for x in data["dependence_groups"]
            if not any("delay_success_fraction" in p for p in x["variables"])]
    elif case == "harmful_returns":
        for arm in data["strategies"]:
            if arm["role"] == "proposed":
                _fixed(arm["relative_return_effect"], -0.4)
    elif case == "zero_addressable_delay":
        _fixed(data["resource"]["addressable_delay_fraction"], 0)
        data["dependence_groups"] = [
            x for x in data["dependence_groups"]
            if "resource.addressable_delay_fraction" not in x["variables"]]
    elif case == "zero_usable_capacity":
        _fixed(data["resource"]["usable_released_capacity_fraction"], 0)
    elif case == "zero_cash_realisability":
        _fixed(data["resource"]["index_cash_realisability_fraction"], 0)
        _fixed(data["resource"]["return_cash_realisability_fraction"], 0)
    else:
        raise ValueError("unknown falsification case")
    return EconomicScenario.model_validate(data)


def run_suite(iterations: int = 128) -> dict[str, Any]:
    if not 32 <= iterations <= 10000:
        raise ValueError("synthetic audit iterations outside 32..10000")
    specification = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert specification["status"] == "synthetic_falsification_only"
    identifiers = [x["id"] for x in specification["cases"]]
    expected = [
        "no_effect", "harmful_returns", "zero_addressable_delay",
        "zero_usable_capacity", "zero_cash_realisability"]
    if identifiers != expected:
        raise ValueError("falsification coverage drift")
    raw = json.loads((ROOT / specification["source"]).read_text(encoding="utf-8"))
    if raw["data_class"] != "synthetic" or raw["safety"]["assessment_status"] != "unmeasured":
        raise ValueError("falsification source must be clinically unmeasured")
    raw["iterations"] = iterations
    base = evaluate_scenarios(EconomicScenario.model_validate(raw))
    outcomes = []
    for case in identifiers:
        run = evaluate_scenarios(_variant(raw, case))
        by_arm = []
        for strategy in base.scenario.strategies:
            if strategy.role != "proposed":
                continue
            current = base.strategies[strategy.id]
            outcome = run.strategies[strategy.id]
            def close(a: ArrayLike, b: ArrayLike) -> bool:
                return np.allclose(a, b, rtol=0, atol=1e-8)
            if case == "no_effect":
                passed = close(outcome.icu_bed_days_released,0) and close(
                    outcome.readmissions_avoided,0) and bool(np.all(outcome.net_resource_benefit_aud<0))
            elif case == "harmful_returns":
                passed = bool(np.all(outcome.readmissions_avoided<0))
            elif case == "zero_addressable_delay":
                passed = close(outcome.icu_bed_days_released,0)
            elif case == "zero_usable_capacity":
                passed = close(outcome.usable_bed_days,0) and close(
                    outcome.net_resource_benefit_aud,current.net_resource_benefit_aud)
            else:
                service = run.sampled_inputs[
                    f"strategy.{strategy.id}.annual_incremental_cost_aud"]
                passed = (close(outcome.net_resource_benefit_aud,
                                current.net_resource_benefit_aud)
                          and close(outcome.net_budget_impact_aud,-service))
            if not passed:
                raise AssertionError(f"{case}: {strategy.id} violates accounting or safety fixture")
            economic_mean = float(np.mean(outcome.net_resource_benefit_aud))
            if evaluate_decision(economic_mean)["investment_ready"] is not False:
                raise AssertionError("synthetic falsification promoted to investment decision")
            by_arm.append({
                "strategy_id":strategy.id,
                "mean_net_resource_benefit_aud":economic_mean,
                "mean_bed_days_released":float(np.mean(outcome.icu_bed_days_released)),
                "mean_usable_bed_days":float(np.mean(outcome.usable_bed_days)),
                "mean_returns_avoided":float(np.mean(outcome.readmissions_avoided)),
                "all_checks_passed":True,
            })
        outcomes.append({"case":case,"strategies":by_arm,"invariants_passed":True})
    return {
        "status":"synthetic_falsification_passed_not_empirically_validated",
        "seed":base.scenario.seed,
        "iterations":iterations,
        "scenario_id":base.scenario.scenario_id,
        "cases":outcomes,
        "clinical_safety_measured":False,
        "investment_ready":False,
        "native_providers_executed":False,
    }


def main() -> int:
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--iterations",type=int,default=128)
    args=parser.parse_args()
    print(json.dumps(run_suite(args.iterations),sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
