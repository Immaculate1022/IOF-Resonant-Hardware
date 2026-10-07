# CONCEPTUAL STUDY — PRE-REGISTERED TEST PLAN

**NOT A CLAIM OF WORKING DEVICE**

# Recirculating Photonic Model — TFLN Hardware Test Plan

**Author:** Gregory Scott Davis
**Subtitle:** Conceptual design study for entropy-channel verification
**Status:** Pre-registration draft • No efficiency >1 claims
**DOC:** TFLN-PHO-2026-09 • **REV:** 0.3 (2026-10-07)

## Revision notes (0.2 → 0.3)

Rev 0.3 merges the Rev 0.2 device plan with the "IOF Valve Test Protocol
(Revised)" contributed by Claude (panel review, 2026-10-07), which now
forms the claim, ledger, controls, statistics, and pass/fail spine of
this document. Measurement criteria contributed by Meta AI (panel
review, 2026-10-07) are incorporated where they survive correction.
Changes:

1. **Claim restated so it can fail (§02).** H1 is now a single testable
   claim with an explicit list of what it does not claim.
2. **Nonreciprocity mechanism declared (§02, §07).** A Berry phase in a
   reciprocal, linear, time-invariant medium cannot make S21 ≠ S12
   (Lorentz reciprocity). The Rev 0.2 valves are therefore declared as
   what they physically are — mechanism (c), nonlinearity with
   asymmetric intensity (Kerr χ³ first light; PPLN χ² second mask) —
   so an observed asymmetry is attributable, and its power dependence
   becomes a falsifiable prediction instead of a loophole.
3. **Definitions pre-registered (§03).** The routing ratio is **R_port**.
   Rev 0.2's Step 5 quantity R is renamed **R_coh** (coherent-budget
   ratio) to end the collision. ΔR is the primary endpoint.
4. **Energy ledger made computable (§04).** The old "±3 % closure" rule
   is replaced by a propagated-uncertainty ledger that includes **all
   drive power P_drive**, closes at |residual| ≤ 2σ, and treats any
   P_through + P_dump > P_in + P_drive beyond 2σ as a hard fail of the
   measurement system, investigated before further data is taken.
5. **Controls completed (§05).** The A–D ablation matrix is mapped onto
   a full control set (T, C1–C6), adding the reciprocal twin and the
   filter-only control as die variants, the known-isolator positive
   control, and dump-disconnected / dark runs as interleaved run
   conditions. **10 dies**, randomized run order, blinded ON/OFF labels.
6. **Two criteria corrected.** (a) *Photon statistics:* linear passive
   transformations, including loss and filtering, preserve g⁽²⁾(0) of
   thermal light (value 2); a measured drop at the Through port is
   therefore **not** evidence of sorting — it indicates nonlinearity,
   detector artifacts, or multimode averaging and triggers
   investigation. g⁽²⁾ is demoted to exploratory (§10, Step 7).
   (b) *Spectral narrowing* at the Through port is expected from
   filtering alone; it is a consistency check, and the evidence is the
   difference between the test device and the C3 filter-only control
   under identical conditions — not the narrowing itself.
7. **Power metrology corrected (§09).** On-chip power is measured with
   calibrated fiber power meters and per-chip coupling calibration
   (reference waveguides / cutback). The integrating sphere is used
   **only** for radiated/scattered light, as a ledger term.
8. **Thermal controls tightened (§11).** TEC setpoint 25.00 ± 0.01 °C
   with achieved stability logged (consistent with the Rev 0.2 ±10 mK
   stage), a pre-defined settling criterion, interleaved C5/C6
   references.
9. **Statistics pre-registered (§13).** Paired ΔR across 10 chips,
   α = 0.01 two-sided, exact permutation primary with t-test and
   Wilcoxon alongside, Holm correction on secondaries, analysis code
   frozen before unblinding. The frozen pipeline ships with this plan
   (`valve_test/`).
