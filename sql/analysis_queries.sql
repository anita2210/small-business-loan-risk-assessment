
SBA LOAN RISK ASSESSMENT - SQL ANALYSIS QUERIES
Database: sba_loan_risk_db
Table: raw_data
------------------------------------------------------------------------------------------------------------------------------------------------
1. OVERALL DEFAULT RATE
Purpose: Calculate portfolio-wide default statistics
SELECT 
    COUNT(*) as total_loans,
    SUM(CASE WHEN chgoffdate IS NULL OR chgoffdate = '' OR chgoffdate = 'N' THEN 0 ELSE 1 END) as defaulted_loans,
    SUM(CASE WHEN chgoffdate IS NULL OR chgoffdate = '' OR chgoffdate = 'N' THEN 1 ELSE 0 END) as paid_loans,
    ROUND(100.0 * SUM(CASE WHEN chgoffdate IS NULL OR chgoffdate = '' OR chgoffdate = 'N' THEN 0 ELSE 1 END) / COUNT(*), 2) as default_rate_percent
FROM raw_data;

-- Result: 16.74% overall default rate (150,494 defaults out of 899,164 loans)
---------------------------------------------------------------------------------------------------------------------------------
 2. DEFAULT RATE BY INDUSTRY SECTOR (NAICS)
 Purpose: Identify highest-risk industry sectors

SELECT 
    SUBSTR(CAST(naics AS VARCHAR), 1, 2) as industry_sector,
    COUNT(*) as total_loans,
    SUM(CASE WHEN chgoffdate IS NULL OR chgoffdate = '' OR chgoffdate = 'N' THEN 0 ELSE 1 END) as defaulted_loans,
    ROUND(100.0 * SUM(CASE WHEN chgoffdate IS NULL OR chgoffdate = '' OR chgoffdate = 'N' THEN 0 ELSE 1 END) / COUNT(*), 2) as default_rate_percent
FROM raw_data
WHERE naics IS NOT NULL
GROUP BY SUBSTR(CAST(naics AS VARCHAR), 1, 2)
HAVING COUNT(*) > 1000
ORDER BY default_rate_percent DESC
LIMIT 15;

-- Key Finding: Finance (52: 27.46%), Real Estate (53: 26.94%), Transportation (48: 26.77%) are riskiest
--Note:I added HAVING COUNT > 1000 here — that's important because without it, 
--a sector with only 5 loans showing 100% default would appear at the top and be misleading
--------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 3. DEFAULT RATE BY STATE (GEOGRAPHIC RISK)
-- Purpose: Identify geographic risk patterns
SELECT 
    state,
    COUNT(*) as total_loans,
    SUM(CASE WHEN chgoffdate IS NULL OR chgoffdate = '' OR chgoffdate = 'N' THEN 0 ELSE 1 END) as defaulted_loans,
    ROUND(100.0 * SUM(CASE WHEN chgoffdate IS NULL OR chgoffdate = '' OR chgoffdate = 'N' THEN 0 ELSE 1 END) / COUNT(*), 2) as default_rate_percent
FROM raw_data
WHERE state IS NOT NULL
  AND LENGTH(state) = 2
  AND state NOT LIKE '%"%'
  AND state NOT LIKE '% %'
  AND state IN ('AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 
                'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC')
GROUP BY state
HAVING COUNT(*) > 500
ORDER BY default_rate_percent DESC
LIMIT 20;

-- Key Finding: DC (28.52%), FL (25.05%), GA (22.74%) have highest default rates
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 4. NEW VS EXISTING BUSINESS RISK
-- Purpose: Compare default rates for new startups vs established businesses
SELECT 
    CASE 
        WHEN newexist = 0 THEN 'Existing (0)'
        WHEN newexist = 1 THEN 'Existing/Recent (1)'
        WHEN newexist = 2 THEN 'New Business (2)'
        ELSE 'Other'
    END as business_type,
    COUNT(*) as total_loans,
    SUM(CASE WHEN chgoffdate IS NULL OR chgoffdate = '' OR chgoffdate = 'N' THEN 0 ELSE 1 END) as defaulted_loans,
    ROUND(100.0 * SUM(CASE WHEN chgoffdate IS NULL OR chgoffdate = '' OR chgoffdate = 'N' THEN 0 ELSE 1 END) / COUNT(*), 2) as default_rate_percent
FROM raw_data
WHERE newexist IS NOT NULL
GROUP BY CASE 
        WHEN newexist = 0 THEN 'Existing (0)'
        WHEN newexist = 1 THEN 'Existing/Recent (1)'
        WHEN newexist = 2 THEN 'New Business (2)'
        ELSE 'Other'
    END
ORDER BY default_rate_percent DESC;

-- Key Finding: New businesses (18.29%) default 9x more than established businesses (2.04%)

---------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 5. LOAN SIZE VS DEFAULT RISK
-- Purpose: Analyze if larger loans are riskier
SELECT 
    CASE 
        WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(disbursementgross, '$', ''), ',', ''), '"', '') AS DOUBLE) < 50000 THEN 'Under $50K'
        WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(disbursementgross, '$', ''), ',', ''), '"', '') AS DOUBLE) < 100000 THEN '$50K-$100K'
        WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(disbursementgross, '$', ''), ',', ''), '"', '') AS DOUBLE) < 250000 THEN '$100K-$250K'
        WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(disbursementgross, '$', ''), ',', ''), '"', '') AS DOUBLE) < 500000 THEN '$250K-$500K'
        ELSE 'Over $500K'
    END as loan_size_range,
    COUNT(*) as total_loans,
    SUM(CASE WHEN chgoffdate IS NULL OR chgoffdate = '' OR chgoffdate = 'N' THEN 0 ELSE 1 END) as defaulted_loans,
    ROUND(100.0 * SUM(CASE WHEN chgoffdate IS NULL OR chgoffdate = '' OR chgoffdate = 'N' THEN 0 ELSE 1 END) / COUNT(*), 2) as default_rate_percent
FROM raw_data
WHERE disbursementgross IS NOT NULL
GROUP BY CASE 
        WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(disbursementgross, '$', ''), ',', ''), '"', '') AS DOUBLE) < 50000 THEN 'Under $50K'
        WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(disbursementgross, '$', ''), ',', ''), '"', '') AS DOUBLE) < 100000 THEN '$50K-$100K'
        WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(disbursementgross, '$', ''), ',', ''), '"', '') AS DOUBLE) < 250000 THEN '$100K-$250K'
        WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(disbursementgross, '$', ''), ',', ''), '"', '') AS DOUBLE) < 500000 THEN '$250K-$500K'
        ELSE 'Over $500K'
    END
ORDER BY default_rate_percent DESC;

-- Key Finding: Smaller loans (<$50K: 17.83%) have HIGHER default rates than large loans (>$500K: 14.66%)


=====================================================
BUSINESS RECOMMENDATIONS
=====================================================
1. Avoid or increase rates for: Finance (Sector 52), Real Estate (53), Transportation (48)
2. Be cautious lending in: DC, Florida, Georgia
3. Prioritize established businesses (newexist=0) - 90% lower default rate
4. Don't assume small loans = low risk - they default more often
5. Safest portfolio: Established businesses in TX/LA doing manufacturing/services
