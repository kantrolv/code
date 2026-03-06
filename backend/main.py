import os
import re
import json
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from dotenv import load_dotenv

# Ensure dotenv is loaded before ai_service is imported
load_dotenv()

from ai_service import call_groq, MODEL, GROQ_API_KEY
from parser import parse_review_response
from github_analyzer import analyze_github_repo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="CodeRefine AI",
    description="AI-powered code review & optimization engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ─────────────────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# ── Pydantic models ──────────────────────────────────────────────────────────
class ReviewRequest(BaseModel):
    code: str
    language: str = "Python"
    focus_areas: List[str] = ["Bugs", "Security", "Performance", "Best Practices"]

    @validator("code")
    def code_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Code cannot be empty")
        return v

class RewriteRequest(BaseModel):
    code: str
    language: str = "Python"

    @validator("code")
    def code_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Code cannot be empty")
        return v
        
class ExplainRequest(BaseModel):
    code: str

    @validator("code")
    def code_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Code cannot be empty")
        return v

class GithubAnalyzeRequest(BaseModel):
    repo_url: str

    @validator("repo_url")
    def url_must_not_be_empty(cls, v):
        if not v or not v.strip() or ("http" not in v and "git@" not in v):
            raise ValueError("Invalid Repository URL")
        return v

class ReportRequest(BaseModel):
    markdown: str

# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def serve_frontend():
    """Serve the main index.html frontend."""
    html_path = FRONTEND_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.post("/api/review", tags=["AI"])
async def review_code(req: ReviewRequest):
    focus_str = ", ".join(req.focus_areas) if req.focus_areas else "all areas"

    prompt = f"""You are a senior software engineer with 15 years of experience.

Analyze the following {req.language} code thoroughly and identify:
1 Bugs
2 Security vulnerabilities
3 Performance issues
4 Best practice violations

Focus specifically on: {focus_str}.

Structure your response with EXACTLY these four Markdown sections (use ## headings):

## Critical Issues
List every critical bug, crash risk, or severe security vulnerability.

## High Priority
List important performance problems, major code-quality issues, or significant security weaknesses.

## Medium Priority
List moderate issues such as code smells, non-optimal algorithms, or missing validations.

## Low Priority
List minor style issues, naming conventions, or nice-to-have improvements.

For each issue provide:
- **What**: Brief description
- **Where**: Line reference or code snippet
- **Why**: Why it matters
- **Fix**: Concrete suggestion

After all four sections, add a ## Summary section with an overall assessment including improvement suggestions.

CODE ({req.language}):
```{req.language.lower()}
{req.code}
```"""

    raw = call_groq(prompt)
    parsed = parse_review_response(raw)
    return JSONResponse(content={"success": True, **parsed})


@app.post("/api/rewrite", tags=["AI"])
async def rewrite_code(req: RewriteRequest):
    prompt = f"""Rewrite the following code to make it production ready. Fix bugs, improve performance, improve security, and follow clean coding principles.

CRITICAL INSTRUCTIONS:
- DO NOT hallucinate or create an entirely new program.
- STRICTLY maintain the original functionality and intent of the user's code. 
- The output MUST be valid {req.language} code.

Return ONLY the rewritten code inside a single fenced code block (``` ```).
Do NOT include explanations outside the code block.
After the code block, add a brief ## Changes Made section in Markdown listing the key improvements.

ORIGINAL CODE ({req.language}):
```{req.language.lower()}
{req.code}
```"""

    raw = call_groq(prompt)

    # Extract fenced code block
    code_match = re.search(r"```[a-zA-Z0-9+#]*\s*\n(.*?)```", raw, re.DOTALL)
    if code_match:
        rewritten_code = code_match.group(1).strip()
    else:
        fallback_match = re.search(r"```[a-zA-Z0-9+#]*\s*\n(.*)", raw, re.DOTALL)
        rewritten_code = fallback_match.group(1).strip() if fallback_match else raw.strip()

    rewritten_code = re.sub(r"(?i)#+\s*changes\s+made.*", "", rewritten_code, flags=re.DOTALL).strip()

    changes_match = re.search(r"(?i)#+\s*changes\s+made(.*?)$", raw, re.DOTALL)
    changes_summary = changes_match.group(1).strip() if changes_match else ""

    return JSONResponse(content={
        "success": True,
        "rewritten_code": rewritten_code,
        "changes_summary": changes_summary,
        "raw_response": raw,
    })