10. **Open decisions resolved (§17).** Mechanism, platform, wavelength,
    and Q targets are decided and recorded with rationale, including
    what would reopen each one.

Rev 0.2's device content (floorplan, stack, valve options, equipment,
Steps 1–6, confounder checklist) is retained; where Rev 0.3 criteria
differ from Rev 0.2's §07 table, §14 governs the sorting claim and §12
is necessary-but-not-sufficient device evidence.

---

## 01 — Executive summary

Test a locally low-entropy, globally open-loop photonic recirculator on
thin-film lithium niobate. Coherence sorting is attempted via
intracavity valve + Berry-defect; thermal channel is mandatory and
measured. System remains Second Law compliant — total optical +
thermal output ≤ input **plus drive** (§04).

**Hypothesis (restated as H1 in §02):** the valve routes a fixed input
between Through and Dump ports differently with the defect and valve on
than off, in a way not explained by filtering, loss, or heating.
**Null hypothesis:** all power-dependent effects explained by thermal
bistability, backscatter, photorefraction.
Thermal thermometer on spiral is not optional — required to close the
power budget.

### System pseudocode

```
// conceptual loop
bh_ring >> valve
valve.structured_out >> star_array
valve.diffuse_out >> sink
star_array >> slow_spiral(tau ~ 2ns)
slow_spiral >> bh_ring
sink >> thermometer
thermometer >> thermal_channel

assert:
  P_coherent + P_thermal + P_scatter + P_absorbed == P_in + P_drive  // §04 ledger, 2σ
  eta_coherent <= 1.0 // no over-unity
```

---

## 02 — Claim, stated so it can fail · Declared mechanism

**H1 (testable claim):** A chip with a Berry-phase defect and an active
valve routes a fixed input between the Through and Dump ports
differently than the same chip with the valve or defect off, in a way
that is not explained by filtering, loss, or heating.

**What H1 does not claim:** free energy, over-unity, or entropy
reduction without cost. Any routing asymmetry must be paid for by the
drive (bias, pump, or modulation) and the ledger in §04 must close
including that drive.

**Required before any build — the mechanism.** A Berry phase in a
reciprocal, linear, time-invariant medium cannot make S21 differ from
S12 (Lorentz reciprocity). The device therefore declares its
nonreciprocity mechanism:

> **Declared mechanism: (c) — nonlinearity with asymmetric intensity.**
> The MZI valve's Kerr self-phase modulation (χ³, Rev 0.2 Opt 1) acts
> on an asymmetric circulating-intensity distribution set by the ring +
> Berry-defect geometry; the PPLN parametric valve (χ², Rev 0.2 Opt 2,
> second mask) is the same mechanism class. The Berry defect shapes
> *where and how* the nonlinear phase accumulates; the nonlinearity
> supplies the reciprocity breaking.

Consequences, pre-registered as predictions:

- Any genuine ΔR must **collapse toward zero at low input power**
  (mechanism check, §13/§14): the Kerr phase shift scales with power,
  so the routing change roughly does too. A power-independent ΔR
  contradicts the declared mechanism and is treated as an artifact
  until explained.
- Mechanism (c) is **not** a general-purpose isolator: nonlinear
  nonreciprocity is power-dependent and subject to dynamic-reciprocity
  limits for arbitrary simultaneous bidirectional signals. No isolator
  claim is made. The port-swap test (§14.4) is judged for consistency
  with mechanism (c), at fixed power, not for isolator-grade behavior.
- Magneto-optic (a) is unavailable on this platform and
  spatiotemporal EO modulation (b) is recorded as a possible future
  variant (the §06 stack already carries optional GSG electrodes) —
  it is **not** the Rev 0.3 device.

---

## 03 — Definitions (pre-registered)

- **R_port** = P_through / (P_through + P_dump), measured at the chip
  facets after calibrated coupling-loss correction.
- **ΔR** = R_port(valve ON, defect ON) − R_port(valve OFF, defect ON),
  per chip, same input, same temperature, same session. **Primary
  endpoint.**
