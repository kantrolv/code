import re

def parse_review_response(raw: str) -> dict:
    """
    Extract severity sections from the AI response and return structured JSON.
    Sections detected:  Critical Issues · High Priority · Medium Priority · Low Priority
    """
    severity_patterns = {
        "critical": r"(?i)#+\s*critical\s+issues?(.*?)(?=#+\s*(high|medium|low)|$)",
        "high":     r"(?i)#+\s*high\s+priority(.*?)(?=#+\s*(medium|low|critical)|$)",
        "medium":   r"(?i)#+\s*medium\s+priority(.*?)(?=#+\s*(low|critical|high)|$)",
        "low":      r"(?i)#+\s*low\s+priority(.*?)(?=#+\s*(critical|high|medium)|$)",
    }

    sections: dict = {}
    counts:   dict = {}

    for severity, pattern in severity_patterns.items():
        match = re.search(pattern, raw, re.DOTALL)
        if match:
            section_text = match.group(1).strip()
            sections[severity] = section_text
            # Count bullet points / numbered items as individual issues
            bullets = re.findall(r"(?m)^[\s]*[-*•\d]+[.)]\s+.+", section_text)
            counts[severity] = len(bullets) if bullets else (1 if section_text else 0)
        else:
            sections[severity] = ""
            counts[severity] = 0

    return {
        "raw_response": raw,
        "sections": sections,
        "counts": counts,
        "total_issues": sum(counts.values()),
    }
