# SPARC Pricing — Indicative Triage Model

**What this is:** A public-data triage tool that produces an **indicative
premium range** for a startup's insurance LOB, every number cited to a public
Indian source.

**What this is NOT:** A bindable quote. India operates under IRDAI's
File-and-Use regime — actual filed rates are not publicly browsable.
This model approximates the market using disclosures, statutes, and
public carrier brochures.

---

## Files

| File | Purpose |
|---|---|
| `parameters.yaml` | **Single source of truth.** Every rate, factor, loading, discount lives here as a structured object with `value` + `source` + `confidence`. |
| `model.py` | The `quote()` function and `Quote` dataclass. Loads parameters at runtime — no restart needed after an edit. |
| `rules.py` | Decline + refer rules. Each cites an Indian regulator/carrier document. |
| `params_cli.py` | CLI: `list`, `edit`, `validate`, `diff`, `export-deck`. |
| `params.py` | Shim so `python -m pricing.params <cmd>` works. |
| `sources.md` | Indian bibliography (IRDAI, IIB, MCA, MoSPI, CERT-In, GIC Re, NCRB, GST, carrier brochures). |
| `ceo_deck.md` | Auto-generated parameter summary for board presentation. Run `python -m pricing.params export-deck`. |
| `audit_log.csv` | Append-only log of every CLI edit: `timestamp,user,path,old,new,reason`. |
| `sources/raw/` | Drop downloaded PDFs here (IIB reports, broker outlooks, internal data). |

---

## Quick start

```bash
# Show every parameter (filtered by LOB)
python -m pricing.params list --lob DO

# Validate schema (every leaf has source + confidence; no orphans)
python -m pricing.params validate

# Edit a rate (audit log required)
python -m pricing.params edit base_rate_per_crore.DO.seriesA 50000 \
    --reason "Tata AIG FY25 brochure update, page 5"

# Show what moved since the last commit
python -m pricing.params diff HEAD~1

# Generate the board-pack Markdown table
python -m pricing.params export-deck
```

```python
# In Python
from pricing.model import quote

q = quote(
    revenue_current_inr=8_00_00_000,
    revenue_projected_inr=15_00_00_000,
    nic_code="6201",                       # NIC 2008, Computer programming
    stage="seriesA",
    state="Karnataka",
    headcount=42,
    years_since_incorporation=3.1,
    cin="U62012KA2022PTC098765",
    dpiit_recognised=True,
    line_of_business="DO",                 # D&O
    sum_insured_inr=5_00_00_000,           # ₹5 Cr
    deductible_inr=1_00_000,
    prior_claims=[],
    underwriter_loadings_discounts={
        "independent_board_majority": 1,   # activate (uses catalog default)
        "audited_financials_big4": 1,
        "dpiit_recognised": 1,
    },
)
print(f"{q.premium_in_lakhs}   conf={q.data_quality_score}")
print(q.disclaimer)
for entry in q.factor_trace:
    print(f"  {entry.step:55} {entry.value:>12}  {entry.source_citation} ({entry.confidence})")
```

---

## How to defend a number to the MD/CEO

Every value in `parameters.yaml` carries:
- A **source citation** (Indian regulator, statute, or carrier brochure).
- A **URL** that resolves to an Indian domain (`.gov.in`, `irdai.gov.in`, named insurer `.com`).
- An **access date**.
- A **confidence** rating (`high` | `medium` | `low`).
- Sometimes **notes** explaining the calibration.

When the CEO asks *"where did this rate come from?"* you can answer in one
sentence by reading the `source.citation` field. When they ask *"can we
move it?"*, edit via the CLI — the change goes into `audit_log.csv`
immutably (committed to git on each edit).

When a value is genuinely a guess (e.g. `stage_factor` has no Indian
public source), it is flagged `PLACEHOLDER` and visible in:
- The `placeholders_used` list on every `Quote`
- The `data_quality_score` (penalised)
- The `disclaimer` (counts placeholders)
- The CEO deck export (visible ⚠ marker)

**Never invent a number. Never import a US benchmark. Never produce a point estimate.**

---

## Adding a new Indian source

1. Drop the PDF in `pricing/sources/raw/<source_name>.pdf` (or just note the URL).
2. Add a numbered entry under the relevant letter section in `sources.md`.
3. Edit the relevant `source.citation` + `source.url` + `source.accessed` in `parameters.yaml`.
4. `python -m pricing.params validate`.
5. `python -m pricing.params edit <path> <new_value> --reason "calibrated to <source>"`.

---

## Output shape

`Quote` is a dataclass — see `model.py:Quote`. Key fields:

```
decision                 indicative_quote | refer | decline
premium_low_inr          float (₹)
premium_high_inr         float (₹)
premium_mid_inr          float (₹)
premium_in_lakhs         "₹4.13 L — ₹7.66 L"
premium_in_crores        "₹0.041 Cr — ₹0.077 Cr"
premium_to_revenue_bps   float (basis points)
factor_trace             list[FactorTraceEntry] — every step, with citation
placeholders_used        list[str]
data_quality_score       0.0–1.0
sources_cited            list[SourceCitation] — [S1], [S2] …
gst_amount_inr           float
stamp_duty_inr           float
gross_premium_inr        float (pre-tax)
technical_premium_inr    float (pre-loadings)
loaded_premium_inr       float (pre-gross-up)
active_loadings          list[dict] — what the broker toggled and effect
net_loading_pct          float (signed, clamped ±25%)
disclaimer               str
refer_reasons            list[str]
decline_reasons          list[str]
inputs_echo              dict — the full input set
```

---

## Tests

```bash
python -m pytest tests/test_pricing.py -v
```

All eight requirements from the spec are covered. The model is calibrated
to the BSU regulated rate (test 1) — if a future YAML edit drifts the
Property model away from the IRDAI floor, that test fails.

---

## Disclaimer (lives also on every Quote)

> Indicative only under IRDAI File-and-Use detariffed regime. Not a
> bindable quote. Final premium subject to underwriter review and
> reinsurance treaty terms.
