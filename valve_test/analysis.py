#!/usr/bin/env python3
"""
Frozen analysis pipeline — IOF Valve Test Protocol (TFLN-PHO-2026-09 Rev 0.3)
==============================================================================

Pre-registered analysis (protocol sections 8-9). This file is frozen with
the Rev 0.3 commit, BEFORE first data. Any change after data exists is a
protocol amendment and must be recorded as one.

Pipeline:
  1. Decode blinded condition codes with the session key (unblinding
     happens here, and only here).
  2. Ledger filter: every analysed run must close its energy ledger and
     pass the over-unity test (ledger.py). Excluded runs are listed with
     the reason; nothing is silently dropped.
  3. Primary endpoint: per-chip DeltaR for the test device T, coherent
     source, 8 mW (the switching regime) —
         DeltaR = mean(R_port | valve ON) - mean(R_port | valve OFF)
     paired across chips. Primary test: exact sign-flip permutation
     (distribution-free, exact for n chips), two-sided, alpha = 0.01.
     Paired t-test and exact Wilcoxon signed-rank reported alongside.
  4. Pre-registered secondary endpoints (Holm-corrected):
       - DeltaR thermal (source-statistics dependence, section 5)
       - DeltaR at 2 mW (declared-mechanism check: a real mechanism-(c)
         effect must collapse at low power)
       - DeltaR on C1 and on C3 (controls: must be null)
       - mean nonreciprocity S21-S12 on T, valve ON, coherent, 8 mW
  5. Minimum detectable effect from the measured per-chip noise, stated
     with the result (protocol section 8 power note).
  6. Verdict checklist per section 9. VALIDATED requires: ledger clean,
     primary p < 0.01 in the predicted (positive) direction, controls
     null after correction, mechanism check consistent (low-power
     collapse), and source dependence present. Anything else is printed
     as what it is — including FALSIFIED / NOT VALIDATED outcomes.

Usage:
    python3 analysis.py runs.jsonl key.json
    python3 analysis.py --selftest

Stdlib only.
"""

from __future__ import annotations

import itertools
import json
import math
import statistics
import sys

sys.path.insert(0, ".")
try:
    from ledger import evaluate_run
except ImportError:  # when run from the valve_test directory vs repo root
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ledger import evaluate_run

ALPHA = 0.01


# ---------------------------------------------------------------------------
# Statistics (stdlib implementations, self-checked below)
# ---------------------------------------------------------------------------

def _betacf(a, b, x):
    """Continued fraction for the incomplete beta function (Numerical Recipes)."""
    MAXIT, EPS, FPMIN = 200, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def betainc_reg(a, b, x):
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_two_sided_p(t_stat, df):
    x = df / (df + t_stat * t_stat)
    return betainc_reg(df / 2.0, 0.5, x)


def paired_t(diffs):
    n = len(diffs)
    mean = statistics.mean(diffs)
    sd = statistics.stdev(diffs) if n > 1 else 0.0
    if sd == 0.0:
        return mean, sd, float("inf") if mean != 0 else 0.0, 0.0 if mean != 0 else 1.0
    t_stat = mean / (sd / math.sqrt(n))
    return mean, sd, t_stat, t_two_sided_p(t_stat, n - 1)


def sign_flip_p(diffs):
    """Exact two-sided sign-flip permutation p for H0: symmetric about 0."""
    n = len(diffs)
    obs = abs(sum(diffs))
    extreme = 0
    for signs in itertools.product((1, -1), repeat=n):
        if abs(sum(s * d for s, d in zip(signs, diffs))) >= obs - 1e-12:
            extreme += 1
    return extreme / (2 ** n)


