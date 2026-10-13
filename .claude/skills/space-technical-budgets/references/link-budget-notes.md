# Link budget notes

Standard radio-engineering relations (general engineering knowledge; textbook level), implemented in
`scripts/link_budget.py`.

| Quantity | Relation |
|---|---|
| Wavelength | λ = c / f, c = 299 792 458 m/s (exact, SI) |
| Free-space path loss | FSPL = 20·log10(4πd/λ) dB |
| EIRP | P_tx(dBW) + G_tx(dBi) − L_tx(dB) |
| Carrier-to-noise density | C/N0 = EIRP − FSPL − ΣL_other + G/T − 10·log10(k), k = 1.380649×10⁻²³ J/K (exact, SI) → −228.6 dBW/(K·Hz) |
| Energy per bit to noise density | Eb/N0 = C/N0 − 10·log10(R_b) |
| Eb/N0 margin | Eb/N0 − required Eb/N0 (for the chosen modulation/coding and bit-error rate) − implementation loss |
| Received power | P_rx(dBm) = EIRP + 30 − FSPL − ΣL_other + G_rx − L_rx; margin = P_rx − receiver sensitivity |

Known answer: f = 2.4 GHz, d = 1 km → λ = 0.124914 m, FSPL = 100.05 dB. Each doubling of distance adds
6.02 dB; ×10 adds 20 dB.

## Unit rules enforced
- Powers: `dBW`, `dBm`, `W`, `mW` (EIRP and sensitivity: `dBW`/`dBm`). Gains: `dBi`. Losses and
  margins: `dB`, non-negative. G/T: `dB/K`. Data rate: `bps`…`Gbps` or `dBHz`. Frequency: `Hz`…`GHz`.
  Distance: `m`, `km`, `AU`. Anything else → exit 2.

## Limits
- Line-of-sight free space only. Surface operations on a small body add horizon blockage (a 250 m
  radius body has a very short horizon for a rover antenna a few tens of cm high), multipath off
  regolith and terrain shadowing; add explicit allowances and, where the link matters, analyse or test.
- The required Eb/N0 comes from the modem/coding specification, not from this skill.
- Required link margin is a programme policy value; the example files use synthetic numbers.
