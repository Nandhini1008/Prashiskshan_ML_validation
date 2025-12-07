#!/usr/bin/env python3
"""
Company Validation API Server

FastAPI server that exposes company legitimacy validation functionality via REST API.
Integrates GST, MCA (Zaubacorp), Reddit, and LinkedIn validations.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from main import CompanyLegitimacyValidator

app = FastAPI(
    title="Company Validation API",
    description="API for validating company legitimacy using GST, MCA, Reddit, and LinkedIn data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ValidationRequest(BaseModel):
    """Request model for company validation"""
    company_name: str = Field(..., description="Name of the company", min_length=2)
    cin_number: str = Field(..., description="Corporate Identification Number (21 characters)", min_length=21, max_length=21)
    gst_number: str = Field(..., description="GST Identification Number (15 characters)", min_length=15, max_length=15)
    domain: Optional[str] = Field(None, description="Company website domain (optional, for WHOIS validation)")
    
    class Config:
        schema_extra = {
            "example": {
                "company_name": "ZOHO CORPORATION PRIVATE LIMITED",
                "cin_number": "U40100TN2010PTC075961",
                "gst_number": "33AABCT1332L1ZU",
                "domain": "zoho.com"
            }
        }


class ValidationResponse(BaseModel):
    """Response model for validation results"""
    success: bool
    validation_summary: Optional[Dict[str, Any]] = None
    legitimacy_assessment: Optional[Dict[str, Any]] = None
    flags: Optional[Dict[str, Any]] = None
    detailed_results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "Company Validation API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "validate": "/validate-company (POST)",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "company-validation",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "gst_validation": "ready",
            "mca_validation": "ready (Tavily API)",
            "reddit_check": "ready",
            "linkedin_check": "ready",
            "whois_check": "ready"
        }
    }


@app.post("/validate-company", response_model=ValidationResponse)
async def validate_company(request: ValidationRequest):
    """
    Validate company legitimacy
    
    Performs comprehensive validation including:
    - GST validation
    - MCA/CIN validation (via Zaubacorp + Tavily)
    - Reddit scam check
    - LinkedIn employability check
    - WHOIS domain check (if domain provided)
    
    Returns legitimacy assessment with scoring and flags.
    """
    try:
        # Trim whitespace from all inputs to ensure clean data
        company_name = request.company_name.strip()
        cin_number = request.cin_number.strip()
        gst_number = request.gst_number.strip()
        domain = request.domain.strip() if request.domain else None
        
        print(f"\n{'='*80}")
        print(f"📥 Received validation request")
        print(f"   Company: {company_name}")
        print(f"   CIN: {cin_number}")
        print(f"   GST: {gst_number}")
        print(f"   Domain: {domain if domain else 'N/A'}")
        print(f"{'='*80}\n")
        
        # Create validator
        validator = CompanyLegitimacyValidator(
            company_name=company_name,
            cin_number=cin_number,
            gst_number=gst_number,
            domain=domain
        )
        
        # Run all validations
        result = await validator.run_all_validations()
        
        # Check if validation was successful
        if result.get('legitimacy_assessment', {}).get('status') == '❌ VALIDATION FAILED':
            return ValidationResponse(
                success=False,
                validation_summary=result.get('validation_summary'),
                legitimacy_assessment=result.get('legitimacy_assessment'),
                error="Input validation failed"
            )
        
        # Return successful validation result
        return ValidationResponse(
            success=True,
            validation_summary=result.get('validation_summary'),
            legitimacy_assessment=result.get('legitimacy_assessment'),
            flags=result.get('flags'),
            detailed_results=result.get('detailed_results')
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Validation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@app.post("/validate-company-async")
async def validate_company_async(request: ValidationRequest, background_tasks: BackgroundTasks):
    """
    Validate company legitimacy (async - returns immediately)
    
    Starts validation in background and returns a task ID.
    Use this for long-running validations.
    
    Note: For production, implement proper task queue (Celery, Redis, etc.)
    """
    # Trim whitespace from all inputs to ensure clean data
    company_name = request.company_name.strip()
    cin_number = request.cin_number.strip()
    gst_number = request.gst_number.strip()
    domain = request.domain.strip() if request.domain else None
    
    task_id = f"{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # In production, you'd store this in Redis/database
    # For now, just start the background task
    background_tasks.add_task(
        run_validation_background,
        company_name,
        cin_number,
        gst_number,
        domain,
        task_id
    )
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "Validation started in background",
        "note": "Check logs for results (in production, implement status endpoint)"
    }


async def run_validation_background(company_name: str, cin_number: str, gst_number: str, domain: Optional[str], task_id: str):
    """Background task for validation"""
    try:
        validator = CompanyLegitimacyValidator(
            company_name=company_name,
            cin_number=cin_number,
            gst_number=gst_number,
            domain=domain
        )
        
        result = await validator.run_all_validations()
        
        # In production, store result in database/cache
        print(f"\n✅ Background validation complete for task: {task_id}")
        print(f"   Status: {result.get('legitimacy_assessment', {}).get('status')}")
        
    except Exception as e:
        print(f"\n❌ Background validation failed for task: {task_id}")
        print(f"   Error: {str(e)}")


@app.get("/api-info")
async def api_info():
    """Get API information and usage examples"""
    return {
        "api_name": "Company Validation API",
        "version": "1.0.0",
        "description": "Validates company legitimacy using multiple data sources",
        "endpoints": {
            "POST /validate-company": {
                "description": "Synchronous validation (waits for result)",
                "request_body": {
                    "company_name": "string (min 2 chars)",
                    "cin_number": "string (exactly 21 chars)",
                    "gst_number": "string (exactly 15 chars)",
                    "domain": "string (optional)"
                },
                "response": {
                    "success": "boolean",
                    "validation_summary": "object",
                    "legitimacy_assessment": "object with status and score",
                    "flags": "object with green_flags and red_flags",
                    "detailed_results": "object with all validation details"
                }
            },
            "POST /validate-company-async": {
                "description": "Asynchronous validation (returns immediately)",
                "note": "For production, implement proper task queue"
            }
        },
        "validation_sources": [
            "GST (gstsearch.in)",
            "MCA/CIN (zaubacorp.com via Tavily API)",
            "Reddit (scam reports)",
            "LinkedIn (employability signals)",
            "WHOIS (who.is - domain registration)"
        ],
        "scoring": {
            "total_score": "0-110",
            "breakdown": {
                "gst_validation": "0-30 points",
                "mca_validation": "0-30 points",
                "cin_consistency": "0-10 points",
                "reddit_reputation": "0-20 points",
                "linkedin_employability": "0-10 points",
                "whois_domain": "0-10 points"
            },
            "classifications": {
                "75-100%": "LEGITIMATE (High confidence)",
                "60-74%": "LIKELY LEGITIMATE (Medium confidence)",
                "40-59%": "QUESTIONABLE (Low confidence)",
                "0-39%": "NOT LEGITIMATE (High confidence)"
            }
        },
        "example_curl": """
curl -X POST http://localhost:8003/validate-company \\
  -H "Content-Type: application/json" \\
  -d '{
    "company_name": "ZOHO CORPORATION PRIVATE LIMITED",
    "cin_number": "U40100TN2010PTC075961",
    "gst_number": "33AABCT1332L1ZU",
    "domain": "zoho.com"
  }'
        """
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8003"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"\n{'='*80}")
    print(f"🚀 Company Validation API Server")
    print(f"{'='*80}")
    print(f"📍 Running on: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"📊 Health Check: http://{host}:{port}/health")
    print(f"{'='*80}\n")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