@app.post("/api/explain", tags=["AI"])
async def explain_code(req: ExplainRequest):
    prompt = f"""You are a senior developer. Provide a detailed, line-by-line explanation of the following code.
Format your response in neat Markdown.

CODE:
```
{req.code}
```"""
    raw = call_groq(prompt)
    return JSONResponse(content={"success": True, "explanation": raw})

@app.post("/api/github-analyze", tags=["AI"])
async def github_analyze(req: GithubAnalyzeRequest):
    try:
        repo_data = analyze_github_repo(req.repo_url)
        repo_code = repo_data["code"]
        repo_metrics = repo_data["metrics"]
    except Exception as e:
        logger.error(f"GitHub analyze failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze repository: {e}")

    prompt = f"""You are a senior cybersecurity engineer.

Analyze the following repository code.

Your task:
1. Detect security vulnerabilities
2. Detect bad coding practices
3. Detect performance issues
4. Detect insecure credential handling

Analyze files individually. Return your answer EXACTLY in this format:

Repository Security Report
--------------------------------

Security Score: <number (0-100)>
Code Quality Score: <number (0-100)>
Risk Level: <Low / Medium / High>

Critical Issues
---------------
File: <filename>
Risk: Critical
Issue: <description>

High Risk Files
---------------
File: <filename>
Risk: High
Issue: <description>

Medium Issues
--------------
File: <filename>
Risk: Medium
Issue: <description>

Improvement Suggestions
-----------------------
• <practical fix>

REPOSITORY CODE:
{repo_code}
"""
    raw = call_groq(prompt)

    # Make scores and info easy to parse
    def parse_stat(pattern, text, default):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else default

    sec_score = parse_stat(r"Security Score[:]*\s*(\d+)", raw, "N/A")
    qual_score = parse_stat(r"Code Quality (?:Score)?[:]*\s*(\d+)", raw, "N/A")
    risk_level = parse_stat(r"Risk Level[:]*\s*(Low|Medium|High)", raw, "Unknown")
    
    return JSONResponse(content={
        "success": True,
        "raw_response": raw,
        "security_score": sec_score,
        "quality_score": qual_score,
        "risk_level": risk_level,
        "metrics": repo_metrics
    })

import io
from fastapi.responses import Response

@app.post("/api/download-report", tags=["Utility"])
async def download_report(req: ReportRequest):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        Story = []

        Story.append(Paragraph("GitHub Repository Security Report", styles["Title"]))
        Story.append(Spacer(1, 14))
        
        # Simple parsing logic
        # Swap out common chars to avoid xml errors
        safe_md = req.markdown.replace("<", "&lt;").replace(">", "&gt;").replace("\r", "")
        # Remove bolding **
        safe_md = safe_md.replace("**", "")
        
        lines = safe_md.split("\n")
        
        for para in lines:
            if not para.strip() and not para.startswith("---"):
                continue
                
            style = styles['Normal']
            # Headings
            if para.startswith('###'):
                style = styles['Heading3']
                para = para[3:]
            elif para.startswith('##'):
                style = styles['Heading2']
                para = para[2:]
            elif para.startswith('#'):
                style = styles['Heading1']
                para = para[1:]
            elif para.startswith('---'):
                Story.append(Spacer(1, 12))
                continue
                
            Story.append(Paragraph(para.strip(), style))
            Story.append(Spacer(1, 4))
            
        doc.build(Story)
        pdf_buffer.seek(0)
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=security_report.pdf"}
        )
    except Exception as e:
        logger.error(f"Generate PDF failed: {e}")
        raise HTTPException(status_code=500, detail="Could not generate PDF")

@app.get("/health", tags=["Utility"])
async def health():
    return {"status": "ok", "model": MODEL, "groq_configured": bool(GROQ_API_KEY)}
