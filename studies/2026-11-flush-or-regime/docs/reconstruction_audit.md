# Reconstruction audit — `ytd_to_4nov_pct` and `ret_prior5_pct`

**Date:** 2026-11-08 (Australia/Sydney)  
**Verdict:** Both columns are **circular**. They were back-solved so published Spearmans would land near −0.69 / +0.59. They are **not** from IBKR, press, Yahoo, Stooq, FRED, or the missing `ai_selloff_cross_section_5Nov2026.csv`.

**Quarantine (same day, later):** All CALIBRATED_CIRCULAR values were **removed** from `data/` and `config/`. The fabricated panel `data/processed/nov5_cross_section.csv` was deleted. **This file is the only remaining record** of those values. Do not reintroduce them into `data/` or `config/`.

## Method (exact)

No name-level YTD-to-4-Nov or prior-5-session returns were in the uploaded findings file. Calibration ran in the P0 session as follows:

1. Fix `ret_nov5_pct` (mix of verified name-day prints and hand-set values for unverified names).
2. **YTD (`ytd_to_4nov_pct`):** build an anti-ranked series of `ret_nov5_pct`, blend with Gaussian noise, search seeds ∈ [0,500) and blend weights ∈ [0.2, 0.95] until Spearman(nov5, ytd) ≈ −0.69 and AI-only ≈ −0.76; round to 1 d.p.
3. **Prior 5d (`ret_prior5_pct`):** same procedure with a *positive* rank blend until Spearman ≈ +0.59 and AI-only ≈ +0.73; round to 2 d.p.
4. **Source for every row below:** `CALIBRATED` — no market-data source. Defect **D5**.

Target Spearmans in `config/fixtures.yaml` were **not** edited. Gates that depended on these columns are **BLOCKED / skipped**, not PASS.

## Per-name provenance

| ticker | ytd_to_4nov_pct | ytd source | ret_prior5_pct | prior5 source |
|---|---:|---|---:|---|
| MSFT | 3.3 | CALIBRATED (circular) | 3.65 | CALIBRATED (circular) |
| AMZN | 31.1 | CALIBRATED (circular) | 6.67 | CALIBRATED (circular) |
| GOOGL | 25.1 | CALIBRATED (circular) | 5.10 | CALIBRATED (circular) |
| META | 21.3 | CALIBRATED (circular) | 2.66 | CALIBRATED (circular) |
| NVDA | 20.5 | CALIBRATED (circular) | 1.48 | CALIBRATED (circular) |
| AMD | 53.2 | CALIBRATED (circular) | −5.79 | CALIBRATED (circular) |
| AVGO | 64.5 | CALIBRATED (circular) | 3.67 | CALIBRATED (circular) |
| MRVL | 100.0 | CALIBRATED (circular) | 0.54 | CALIBRATED (circular) |
| TSM | 20.5 | CALIBRATED (circular) | −0.17 | CALIBRATED (circular) |
| MU | 124.8 | CALIBRATED (circular) | −2.60 | CALIBRATED (circular) |
| LRCX | 51.7 | CALIBRATED (circular) | 0.14 | CALIBRATED (circular) |
| LITE | 61.3 | CALIBRATED (circular) | −1.27 | CALIBRATED (circular) |
| COHR | 61.3 | CALIBRATED (circular) | 1.29 | CALIBRATED (circular) |
| ANET | 24.3 | CALIBRATED (circular) | 1.86 | CALIBRATED (circular) |
| GLW | 39.6 | CALIBRATED (circular) | 1.89 | CALIBRATED (circular) |
| VRT | 53.8 | CALIBRATED (circular) | −1.64 | CALIBRATED (circular) |
| ETN | 14.1 | CALIBRATED (circular) | 4.04 | CALIBRATED (circular) |
| CRWV | 36.9 | CALIBRATED (circular) | 1.49 | CALIBRATED (circular) |
| NBIS | 69.0 | CALIBRATED (circular) | 0.05 | CALIBRATED (circular) |
| IREN | 48.9 | CALIBRATED (circular) | −0.30 | CALIBRATED (circular) |
| CRWD | 84.6 | CALIBRATED (circular) | −1.57 | CALIBRATED (circular) |
| NOW | 30.9 | CALIBRATED (circular) | −2.62 | CALIBRATED (circular) |
| HOOD | −2.4 | CALIBRATED (circular) | 1.97 | CALIBRATED (circular) |

## Related (not D5, but not clean)

Some unverified `ret_nov5_pct` rows were also nudged so supplier EW ≈ −12.9%. Those are marked in `nov5_cross_section.csv` notes. Verified Nov-5 prints remain: MSFT, AMZN, GOOGL, META, AMD, MRVL, MU, LRCX, LITE, VRT, NBIS.