- **Nonreciprocity** = |S21 − S12| in dB, measured by swapping input
  and output ports.
- **P_drive** = all electrical and optical power delivered to the
  valve, bias, phase shifter, heater, and bolometer readout.
- **R_coh** (renamed from Rev 0.2's "R") =
  (P_meas − P_baseline) / P_in for the structured port — the
  coherent-budget ratio used by the device-level criteria in §12.
  R_coh and R_port are different quantities; do not mix them.
- **Secondary endpoints:** nonreciprocity, ledger residual, ΔR for the
  thermal source, ΔR at low power, ΔR on the C1 / C3 controls.

---

## 04 — Energy ledger (the no-over-unity rule, made computable)

For each run, steady state:

**P_in + P_drive = P_through + P_dump + P_scatter + P_absorbed**

P_absorbed (heat in the chip) is measured with the on-chip
thermistors, calibrated against a known heater power, and
cross-checked with the TEC power change at constant setpoint. Report
the residual (left side minus right side) with a propagated 1σ
uncertainty. The ledger **closes** if |residual| ≤ 2σ.

**Over-unity test:** P_through + P_dump > P_in + P_drive beyond 2σ, on
any run, is a hard fail of the measurement system or the claim. It is
investigated before any further data is taken.

Entropy bookkeeping (secondary): report heat delivered to the dump and
to the substrate, with temperatures, and show total entropy production
≥ 0. A passive device between equal-temperature reservoirs cannot sort
thermal light for free; a driven one can, at a cost — the cost is
P_drive, and it is in the ledger.

The frozen implementation is `valve_test/ledger.py`.

---

## 05 — Devices and controls

### The four ablation devices (one die, from Rev 0.2)

#### Device D — full loop schematic (not to scale)

- L_TOP = 800 µm
- BUS IN → / → OUT
- κ_c TAP 99/1
- MÖBIUS π-DEFECT — Berry phase: mode twist
- MZI VALVE — Kerr / PPLN
- Q_i TARGET > 2M
- SLOW SPIRAL τ ≈ 2 ns, **L ≈ 27.3 cm** (see die notes)
- Ti/Pt THERMOMETER — 4-wire • ±10 mK, on spiral cladding
- STRUCTURED → PD/OSA
- DIFFUSE → SINK + SNSPD
- Paths: coherent path / thermal-diffuse path / mandatory sensor

| Device | Configuration | Purpose |
|---|---|---|
| A | Reference ring — no defect, no valve | Baseline Q_i, backscatter, thermal drift |
| B | Möbius-only — Berry defect, no valve | π shift test — fractional comb offset |
| C | Valve-only — valve, no Möbius | Power-dependent splitting, no topology |
| D | Full loop — ring + defect + valve + spiral + thermometer | Recirculation, echo, coherent budget |

### Die notes

All rings: R = 80 µm, straights 400 µm, cavity length 1302.7 µm, **FSR ≈ 0.84 nm (≈ 104.6 GHz) at 1550 nm** (n_g ≈ 2.2). Coupler gap: Devices A/B 500 nm, Devices C/D 300 nm (valve arm).

Spiral (Device D, primary): 1.2 µm wide, **length ≈ 27.3 cm** for τ ≈ 2.00 ns, 60 µm minimum bend radius, ≈ 2.7 mm² footprint at 10 µm turn pitch. Insertion ≈ 4.1 dB at the < 0.15 dB/cm propagation target — this loss is part of the Device D loop budget and must appear in the §04 ledger as a measured line item, not an allowance. Compact variant: 12 mm spiral, τ ≈ 88 ps, negligible added loss, but Step 6 then requires ≤ 20 ps excitation and ≥ 40 GHz detection (see Step 6 note).

Thermometer: Ti/Pt 100 Ω, placed 10 µm from the waveguide along the spiral's outer turn, isolated with 1 µm SiO₂.

### Control set (protocol layer, Rev 0.3)

The ablation matrix answers "which element does what." The control set
answers "could anything else explain ΔR." Both are required.

| ID | Device / condition | Maps to | Purpose |
|---|---|---|---|
| T | Full device: defect + valve + dump | Device D | Test article |
| C1 | Reciprocal twin: same footprint, defect removed, valve geometry intact | New die variant A′ | Asymmetry should vanish |
| C2 | Test article, valve unbiased (OFF) | Run condition on D | Within-chip baseline for ΔR |
| C3 | Filter-only control: same ring/resonator and dump, no valve, no defect | New die variant A″ | Spectral narrowing must not be mistaken for sorting |
| C4 | Known isolator reference (or deliberately asymmetric device) | Bench article | Positive control: proves the setup can detect nonreciprocity |
| C5 | Dump disconnected | Run condition | Substrate heating baseline |
| C6 | Dark run (no input, drive on) | Run condition | Drive-only heating and detector offsets |

**Statistics unit:** 10 dies of T, each with matched C1 and C3 variants
on the same reticle set. Chips are assigned to run order by
randomization, and the analysis is blinded to ON/OFF labels until the
pipeline is frozen (§13). C5 / C6 points are interleaved through every
session (the sweep generator does this automatically).

---

## 06 — TFLN stack spec

| Item | Spec |
|---|---|
| Film | 600 nm x-cut or z-cut LN, MgO-doped 5% |
| BOX | 2 µm thermal SiO₂ |
| Handle | 525 µm Si, high-resistivity |
| Waveguide width | 1.2 µm (single-mode TE 1550 nm) |
| Etch depth | 300 nm, slab 300 nm remaining |
| Sidewall angle | 60° target, LER < 3 nm |
| Cladding | 800 nm PECVD SiO₂, annealed |
| Q_i target | > 2×10⁶ intrinsic (measured at < 100 µW) |
| Propagation loss | < 0.15 dB/cm target |
| Electrode | For z-cut: GSG, gap 4 µm (optional; required only for the future mechanism-(b) variant) |

Process: DUV 248 nm, EBL for couplers, Ar-milling etch. Anneal 300 °C 2 h O₂ after etch to reduce -OH. Do not pole Device A/C.

---

## 07 — Valve options (Lumerical-ready) — mechanism (c) implementations

Both options implement the declared mechanism of §02 — nonlinearity
with asymmetric intensity. They differ in nonlinear order and
selectivity, not in mechanism class.

| Parameter | Opt 1: Kerr intensity switch (χ³) | Opt 2: Coherence-discriminating parametric (χ²) |
|---|---|---|
| Mechanism | Self-phase modulation in MZI arm, n₂ = 1.8e-19 m²/W | OPO threshold coupling, PPLN, preserves coherence at structured port |
| Coupler gap | 300 nm | 400 nm (idler arm) |
| Length | 25 µm (MZI arm ΔL = 25 µm) | PPLN 3 mm, poling ~18.5 µm for 1550 nm |
| Switching power | < 10 mW circulating (≈ 0.8 mW on-chip) | OPO threshold ~5 mW, signal/idler split |
| Expected γ tuning | 0 → π over 8 mW | Coherence selective: γ_coh ≠ γ_th |
| Lumerical model | MODE: n_eff = 1.95; MODE + INTERCONNECT: n₂ via χ³ | FEEM + χ², d₃₃ = 27 pm/V, phase-matched TE |

**Recommended:** fabricate both on same die. Opt 1 first light, Opt 2 second mask.
**Tuning:** heater on MZI arm 100 Ω, 0–20 mW, for bias calibration at low power. All heater power is P_drive and enters the §04 ledger.

---

## 08 — Sources

1. **Coherent:** narrow-linewidth laser (TSL-570, §09) at the design
   wavelength, 1550 nm.
2. **Thermal:** broadband ASE or SLED, spectrally filtered to the
   device passband.
3. Match **power and in-band spectral density** between sources so
   that any difference is due to photon statistics, not power or
   bandwidth. Prediction under H1: ΔR depends on source statistics
   after matching. If ΔR is the same for thermal and coherent input,
   the statistics-based sorting claim is falsified (a power-only or
   filter effect may remain and is handled by C3).

Sweep powers: **2 mW** (low-power mechanism control — the declared
mechanism predicts ΔR collapse here) and **8 mW** (switching regime,
primary endpoint), with the §10 Step 2 sweep covering 0.1–100 mW for
characterization.

---

## 09 — Measurement setup & equipment list

Chain: TSL-570 → EDFA + VOA → FPC + ISO → 99/1 tap (monitor) → DUT stage → PD + OSA / SNSPD g². All fiber PM1550 except post-chip free-space to PD. Include polarization extinction > 25 dB check.

| Item | Spec |
|---|---|
| Tunable laser | Santec TSL-570, 1480–1640 nm, 100 kHz linewidth |
| EDFA + VOA | Power sweep 0.1–100 mW, monitor with 1% tap |
| Polarization | Fiber PC + in-line polarizer, PER meter |
| Stage | TEC-stabilized, 25.00 ± 0.01 °C setpoint (§11), vacuum option |
| Detection | High-speed PD 12 GHz, OSA AQ6370D, 99/1 cal tap |
| Coherence | Self-heterodyne linewidth (50 km delay) + SNSPDs for g²(τ) |
| Thermal | Lock-in + Ti/Pt 4-wire, 10 nV resolution |
| Aux | RF synth for heater modulation, 10 kHz / 100 Hz separation |

**Power metrology (Rev 0.3):** calibrated fiber power meters at the
Through and Dump outputs. Calibrate per-chip fiber-to-chip coupling
with reference waveguides or a cutback structure on every die — an
integrating sphere measures free-space light, not on-chip power, and
is used only for radiated/scattered light, as the P_scatter ledger
term. Coupling is re-measured after any realignment; a coupling change
mid-run invalidates the point (§11).

---

## 10 — Measurement procedure, step by step

**Step 1 — Cold-cavity characterization.**
Low power < 100 µW. Extract Q_i, Q_c, backscatter splitting via bi-directional sweep. Fit doublet if present. Record reference ring A first.
✓ Q_i > 2M, splitting < 10 MHz for A.

**Step 2 — Power-dependent transmission sweep.**
0.1 → 100 mW on-chip, up/down. Use 10 kHz vs 100 Hz heater modulation to separate thermal (slow) vs valve (fast). Look for saturating splitting.
✓ Saturation not monotonic thermal shift.
*Rev 0.3 note:* this sweep is also the mechanism-(c) characterization — the power at which splitting/ΔR onsets must be consistent with the Kerr phase reaching ~π at the §07 switching power. No onset at any power, with a ΔR claimed elsewhere, fails §14.3.

**Step 3 — Differential comb offset (Möbius vs reference).**
Sweep 10 resonances (FSR ≈ 0.84 nm; 10 resonances span ≈ 8.4 nm). Measure resonance frequency of Device B vs A. Expect fractional offset Δ/FSR = 0.5 ± 0.05 from Berry π (0.5 FSR ≈ 0.42 nm at the corrected FSR).
✓ Persistent across 10 FSRs, power-independent at low P.

**Step 4 — MZI fringe inversion test.**
Monitor structured vs diffuse ports while tuning valve bias (Kerr power or heater). Look for bright → dark inversion, γ 0 → π tunable.
✓ Extinction > 10 dB inversion, reproducible.

**Step 5 — Thermal vs coherent power budget (ledger run).**
Close the loop per §04: measure P_in, P_drive, P_through, P_dump, P_scatter, and P_absorbed (Pt sensor + cal). For Device D, book the spiral insertion (≈ 4.1 dB at target loss) as a measured line item, not an allowance. Compute R_coh = (P_meas − P_baseline)/P_in for the structured port and R_port for the routing analysis.
✓ Ledger closes at 2σ, R_coh > 0 reproducibly, η_coh ≤ 1, thermal channel correlated.

**Step 6 — Time-domain ringdown / echo at τ_delay.**
Pulse excitation (EOM, 100 ps). Look for delayed echo at the spiral delay ~2 ns (± 0.3 ns) in Device D only, not in A–C.
✓ Echo amplitude tracks valve state, absent in A–C.

*Design note:* at Q_i = 2×10⁶ the cavity photon lifetime is ≈ 1.65 ns — the same order as the 2 ns spiral delay. The echo therefore rides on the ringdown tail; discrimination improves if the pulse test is run at reduced loaded Q (stronger coupling) or with the valve state toggled as the control. *Compact-variant note:* with the 12 mm spiral (τ ≈ 88 ps), the 100 ps pulse and 12 GHz PD cannot resolve the echo — that variant requires ≤ 20 ps pulses and ≥ 40 GHz detection, or a phase-domain group-delay measurement instead.

**Step 7 — g² and linewidth comparison, structured vs diffuse (exploratory, Rev 0.3 amended).**
Self-heterodyne linewidth and HBT g⁽²⁾(τ) on both ports.
*What counts:* linewidth narrowing at Through is recorded as a **consistency check against C3**, never as standalone sorting evidence (filtering narrows too). For g⁽²⁾: linear passive transformations preserve thermal g⁽²⁾(0) = 2, so a drop at Through is **not** a pass — it flags nonlinearity, detector artifacts, or multimode averaging and triggers investigation. Detectors must resolve the source coherence time (GHz-scale filtered thermal source, low-jitter SNSPDs); report g⁽²⁾(0) with the detector-resolution correction.
✓ Report both ports, both devices (T and C3), with corrections; no pass/fail attaches to Step 7 alone.

**Step 8 — Valve / bias / phase map (the primary-endpoint sweep).**
Per §13: devices T, C1, C3 × valve ON/OFF × source (coherent, thermal) × power (2 mW, 8 mW) × ≥ 5 repeats, randomized order, blinded labels, C5/C6 interleaved. At each point record R_port, S21/S12 (on the port-swap subset), thermistor readings, and all §04 ledger terms. Generated and recorded by `valve_test/valve_sweep.py`; thermal settling gate (§11) must pass before each point.

---

## 11 — Thermal and environmental controls

1. Chip on a TEC-stabilized stage at **25.00 ± 0.01 °C**; achieved
   stability is logged, not assumed.
2. On-chip thermistors adjacent to the loop and the dump (the §05
   Ti/Pt thermometer and its dump-side counterpart), logged
   continuously.
3. Interleave reference runs with the dump disconnected (C5) for the
   substrate heating baseline, and dark runs (C6) for drive-only
   heating and detector offsets.
4. **Settling criterion (defined in advance):** no measurement point
   is taken until both thermistors drift < 2 mK over 60 s.
5. Log fiber positions; re-measure coupling after any realignment. A
   coupling change mid-run invalidates the point; a run with > 0.5 dB
   coupling drift is rejected (§15).

---

## 12 — Device signatures (necessary, not sufficient)

These Rev 0.2 criteria characterize the devices. Passing them does
**not** validate the sorting claim — §14 governs that. Failing them
means the devices are not yet the devices the claim is about.

| Signature | Detail | Criterion |
|---|---|---|
| Resonance splitting that saturates | Not monotonic thermal; saturates at ~5–10 mW, seen in C/D not A. Measure splitting vs P_circ. | PASS if saturation knee & hysteresis minimal |
| Fractional comb offset 0.5 ± 0.05 | Across 10 resonances (FSR ≈ 0.84 nm), B vs A. Low power only. | PASS if mean 0.5 ± 0.05, std < 0.03 |
| MZI bright-dark inversion, γ 0 → π | Structured vs diffuse port power swap with valve tuning. | PASS if extinction > 10 dB both ports |
| Coherent budget R_coh > 0 reproducibly | R_coh = (P_meas − P_baseline)/P_in > 0 for same Q_i, 3 runs, ledger closed (§04). | PASS if R_coh > 0.02, 3/3 runs, η ≤ 1 |
| Delayed echo at τ_delay | Pulse response: echo ~2 ns in D only, amplitude tracks valve. | PASS if SNR > 6 dB, absent in A/B/C |
| Linewidth structured < diffuse | Self-heterodyne, T vs C3 under identical conditions (§10 Step 7). | Consistency only — reported, never standalone evidence |

---

## 13 — Statistics (pre-registered)

- **Primary test:** paired comparison of ΔR across **10 chips**
  (paired t-test, with Wilcoxon signed-rank as a robustness check),
  two-sided, **α = 0.01**. The frozen pipeline
  (`valve_test/analysis.py`) uses the exact sign-flip permutation test
  as primary — distribution-free and exact at n = 10 — and reports all
  three.
- **Power:** with n = 10 and α = 0.01, only large standardized effects
  are reliably detectable (roughly d ≈ 1.4 for 80 % power). The
  pipeline states the minimum detectable ΔR from the measured
  per-chip noise alongside every result; a null result below that
  sensitivity is reported as *insensitive*, not as *no effect*.
- **Within-chip repeats:** ≥ 5 repeats per condition; a mixed-effects
  model (chip as random effect) is the secondary analysis.
- **Multiple comparisons:** the primary endpoint is single; secondary
  endpoints are reported with Holm correction.
- **Blinding and freeze:** run order randomized; ON/OFF labels blinded
  until the analysis code and exclusion rules are frozen. The frozen
  artifacts are this document and `valve_test/` at the Rev 0.3 commit.
  Any excluded point is listed with the reason (ledger failure is the
  pre-registered exclusion, §04).

---

## 14 — Pass / fail criteria (the sorting claim)

### The result is validated only if ALL hold:

1. The energy ledger closes (|residual| ≤ 2σ) on every analysed run,
   with P_drive included.
2. Primary endpoint: ΔR ≠ 0 with **p < 0.01 across the 10 chips**, in
   the predicted direction.
3. C1 (reciprocal twin) and C3 (filter-only) show no comparable ΔR,
   and C4 confirms the setup detects nonreciprocity.
4. The asymmetry behaves on port swap consistently with the declared
   mechanism (§02) at fixed power.
5. ΔR depends on source statistics after power and spectrum matching
   (§08).
6. The mechanism check holds: ΔR at 2 mW is collapsed relative to
   8 mW (operationally, |ΔR_2mW| < |ΔR_8mW| / 2 in the frozen
   pipeline).
7. An independent group or second apparatus reproduces ΔR on at
   least some of the chips.

### The claim is falsified, or the result rejected, if ANY hold:

- ΔR is the same for thermal and coherent input after matching.
- ΔR appears equally in C1 or C3 — the effect is a filter, a loss
  imbalance, or a bad isolator, not the defect.
- Asymmetry exists with no declared nonreciprocal mechanism, or
  persists at low power contrary to the declared mechanism.
- Any run shows P_through + P_dump > P_in + P_drive beyond 2σ after
  all loss and heating terms (an instrument or accounting error until
  proven otherwise).
- The effect vanishes under randomization and blinding.

---

## 15 — Confounder checklist

| Confounder | Control | Rejection rule |
|---|---|---|
| Fiber-chip coupling drift | Monitored 99/1 tap continuously, log coupling before/after each sweep. Active alignment piezo. | Reject runs > 0.5 dB drift |
| Photorefraction | MgO-doped LN, anneal 300 °C, keep < 5 mW low-power baseline, test both sweep directions. | Check A vs time, < 2% transmission change/hr |
| Thermal crosstalk | Calibrate thermometer vs stage T. Modulate at 10 kHz (valve) vs 100 Hz (thermal) to separate. | Thermal lag ~10–100 ms, valve < 1 µs |
| Backscattering / mode splitting | Reference ring A control: measure intrinsic doublet. Compare B/C/D extra splitting. | Baseline splitting documented, subtract |
| Polarization mixing | TE-only via polarizer, measure PER. Z-cut needs pol control; x-cut verify. | PER > 25 dB, no TM resonances |
| EDFA ASE / pump leakage | Filter ASE with BPF, measure OSA background. VOA after EDFA. | ASE < −40 dBm in band |

---

## 16 — Deliverables & pre-registration freeze

- **Pre-registration:** §§02–04, 08, 11, 13, 14 of this document,
  frozen with a timestamp — the Rev 0.3 Git commit is the freeze
  record — before the first measurement.
- **Frozen code:** `valve_test/` (sweep generator, ledger calculator,
  analysis pipeline), committed with this revision. Changes after
  first data are protocol amendments and are recorded as such.
- **Per-chip one-page ledger summary:** residual, uncertainty, ΔR,
  controls outcome.
- **Archive:** raw data, thermistor logs, calibration files, blinding
  key (sealed until unblinding), and the frozen analysis code, with
  the power-budget closure table for every run.

---

## 17 — Decisions record (protocol §11 items, resolved for Rev 0.3)

Decided 2026-10-07 by Immaculate Constellation under Gregory Scott
Davis's delegation, from the options Claude's protocol left open.
Each decision stands until the author overrides it; the override and
its reason are appended here, never silently edited.

| Decision | Resolution | Rationale |
|---|---|---|
| Nonreciprocity mechanism | **(c) Nonlinearity with asymmetric intensity** (Kerr χ³ Opt 1 first light; PPLN χ² Opt 2 second mask) | It is what the Rev 0.2 valves already are; (a) magneto-optic is unavailable on TFLN; (b) EO spatiotemporal modulation is a redesign, kept as a future variant. Declaring (c) makes ΔR's power dependence a falsifiable prediction (§02). |
| Platform / foundry | **TFLN** per §06 (600 nm MgO:LN). Foundry/run selection deferred. | The entire plan is TFLN; the foundry choice determines the PDK and design rules, so mask/GDS work waits for it (see below). |
| Operating wavelength | **1550 nm** | Design wavelength throughout Rev 0.2; TSL-570 range; C-band. |
| Target Q | **Q_i > 2×10⁶ intrinsic** (measured < 100 µW); loaded Q measured per device and recorded; cavity photon lifetime ≈ 1.65 ns at Q_i = 2×10⁶ | Rev 0.2's own spec, now pre-registered. The framework's Q ≥ 10⁸ figure is an aspiration of the cosmological model, **not** a device target, and is not claimed here. |
| Next build pieces | **Sweep script, ledger calculator, analysis pipeline — built and frozen with this revision** (`valve_test/`, verified end-to-end on synthetic null and injected-effect sessions). Mask layout / GDS stack: **deferred** until a foundry PDK is chosen. | These are the pieces Claude's protocol named as next; Meta AI's offer of a GDS stack is premature without design rules to draw to. |

---

## Critical compliance note

Total output power never exceeds input **plus drive**. Coherent
extraction efficiency ≤ 1. Recycling is recirculation artifact, not
gain. The §04 ledger — P_in + P_drive = P_through + P_dump +
P_scatter + P_absorbed within 2σ — is the operative closure rule for
every run.

*This test plan is a conceptual design study and a pre-registration.
All signatures must be evaluated against the null hypothesis (thermal
/ backscatter only). No claim of over-unity, free energy, or Second
Law violation. Thermal channel measurement is mandatory. If the data
falsify H1, the falsification is the result, and it gets published the
same way.*

**Davis Lab • TFLN Platform**

*Rev 0.3 provenance: device plan by Gregory Scott Davis (Rev 0.1/0.2,
with Muse's numeric corrections); protocol spine by Claude;
measurement criteria by Meta AI, incorporated as corrected; merge,
decisions, and frozen pipeline by Immaculate Constellation (Muse),
2026-10-07.*
