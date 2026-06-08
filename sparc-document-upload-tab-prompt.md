# Claude Code Prompt — SPARC Document Upload Feature
## "Financial Documents Tab"

Paste this entire prompt into Claude Code to build the document upload feature.

---

## CONTEXT: READ FIRST

Same as before:
- Backend: `startup_shield_web/server.py`
- Frontend: `startup_shield_web/app.js` + `styles.css`
- Risk Engine: `risk_engine.py`
- Routing: `vercel.json`

This feature is **independent** of the auto-enrichment path. It lives as a separate tab on the home screen.

---

## FEATURE OVERVIEW

**Three tabs on the SPARC home screen:**

1. **Risk Assessment** (existing) — user fills 25-field form → risk scores → bundle recommendation
2. **Company Lookup** (auto-enrichment, optional) — user types name/CIN → 3-question form → risk scores
3. **Upload Documents** (NEW) — user uploads P&L/Balance Sheet/ITR/GSTR PDFs → extracts numbers → auto-fills risk profile → risk scores

Each tab is independent. User can start on any tab.

---

## DELIVERABLES

---

## 1. PRD — Product Requirements Document

Write `docs/PRD_document_upload.md`:

```markdown
# PRD: SPARC Document Upload Feature

## Problem Statement

Users currently must manually type or estimate financial figures (revenue, assets, profit, payroll, etc.) when using SPARC. For companies with recent audited financials, this is wasteful — the data already exists in PDFs. The upload feature extracts these numbers automatically, reducing form-filling friction and improving data accuracy.

## Goals

- [ ] Reduce time to risk assessment from ~10 minutes to ~2 minutes for users with documents
- [ ] Achieve ≥95% extraction accuracy for standard P&L and Balance Sheet line items
- [ ] Provide confidence scoring per extracted field so users know what's verified vs estimated
- [ ] Enable cross-document validation (ITR vs GSTR match, Balance Sheet balances)
- [ ] Support all 4 Tier 1 document types: P&L, Balance Sheet, ITR, GSTR

## Non-Goals

- [ ] OCR for scanned images — only text-based PDFs
- [ ] Handling of non-Indian accounting formats
- [ ] Real-time document processing (async jobs okay)
- [ ] Integrating with cloud document storage (Google Drive, etc.)
- [ ] Modifying existing Risk Assessment or Company Lookup tabs

## User Journey

**As-is:** User lands on SPARC → fills 25-field form → waits for risk scores

**To-be:** User lands on SPARC → sees 3 tabs → clicks "Upload Documents" → drags PDFs → fields auto-fill → 3 confirmation questions → risk scores

## Feature Requirements

### FR-1: Multi-Tab Home Screen

- Home screen displays 3 tabs:
  - Risk Assessment (existing, default active)
  - Company Lookup (optional, if enabled)
  - Upload Documents (new)
- Clicking a tab switches content without page reload
- Tab state persists during session (not across sessions)

### FR-2: Document Upload Interface

- Drag-and-drop zone for multiple files
- Alternatively: file browser button
- Supported file types: PDF only
- Max 25 MB per file, 100 MB total
- Multiple files can be uploaded in one batch
- Show progress bar per file during upload
- Display file list with status (uploading, processing, success, error)

### FR-3: Document Type Detection

System automatically detects document type from filename or content:
- P&L Statement (keywords: "profit", "loss", "p&l", "income", "statement")
- Balance Sheet (keywords: "balance", "sheet", "assets", "liabilities")
- Income Tax Return (keywords: "itr", "income tax", "schedule ar", "26as")
- GST Return (keywords: "gstr", "gst", "return")
- PF/Payroll document (keywords: "pf", "ecr", "challan", "payroll")

### FR-4: Financial Field Extraction

Extract these fields from PDFs:
- From P&L: Revenue, COGS, Gross Profit, EBITDA, Net Profit, Employee Cost
- From Balance Sheet: Total Assets, Fixed Assets, Current Assets, Inventory, Receivables, Total Liabilities, Equity, Debt
- From ITR: Declared Revenue, Profit Before Tax, Advance Tax Paid, Related Party Transactions
- From GSTR-1: B2B Turnover, B2C Turnover, Export Turnover, HSN/SAC Summary
- From GSTR-3B: Total GST Liability, Tax Paid
- From PF ECR: Employee Count (inferred from contribution), Payroll (inferred from contribution)

Each field tagged with:
- `confidence`: "extracted" | "calculated" | "estimated"
- `source`: which document + which line item
- `value`: the number

### FR-5: Field Confidence Scoring

- "extracted": Regex matched the exact number from the document
- "calculated": Derived from other fields (e.g., Gross Profit = Revenue - COGS)
- "estimated": Inferred heuristically (e.g., employee count from payroll)
- "not_found": Field not present in uploaded documents

Fields with "calculated" or "estimated" confidence must be flagged for user review.

### FR-6: Cross-Document Consistency Checks

Run automated checks if user uploads multiple documents:
- ITR Revenue vs GSTR Revenue: should match within 5%
- P&L Revenue vs ITR Revenue: should match within 3%
- Balance Sheet balances: Assets = Liabilities + Equity (within ±₹5 Cr tolerance)
- B2B % consistency: if both GSTR and P&L provide B2B signals, should align

Display results as:
- ✓ Check passed
- ⚠ Warning — values differ but within tolerance, show both, ask user to confirm
- ✗ Check failed — significant mismatch, ask user which to trust

### FR-7: Extracted Profile Pre-Fill

After extraction and validation, system displays a "Extracted Profile" summary showing:
- All extracted financial numbers with confidence badges
- Consistency check results
- Any ambiguous or conflicting values requiring user confirmation
- A "Looks right?" button to proceed or "Edit values" to override

Once user confirms, system pre-fills these extracted values into the risk profile:
- annual_revenue_cr
- gross_profit_cr
- total_insurable_asset_cr
- fixed_assets_cr
- inventory_cr
- receivables_cr
- payroll_cr
- employee_count
- b2b_pct
- And all others

### FR-8: Remaining 3 Questions

After extraction, system asks 3 confirmation questions:
1. Data sensitivity (Low / Medium / High)
2. B2B % (if not extracted from GSTR)
3. Gig workforce % (if not in documents)

These feed directly into risk scoring.

### FR-9: Error Handling & Fallbacks

- Scanned images (no text extractable): Show message "This appears to be a scanned image. Please upload a text-based PDF."
- Corrupted PDFs: Skip file, show error, continue with others
- No documents uploaded: Show empty state
- Extraction partially successful: Show what was found, let user confirm/edit
- All extractions failed: Show fallback to manual form

### FR-10: Enrichment Confidence & Premium Banding

- Profiles built from document upload have `enrichment_source: "document_upload"` and `enrichment_confidence: "verified"`
- Risk assessment uses these verified fields directly (no stage/team proxies)
- Premium output shows tighter confidence band
- UI displays: "Premium calculated from your verified financial documents"

## Acceptance Criteria

- [ ] Home screen displays 3 tabs; clicking "Upload Documents" switches to upload panel
- [ ] User can drag 3 PDFs onto dropzone; all upload successfully
- [ ] P&L extraction finds Revenue, COGS, Gross Profit within ±5% of manual read
- [ ] Balance Sheet extraction finds Assets, Liabilities, Equity within ±5% of manual read
- [ ] ITR extraction finds Declared Revenue within ±3% of official figure
- [ ] GSTR extraction finds B2B/B2C split correctly
- [ ] Consistency checks flag ITR ≠ GSTR mismatches as warnings
- [ ] Extracted profile summary displays all fields with confidence badges
- [ ] User can edit any extracted value before proceeding
- [ ] After confirmation, risk assessment runs with extracted data
- [ ] Premium confidence band shows "verified" (not "estimated")
- [ ] Scanned PDF handled gracefully with fallback message

## Out of Scope

- OCR for scanned images
- Batch document processing
- Document storage / retention
- Integration with external cloud storage
- Modification of Risk Assessment or Company Lookup tabs
- Support for non-Indian financial formats
- Historical document comparison (multi-year analysis)
```

