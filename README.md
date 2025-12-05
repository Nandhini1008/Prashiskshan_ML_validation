# Company Validation API Service

AI-powered company legitimacy validation service that checks GST, MCA/CIN, Reddit reputation, and LinkedIn employability signals.

## Features

- ✅ **GST Validation**: Verify GST number and status
- ✅ **MCA/CIN Validation**: Check company registration via Zaubacorp (Tavily API)
- ✅ **Reddit Scam Check**: Search for scam reports and complaints
- ✅ **LinkedIn Analysis**: Assess employability signals using AI
- ✅ **Legitimacy Scoring**: 0-100 score with confidence levels
- ✅ **REST API**: Easy integration with any frontend/backend

## Quick Start

### Local Development

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   Create `.env` file:

   ```env
   TAVILY_API_KEY=your_tavily_api_key
   GEMINI_API_KEY=your_gemini_api_key
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   ```

3. **Run Server**

   ```bash
   python api_server.py
   ```

4. **Test API**
   ```bash
   python test_api.py
   ```

### Docker Deployment

1. **Build Image**

   ```bash
   docker build -t validation-service .
   ```

2. **Run Container**

   ```bash
   docker run -p 8003:8003 --env-file .env validation-service
   ```

3. **Access API**
   - API: http://localhost:8003
   - Docs: http://localhost:8003/docs
   - Health: http://localhost:8003/health

## API Endpoints

### Health Check

```http
GET /health
```

### Validate Company

```http
POST /validate-company
Content-Type: application/json

{
  "company_name": "ZOHO CORPORATION PRIVATE LIMITED",
  "cin_number": "U40100TN2010PTC075961",
  "gst_number": "33AABCT1332L1ZU"
}
```

### API Information

```http
GET /api-info
```

## Response Format

```json
{
  "success": true,
  "validation_summary": {
    "company_name": "...",
    "validation_timestamp": "...",
    "validation_duration_seconds": 8.5
  },
  "legitimacy_assessment": {
    "status": "✅ COMPANY IS LEGITIMATE",
    "classification": "LEGITIMATE",
    "confidence_level": "HIGH",
    "total_score": 85,
    "score_breakdown": {
      "gst_validation_score": 30,
      "mca_validation_score": 30,
      "cin_consistency_score": 10,
      "reddit_reputation_score": 20,
      "linkedin_employability_score": 10
    }
  },
  "flags": {
    "green_flags": [
      "GST number is valid and registered",
      "Company status is Active",
      "No scam reports found on Reddit"
    ],
    "red_flags": []
  },
  "detailed_results": {
    "gst_validation": {...},
    "mca_validation": {...},
    "reddit_scam_check": {...},
    "linkedin_employability": {...}
  }
}
```

## Scoring System

### Total Score: 0-100

| Score Range | Classification    | Confidence |
| ----------- | ----------------- | ---------- |
| 80-100      | LEGITIMATE        | HIGH       |
| 60-79       | LIKELY LEGITIMATE | MEDIUM     |
| 40-59       | QUESTIONABLE      | LOW        |
| 0-39        | NOT LEGITIMATE    | HIGH       |

### Score Breakdown:

- **GST Validation**: 0-30 points
- **MCA Validation**: 0-30 points
- **CIN Consistency**: 0-10 points
- **Reddit Reputation**: 0-20 points
- **LinkedIn Employability**: 0-10 points

## Deployment

### Render (Recommended)

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed instructions.

**Quick Deploy**:

1. Push code to GitHub
2. Create new Web Service on Render
3. Select Docker environment
4. Add environment variables
5. Deploy!

**Cost**: Free tier available (512MB RAM)

### Other Platforms

- **Railway**: `railway up`
- **Google Cloud Run**: `gcloud run deploy`
- **AWS ECS**: Use provided Dockerfile
- **Heroku**: Add `heroku.yml`

## Environment Variables

### Required:

- `TAVILY_API_KEY`: For Zaubacorp scraping
- `GEMINI_API_KEY`: For LinkedIn analysis

### Optional:

- `REDDIT_CLIENT_ID`: For Reddit validation
- `REDDIT_CLIENT_SECRET`: For Reddit validation
- `REDDIT_USER_AGENT`: Reddit API user agent
- `SCRAPER_API_KEY`: For enhanced scraping reliability
- `PORT`: Server port (default: 8003)

## Testing

### Run Test Suite

```bash
python test_api.py
```

### Test with cURL

```bash
# Health check
curl http://localhost:8003/health

# Validate company
curl -X POST http://localhost:8003/validate-company \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "ZOHO CORPORATION PRIVATE LIMITED",
    "cin_number": "U40100TN2010PTC075961",
    "gst_number": "33AABCT1332L1ZU"
  }'
```

## Integration Examples

### JavaScript/TypeScript

```typescript
async function validateCompany(
  companyName: string,
  cinNumber: string,
  gstNumber: string
) {
  const response = await fetch("https://your-api.com/validate-company", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      company_name: companyName,
      cin_number: cinNumber,
      gst_number: gstNumber,
    }),
  });

  return response.json();
}
```

### Python

```python
import requests

def validate_company(company_name, cin_number, gst_number):
    response = requests.post(
        'https://your-api.com/validate-company',
        json={
            'company_name': company_name,
            'cin_number': cin_number,
            'gst_number': gst_number
        }
    )
    return response.json()
```

## Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Server (Port 8003)      │
├─────────────────────────────────────────┤
│  Endpoints:                             │
│  ├─ POST /validate-company              │
│  ├─ GET /health                         │
│  └─ GET /api-info                       │
├─────────────────────────────────────────┤
│  Validation Pipeline:                   │
│  ├─ GST Validation (Selenium)           │
│  ├─ MCA Validation (Tavily API)         │
│  ├─ Reddit Check (PRAW)                 │
│  └─ LinkedIn Check (Gemini AI)          │
├─────────────────────────────────────────┤
│  Async Processing (asyncio)             │
│  Concurrent validation execution        │
└─────────────────────────────────────────┘
```

## Performance

- **Average Response Time**: 8-15 seconds
- **Concurrent Validations**: Yes (async)
- **Rate Limiting**: Configurable
- **Caching**: Recommended for production

## Troubleshooting

### Common Issues:

**Port already in use**

```bash
# Change port
PORT=8004 python api_server.py
```

**API keys not found**

```bash
# Check .env file exists
# Verify environment variables are set
```

**Validation timeout**

```bash
# Increase timeout in code
# Check internet connection
# Verify API keys are valid
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

MIT License - see LICENSE file

## Support

- **Documentation**: See RENDER_DEPLOYMENT.md
- **Issues**: GitHub Issues
- **API Docs**: /docs endpoint

---

**Version**: 1.0.0
**Last Updated**: December 6, 2024
