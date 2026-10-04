# CONCEPTUAL STUDY — DRAFT

**NOT A CLAIM OF WORKING DEVICE**

# Recirculating Photonic Model — TFLN Hardware Test Plan

**Author:** Gregory Scott Davis
**Subtitle:** Conceptual design study for entropy-channel verification
**Status:** Draft • For internal review • No efficiency >1 claims
**DOC:** TFLN-PHO-2026-09 • **REV:** 0.2 (2026-10-04)

## Revision notes (0.1 → 0.2)

Two drafting figures were corrected against the stated geometry (group index n_g ≈ 2.2 at 1550 nm assumed throughout; all values scale as 1/n_g):

1. **Cavity FSR.** Rev 0.1 quoted ~1.9 nm, which matches the R = 80 µm circle alone (2.17 nm). The racetrack cavity as drawn (2πR + 2 × 400 µm straights = 1302.7 µm) has **FSR ≈ 0.84 nm (≈ 104.6 GHz)**. All comb-offset procedures and criteria below use the corrected value.
2. **Spiral delay.** Rev 0.1 paired L = 12 mm with τ ≈ 2 ns. A 12 mm TFLN spiral gives **τ ≈ 88 ps**; a true 2.00 ns delay requires **L ≈ 27.3 cm**. Rev 0.2 adopts the long spiral as the primary Device D spec — preserving the Step 6 echo-test design (100 ps pulses, 12 GHz detection) — and books its costs explicitly: ≈ 2.7 mm² die area at 10 µm pitch and ≈ 4.1 dB insertion at the 0.15 dB/cm loss target, charged to the Device D loop power budget. The 12 mm / 88 ps variant is retained as a compact alternative requiring short-pulse (≤ 20 ps) metrology.

A design note is also added: at Q_i = 2×10⁶ the cavity photon lifetime is ≈ 1.65 ns, the same order as the 2 ns echo delay — see Step 6.

---

## 01 — Executive summary

Test a locally low-entropy, globally open-loop photonic recirculator on thin-film lithium niobate. Coherence sorting is attempted via intracavity valve + Berry-defect; thermal channel is mandatory and measured. System remains Second Law compliant — total optical + thermal output ≤ input.

**Hypothesis:** structured (coherent) port can exceed diffuse baseline at fixed Q_i due to recirculation artifact, not gain.
**Null hypothesis:** all power-dependent effects explained by thermal bistability, backscatter, photorefraction.
Thermal thermometer on spiral is not optional — required to close power budget.

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
  P_coherent + P_thermal + P_scatter == P_in
  eta_coherent <= 1.0 // no over-unity