---

## 2. TRD — Technical Requirements Document

Write `docs/TRD_document_upload.md`:

```markdown
# TRD: SPARC Document Upload Feature

## Architecture Overview

```
Frontend (app.js)
  ↓ [Upload Documents Tab]
    ├─ Drag-drop zone
    ├─ File list + progress
    └─ POST /api/upload (multipart/form-data)
        ↓
Backend (server.py → enrichment/ package)
  ├─ api/upload.py [new route]
  │   ├─ Extract text from PDF (subprocess → pdftotext)
  │   ├─ Detect document type (filename heuristics)
  │   └─ Route to type-specific extractor
  ├─ enrichment/document_extractor.py [new]
  │   ├─ extract_pl_fields(pdf_text) → {revenue, cogs, profit}
  │   ├─ extract_bs_fields(pdf_text) → {assets, liabilities, equity}
  │   ├─ extract_itr_fields(pdf_text) → {revenue, profit}
  │   ├─ extract_gstr_fields(pdf_text) → {b2b%, b2c%}
  │   └─ extract_pf_fields(pdf_text) → {payroll, employees}
  ├─ enrichment/consistency_checker.py [new]
  │   ├─ check_revenue_match(itr, gstr, p&l)
  │   ├─ check_balance_sheet_balance(assets, liabilities, equity)
  │   └─ run_all_checks(extracts)
  └─ enrichment/confidence.py [new]
      └─ tag_field(value, source, method) → FieldConfidence

        ↓
        Returns JSON response to frontend
        
Frontend (app.js)
  ↓ [Extraction Summary Panel]
    ├─ Display all extracted fields
    ├─ Show consistency check results
    ├─ Flag ambiguous values
    └─ Button: "Confirm & Continue" or "Edit Values"
        ↓
        Merge extracted profile + 3-question answers
        ↓
        POST /api/analyze [existing endpoint]
        ↓
        Risk Assessment results
```

## New Files

```
enrichment/
  __init__.py
  document_extractor.py          # PDF text extraction + field parsing
  consistency_checker.py         # Cross-document validation
  confidence.py                  # Field confidence scoring
  cache.py                       # TTL cache for extraction results (optional)

api/
  upload.py                      # POST /api/upload endpoint [new]

docs/
  PRD_document_upload.md         # This PRD
  TRD_document_upload.md         # This TRD
  SCHEMA_document_upload.md      # Data structures
  UX_document_upload.md          # UI/UX wireframes
  IMPLEMENTATION_PLAN_document_upload.md
  APPFLOW_document_upload.md
```

## Modified Files

- `startup_shield_web/server.py`: Add upload route handler
- `startup_shield_web/app.js`: Add upload tab, upload UI, extraction summary panel
- `startup_shield_web/styles.css`: Add upload panel styles
- `vercel.json`: Route `/api/upload` to `api/upload.py`
- `risk_engine.py`: Add `enrichment_source` and `enrichment_confidence` to `StartupInput`
- `quote_prefill.py`: Check for verified fields before running proxies

## API Contracts

### POST /api/upload

**Request:**
```
Content-Type: multipart/form-data
Body:
  files[]       : [file1.pdf, file2.pdf, ...]
  company_id    : (optional) "U74999KA2010PLC096789"
