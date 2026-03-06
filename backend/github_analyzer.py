import os
import tempfile
import shutil
import logging
import json
from pathlib import Path
from git import Repo

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".java", ".cpp", ".html", ".css", ".go", ".rb", ".php"}

def analyze_github_repo(repo_url: str) -> dict:
    """
    Clones a GitHub repository, reads the supported source files,
    and returns a summary dict of metrics and the code content.
    """
    temp_dir = tempfile.mkdtemp()
    extracted_code = []
    
    metrics = {
        "files_scanned": 0,
        "languages_detected": set(),
        "dependencies": 0
    }
    
    LANG_MAP = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", 
        ".java": "Java", ".cpp": "C++", ".html": "HTML", 
        ".css": "CSS", ".go": "Go", ".rb": "Ruby", ".php": "PHP"
    }

    try:
        logger.info(f"Cloning repo: {repo_url} into {temp_dir}")
        Repo.clone_from(repo_url, temp_dir, depth=1)

        for root, _, files in os.walk(temp_dir):
            if ".git" in root:
                continue

            for file_name in files:
                ext = Path(file_name).suffix
                
                # Check for dependencies
                if file_name in ["package.json", "requirements.txt", "pom.xml", "Gemfile", "go.mod"]:
                    metrics["dependencies"] += 1
                
                if ext in SUPPORTED_EXTENSIONS:
                    metrics["files_scanned"] += 1
                    metrics["languages_detected"].add(LANG_MAP.get(ext, ext.strip('.')))
                    
                    file_path = os.path.join(root, file_name)
                    # Use a relative path to keep it clean
                    rel_path = os.path.relpath(file_path, temp_dir)
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            # Basic limit per file to avoid huge files crashing the prompt
                            if len(content) > 100000:
                                content = content[:100000] + "\n... [truncated]"
                            
                            extracted_code.append(f"--- File: {rel_path} ---\n{content}\n")
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")

        # limit total code to avoid overflowing the AI context
        total_code = "\n".join(extracted_code)
        # Using ~9000 tokens space
        if len(total_code) > 35000:
            total_code = total_code[:35000] + "\n... [truncated due to length]"
            
        metrics["languages_detected"] = list(metrics["languages_detected"])
            
        return {
            "code": total_code,
            "metrics": metrics
        }

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
