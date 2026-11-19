# P10 synthetic falsification cases

Five [versioned adversarial scenarios](falsification-matrix.json) are executed using the existing P4 probabilistic model and original synthetic inputs, with a fixed draw count and declared seed.

`python -m tools.p10_falsification --iterations 128` tests no intervention effect, harmful ICU return effects, zero addressable delay, zero reusable capacity and zero cash realisability. Both proposed strategies are evaluated under paired model draws. The code explicitly preserves the distinction between usable bed-days, incremental economic resource costs, cash budget and missing safety evidence.

**Not** an observed clinical validation or evidence of liaison effectiveness. Null/harm conditions are deliberately hypothetical; no clinical safety margin is approved.
