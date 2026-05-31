"""
WebGuard Pro — Health Score Calculator
Implements the weighted score formula across audit categories.
"""

from typing import Dict, Any

def calculate_health_score(
    seo_score: int,
    security_score: int,
    performance_score: int,
    code_quality_score: int,
    accessibility_score: int,
    mobile_score: int
) -> Dict[str, Any]:
    """
    Calculates overall health score based on weighted categories:
      - SEO: 20%
      - Security: 25%
      - Performance: 20%
      - Code Quality: 15%
      - Accessibility: 10%
      - Mobile: 10%
    Returns overall score, breakdown, and letter grade.
    """
    # Constrain individual scores to 0-100
    seo = max(0, min(100, seo_score))
    sec = max(0, min(100, security_score))
    perf = max(0, min(100, performance_score))
    code = max(0, min(100, code_quality_score))
    access = max(0, min(100, accessibility_score))
    mob = max(0, min(100, mobile_score))

    # Calculate weighted overall score
    raw_score = (
        (seo * 0.20) +
        (sec * 0.25) +
        (perf * 0.20) +
        (code * 0.15) +
        (access * 0.10) +
        (mob * 0.10)
    )
    
    overall_score = int(raw_score + 0.5)

    # Determine letter grade
    if overall_score >= 90:
        grade = 'A'
    elif overall_score >= 80:
        grade = 'B'
    elif overall_score >= 70:
        grade = 'C'
    elif overall_score >= 60:
        grade = 'D'
    elif overall_score >= 50:
        grade = 'E'
    else:
        grade = 'F'

    return {
        'health_score': overall_score,
        'grade': grade,
        'breakdown': {
            'seo': seo,
            'security': sec,
            'performance': perf,
            'code_quality': code,
            'accessibility': access,
            'mobile': mob
        }
    }
