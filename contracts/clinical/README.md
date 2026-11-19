# ICU liaison patient safety and economic decision gate

The [source policy](safety-decision.json) and [Draft 2020-12 schema](safety-decision.schema.json) map the six mandatory safety outcomes already in the P2 protocol. No numeric noninferiority margins, measurements, or local approvals are available.

Run `python tools/evaluate_safety_decision.py --synthetic-net-resource-benefit 1000000` to verify that even a large favourable synthetic resource result produces `not_authorised`. The decision gate never treats fewer readmissions as automatically safer: appropriate rescue returns may increase under better surveillance.

This is a fail-closed demonstration contract, **not** an approved CHHHS clinical risk threshold, authorisation to treat patients, or evidence of clinical effectiveness.
