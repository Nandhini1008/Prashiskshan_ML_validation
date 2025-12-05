# Company Validation Service - Render Deployment Guide

## Overview

This guide covers deploying the Company Validation API service to Render using Docker.

## Service Architecture

```
┌─────────────────────────────────────────┐
│   Company Validation API (Port 8003)   │
├─────────────────────────────────────────┤
│  FastAPI Server                         │
│  ├─ POST /validate-company              │
│  ├─ GET /health                         │
│  └─ GET /docs                           │
├─────────────────────────────────────────┤
│  Validation Components:                 │
│  ├─ GST Validation (Selenium)           │
│  ├─ MCA Validation (Tavily API)         │
│  ├─ Reddit Scam Check (PRAW)            │
│  └─ LinkedIn Check (Gemini AI)          │
└─────────────────────────────────────────┘
```

## Prerequisites

1. **Render Account**: Sign up at https://render.com
2. **GitHub Repository**: Code pushed to GitHub
3. **API Keys**:
   - Tavily API Key (for Zaubacorp scraping)
   - Google Gemini API Key (for LinkedIn analysis)
   - Reddit API credentials (optional)

## Deployment Steps

### Step 1: Prepare Your Repository

Ensure these files exist in `Prashiskshan_ml/validation/`:

```
✅ api_server.py          # FastAPI server
✅ main.py                # Validation logic
✅ gst.py                 # GST validation
✅ mca.py                 # MCA validation (Selenium fallback)
✅ zaubacorp_tavily.py    # Zaubacorp scraper (Tavily)
✅ reddit.py              # Reddit scam check
✅ linked.py              # LinkedIn check
✅ requirements.txt       # Python dependencies
✅ Dockerfile             # Docker configuration
✅ .dockerignore          # Docker ignore rules
```

### Step 2: Push to GitHub

```bash
cd Prashiskshan_ml/validation

git add .
git commit -m "Add validation API service with Docker"
git push origin main
```

### Step 3: Create Render Service

1. **Go to Render Dashboard**

   - Visit https://dashboard.render.com
   - Click "New +" → "Web Service"

2. **Connect Repository**

   - Select your GitHub repository
   - Grant Render access if needed

3. **Configure Service**

   - **Name**: `company-validation-service`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `Prashiskshan_ml/validation`
   - **Environment**: `Docker`
   - **Instance Type**: `Free` (512MB) or `Starter` ($7/month, 512MB)

4. **Build Settings**
   - **Dockerfile Path**: `Dockerfile` (auto-detected)
   - Leave other settings as default

### Step 4: Add Environment Variables

In Render dashboard, add these environment variables:

```env
# Required
TAVILY_API_KEY=your_tavily_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (for Reddit validation)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=CompanyValidator/1.0

# Optional (for Scraper API - better reliability)
SCRAPER_API_KEY=your_scraper_api_key
SCRAPER_API_URL=http://api.scraperapi.com

# Port (auto-set by Render)
PORT=8003
```

### Step 5: Deploy

1. Click "Create Web Service"
2. Render will:

   - Clone your repository
   - Build Docker image
   - Deploy container
   - Assign public URL

3. **Monitor Build Logs**
   - Watch for successful build
   - Check for any errors
   - Wait for "Live" status

### Step 6: Test Deployment

Once deployed, test your service:

```bash
# Replace with your Render URL
RENDER_URL="https://company-validation-service.onrender.com"

# Health check
curl $RENDER_URL/health

# Validate company
curl -X POST $RENDER_URL/validate-company \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "ZOHO CORPORATION PRIVATE LIMITED",
    "cin_number": "U40100TN2010PTC075961",
    "gst_number": "33AABCT1332L1ZU"
  }'
```

## API Documentation

Once deployed, access interactive API docs at:

```
https://your-service.onrender.com/docs
```

## API Endpoints

### 1. Health Check

```http
GET /health
```

**Response**:

```json
{
  "status": "healthy",
  "service": "company-validation",
  "components": {
    "gst_validation": "ready",
    "mca_validation": "ready (Tavily API)",
    "reddit_check": "ready",
    "linkedin_check": "ready"
  }
}
```

### 2. Validate Company

```http
POST /validate-company
Content-Type: application/json

{
  "company_name": "Company Name",
  "cin_number": "21-character CIN",
  "gst_number": "15-character GST"
}
```

**Response**:

```json
{
  "success": true,
  "validation_summary": {
    "company_name": "...",
    "cin_number": "...",
    "gst_number": "...",
    "validation_timestamp": "...",
    "validation_duration_seconds": 8.5
  },
  "legitimacy_assessment": {
    "status": "✅ COMPANY IS LEGITIMATE",
    "classification": "LEGITIMATE",
    "confidence_level": "HIGH",
    "total_score": 85,
    "score_breakdown": {...}
  },
  "flags": {
    "green_flags": [...],
    "red_flags": [...]
  },
  "detailed_results": {
    "gst_validation": {...},
    "mca_validation": {...},
    "reddit_scam_check": {...},
    "linkedin_employability": {...}
  }
}
```