```

**Response:**
```json
{
  "status": "success" | "partial" | "error",
  "documents_processed": 3,
  "documents": [
    {
      "filename": "profit_loss_fy2024.pdf",
      "document_type": "p&l",
      "status": "success" | "partial" | "error",
      "extraction_count": 6,
      "errors": []
    }
  ],
  "extraction_summary": {
    "annual_revenue_cr": {
      "value": 3288.5,
      "confidence": "extracted",
      "source": "P&L Line 1",
      "document_source": "profit_loss_fy2024.pdf"
    },
    "gross_profit_cr": {
      "value": 821.3,
      "confidence": "calculated",
      "source": "Revenue - COGS",
      "document_source": "profit_loss_fy2024.pdf"
    },
    "total_insurable_asset_cr": {
      "value": 4200.0,
      "confidence": "extracted",
      "source": "Balance Sheet - Total Assets",
      "document_source": "balance_sheet_fy2024.pdf"
    },
    ...
  },
  "consistency_checks": [
    {
      "check": "ITR Revenue vs GSTR Revenue",
      "values": {"itr": 3288.5, "gstr": 3245.2},
      "variance_pct": 1.3,
      "status": "pass",
      "message": "Within 5% tolerance"
    },
    {
      "check": "Balance Sheet Balances",
      "values": {"assets": 4200, "liabilities_plus_equity": 4198.5},
      "variance_cr": 1.5,
      "status": "pass",
      "message": "Within ±5 Cr tolerance"
    }
  ],
  "extraction_issues": [
    {
      "document": "balance_sheet_fy2024.pdf",
      "field": "total_liabilities",
      "confidence": "ambiguous",
      "issue": "Found two possible values: ₹2000 Cr and ₹2100 Cr",
      "requires_user_confirmation": true,
      "options": [
        {"value": 2000, "location": "Section 1, line 5"},
        {"value": 2100, "location": "Section 2, reconciliation"}
      ]
    }
  ],
  "enriched_profile": {
    "annual_revenue_cr": 3288.5,
    "annual_revenue_cr_verified": 3288.5,
    "gross_profit_cr": 821.3,
    "gross_profit_cr_verified": 821.3,
    "total_insurable_asset_cr": 4200.0,
    "total_insurable_asset_cr_verified": 4200.0,
    ...
    "enrichment_source": "document_upload",
    "enrichment_confidence": "verified"
  },
  "next_steps": [
    "confirm_ambiguous_fields",
    "answer_3_questions",
    "run_analysis"
  ]
}
```

## PDF Text Extraction Strategy

**Constraint:** Stdlib only. No `pdfplumber`, no `PyPDF2`.

**Approach:**
1. Use `subprocess` to call `pdftotext` (command-line tool, commonly available)
2. If `pdftotext` not available or fails, return error: "Unable to extract text. Ensure PDF is text-based, not a scanned image."
3. Extraction returns raw text; parsing done with regex + string matching

**Subprocess call:**
```python
import subprocess

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        result = subprocess.run(
            ["pdftotext", "-", pdf_path],  # output to stdout
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return ""
    except FileNotFoundError:
        raise Exception("pdftotext not found. Install: brew install poppler (Mac) or apt-get install poppler-utils (Linux)")
    except subprocess.TimeoutExpired:
        raise Exception(f"PDF extraction timed out (file too large?)")
    except Exception as e:
        raise Exception(f"PDF extraction failed: {str(e)}")
```

## Field Extraction via Regex

Each document type has type-specific regex patterns. Examples:

**P&L Revenue:**
```python
patterns = [
    r"(?:Sales|Revenue|Turnover|Income from Operations)[:\s]+[₹$]?\s*([\d,]+\.?\d*)\s*(?:Cr|crore)",
    r"^Total Revenue[:\s]+[₹$]?\s*([\d,]+\.?\d*)\s*(?:Cr|crore)",
]
```

**Balance Sheet Total Assets:**
```python
patterns = [
    r"(?:Total Assets|Total Current Assets|Current & Non-Current Assets)[:\s]+[₹$]?\s*([\d,]+\.?\d*)\s*(?:Cr|crore)",
    r"^TOTAL ASSETS[:\s]+[₹$]?\s*([\d,]+\.?\d*)\s*(?:Cr|crore)",
]
```

All patterns are case-insensitive and handle currency symbols (₹, $), separators (commas), decimals, and units (Cr, crore, Lac, lakh).

**Confidence levels per extraction method:**
- Regex match with high certainty → "extracted" (confidence: 0.95)
- Regex match but ambiguous (found 2+ values) → "extracted" with flag (confidence: 0.70)
- Calculated from other fields (e.g., GP = Revenue - COGS) → "calculated" (confidence: 0.90)
- Heuristic estimation (e.g., employees from payroll) → "estimated" (confidence: 0.60)
- Field not found → "not_found" (confidence: 0)

## Consistency Checking Logic

### Revenue Match (ITR vs GSTR)
```python
def check_revenue_match(itr_revenue: float, gstr_revenue: float, tolerance_pct: float = 5.0):
    if not itr_revenue or not gstr_revenue:
        return {"status": "not_applicable"}
    
    variance_pct = abs(itr_revenue - gstr_revenue) / max(itr_revenue, gstr_revenue) * 100
    
    if variance_pct <= tolerance_pct:
        return {"status": "pass", "variance_pct": variance_pct}
    else:
        return {"status": "warning", "variance_pct": variance_pct, "msg": f"Variance {variance_pct:.1f}% — verify with company"}
```

### Balance Sheet Balance
```python
def check_balance_sheet_balance(assets: float, liabilities: float, equity: float, tolerance_cr: float = 5.0):
    if not assets or not (liabilities and equity):
        return {"status": "not_applicable"}
    
    calculated_assets = liabilities + equity
    variance = abs(assets - calculated_assets)
    
    if variance <= tolerance_cr:
        return {"status": "pass"}
    else:
        return {"status": "warning", "variance_cr": variance, "msg": f"Variance ₹{variance}Cr"}
```

## Data Structures

### FieldExtraction
```python
@dataclass
class FieldExtraction:
    field_name: str              # "annual_revenue_cr", "total_assets_cr", etc.
    value: float | int | str     # The extracted number or string
    confidence: str              # "extracted" | "calculated" | "estimated" | "not_found"
    source: str                  # "P&L Line 1", "Balance Sheet - Fixed Assets", etc.
    document_source: str         # filename
    regex_pattern: str           # which pattern matched (for debugging)
    alternatives: List[float]    # if multiple interpretations found
```

### DocumentExtraction
```python
@dataclass
class DocumentExtraction:
    filename: str
    document_type: str           # "p&l", "balance_sheet", "itr", "gstr", "pf"
    extraction_status: str       # "success", "partial", "error"
    fields_extracted: Dict[str, FieldExtraction]
    extraction_errors: List[str]
```

### UploadResult
```python
@dataclass
class UploadResult:
    status: str                  # "success", "partial", "error"
    documents_processed: int
    documents: List[DocumentExtraction]
    extraction_summary: Dict[str, FieldExtraction]  # merged across all docs
    consistency_check_results: List[Dict]
    extraction_issues: List[Dict]                    # ambiguous fields, missing data
    enriched_profile: Dict                           # pre-filled StartupInput fields
    enrichment_confidence: str                       # "verified" | "inferred" | "estimated"
    next_steps: List[str]                            # user actions required
```

## Error Handling

| Error | Handling |
|-------|----------|
| File too large (>25MB) | Reject before upload, show message |
| Total >100MB | Reject, show message |
| Non-PDF file | Reject with message "PDF files only" |
| Corrupted PDF | Skip file, show error, continue with others |
| pdftotext not installed | Graceful error: suggest installation or text-based PDF |
| Scanned image (no text) | Status "no_text_extractable", skip field extraction |
| Regex finds 0 matches | Status "not_found", show user |
| Regex finds 2+ matches | Status "ambiguous", show options to user, ask to confirm |
| Consistency check fails | Status "warning", show both values, ask user which to trust |
| All documents fail to extract | Show message, offer fallback to manual form |

## Caching (Optional)

If implementing cache:
- Key: `sha256(filename + file_size + modification_date)`
- TTL: 24 hours
- Storage: `.enrichment_cache/` directory (gitignored)
- Benefit: Re-uploading same file returns cached result instantly
- Trade-off: Added complexity for marginal UX benefit

For MVP, **skip caching**. Just extract fresh every time.

## Rate Limiting & File Validation

```python
MAX_FILE_SIZE_MB = 25
MAX_TOTAL_SIZE_MB = 100
ALLOWED_EXTENSIONS = [".pdf"]
ALLOWED_MIME_TYPES = ["application/pdf"]

def validate_upload(files: List):
    total_size = 0
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise Exception(f"{file.filename} — PDF files only")
        if file.size > MAX_FILE_SIZE_MB * 1_000_000:
            raise Exception(f"{file.filename} — exceeds {MAX_FILE_SIZE_MB}MB limit")
        total_size += file.size
    
    if total_size > MAX_TOTAL_SIZE_MB * 1_000_000:
        raise Exception(f"Total upload {total_size/(1_000_000):.1f}MB exceeds {MAX_TOTAL_SIZE_MB}MB limit")
```

## Testing Strategy

**Unit tests** (`tests/test_document_extraction.py`):
- extract_pl_fields() with sample P&L PDF text
- extract_balance_sheet_fields() with sample BS text
- extract_itr_fields() with sample ITR text
- extract_gstr_fields() with sample GSTR text
- Consistency checks pass/fail cases
- Confidence scoring logic

**Integration tests** (`tests/test_upload_api.py`):
- POST /api/upload with single PDF → returns correct extraction
- POST /api/upload with 3 PDFs → returns merged extraction + consistency checks
- POST /api/upload with ambiguous field → flags for user confirmation
- POST /api/upload with scanned image → returns "no_text_extractable"
- POST /api/upload with corrupted PDF → skips file, processes others

**End-to-end test:**
- User uploads P&L + Balance Sheet
- Risk assessment runs with extracted data
- Premium output shows "verified" confidence
```

---

## 3. BACKEND SCHEMA

Write `docs/SCHEMA_document_upload.md`:

```markdown
# Schema: SPARC Document Upload

## New Data Classes

Add to `risk_engine.py`:

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

@dataclass
class FieldExtraction:
    """Single extracted field from a document."""
    field_name: str              # "annual_revenue_cr", "total_assets_cr"
    value: Any                   # float, int, or str
    confidence: str              # "extracted" | "calculated" | "estimated" | "not_found"
    source: str                  # "P&L Line 1", "Balance Sheet - Total Assets"
    document_source: str         # filename: "P&L_FY2024.pdf"
    regex_pattern: Optional[str] = None
    alternatives: List[float] = field(default_factory=list)  # if ambiguous

@dataclass
class DocumentExtraction:
    """All fields extracted from a single document."""
    filename: str
    document_type: str           # "p&l" | "balance_sheet" | "itr" | "gstr" | "pf"
    extraction_status: str       # "success" | "partial" | "error"
    fields_extracted: Dict[str, FieldExtraction] = field(default_factory=dict)
    extraction_errors: List[str] = field(default_factory=list)
    extracted_at: str = ""       # ISO timestamp

@dataclass
class UploadResult:
    """Complete result of POST /api/upload."""
    status: str                  # "success" | "partial" | "error"
    documents_processed: int
    documents: List[DocumentExtraction] = field(default_factory=list)
    extraction_summary: Dict[str, FieldExtraction] = field(default_factory=dict)  # merged
    consistency_check_results: List[Dict] = field(default_factory=list)
    extraction_issues: List[Dict] = field(default_factory=list)  # ambiguous fields
    enriched_profile: Dict[str, Any] = field(default_factory=dict)  # StartupInput fields
    enrichment_confidence: str = "estimated"
    next_steps: List[str] = field(default_factory=list)
```

## StartupInput Additions (if not already done in auto-enrichment)

```python
@dataclass
class StartupInput:
    # ... existing fields ...
    
    # Enrichment metadata
    enrichment_source: str = "manual"         # "manual" | "document_upload"
    enrichment_confidence: str = "estimated"  # "verified" | "inferred" | "estimated"
    field_confidence: Dict[str, str] = field(default_factory=dict)
    
    # Verified financial fields (from documents)
    annual_revenue_cr_verified: Optional[float] = None
    gross_profit_cr_verified: Optional[float] = None
    total_insurable_asset_cr_verified: Optional[float] = None
    fixed_assets_cr_verified: Optional[float] = None
    inventory_cr_verified: Optional[float] = None
    receivables_cr_verified: Optional[float] = None
    net_worth_cr_verified: Optional[float] = None
    debt_equity_ratio_verified: Optional[float] = None
    payroll_cr_verified: Optional[float] = None
    employee_count_verified: Optional[int] = None
    b2b_pct_verified: Optional[float] = None
```

## Modify compute_risk_scores() in risk_engine.py

```python
def compute_risk_scores(inp: StartupInput) -> dict:
    """
    Use verified fields from document upload if available.
    Fall through to existing proxy logic if not.
    """
    # Use verified values if available
    revenue = inp.annual_revenue_cr_verified or inp.annual_revenue_cr or 0.0
    gross_profit = inp.gross_profit_cr_verified or 0.0
    fixed_assets = inp.total_insurable_asset_cr_verified or 0.0
    debt_equity = inp.debt_equity_ratio_verified
    payroll = inp.payroll_cr_verified or inp.payroll_cr or 0.0
    
    # ... rest of existing scoring logic ...
```
```

---

## 4. UI/UX DESIGN

Write `docs/UX_document_upload.md`:

```markdown
# UX: SPARC Document Upload

## Home Screen Tab Layout

```
┌─────────────────────────────────────────────────────┐
│  SPARC Insurance Risk Assessment                     │
│                                                      │
│  [Risk Assessment] [Company Lookup] [Upload Docs]   │
│                                                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  (Tab content appears below)                         │
│                                                      │
└─────────────────────────────────────────────────────┘
```

Tab styles:
- Active tab: bold text, underline, highlight
- Inactive tab: normal text, hover shows pointer
- Smooth transition between tabs (no page reload)

## Upload Documents Tab — State 0: Initial

```
┌────────────────────────────────────────────────┐
│  Upload Financial Documents                     │
│                                                 │
│  Drag your PDFs here to auto-fill your profile  │
│  (Keeps everything private — only extracting    │
│   numbers locally on your device)               │
│                                                 │
│  ╔════════════════════════════════════════╗   │
│  ║ 📄 Drag PDFs here                       ║   │
│  ║     or                                   ║   │
│  ║    [Browse Files]                        ║   │
│  ║                                          ║   │
│  ║ Supported:                               ║   │
│  ║ • Profit & Loss Statement                ║   │
│  ║ • Balance Sheet                          ║   │
│  ║ • Income Tax Return (ITR)                ║   │
│  ║ • GST Returns (GSTR-1, GSTR-3B)         ║   │
│  ║ • PF ECR Challan (optional)              ║   │
│  ║                                          ║   │
│  ║ Max 100 MB total, 25 MB per file         ║   │
│  ╚════════════════════════════════════════╝   │
│                                                 │
└────────────────────────────────────────────────┘
```

## State 1: Uploading

```
┌────────────────────────────────────────────────┐
│  Processing Your Documents                      │
│                                                 │
│  P&L_FY2024.pdf                                │
│  [████████████░░░░░] 75% — extracting fields  │
│  Status: Reading PDF                           │
│                                                 │
│  BalanceSheet_FY2024.pdf                      │
│  [██████████████████] 100% ✓ Done              │
│  Extracted: Assets, Liabilities, Equity       │
│                                                 │
│  ITR_2024.pdf                                  │
│  [░░░░░░░░░░░░░░░░░░] 0% — queued             │
│                                                 │
│  ⟳ This usually takes 30–60 seconds per file   │
│                                                 │
└────────────────────────────────────────────────┘
```

## State 2: Extraction Summary (The Results Card)

```
┌───────────────────────────────────────────────┐
│ ✅ Extracted from your documents              │
│    Confidence: VERIFIED                        │
│                                                │
│ CONFIRMED FIGURES:                            │
│                                                │
│ Revenue            ₹3,288 Cr   ✓ P&L + ITR   │
│ Gross Profit       ₹821 Cr     ✓ P&L         │
│ Fixed Assets       ₹842 Cr     ✓ Balance Sht │
│ Total Liabilities  ₹2,100 Cr   ✓ Balance Sht │
│ Equity             ₹2,098 Cr   ✓ Calculated │
│ Employee Payroll   ₹285 Cr     ✓ ITR Notes   │
│ B2B %              35%         ✓ GSTR-1      │
│                                                │
│ ⚠️  NEEDS YOUR CONFIRMATION:                  │
│ • Inventory (found 2 values)                   │
│   [Use ₹156 Cr] [Use ₹150 Cr] [Edit: ___]   │
│                                                │
│ ✓ CONSISTENCY CHECKS:                         │
│ • ITR Revenue (₹3,288) vs GSTR (₹3,245)     │
│   Variance: 1.3% ✓ OK                        │
│ • Balance Sheet Balances                      │
│   Assets ₹4,200 = Liabilities+Equity ₹4,198 ✓│
│                                                │
│ [Edit any value] [Looks good, continue →]     │
└───────────────────────────────────────────────┘
```

## State 3: 3-Question Confirmation

```
┌────────────────────────────────────────────┐
│ Just 3 quick questions                      │
│                                             │
│ 1. How sensitive is your customer data?     │
│    ○ Low   ○ Medium   ○ High                │
│                                             │
│ 2. What % of your revenue is B2B?           │
│    (Business to business vs B2C consumer)   │
│    [=======●=============] 35% / 65%       │
│                                             │
│ 3. What % of your workforce is gig?         │
│    (Contractors vs full-time employees)     │
│    [=●====================] 10% / 90%      │
│                                             │
│ [Run Risk Assessment →]                     │
└────────────────────────────────────────────┘
```

## State 4: Fallback — Empty Upload

```
┌────────────────────────────────────────────┐
│ No documents yet                             │
│                                             │
│ Drag PDFs here, or use one of these         │
│ alternatives:                                │
│                                             │
│ [Fill the form manually →]                  │
│ [Use company lookup (faster) →]             │
│                                             │
└────────────────────────────────────────────┘
```

## State 5: Fallback — Scanned Image

```
┌──────────────────────────────────────────────┐
│ ⚠️  Couldn't read this PDF                    │
│                                              │
│ It looks like a scanned image. This feature  │
│ requires text-based PDFs (most online        │
│ PDFs are text-based).                        │
│                                              │
│ Try:                                         │
│ • Download the PDF directly from your bank   │
│   or accounting software                     │
│ • Ensure it's not a photo of a document      │
│ • Try a different fiscal year's filing       │
│                                              │
│ [Try different file] [Use manual form]       │
└──────────────────────────────────────────────┘
```

## CSS Classes to Add

```css
.upload-tab-content              /* Main container for upload tab */
.upload-dropzone                 /* Drag-drop area */
.upload-dropzone.active          /* When file is dragged over */
.upload-file-browser-btn         /* Browse files button */
.upload-file-list                /* Container for uploaded files */
.upload-file-item                /* Single file in list */
.upload-file-item.success        /* File successfully extracted */
.upload-file-item.error          /* File failed to extract */
.upload-progress-bar             /* Progress bar for single file */
.upload-extraction-card          /* Results summary card */
.extraction-field-row            /* Single extracted field + badge */
.extraction-field-value          /* The number value */
.extraction-field-badge          /* Confidence badge: extracted/calculated/estimated */
.extraction-field-badge.extracted    /* Green for extracted */
.extraction-field-badge.calculated   /* Blue for calculated */
.extraction-field-badge.estimated    /* Orange for estimated */
.extraction-issue-row            /* Ambiguous field requiring confirmation */
.extraction-issue-options        /* Radio/select buttons for ambiguous values */
.extraction-check-pass           /* Green checkmark for passed consistency check */
.extraction-check-warning        /* Orange warning for tolerance exceeded */
.upload-fallback-panel           /* Fallback empty/error state */
.upload-3q-panel                 /* 3-question confirmation panel */
.q-option-input                  /* Radio/select for each question */
.q-slider                        /* Range slider for % questions */
.q-slider-value                  /* Display current % value */
```

## CSS Design Principles

- Match existing SPARC color palette (use `var(--red)`, `var(--ink)`, `var(--border)`, etc.)
- Dropzone: dashed border when active, solid when inactive
- Progress bars: animated fill left-to-right
- Confidence badges: small colored pills (green=verified, orange=estimated)
- Results card: large white panel with padding, subtle shadow
- Error messages: orange/red tint, icon + text
- Buttons: rounded, hover effects, matching existing button styles
- Font: match existing (DM Sans or system default)
```

---

## 5. IMPLEMENTATION PLAN

Write `docs/IMPLEMENTATION_PLAN_document_upload.md`:

```markdown
# Implementation Plan: SPARC Document Upload

## Phase 1 — Backend Foundation (no frontend changes)

### Step 1.1: Create enrichment package structure
```bash
mkdir -p enrichment
touch enrichment/__init__.py
touch enrichment/document_extractor.py
touch enrichment/consistency_checker.py
touch enrichment/confidence.py
```
**Verify:** `python -c "from enrichment import document_extractor"` works with no import errors.

### Step 1.2: Implement document_extractor.py

Functions:
- `extract_text_from_pdf(pdf_path: str) → str`
  - Uses subprocess.run(["pdftotext", "-", pdf_path])
  - Returns extracted text or empty string on failure
  - Handles exceptions gracefully (no pdftotext, timeout, etc.)

- `extract_pl_fields(pdf_text: str) → dict`
  - Regex patterns for Revenue, COGS, Gross Profit, EBITDA, Net Profit, Employee Cost
  - Returns {field_name: {value, confidence, source}}

- `extract_balance_sheet_fields(pdf_text: str) → dict`
  - Regex patterns for Assets, Fixed Assets, Current Assets, Liabilities, Equity, Debt
  - Calculates Debt/Equity if both present

- `extract_itr_fields(pdf_text: str) → dict`
  - Regex patterns for Turnover, Profit, Advance Tax

- `extract_gstr_fields(pdf_text: str) → dict`
  - Regex patterns for B2B, B2C, Export totals
  - Calculates B2B %

- `extract_pf_fields(pdf_text: str) → dict`
  - Estimates payroll and employee count from contribution

**Verify:** Test with a real P&L PDF. Extract revenue, confirm value matches manual read ±5%.

### Step 1.3: Implement consistency_checker.py

Functions:
- `check_revenue_consistency(itr: float, gstr: float, tolerance: float = 5.0) → dict`
  - Returns {status: "pass"|"warning", variance_pct, message}

- `check_balance_sheet_balance(assets, liabilities, equity, tolerance: float = 5.0) → dict`
  - Returns {status, variance_cr, message}

- `run_all_consistency_checks(extraction_dict) → list`
  - Runs all available checks on merged extractions

**Verify:** Unit test — pass ITR=100, GSTR=95, expect "pass"; ITR=100, GSTR=80, expect "warning".

### Step 1.4: Implement confidence.py

Functions:
- `tag_field(value, source, method) → FieldConfidence`
  - Assigns confidence level based on extraction method
  - "extracted" for regex match, "calculated" for derived, "estimated" for heuristic

- `summarize_confidence(field_dict: dict) → str`
  - Aggregates field confidences into overall "verified" | "inferred" | "estimated"

**Verify:** Unit test — 8 "extracted" fields → summary "verified", 3 "estimated" fields → summary "estimated".

### Step 1.5: Add StartupInput fields in risk_engine.py

Add these fields to `StartupInput` dataclass (with defaults):
- `enrichment_source: str = "manual"`
- `enrichment_confidence: str = "estimated"`
- `field_confidence: Dict[str, str] = field(default_factory=dict)`
- `annual_revenue_cr_verified: Optional[float] = None`
- `gross_profit_cr_verified: Optional[float] = None`
- `total_insurable_asset_cr_verified: Optional[float] = None`
- `fixed_assets_cr_verified: Optional[float] = None`
- `inventory_cr_verified: Optional[float] = None`
- `receivables_cr_verified: Optional[float] = None`
- `net_worth_cr_verified: Optional[float] = None`
- `debt_equity_ratio_verified: Optional[float] = None`
- `payroll_cr_verified: Optional[float] = None`
- `employee_count_verified: Optional[int] = None`
- `b2b_pct_verified: Optional[float] = None`

**Verify:** Existing tests still pass: `python -m pytest tests/ -q` (should be 66 passing).

### Step 1.6: Modify compute_risk_scores() in risk_engine.py

At the top of the function, add:
```python
# Use verified values if available, fall through to proxies if not
revenue = inp.annual_revenue_cr_verified or inp.annual_revenue_cr or 0.0
gross_profit = inp.gross_profit_cr_verified or 0.0
# ... repeat for other critical fields
```

**Verify:** Unit test — StartupInput with annual_revenue_cr_verified=1000 produces different scores than same input without verified revenue.

### Step 1.7: Create api/upload.py

Implement:
```python
def upload(request):
    """Handle POST /api/upload with multipart/form-data files."""
    files = request.files.getlist('files')
    validate_upload(files)
    
    results = []
    for file in files:
        doc_type = detect_document_type(file.filename)
        pdf_text = extract_text_from_pdf(file)
        
        if not pdf_text:
            results.append(DocumentExtraction(
                filename=file.filename,
                extraction_status="error",
                extraction_errors=["No text extractable — ensure PDF is text-based, not a scanned image"]
            ))
            continue
        
        # Route to type-specific extractor
        if doc_type == "p&l":
            fields = extract_pl_fields(pdf_text)
        elif doc_type == "balance_sheet":
            fields = extract_balance_sheet_fields(pdf_text)
        # ... etc
        
        results.append(DocumentExtraction(filename=file.filename, fields=fields))
    
    # Merge all extractions
    merged = merge_extractions([r.fields for r in results])
    
    # Run consistency checks
    checks = run_all_consistency_checks(merged)
    
    # Build enriched profile
    enriched = build_startup_input_from_extracts(merged)
    
    return UploadResult(
        status="success" if all(r.extraction_status == "success" for r in results) else "partial",
        documents=results,
        extraction_summary=merged,
        consistency_check_results=checks,
        enriched_profile=enriched,
        enrichment_confidence=summarize_confidence(merged)
    )
```

**Verify:** POST to /api/upload with a real P&L PDF; confirm JSON response contains extracted fields.

### Step 1.8: Wire into server.py

Add route:
```python
if path == "/api/upload":
    self.handle_upload(request)
```

And vercel.json:
```json
{
  "source": "/api/upload",
  "destination": "/api/upload.py"
}
```

**Verify:** Restart server, curl localhost:5199/api/upload → endpoint responds.

---

## Phase 2 — Frontend: Tabs & Upload Panel

### Step 2.1: Add multi-tab structure to app.js

Create 3 tabs:
- Tab 1: Risk Assessment (existing form, currently active)
- Tab 2: Company Lookup (optional, placeholder)
- Tab 3: Upload Documents (new)

Update `renderApp()` to:
```javascript
function renderApp() {
  const tabs = [
    { id: "risk", label: "Risk Assessment", active: true },
    { id: "company", label: "Company Lookup", active: false },
    { id: "upload", label: "Upload Documents", active: false }
  ];
  
  // Render tab buttons
  // Render tab content (switched on tab.active)
}
```

**Verify:** Home page loads with 3 tabs visible. Clicking tabs switches content without page reload.

### Step 2.2: Implement renderUploadPanel()

State 0 (empty):
```javascript
function renderUploadPanel() {
  return `
    <div class="upload-tab-content">
      <h2>Upload Financial Documents</h2>
      <div class="upload-dropzone" id="dropzone">
        <p>Drag PDFs here or <button onclick="openFileBrowser()">Browse Files</button></p>
        <p class="upload-help">Supports: P&L, Balance Sheet, ITR, GSTR-1, GSTR-3B, PF ECR</p>
        <p class="upload-limit">Max 100 MB total, 25 MB per file</p>
      </div>
      <div id="upload-file-list"></div>
    </div>
  `;
}
```

**Verify:** Upload tab renders dropzone. Drag-over changes border/background.

### Step 2.3: Wire drag-drop + file upload

```javascript
const dropzone = $("dropzone");
dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("active");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("active"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("active");
  handleFileUpload(e.dataTransfer.files);
});
```

**Verify:** Drag PDF onto dropzone, see visual feedback, files are processed.

### Step 2.4: POST /api/upload with progress tracking

```javascript
async function handleFileUpload(files) {
  const formData = new FormData();
  for (let file of files) formData.append("files", file);
  
  try {
    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData
    });
    const result = await response.json();
    showExtractionSummary(result);
  } catch (err) {
    showUploadError(err.message);
  }
}
```

**Verify:** Upload 3 PDFs, see POST succeed, extraction summary renders.

### Step 2.5: Render extraction summary (State 2)

```javascript
function showExtractionSummary(result) {
  const html = `
    <div class="upload-extraction-card">
      <h3>✅ Extracted from your documents</h3>
      <p>Confidence: <strong>${result.enrichment_confidence.toUpperCase()}</strong></p>
      
      ${Object.entries(result.extraction_summary).map(([key, field]) => `
        <div class="extraction-field-row">
          <span class="extraction-field-name">${humanize(key)}</span>
          <span class="extraction-field-value">₹${field.value}</span>
          <span class="extraction-field-badge ${field.confidence}">${field.confidence}</span>
          <span class="extraction-field-source">${field.source}</span>
        </div>
      `).join("")}
      
      ${result.consistency_check_results.map(check => `
        <div class="extraction-check-${check.status}">
          ${check.status === 'pass' ? '✓' : '⚠'} ${check.check}: ${check.message}
        </div>
      `).join("")}
      
      ${result.extraction_issues.map(issue => `
        <div class="extraction-issue-row">
          ⚠️ ${issue.field}: ${issue.issue}
          ${issue.options ? `
            ${issue.options.map(opt => `
              <button onclick="selectValue('${issue.field}', ${opt.value})">${opt.value}</button>
            `).join("")}
          ` : ""}
        </div>
      `).join("")}
      
      <button onclick="proceedWithExtraction()">Looks good, continue →</button>
    </div>
  `;
  renderPage(html);
}
```

**Verify:** Extraction card displays all fields with badges, consistency checks, and any ambiguous fields.

### Step 2.6: Implement 3-question panel (State 3)

```javascript
function show3QuestionPanel() {
  return `
    <div class="upload-3q-panel">
      <h3>Just 3 quick questions</h3>
      
      <div class="q-row">
        <label>1. How sensitive is your customer data?</label>
        <div class="q-option-group">
          <label><input type="radio" name="data_sensitivity" value="Low"> Low</label>
          <label><input type="radio" name="data_sensitivity" value="Medium"> Medium</label>
          <label><input type="radio" name="data_sensitivity" value="High"> High</label>
        </div>
      </div>
      
      <div class="q-row">
        <label>2. What % of revenue is B2B?</label>
        <input type="range" id="b2b-slider" min="0" max="100" value="${state.profile.b2b_pct * 100}" 
               oninput="updateB2BDisplay(this.value)">
        <span id="b2b-display">${(state.profile.b2b_pct * 100).toFixed(0)}%</span>
      </div>
      
      <div class="q-row">
        <label>3. What % of workforce is gig?</label>
        <input type="range" id="gig-slider" min="0" max="100" value="${state.profile.gig_headcount_pct * 100}"
               oninput="updateGigDisplay(this.value)">
        <span id="gig-display">${(state.profile.gig_headcount_pct * 100).toFixed(0)}%</span>
      </div>
      
      <button onclick="runAnalysisWithDocuments()">Run Risk Assessment →</button>
    </div>
  `;
}
```

**Verify:** 3 questions render correctly. Sliders update display values in real time.

### Step 2.7: Merge extracted profile + 3 answers → runAnalysis()

```javascript
function runAnalysisWithDocuments() {
  const answers = {
    data_sensitivity: document.querySelector('input[name="data_sensitivity"]:checked').value,
    b2b_pct: parseFloat($("b2b-slider").value) / 100,
    gig_headcount_pct: parseFloat($("gig-slider").value) / 100
  };
  
  // Merge with extracted profile
  state.profile = {
    ...state.extractedProfile,
    ...answers,
    enrichment_source: "document_upload",
    enrichment_confidence: "verified"
  };
  
  runAnalysis();  // existing function
}
```

**Verify:** Click "Run Risk Assessment" → risk assessment runs with extracted + user answers.

---

## Phase 3 — Testing

### Step 3.1: Write unit tests for extraction

```python
# tests/test_document_extraction.py
import unittest
from enrichment.document_extractor import extract_pl_fields, extract_balance_sheet_fields

class TestPLExtraction(unittest.TestCase):
    def test_extract_revenue_simple(self):
        text = "Sales Revenue: ₹3,288 Cr"
        result = extract_pl_fields(text)
        self.assertAlmostEqual(result["annual_revenue_cr"]["value"], 3288.0, delta=1.0)
        self.assertEqual(result["annual_revenue_cr"]["confidence"], "extracted")
```

**Verify:** `python -m pytest tests/test_document_extraction.py -q` → tests pass.

### Step 3.2: Write integration tests for /api/upload

```python
# tests/test_upload_api.py
def test_upload_single_pdf():
    with open("sample_pl.pdf", "rb") as f:
        response = client.post("/api/upload", data={"files": (f, "P&L.pdf")})
    
    assert response.status_code == 200
    result = response.json()
    assert result["status"] in ["success", "partial"]
    assert "extraction_summary" in result
```

**Verify:** `python -m pytest tests/test_upload_api.py -q` → tests pass.

### Step 3.3: Full test suite

```bash
python -m pytest tests/ -q
```

**Verify:** All 66 existing tests + new tests pass. No regressions.

---

## Phase 4 — End-to-End Verification

### Step 4.1: Manual end-to-end test

1. Navigate to home screen → see 3 tabs
2. Click "Upload Documents" tab
3. Drag 3 PDFs (P&L, Balance Sheet, ITR)
4. See progress bars, then extraction summary
5. Review extracted fields, consistency checks
6. Click "Looks good, continue"
7. Answer 3 questions
8. Click "Run Risk Assessment"
9. See full risk assessment with "verified" confidence badge

**Verify:** Each step works as expected. Premium output shows "verified" not "estimated".

### Step 4.2: Test error paths

1. Upload scanned image → see graceful error message
2. Upload corrupted PDF → see skip + error, other files process
3. Upload non-PDF → see rejection before upload
4. Upload >100 MB total → see size validation error

**Verify:** All error paths handled gracefully.

### Step 4.3: Regression test

1. Existing Risk Assessment tab still works normally
2. Can fill form manually → risk assessment runs
3. No changes to existing tabs' behavior

**Verify:** Full backward compatibility.
```

---

## 6. APP FLOW

Write `docs/APPFLOW_document_upload.md`:

```markdown
# App Flow: SPARC Document Upload

## Happy Path: User Uploads 3 Documents

```
User lands on SPARC home screen
    ↓
Sees 3 tabs: [Risk Assessment] [Company Lookup] [Upload Documents]
    ↓
Clicks "Upload Documents" tab
    ↓
[Upload Panel — State 0: Empty]
Sees dropzone: "Drag PDFs here"
    ↓
Drags P&L.pdf, BalanceSheet.pdf, ITR.pdf onto dropzone
    ↓
[State 1: Uploading + Progress]
Shows:
  ✓ P&L.pdf — 100% done, extracted 6 fields
  ⟳ BalanceSheet.pdf — 50% processing
  ○ ITR.pdf — queued
    ↓
POST /api/upload (multipart/form-data with 3 files)
    ↓
api/upload.py (backend):
    For each file:
      1. extract_text_from_pdf() → use subprocess → pdftotext
      2. detect_document_type() → "p&l" | "balance_sheet" | "itr"
      3. route to type-specific extractor:
         - extract_pl_fields() → {revenue: 3288.5, cogs: 2467, profit: 821.5}
         - extract_balance_sheet_fields() → {assets: 4200, liabilities: 2100, equity: 2098}
         - extract_itr_fields() → {revenue: 3288.5, profit: 985}
    ↓
    Merge all extractions:
      {
        "annual_revenue_cr": {"value": 3288.5, "confidence": "extracted", "source": "ITR + P&L + GSTR"},
        "gross_profit_cr": {"value": 821.5, "confidence": "extracted", "source": "P&L"},
        ...
      }
    ↓
    Run consistency checks:
      check_revenue_consistency(ITR=3288.5, GSTR=3245.2)
        → variance 1.3% → "pass"
      check_balance_sheet_balance(Assets=4200, Liabilities+Equity=4198.5)
        → variance ₹1.5 Cr → "pass"
    ↓
    Build enriched profile:
      {
        "annual_revenue_cr": 3288.5,
        "annual_revenue_cr_verified": 3288.5,
        "gross_profit_cr": 821.5,
        "gross_profit_cr_verified": 821.5,
        "total_insurable_asset_cr": 4200,
        "total_insurable_asset_cr_verified": 4200,
        "enrichment_source": "document_upload",
        "enrichment_confidence": "verified",
        ...
      }
    ↓
    Return UploadResult JSON
    ↓
[State 2: Extraction Summary Card]
Frontend renders:
  ✅ Extracted from your documents
  Confidence: VERIFIED
  
  Revenue           ₹3,288 Cr      ✓ extracted (P&L, ITR, GSTR)
  Gross Profit      ₹821 Cr        ✓ extracted (P&L)
  Fixed Assets      ₹842 Cr        ✓ extracted (Balance Sheet)
  Total Assets      ₹4,200 Cr      ✓ extracted (Balance Sheet)
  Equity            ₹2,098 Cr      ✓ calculated
  
  ✓ ITR Revenue (₹3,288) vs GSTR (₹3,245): 1.3% variance ✓ OK
  ✓ Balance Sheet Balances ✓ OK
  
  [Edit any value] [Looks good, continue →]
    ↓
User clicks "Looks good, continue"
    ↓
[State 3: 3-Question Panel]
1. Data sensitivity? → User selects "High"
2. B2B %? → User drags to 35%
3. Gig %? → User drags to 10%
    ↓
User clicks "Run Risk Assessment"
    ↓
app.js merges:
  {
    ...extractedProfile,
    data_sensitivity: "High",
    b2b_pct: 0.35,
    gig_headcount_pct: 0.10
  }
    ↓
POST /api/analyze with merged profile
    ↓
server.py → analyze():
    1. effective_profile() merges user input with defaults
    2. Converts to StartupInput:
       - annual_revenue_cr_verified = 3288.5 (from document)
       - gross_profit_cr_verified = 821.5 (from document)
       - total_insurable_asset_cr_verified = 4200 (from document)
       - enrichment_source = "document_upload"
       - enrichment_confidence = "verified"
    ↓
    3. compute_risk_scores(inp):
       - Uses annual_revenue_cr_verified directly (no stage proxy)
       - Uses total_insurable_asset_cr_verified directly
       - Scores based on actual verified data
    ↓
    4. quote_prefill.py:
       - Sees annual_revenue_cr_verified → skips all revenue proxies
       - Uses verified revenue for cyber/PI/D&O limit calibration
    ↓
    5. recommend_products() → bundle scoring
    ↓
    6. Returns full risk assessment
    ↓
[Results Panel]
Shows:
  ✅ Risk Assessment Complete
  Confidence: VERIFIED (from your financial documents)
  
  Risk Scores:
    Cyber Technical Risk: 82
    Data Privacy Risk: 77
    ...
  
  Recommended Bundle: Startup Shield Pack
  
  Premium: ₹18.2 - ₹22.5 Lakh
  (Technically priced from verified company data)
```

## Fallback Path: Scanned Image

```
User drags scanned ITR_scan.pdf
    ↓
extract_text_from_pdf() → subprocess pdftotext returns empty
    ↓
api/upload.py detects no text extractable
    ↓
Returns UploadResult:
  {
    "status": "partial",
    "documents": [{
      "filename": "ITR_scan.pdf",
      "extraction_status": "error",
      "extraction_errors": ["No text extractable — PDF appears to be a scanned image"]
    }]
  }
    ↓
[State 4: Fallback Message]
Frontend renders:
  ⚠️ Couldn't read this PDF
  
  It looks like a scanned image. Please upload
  a text-based PDF from your bank or accounting
  software.
  
  [Try different file] [Use manual form]
```

## Error Path: Corrupted File

```
User uploads corrupted_file.pdf + good_file.pdf
    ↓
extract_text_from_pdf("corrupted_file.pdf") → throws exception
    ↓
api/upload.py catches, logs error, continues with next file
    ↓
Returns UploadResult:
  {
    "status": "partial",
    "documents": [
      {"filename": "corrupted_file.pdf", "extraction_status": "error"},
      {"filename": "good_file.pdf", "extraction_status": "success", ...}
    ]
  }
    ↓
[State 2: Partial Summary]
Frontend shows:
  ⚠️ Partial Extraction
  
  ✓ good_file.pdf — successfully extracted 5 fields
  ✗ corrupted_file.pdf — unable to read (corrupted PDF?)
  
  You can proceed with the good data, or try re-uploading
  the corrupted file.
  
  [Proceed with what we have] [Try again]
```
```

---

## FINAL INSTRUCTIONS FOR CLAUDE CODE

1. **Read all files first** — before coding, read the entire codebase paths listed at the top.

2. **Phases in order** — Complete Phase 1, then Phase 2, then Phase 3, then Phase 4. Verify each step.

3. **Stdlib only** — No new pip packages. Use `subprocess` for pdftotext, `urllib` for HTTP (already used), `re` for regex.

4. **Keep existing tabs untouched** — The Risk Assessment and Company Lookup tabs must work identically. This is a new tab only.

5. **Graceful error handling** — No scanned images? No problem. No pdftotext? Show clear message. Corrupted PDF? Skip and continue.

6. **Confidence tagging is critical** — Every extracted field must have a confidence level. This drives the premium output.

7. **Consistency checks are gates** — ITR ≠ GSTR → flag as warning, show both, ask user which to trust.

8. **Test suite must pass** — `python -m pytest tests/ -q` must show all tests green. Run after Phase 1, Phase 2, and final.

9. **Document types auto-detected** — Use filename heuristics (not file MIME types) to guess if file is P&L, Balance Sheet, etc.

10. **Multipart form parsing** — Use the existing server's ability to parse multipart. If needed, add simple RFC 7578 parser.

---

## SUCCESS CRITERIA

Feature is complete when:

- [ ] Home screen has 3 tabs; clicking "Upload Documents" shows upload panel
- [ ] Drag 3 PDFs onto dropzone; all upload successfully
- [ ] P&L extraction finds Revenue ±5%, COGS ±5%, Gross Profit ±5%
- [ ] Balance Sheet extraction finds Assets ±5%, Equity ±5%
- [ ] ITR extraction finds Declared Revenue ±3%
- [ ] GSTR extraction finds B2B/B2C split correctly
- [ ] Consistency checks flag mismatches as warnings (not errors)
- [ ] Extracted profile summary shows all fields with confidence badges
- [ ] User can edit any extracted value before proceeding
- [ ] Risk assessment runs with extracted data (no proxies)
- [ ] Premium output shows "verified" confidence band
- [ ] Scanned PDF handled gracefully (fallback message)
- [ ] All tests pass: `python -m pytest tests/ -q`
- [ ] Risk Assessment and Company Lookup tabs unchanged (no regressions)
- [ ] All 6 docs exist and are complete
