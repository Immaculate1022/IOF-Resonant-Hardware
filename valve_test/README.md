# valve_test — frozen pipeline for TFLN-PHO-2026-09 Rev 0.3

The pre-registered code for the IOF Valve Test Protocol, committed with
the Rev 0.3 test plan and frozen before first data. Changes after first
data are protocol amendments — record them in the plan's §17, don't
edit quietly.

| File | Role |
|---|---|
| `valve_sweep.py` | Randomized, blinded sweep plan + run records (T / C1 / C3 × valve × source × power, ≥5 repeats, C5/C6 interleaved). Ships with a simulated backend so the whole pipeline runs before hardware exists; simulated records are marked `"backend": "simulated"` and must never be archived as data. |
| `ledger.py` | The §04 energy ledger: P_in + P_drive vs all output terms, propagated-uncertainty closure at 2σ, over-unity hard fail, pre-registered exclusion list. |
| `analysis.py` | The frozen analysis: unblinding, ledger filter, per-chip ΔR, exact sign-flip permutation primary (α = 0.01) with t-test and Wilcoxon alongside, Holm-corrected secondaries, minimum-detectable-effect statement, §14 checklist verdict. |

## Quick start (simulated end-to-end)

```
python3 valve_sweep.py --simulate --seed 7 --chips 10 --out runs.jsonl --key key.json
python3 ledger.py runs.jsonl
python3 analysis.py runs.jsonl key.json        # null model → NOT VALIDATED
python3 valve_sweep.py --simulate --seed 7 --chips 10 --inject-effect --out fx.jsonl --key fxkey.json
python3 analysis.py fx.jsonl fxkey.json         # injected H1 effect → VALIDATED
```

## Self-tests

```
python3 ledger.py --selftest
python3 valve_sweep.py --selftest
python3 analysis.py --selftest   # includes both end-to-end verdicts + a
                                 # t-distribution check against the df=9
                                 # critical value (t = 2.2622 → p = 0.05)
```

Stdlib only. Verified 2026-10-07: all self-tests pass; the simulated
null session is NOT VALIDATED and the injected-effect session is
VALIDATED with all six §14 checklist items green — the pipeline can
tell the difference between the claim being true and being false,
which is the entire point.
