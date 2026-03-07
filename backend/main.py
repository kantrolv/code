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
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

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

# ── Frontend Directory ─────────────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

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

class CheckSyntaxRequest(BaseModel):
    code: str
    language: str

# ── API Routes ───────────────────────────────────────────────────────────────────


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
import ast
from fastapi.responses import Response

SYNTAX_HINTS = {
    "unterminated string literal": {
        "what": "A string literal (text enclosed in quotes) is missing its closing quote.",
        "improve": "Always ensure every opening quote has a matching closing quote of the same type.",
        "correct": "Add the missing quote (e.g. \") at the end of the text.",
    },
    "unexpected eof while parsing": {
        "what": "The code ended unexpectedly. You likely have unclosed parentheses, brackets, or blocks.",
        "improve": "Use an editor with bracket matching to ensure all blocks are closed.",
        "correct": "Check for missing closing parentheses ')', brackets ']', or braces '}'.",
    },
    "invalid syntax": {
        "what": "The code violates Python's grammar rules.",
        "improve": "Review the exact character or statement at the error line.",
        "correct": "Ensure you aren't missing colons ':', commas ',', or using reserved keywords incorrectly.",
    },
    "expected an indented block": {
        "what": "Python expected indented code after a statement ending with a colon (like if, for, def).",
        "improve": "Be consistent with indentation (use 4 spaces).",
        "correct": "Add proper indentation to the line following the colon.",
    },
    "unmatched": {
        "what": "There's a closing parenthesis, bracket, or brace without a corresponding opening one.",
        "improve": "Visually trace your braces to ensure they come in pairs.",
        "correct": "Add the missing opening bracket or remove the extra closing bracket."
    }
}

def enhance_syntax_error(msg: str):
    msg_lower = msg.lower()
    for key, hints in SYNTAX_HINTS.items():
        if key in msg_lower:
            return hints
    return {
        "what": "The code contains a syntax formulation error that prevents it from running.",
        "improve": "Review the syntax rules for this specific programming language construct.",
        "correct": "Check for typos, missing punctuation, unclosed quotes/brackets, or misspellings."
    }

@app.post("/api/check_syntax", tags=["Utility"])
async def check_syntax_api(req: CheckSyntaxRequest):
    errors = []
    if req.language.lower() == "python":
        try:
            ast.parse(req.code)
        except SyntaxError as e:
            msg = e.msg or "Syntax Error"
            hints = enhance_syntax_error(msg)
            errors.append({
                "line": e.lineno,
                "column": e.offset or 0,
                "message": msg,
                "what": hints["what"],
                "improve": hints["improve"],
                "correct": hints["correct"]
            })
    return JSONResponse(content={"errors": errors})

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

# ── Serve Frontend ──────────────────────────────────────────────────────────────────
# Mount at the root, MUST be defined after API routes to avoid shadowing
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
