#!/usr/bin/env python3
"""
Energy ledger calculator — IOF Valve Test Protocol (TFLN-PHO-2026-09 Rev 0.3)
==============================================================================

Implements the section 3 energy ledger of the protocol. For every run:

    P_in + P_drive = P_through + P_dump + P_scatter + P_absorbed

  * P_drive    — ALL electrical/optical power delivered to the valve, bias,
                 phase shifter, heater, and bolometer readout. The sorting,
                 if any, is paid for here; it is never optional in the ledger.
  * P_absorbed — heat in the chip, from on-chip thermistors calibrated
                 against a known heater power, cross-checked with the TEC
                 power change at constant setpoint.

The ledger CLOSES if |residual| <= 2 * sigma_residual, with uncertainties
propagated in quadrature. A run where

    P_through + P_dump > P_in + P_drive   (beyond 2 sigma)

is an OVER-UNITY HARD FAIL: an instrument or accounting error until proven
otherwise, investigated before any further data is taken.

Input: JSONL run records. Each power term is {"v": value_watts, "s": sigma_watts}.
Output: one verdict line per run plus a summary. A run that fails closure or
trips the over-unity test is excluded from analysis and listed with its reason
(the protocol's pre-registered exclusion rule).

Usage:
    python3 ledger.py runs.jsonl
    python3 ledger.py --selftest

Stdlib only. Frozen as part of the Rev 0.3 pre-registration: changes after
first data require a protocol amendment, not a quiet edit.
"""

from __future__ import annotations

import json
import math
import sys

TERMS_IN = ["P_in", "P_drive"]
TERMS_OUT = ["P_through", "P_dump", "P_scatter", "P_absorbed"]


def _vs(record, key):
    term = record.get(key)
    if term is None:
        raise ValueError(f"run {record.get('run_id', '?')}: missing ledger term {key}")
    return float(term["v"]), float(term["s"])


def evaluate_run(record) -> dict:
    """Return the ledger verdict for one run record."""
    total_in, var_in = 0.0, 0.0
    for k in TERMS_IN:
        v, s = _vs(record, k)
        total_in += v
        var_in += s * s
    total_out, var_out = 0.0, 0.0
    for k in TERMS_OUT:
        v, s = _vs(record, k)
        total_out += v
        var_out += s * s

    residual = total_in - total_out
    sigma_res = math.sqrt(var_in + var_out)
    closes = abs(residual) <= 2.0 * sigma_res

    # Over-unity test on the routed ports alone, against everything paid in.
    p_through, s_through = _vs(record, "P_through")
    p_dump, s_dump = _vs(record, "P_dump")
    excess = (p_through + p_dump) - total_in
    sigma_excess = math.sqrt(s_through**2 + s_dump**2 + var_in)
    over_unity = excess > 2.0 * sigma_excess

    return {
        "run_id": record.get("run_id"),
        "total_in": total_in,
        "total_out": total_out,
        "residual": residual,
        "sigma_residual": sigma_res,
        "closes": closes,
        "over_unity_hard_fail": over_unity,
        "usable": closes and not over_unity,
    }


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if len(argv) != 2:
        print(__doc__)
        return 2
    n = usable = refs = 0
    failures = []
    with open(argv[1]) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if "P_in" not in record:
                refs += 1  # C5 / C6 reference points carry no ledger terms
                continue
            verdict = evaluate_run(record)
            n += 1
            if verdict["usable"]:
                usable += 1
            else:
                failures.append(verdict)
            flag = "OK " if verdict["usable"] else "EXCLUDE"
            print(f"{flag} run {verdict['run_id']}: residual {verdict['residual']:+.3e} W "
                  f"(2σ = {2 * verdict['sigma_residual']:.3e})"
                  + ("  OVER-UNITY HARD FAIL" if verdict["over_unity_hard_fail"] else ""))
    print(f"\n{n} runs, {usable} usable, {len(failures)} excluded, {refs} reference points skipped")
    return 0 if usable == n else 1


def selftest():
    def term(v, s):
        return {"v": v, "s": s}

    base = {
        "run_id": "synthetic-balanced",
        "P_in": term(10.0e-3, 0.05e-3),
        "P_drive": term(2.0e-3, 0.02e-3),
        "P_through": term(6.5e-3, 0.05e-3),
        "P_dump": term(3.0e-3, 0.04e-3),
        "P_scatter": term(0.5e-3, 0.05e-3),
        "P_absorbed": term(2.0e-3, 0.10e-3),
    }
    v = evaluate_run(base)
    assert v["closes"] and v["usable"] and not v["over_unity_hard_fail"], v

    broken = dict(base, run_id="synthetic-over-unity")
    broken["P_through"] = term(11.0e-3, 0.05e-3)  # out alone exceeds everything in
    broken["P_dump"] = term(3.0e-3, 0.04e-3)
    v = evaluate_run(broken)
    assert v["over_unity_hard_fail"] and not v["usable"], v

    leaky = dict(base, run_id="synthetic-unclosed")
    leaky["P_absorbed"] = term(0.2e-3, 0.05e-3)  # 1.8 mW unaccounted >> 2 sigma
    v = evaluate_run(leaky)
    assert not v["closes"] and not v["usable"], v

    print("ledger.py selftest: balanced run closes, over-unity run hard-fails, "
          "unclosed run excluded — all as specified.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
