#!/usr/bin/env python3
"""
Valve / bias / phase sweep — IOF Valve Test Protocol (TFLN-PHO-2026-09 Rev 0.3)
================================================================================

Generates the pre-registered sweep plan and run records for the valve test:

  * Factors: device (T test article, C1 reciprocal twin, C3 filter-only
    control) x valve (ON / OFF) x source (coherent / thermal) x input power
    (2 mW low-power mechanism control, 8 mW switching regime), 5 repeats
    per condition per chip, run order randomized under a recorded seed.
  * Reference points interleaved every 24 runs: C5 (dump disconnected,
    substrate heating baseline) and C6 (dark run, drive-only heating).
  * Blinding: run records carry an opaque condition_code. The decode key
    is written to a SEPARATE file and is only handed to analysis.py after
    the pipeline is frozen (protocol section 4 / 8).
  * Every record carries the full energy-ledger terms (see ledger.py),
    thermistor readings, and the S21-S12 nonreciprocity reading.

Declared mechanism (Rev 0.3, section 1): (c) nonlinearity with asymmetric
intensity — Kerr MZI valve (Opt 1, first light) / PPLN parametric valve
(Opt 2). Its signature prediction, built into the sweep design: any real
DeltaR must COLLAPSE at the 2 mW low-power point. A power-independent
DeltaR contradicts the declared mechanism.

Backends:
  * simulate — a synthetic instrument model so the whole pipeline
    (sweep -> ledger -> analysis) can be exercised before hardware
    exists. The null model has NO valve effect anywhere. --inject-effect
    adds a known H1-consistent effect (T only, power-gated, stronger for
    coherent than thermal) purely to prove the analysis can see one.
    Simulated records are marked "backend": "simulated" and must never
    be archived as data.
  * hardware — interface stub. Wire real instruments (power meters, OSA,
    HBT, TEC/thermistor loggers) into HardwareBackend.measure() when a
    chip exists; the plan, blinding, and record schema do not change.

Usage:
    python3 valve_sweep.py --simulate --seed 7 --chips 10 --out runs.jsonl --key key.json
    python3 valve_sweep.py --simulate --seed 7 --chips 10 --inject-effect --out runs_fx.jsonl --key key_fx.json
    python3 valve_sweep.py --selftest

Stdlib only. Frozen as part of the Rev 0.3 pre-registration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys

DEVICES = ["T", "C1", "C3"]
VALVE = ["ON", "OFF"]
SOURCES = ["coherent", "thermal"]
POWERS_MW = [2.0, 8.0]          # low-power mechanism control / switching regime
REPEATS = 5                     # protocol: at least 5 repeats per condition
INTERLEAVE_EVERY = 24           # C5 / C6 reference cadence

# Simulated-instrument base routing ratios (fraction to Through port).
BASE_R = {"T": 0.62, "C1": 0.60, "C3": 0.61}
SIGMA_R = 0.01


def condition_code(cond: dict, session_key: str) -> str:
    raw = json.dumps(cond, sort_keys=True) + session_key
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def build_plan(seed: int, chips: int):
    """Return (points, key). Points are run dicts in randomized order;
    key maps condition_code -> true condition (the blinding key)."""
    rng = random.Random(seed)
    session_key = f"session-seed-{seed}"
    key = {}
    points = []
    for chip in range(1, chips + 1):
        for device in DEVICES:
            for valve in VALVE:
                for source in SOURCES:
                    for power in POWERS_MW:
                        for rep in range(REPEATS):
                            cond = {"chip": chip, "device": device, "valve": valve,
                                    "source": source, "power_mw": power, "rep": rep}
                            code = condition_code(cond, session_key)
                            key[code] = cond
                            points.append({"condition_code": code})
    rng.shuffle(points)
    # Interleave C5 / C6 reference points (unblinded run conditions).
    planned = []
    for i, pt in enumerate(points):
        planned.append(pt)
        if (i + 1) % INTERLEAVE_EVERY == 0:
            planned.append({"condition_code": "REF-C5"})
            planned.append({"condition_code": "REF-C6"})
    for i, pt in enumerate(planned):
        pt["run_id"] = f"run-{i + 1:04d}"
    return planned, key


# ---------------------------------------------------------------------------
# Simulated backend
# ---------------------------------------------------------------------------

def _term(v: float, rel_sigma: float, rng: random.Random):
    return {"v": v, "s": abs(v) * rel_sigma}


def simulate_point(cond: dict, rng: random.Random, inject_effect: bool) -> dict:
    device, valve, source = cond["device"], cond["valve"], cond["source"]
    p_in = cond["power_mw"] * 1e-3
    p_drive = 2.0e-3 if valve == "ON" else 0.3e-3

    r_port = BASE_R[device] + rng.gauss(0.0, SIGMA_R)
    nonrecip_db = rng.gauss(0.0, 0.05)

    if inject_effect and device == "T" and valve == "ON":
        # H1-consistent injected effect: mechanism (c) => power-gated
        # (Kerr phase shift scales with power, so the routing change
        # roughly does too), statistics-dependent (coherent >> thermal),
        # T only.
        gate = cond["power_mw"] / 8.0
        r_port += gate * (0.06 if source == "coherent" else 0.015)
        nonrecip_db += gate * (1.8 if source == "coherent" else 0.4)

    optical_out = 0.90 * p_in
    p_through = r_port * optical_out
    p_dump = (1.0 - r_port) * optical_out
    record = {
        "chip": cond["chip"], "device": device, "valve": valve,
        "source": source, "power_mw": cond["power_mw"],
        "R_port": round(r_port, 5),
        "S21_minus_S12_dB": round(nonrecip_db, 4),
        "P_in": _term(p_in, 0.005, rng),
        "P_drive": _term(p_drive, 0.01, rng),
        "P_through": _term(p_through, 0.008, rng),
        "P_dump": _term(p_dump, 0.008, rng),
        "P_scatter": _term(0.04 * p_in, 0.05, rng),
        "P_absorbed": _term(0.06 * p_in + p_drive, 0.05, rng),
        "thermistor_C": round(25.0 + rng.gauss(0.0, 0.004), 4),
        "backend": "simulated",
    }
    return record


def simulate_session(seed: int, chips: int, inject_effect: bool):
    """Return (records, key) — full simulated session, blinded codes on."""
    plan, key = build_plan(seed, chips)
    rng = random.Random(seed + 1)
    records = []
    for pt in plan:
        code = pt["condition_code"]
        if code.startswith("REF-"):
            records.append({"run_id": pt["run_id"], "condition_code": code,
                            "reference": code, "backend": "simulated"})
            continue
        rec = simulate_point(key[code], rng, inject_effect)
        rec["run_id"] = pt["run_id"]
        rec["condition_code"] = code
        # Strip the true condition from the record: blinding means the
        # record itself must not carry it. Analysis decodes via the key.
        for field in ("chip", "device", "valve", "source", "power_mw"):
            rec.pop(field, None)
        rec["_chip"] = key[code]["chip"]  # chip identity is not blinded
        records.append(rec)
    return records, key


class HardwareBackend:
    """Stub for the real instrument chain. Implement measure() against the
    calibrated power meters / OSA / thermistor loggers when a chip exists.
    The plan, blinding, and record schema above do not change."""

    def measure(self, cond: dict) -> dict:  # pragma: no cover
        raise NotImplementedError("No hardware attached. Use --simulate to "
                                  "exercise the pipeline.")


# ---------------------------------------------------------------------------
# CLI + self-test
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--inject-effect", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--chips", type=int, default=10)
    ap.add_argument("--out")
    ap.add_argument("--key")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.simulate:
        print("Only the simulated backend is available until hardware exists "
              "(see HardwareBackend). Re-run with --simulate.")
        return 2
    records, key = simulate_session(args.seed, args.chips, args.inject_effect)
    if args.out:
        with open(args.out, "w") as fh:
            for rec in records:
                fh.write(json.dumps(rec) + "\n")
    if args.key:
        with open(args.key, "w") as fh:
            json.dump(key, fh, indent=1)
    print(f"{len(records)} run records "
          f"({'effect injected' if args.inject_effect else 'null model'}), "
          f"key holds {len(key)} blinded conditions.")
    return 0


def selftest():
    plan_a, key_a = build_plan(7, 2)
    plan_b, _ = build_plan(7, 2)
    assert [p["condition_code"] for p in plan_a] == [p["condition_code"] for p in plan_b], \
        "plan must be deterministic under its seed"
    refs = [p for p in plan_a if p["condition_code"].startswith("REF-")]
    assert refs and all(r["condition_code"] in ("REF-C5", "REF-C6") for r in refs)
    records, key = simulate_session(7, 2, inject_effect=False)
    data = [r for r in records if "R_port" in r]
    assert data and all("device" not in r and "valve" not in r for r in data), \
        "blinded records must not carry their condition"
    assert all(key[r["condition_code"]]["chip"] == r["_chip"] for r in data)
    fx, _ = simulate_session(7, 2, inject_effect=True)
    assert len(fx) == len(records)
    print("valve_sweep.py selftest: deterministic randomized plan, C5/C6 "
          "interleaves present, blinding round-trips through the key — OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