### 3. API Info

```http
GET /api-info
```

Returns detailed API documentation and usage examples.

## Memory Considerations

### Free Tier (512MB):

- ✅ FastAPI server (~50MB)
- ✅ Tavily API scraping (~20MB)
- ✅ Selenium headless (~200MB)
- ✅ Python dependencies (~150MB)
- **Total**: ~420MB ✅ Fits!

### If OOM Issues:

1. Upgrade to Starter plan ($7/month, 512MB)
2. Or optimize by removing Selenium (use only Tavily)

## Performance

### Expected Response Times:

- **Health Check**: < 100ms
- **Company Validation**: 8-15 seconds
  - GST: 3-5 seconds
  - MCA (Tavily): 2-4 seconds
  - Reddit: 2-3 seconds
  - LinkedIn: 1-2 seconds

### Optimization Tips:

1. **Caching**: Implement Redis for repeated queries
2. **Async**: Use background tasks for long validations
3. **Rate Limiting**: Add rate limiting to prevent abuse

## Troubleshooting

### Build Fails

**Error**: "Out of memory during build"
**Solution**:

- Remove unnecessary files via `.dockerignore`
- Use multi-stage Docker build
- Upgrade to paid plan

**Error**: "Chrome/ChromeDriver not found"
**Solution**:

- Dockerfile installs Chrome automatically
- Check Dockerfile has Chrome installation steps

### Service Crashes

**Error**: "Container exited with code 137"
**Solution**: Out of memory - upgrade plan

**Error**: "Port binding failed"
**Solution**: Ensure `PORT` env variable is used correctly

### Validation Fails

**Error**: "TAVILY_API_KEY not found"
**Solution**: Add API key in Render environment variables

**Error**: "GST validation timeout"
**Solution**:

- Increase timeout in code
- Check Chrome is running in headless mode

## Monitoring

### Render Dashboard:

- **Metrics**: CPU, Memory, Response time
- **Logs**: Real-time application logs
- **Events**: Deployment history

### Health Monitoring:

```bash
# Add to cron or monitoring service
curl https://your-service.onrender.com/health
```

## Scaling

### Horizontal Scaling:

- Render Free: 1 instance
- Render Paid: Multiple instances with load balancing

### Vertical Scaling:

- Free: 512MB RAM
- Starter: 512MB RAM ($7/month)
- Standard: 2GB RAM ($25/month)
- Pro: 4GB+ RAM ($85+/month)

## Cost Estimate

### Free Tier:

- **Cost**: $0
- **RAM**: 512MB
- **Limitations**:
  - Spins down after 15 min inactivity
  - 750 hours/month
  - Slower cold starts

### Starter Plan:

- **Cost**: $7/month
- **RAM**: 512MB
- **Benefits**:
  - Always on
  - Faster response
  - No spin down

## Integration with Frontend

### Example: React/Next.js

```typescript
// services/validation.ts
export async function validateCompany(
  companyName: string,
  cinNumber: string,
  gstNumber: string
) {
  const response = await fetch(
    "https://your-service.onrender.com/validate-company",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_name: companyName,
        cin_number: cinNumber,
        gst_number: gstNumber,
      }),
    }
  );

  return response.json();
}
```

### Example: Node.js Backend

```javascript
// controllers/validationController.js
const axios = require("axios");

async function validateCompany(req, res) {
  try {
    const { companyName, cinNumber, gstNumber } = req.body;

    const response = await axios.post(
      "https://your-service.onrender.com/validate-company",
      {
        company_name: companyName,
        cin_number: cinNumber,
        gst_number: gstNumber,
      }
    );

    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
```

## Security

### Best Practices:

1. **API Keys**: Store in Render environment variables
2. **CORS**: Configure allowed origins in `api_server.py`
3. **Rate Limiting**: Add rate limiting middleware
4. **Input Validation**: Pydantic models validate inputs
5. **HTTPS**: Render provides free SSL

### Add Rate Limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/validate-company")
@limiter.limit("10/minute")
async def validate_company(request: Request, ...):
    ...
```

## Maintenance

### Update Deployment:

```bash
# Make changes
git add .
git commit -m "Update validation service"
git push origin main

# Render auto-deploys on push
```

### Manual Redeploy:

- Go to Render dashboard
- Click "Manual Deploy" → "Deploy latest commit"

### View Logs:

- Render dashboard → Your service → "Logs" tab
- Real-time streaming logs

## Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **FastAPI Docs**: https://fastapi.tiangolo.com

---

**Deployment Time**: 10-15 minutes
**Cost**: Free or $7/month
**Maintenance**: Auto-deploy on git push
**Uptime**: 99.9% (paid plans)