def wilcoxon_p(diffs):
    """Exact two-sided Wilcoxon signed-rank p (zeros dropped, ties averaged)."""
    vals = [d for d in diffs if d != 0.0]
    n = len(vals)
    if n == 0:
        return 1.0
    order = sorted(range(n), key=lambda i: abs(vals[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(vals[order[j + 1]]) == abs(vals[order[i]]):
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    w_plus = sum(r for r, d in zip(ranks, vals) if d > 0)
    total = sum(ranks)
    w_obs = min(w_plus, total - w_plus)
    extreme = 0
    for signs in itertools.product((0, 1), repeat=n):
        w = sum(r for r, s in zip(ranks, signs) if s)
        if min(w, total - w) <= w_obs + 1e-12:
            extreme += 1
    return extreme / (2 ** n)


def holm(pvals):
    """Holm step-down adjusted p-values, returned in original order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * pvals[idx])
        adj[idx] = min(1.0, running)
    return adj


def minimum_detectable(diffs, alpha=ALPHA, power=0.80):
    """Normal-approximation MDE for the paired mean, from measured noise."""
    n = len(diffs)
    sd = statistics.stdev(diffs) if n > 1 else 0.0
    nd = statistics.NormalDist()
    z = nd.inv_cdf(1 - alpha / 2) + nd.inv_cdf(power)
    return z * sd / math.sqrt(n)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def load_usable_runs(runs_path, key_path):
    with open(key_path) as fh:
        key = json.load(fh)
    usable, excluded = [], []
    with open(runs_path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "R_port" not in rec:
                continue  # reference points (C5/C6) carry no routing data
            verdict = evaluate_run(rec)
            if not verdict["usable"]:
                excluded.append((rec["run_id"],
                                   "over-unity hard fail" if verdict["over_unity_hard_fail"]
                                   else "ledger did not close"))
                continue
            cond = key[rec["condition_code"]]
            rec["_cond"] = cond
            usable.append(rec)
    return usable, excluded


def delta_r(runs, device, source, power_mw):
    """Per-chip DeltaR (ON - OFF) for one stratum, chips sorted."""
    by_chip = {}
    for rec in runs:
        c = rec["_cond"]
        if (c["device"], c["source"], c["power_mw"]) != (device, source, power_mw):
            continue
        slot = by_chip.setdefault(c["chip"], {"ON": [], "OFF": []})
        slot[c["valve"]].append(rec["R_port"])
    return [statistics.mean(v["ON"]) - statistics.mean(v["OFF"])
            for _, v in sorted(by_chip.items()) if v["ON"] and v["OFF"]]


def mean_nonrecip(runs, device="T", source="coherent", power_mw=8.0):
    vals = [rec["S21_minus_S12_dB"] for rec in runs
            if (rec["_cond"]["device"], rec["_cond"]["source"],
                rec["_cond"]["power_mw"], rec["_cond"]["valve"])
            == (device, source, power_mw, "ON")]
    return statistics.mean(vals) if vals else 0.0


def analyse(runs_path, key_path, out=sys.stdout):
    usable, excluded = load_usable_runs(runs_path, key_path)
    print(f"usable runs: {len(usable)}   excluded: {len(excluded)}", file=out)
    for run_id, reason in excluded:
        print(f"  excluded {run_id}: {reason}", file=out)

    primary = delta_r(usable, "T", "coherent", 8.0)
    if len(primary) < 3:
        print("NOT ANALYSABLE: fewer than 3 chips with complete primary strata.", file=out)
        return 1
    mean, sd, t_stat, p_t = paired_t(primary)
    p_perm = sign_flip_p(primary)
    p_wil = wilcoxon_p(primary)
    mde = minimum_detectable(primary)
    print(f"\nPRIMARY  DeltaR (T, coherent, 8 mW), n={len(primary)} chips", file=out)
    print(f"  mean DeltaR = {mean:+.4f}  (sd {sd:.4f})", file=out)
    print(f"  sign-flip permutation p = {p_perm:.4f}   t-test p = {p_t:.4f}   "
          f"Wilcoxon p = {p_wil:.4f}   alpha = {ALPHA}", file=out)
    print(f"  minimum detectable DeltaR at 80% power ~ {mde:.4f}", file=out)

    secondaries = [
        ("DeltaR thermal (T, 8 mW)", delta_r(usable, "T", "thermal", 8.0)),
        ("DeltaR low power (T, coherent, 2 mW)", delta_r(usable, "T", "coherent", 2.0)),
        ("DeltaR control C1 (coherent, 8 mW)", delta_r(usable, "C1", "coherent", 8.0)),
        ("DeltaR control C3 (coherent, 8 mW)", delta_r(usable, "C3", "coherent", 8.0)),
    ]
    raw_p, sec_means = [], {}
    for name, diffs in secondaries:
        if len(diffs) >= 3:
            m, _, _, pp = paired_t(diffs)
            raw_p.append(sign_flip_p(diffs))
            sec_means[name] = (m, pp)
        else:
            raw_p.append(1.0)
            sec_means[name] = (float("nan"), float("nan"))
    adj_p = holm(raw_p)
    print("\nSECONDARY (Holm-corrected)", file=out)
    for (name, _), ap in zip(secondaries, adj_p):
        m, _ = sec_means[name]
        print(f"  {name:<42} mean {m:+.4f}   adj. p = {ap:.4f}", file=out)
    nonrecip = mean_nonrecip(usable)
    print(f"  {'nonreciprocity S21-S12 (T, ON, coherent, 8 mW)':<42} mean {nonrecip:+.2f} dB", file=out)

    sec = {name: ap for (name, _), ap in zip(secondaries, adj_p)}
    checks = {
        "ledger clean on all analysed runs": len(excluded) == 0,
        "primary p < 0.01 (permutation)": p_perm < ALPHA,
        "primary direction as predicted (DeltaR > 0)": mean > 0,
        "controls null (C1, C3 adj. p >= 0.01)":
            sec["DeltaR control C1 (coherent, 8 mW)"] >= ALPHA
            and sec["DeltaR control C3 (coherent, 8 mW)"] >= ALPHA,
        "mechanism check: low-power DeltaR collapsed (< half of high-power)":
            abs(sec_means["DeltaR low power (T, coherent, 2 mW)"][0]) < abs(mean) / 2,
        "source dependence: thermal DeltaR differs from coherent "
        "(thermal adj. p >= 0.01 while primary < 0.01, or |thermal| < |coherent|/2)":
            (sec["DeltaR thermal (T, 8 mW)"] >= ALPHA and p_perm < ALPHA)
            or abs(sec_means["DeltaR thermal (T, 8 mW)"][0]) < abs(mean) / 2,
    }
    print("\nSECTION 9 CHECKLIST", file=out)
    for name, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}", file=out)
    validated = all(checks.values())
    print(f"\nVERDICT: {'VALIDATED (protocol section 9)' if validated else 'NOT VALIDATED'}",
          file=out)
    if not validated and p_perm < ALPHA and mean > 0 and \
            (sec["DeltaR control C1 (coherent, 8 mW)"] < ALPHA
             or sec["DeltaR control C3 (coherent, 8 mW)"] < ALPHA):
        print("Pattern note: an effect that appears equally in the controls is a "
              "filter, a loss imbalance, or a bad isolator — the claim is falsified "
              "as stated (section 9).", file=out)
    return 0


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def selftest():
    # t-distribution implementation check: t_{0.975, df=9} = 2.2622 -> p = 0.05
    p = t_two_sided_p(2.2622, 9)
    assert abs(p - 0.05) < 0.003, p
    # permutation / Wilcoxon sanity on a clear effect and on null-ish data
    effect = [0.05, 0.07, 0.04, 0.06, 0.055, 0.065, 0.045, 0.06, 0.05, 0.058]
    assert sign_flip_p(effect) < 0.01 and wilcoxon_p(effect) < 0.01
    nullish = [0.004, -0.006, 0.002, -0.003, 0.005, -0.001, 0.003, -0.004, 0.001, -0.002]
    assert sign_flip_p(nullish) > 0.05
    adj = holm([0.001, 0.02, 0.04])
    assert adj[0] <= adj[1] <= adj[2] and abs(adj[0] - 0.003) < 1e-9, adj

    # End-to-end: null session must NOT validate; injected effect MUST.
    import io
    import os
    import tempfile
    import valve_sweep
    tmp = tempfile.mkdtemp()
    for inject, expect_validated in [(False, False), (True, True)]:
        records, key = valve_sweep.simulate_session(11, 10, inject_effect=inject)
        rp, kp = os.path.join(tmp, "r.jsonl"), os.path.join(tmp, "k.json")
        with open(rp, "w") as fh:
            for rec in records:
                fh.write(json.dumps(rec) + "\n")
        with open(kp, "w") as fh:
            json.dump(key, fh)
        buf = io.StringIO()
        analyse(rp, kp, out=buf)
        text = buf.getvalue()
        got = "VERDICT: VALIDATED" in text
        assert got == expect_validated, (inject, text)
    print("analysis.py selftest: t-distribution verified against the df=9 "
          "critical value; exact tests behave on known data; Holm ordering OK; "
          "end-to-end — null session NOT VALIDATED, injected-effect session "
          "VALIDATED. All as specified.")
    return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if len(argv) != 3:
        print(__doc__)
        return 2
    return analyse(argv[1], argv[2])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