```

---

## 02 — Chip floorplan: 4-device matrix (one die)

### Device D — full loop schematic (not to scale)

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

### The four devices

| Device | Configuration | Purpose |
|---|---|---|
| A | Reference ring — no defect, no valve | Baseline Q_i, backscatter, thermal drift |
| B | Möbius-only — Berry defect, no valve | π shift test — fractional comb offset |
| C | Valve-only — valve, no Möbius | Power-dependent splitting, no topology |
| D | Full loop — ring + defect + valve + spiral + thermometer | Recirculation, echo, coherent budget |

### Die notes

All rings: R = 80 µm, straights 400 µm, cavity length 1302.7 µm, **FSR ≈ 0.84 nm (≈ 104.6 GHz) at 1550 nm** (n_g ≈ 2.2). Coupler gap: Devices A/B 500 nm, Devices C/D 300 nm (valve arm).

Spiral (Device D, primary): 1.2 µm wide, **length ≈ 27.3 cm** for τ ≈ 2.00 ns, 60 µm minimum bend radius, ≈ 2.7 mm² footprint at 10 µm turn pitch. Insertion ≈ 4.1 dB at the < 0.15 dB/cm propagation target — this loss is part of the Device D loop budget and must appear in the Step 5 power closure. Compact variant: 12 mm spiral, τ ≈ 88 ps, negligible added loss, but Step 6 then requires ≤ 20 ps excitation and ≥ 40 GHz detection (see Step 6 note).

Thermometer: Ti/Pt 100 Ω, placed 10 µm from the waveguide along the spiral's outer turn, isolated with 1 µm SiO₂.

---

## 03 — TFLN stack spec

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
| Electrode | For z-cut: GSG, gap 4 µm (optional) |

Process: DUV 248 nm, EBL for couplers, Ar-milling etch. Anneal 300 °C 2 h O₂ after etch to reduce -OH. Do not pole Device A/C.

---

## 04 — Valve options (Lumerical-ready)

| Parameter | Opt 1: Kerr intensity switch | Opt 2: Coherence-discriminating parametric |
|---|---|---|
| Mechanism | Self-phase modulation in MZI arm, n₂ = 1.8e-19 m²/W | OPO threshold coupling, PPLN, preserves coherence at structured port |
| Coupler gap | 300 nm | 400 nm (idler arm) |
| Length | 25 µm (MZI arm ΔL = 25 µm) | PPLN 3 mm, poling ~18.5 µm for 1550 nm |
| Switching power | < 10 mW circulating (≈ 0.8 mW on-chip) | OPO threshold ~5 mW, signal/idler split |
| Expected γ tuning | 0 → π over 8 mW | Coherence selective: γ_coh ≠ γ_th |
| Lumerical model | MODE: n_eff = 1.95; MODE + INTERCONNECT: n₂ via χ³ | FEEM + χ², d₃₃ = 27 pm/V, phase-matched TE |

**Recommended:** fabricate both on same die. Opt 1 first light, Opt 2 second mask.
**Tuning:** heater on MZI arm 100 Ω, 0–20 mW, for bias calibration at low power.

---

## 05 — Measurement setup & equipment list

Chain: TSL-570 → EDFA + VOA → FPC + ISO → 99/1 tap (monitor) → DUT stage → PD + OSA / SNSPD g². All fiber PM1550 except post-chip free-space to PD. Include polarization extinction > 25 dB check.

| Item | Spec |
|---|---|
| Tunable laser | Santec TSL-570, 1480–1640 nm, 100 kHz linewidth |
| EDFA + VOA | Power sweep 0.1–100 mW, monitor with 1% tap |
| Polarization | Fiber PC + in-line polarizer, PER meter |
| Stage | Cryostat or Peltier stage ±10 mK, vacuum option |
| Detection | High-speed PD 12 GHz, OSA AQ6370D, 99/1 cal tap |
| Coherence | Self-heterodyne linewidth (50 km delay) + SNSPDs for g²(τ) |
| Thermal | Lock-in + Ti/Pt 4-wire, 10 nV resolution |
| Aux | RF synth for heater modulation, 10 kHz / 100 Hz separation |

---

## 06 — Measurement procedure, step by step

**Step 1 — Cold-cavity characterization.**
Low power < 100 µW. Extract Q_i, Q_c, backscatter splitting via bi-directional sweep. Fit doublet if present. Record reference ring A first.
✓ Q_i > 2M, splitting < 10 MHz for A.

**Step 2 — Power-dependent transmission sweep.**
0.1 → 100 mW on-chip, up/down. Use 10 kHz vs 100 Hz heater modulation to separate thermal (slow) vs valve (fast). Look for saturating splitting.
✓ Saturation not monotonic thermal shift.

**Step 3 — Differential comb offset (Möbius vs reference).**
Sweep 10 resonances (FSR ≈ 0.84 nm; 10 resonances span ≈ 8.4 nm). Measure resonance frequency of Device B vs A. Expect fractional offset Δ/FSR = 0.5 ± 0.05 from Berry π (0.5 FSR ≈ 0.42 nm at the corrected FSR).
✓ Persistent across 10 FSRs, power-independent at low P.

**Step 4 — MZI fringe inversion test.**
Monitor structured vs diffuse ports while tuning valve bias (Kerr power or heater). Look for bright → dark inversion, γ 0 → π tunable.
✓ Extinction > 10 dB inversion, reproducible.

**Step 5 — Thermal vs coherent power budget.**
Close loop: measure P_in, P_coherent (structured), P_thermal (Pt sensor + cal), P_scattered. For Device D, book the spiral insertion (≈ 4.1 dB at target loss) as a measured line item, not an allowance. Compute R = (P_meas − P_baseline)/P_in. Must have P_total ≤ P_in always.
✓ R > 0 reproducibly, η_coh ≤ 1, thermal channel correlated.

**Step 6 — Time-domain ringdown / echo at τ_delay.**
Pulse excitation (EOM, 100 ps). Look for delayed echo at the spiral delay ~2 ns (± 0.3 ns) in Device D only, not in A–C.
✓ Echo amplitude tracks valve state, absent in A–C.

*Design note:* at Q_i = 2×10⁶ the cavity photon lifetime is ≈ 1.65 ns — the same order as the 2 ns spiral delay. The echo therefore rides on the ringdown tail; discrimination improves if the pulse test is run at reduced loaded Q (stronger coupling) or with the valve state toggled as the control. *Compact-variant note:* with the 12 mm spiral (τ ≈ 88 ps), the 100 ps pulse and 12 GHz PD cannot resolve the echo — that variant requires ≤ 20 ps pulses and ≥ 40 GHz detection, or a phase-domain group-delay measurement instead.

**Step 7 — g² and linewidth comparison, structured vs diffuse.**
Self-heterodyne linewidth: structured < diffuse expected. g²(τ): structured shows higher coherence, diffuse thermal-like.
✓ Δν_struct < Δν_diffuse, g²(0) difference > 2σ.

---

## 07 — Expected signatures & pass/fail criteria

| Signature | Detail | Criterion |
|---|---|---|
| Resonance splitting that saturates | Not monotonic thermal; saturates at ~5–10 mW, seen in C/D not A. Measure splitting vs P_circ. | PASS if saturation knee & hysteresis minimal |
| Fractional comb offset 0.5 ± 0.05 | Across 10 resonances (FSR ≈ 0.84 nm), B vs A. Low power only. | PASS if mean 0.5 ± 0.05, std < 0.03 |
| MZI bright-dark inversion, γ 0 → π | Structured vs diffuse port power swap with valve tuning. | PASS if extinction > 10 dB both ports |
| Coherent budget R > 0 reproducibly | R = (P_meas − P_baseline)/P_in > 0 for same Q_i, 3 runs, P_total ≤ P_in always. | PASS if R > 0.02, 3/3 runs, η ≤ 1 |
| Delayed echo at τ_delay | Pulse response: echo ~2 ns in D only, amplitude tracks valve. | PASS if SNR > 6 dB, absent in A/B/C |
| Linewidth structured < diffuse | Self-heterodyne: Δν_struct 0.5–0.8× Δν_diffuse. g² coherent higher. | PASS if ratio < 0.85, p < 0.05 |

---

## 08 — Confounder checklist

| Confounder | Control | Rejection rule |
|---|---|---|
| Fiber-chip coupling drift | Monitored 99/1 tap continuously, log coupling before/after each sweep. Active alignment piezo. | Reject runs > 0.5 dB drift |
| Photorefraction | MgO-doped LN, anneal 300 °C, keep < 5 mW low-power baseline, test both sweep directions. | Check A vs time, < 2% transmission change/hr |
| Thermal crosstalk | Calibrate thermometer vs stage T. Modulate at 10 kHz (valve) vs 100 Hz (thermal) to separate. | Thermal lag ~10–100 ms, valve < 1 µs |
| Backscattering / mode splitting | Reference ring A control: measure intrinsic doublet. Compare B/C/D extra splitting. | Baseline splitting documented, subtract |
| Polarization mixing | TE-only via polarizer, measure PER. Z-cut needs pol control; x-cut verify. | PER > 25 dB, no TM resonances |
| EDFA ASE / pump leakage | Filter ASE with BPF, measure OSA background. VOA after EDFA. | ASE < −40 dBm in band |

---

## Critical compliance note

Total output power never exceeds input. Coherent extraction efficiency ≤ 1. Recycling is recirculation artifact, not gain. P_coh + P_th + P_scatter = P_in within cal error ±3%.

*This test plan is a conceptual design study. All signatures must be evaluated against the null hypothesis (thermal / backscatter only). No claim of over-unity, free energy, or Second Law violation. Thermal channel measurement is mandatory. Data to be archived with power budget closure table for every run.*

**Davis Lab • TFLN Platform**
