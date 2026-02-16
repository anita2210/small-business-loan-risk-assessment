# Key Findings - SBA Loan Risk Analysis

**Dataset:** 899,164 small business loans  
**Date:** February 2026

---

## Main Results

### Overall Stats
- Total loans: 899,164
- Default rate: 16.74%
- Defaults: 150,494
- Paid in full: 748,670

---

## What I Found

### 1. Industry Risk

**Highest default rates:**
- Finance (52): 27.46%
- Real Estate (53): 26.94%
- Transportation (48): 26.77%

**Lowest default rates:**
- Other Services (81): 19.10%
- Manufacturing (31): 19.55%

Finance sector defaults 44% more than safest sectors.

---

### 2. Geographic Risk

**Riskiest states:**
- DC: 28.52%
- Florida: 25.05%
- Georgia: 22.74%

**Safest states:**
- Louisiana: 18.17%
- Texas: 19.91%

DC has 57% higher defaults than Louisiana.

---

### 3. New vs Established Businesses

| Type | Default Rate |
|------|--------------|
| Established (>2 yrs) | 2.04% |
| Recent | 17.18% |
| New startup | 18.29% |

New businesses default 9x more than established ones.

---

### 4. Loan Size

- Under $50K: 17.83% default rate
- Over $500K: 14.66% default rate

Smaller loans are actually riskier (22% higher defaults).

---

## Recommendations

1. Charge higher rates for Finance/Real Estate sectors
2. Require more collateral in DC/FL/GA
3. Prioritize lending to established businesses
4. Don't assume small loans = low risk

---

## How I Did This

- Uploaded 171MB CSV to AWS S3
- Used AWS Glue to catalog the data
- Ran SQL queries in Athena
- Found patterns across 27 data columns

---