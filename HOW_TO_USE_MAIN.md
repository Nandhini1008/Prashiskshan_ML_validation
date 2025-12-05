# How to Use main.py - Company Legitimacy Scorer

## Input Format

The `main.py` script accepts company validation inputs in two ways:

### 1. Command Line Arguments

```bash
python main.py "<Company Name>" "<GSTIN>" "<CIN>"
```

**Arguments:**
- **Argument 1** (Required): Company Name (in quotes if it has spaces)
- **Argument 2** (Optional): GST Identification Number (GSTIN)
- **Argument 3** (Optional): Corporate Identification Number (CIN)

### 2. Interactive Input

If you run without arguments, it will prompt you:

```bash
python main.py
```

Then it will ask:
```
Enter company name to validate: Infosys
Enter GSTIN (optional, press Enter to skip): 33AAACI4798L1Z5
Enter CIN (optional, press Enter to skip): L85110KA1981PLC013115
```

---

## Examples

### Example 1: Full Validation (All Inputs)
```bash
python main.py "Infosys Springboard" "33AAACI4798L1Z5" "L85110KA1981PLC013115"
```

This will run:
- ✅ GST validation using the provided GSTIN
- ✅ MCA validation using the provided CIN
- ✅ LinkedIn employability research
- ✅ Reddit scam detection

### Example 2: Without GST/CIN (LinkedIn + Reddit Only)
```bash
python main.py "Google"
```

This will run:
- ⚠️ GST validation skipped (no GSTIN)
- ⚠️ MCA validation skipped (no CIN)
- ✅ LinkedIn employability research
- ✅ Reddit scam detection

### Example 3: With Only GSTIN
```bash
python main.py "TCS" "27AAACT2727Q1ZT"
```

This will run:
- ✅ GST validation using the provided GSTIN
- ⚠️ MCA validation skipped (no CIN)
- ✅ LinkedIn employability research
- ✅ Reddit scam detection

---

## Input Validation

### GSTIN Format
- **Length**: 15 characters
- **Format**: `##AAAAA####A#Z#`
  - First 2 digits: State code
  - Next 5 characters: PAN of the business
  - Next 4 digits: Entity number
  - 1 character: Alphabet (Z by default)
  - 1 character: Checksum
- **Example**: `27AAACR4849R2ZK`

### CIN Format
- **Length**: 21 characters
- **Format**: `L#####AA####AAA######`
  - L: Listing status
  - 5 digits: Industry code
  - 2 letters: State code
  - 4 digits: Year of incorporation
  - 3 letters: Type (PLC/PTC/etc.)
  - 6 digits: Registration number
- **Example**: `L85110KA1981PLC013115`

---

## Output Files

After running, the following files will be created in the `outputs/` directory:

1. `{company}_gst.json` - GST validation results
2. `{company}_mca.json` - MCA validation results
3. `{company}_linkedin.json` - LinkedIn research data
4. `{company}_reddit.json` - Reddit scam detection data
5. `{company}_scam_report.json` - Detailed scam report
6. `{company}_legitimacy_score.json` - **Final legitimacy score (0-100)**

---

## Scoring Breakdown

The final legitimacy score (0-100) is calculated from:

| Component | Max Score | Description |
|-----------|-----------|-------------|
| GST Validation | 20 | GSTIN validity + Active status |
| MCA Validation | 20 | CIN validity + Active status |
| Consistency | 15 | Name/State/Year matching between GST & MCA |
| Digital Presence | 20 | LinkedIn page + Recent activity |
| Employability | 15 | Employee count + Hiring signals |
| Public Feedback | 10 | Reddit sentiment + Intern reviews |
| **TOTAL** | **100** | |

---

## Classification Thresholds

Based on the total score:

- **80-100**: `LEGIT` (High confidence)
- **60-79**: `POTENTIALLY LEGIT` (Medium confidence)
- **40-59**: `HIGH RISK` (Medium confidence)
- **0-39**: `NON-LEGIT` (High confidence)

### Red Flag Overrides

If 2+ red flags are detected, classification may be overridden to `HIGH RISK` or `NON-LEGIT` regardless of score.

Red flags include:
- GST status cancelled/suspended
- MCA status strike-off/inactive
- 7+ scam mentions on Reddit
- Severe name inconsistency between GST and MCA

---

## Important Notes

⚠️ **API Credits**: Running with company name only (no GSTIN/CIN) will still consume:
- Tavily API credits (for LinkedIn and Reddit searches)
- ScraperAPI credits (for Reddit scraping)

💡 **Best Practice**: Always provide GSTIN and CIN when available for most accurate scoring.

🔒 **Privacy**: All data is scraped from publicly available sources. No login or authentication required.

---

## Troubleshooting

### Issue: "No module named 'gst'"
**Solution**: Make sure `gst.py` and `mca.py` are in the same directory as `main.py`

### Issue: "Selenium WebDriver not found"
**Solution**: Install Chrome and ChromeDriver:
```bash
pip install selenium webdriver-manager
```

### Issue: "Tavily API error"
**Solution**: Check if the Tavily API key is valid in the code

### Issue: main.py is corrupted
**Solution**: The file may need to be restored. Contact support or restore from backup.
