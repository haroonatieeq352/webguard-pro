"""
WebGuard Pro — Google PageSpeed Insights API Integration
Retrieves performance, accessibility, and Core Web Vitals with mock fallback.
"""

import requests
import random
import logging
from django.conf import settings
from typing import Dict, Any

logger = logging.getLogger('apps.scans')

def fetch_pagespeed_metrics(url: str) -> Dict[str, Any]:
    """
    Fetches performance, accessibility, and mobile scores from Google PageSpeed Insights.
    If no API key is set, or request fails, returns a realistic mock fallback.
    """
    api_key = getattr(settings, 'GOOGLE_PAGESPEED_API_KEY', '')
    
    if not api_key:
        logger.info("[PageSpeed] No API key configured. Using realistic mock fallback.")
        return generate_mock_pagespeed_data(url)

    # 1. Fetch via Google API
    api_url = "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed"
    
    # We query mobile strategy with multiple categories
    params = {
        'url': url,
        'key': api_key,
        'strategy': 'mobile',
        'category': ['performance', 'accessibility', 'best-practices']
    }

    try:
        response = requests.get(api_url, params=params, timeout=20)
        if response.status_code == 200:
            data = response.json()
            lh = data.get('lighthouseResult', {})
            categories = lh.get('categories', {})
            
            # Extract scores (Lighthouse scores are 0.0 to 1.0, convert to 0-100)
            perf_score = int(categories.get('performance', {}).get('score', 0.8) * 100)
            access_score = int(categories.get('accessibility', {}).get('score', 0.85) * 100)
            best_pract_score = int(categories.get('best-practices', {}).get('score', 0.8) * 100)
            
            # Extract Core Web Vitals metrics
            audits = lh.get('audits', {})
            fcp = audits.get('first-contentful-paint', {}).get('displayValue', '1.8s')
            lcp = audits.get('largest-contentful-paint', {}).get('displayValue', '2.5s')
            cls = audits.get('cumulative-layout-shift', {}).get('displayValue', '0.05')
            tbt = audits.get('total-blocking-time', {}).get('displayValue', '200ms')
            speed_index = audits.get('speed-index', {}).get('displayValue', '2.2s')
            
            logger.info(f"[PageSpeed] Fetched live PageSpeed metrics for {url}")
            return {
                'performance_score': perf_score,
                'accessibility_score': access_score,
                'best_practices_score': best_pract_score,
                'mobile_score': perf_score,  # Mobile strategy score
                'metrics': {
                    'first_contentful_paint': fcp,
                    'largest_contentful_paint': lcp,
                    'cumulative_layout_shift': cls,
                    'total_blocking_time': tbt,
                    'speed_index': speed_index
                },
                'is_mock': False
            }
        else:
            logger.warning(f"[PageSpeed] API returned status {response.status_code}. Falling back to mock data.")
    except Exception as e:
        logger.error(f"[PageSpeed] Failed to query PageSpeed API: {e}. Falling back to mock data.")

    return generate_mock_pagespeed_data(url)


def generate_mock_pagespeed_data(url: str) -> Dict[str, Any]:
    """Generates a realistic set of PageSpeed metrics based on hostname length (for consistency)."""
    # Seed based on URL hostname length to keep it consistent for the same domain
    import urllib.parse
    netloc = urllib.parse.urlparse(url).netloc or url
    seed = len(netloc)
    random.seed(seed)

    # Generate realistic base scores
    perf = random.randint(65, 94)
    access = random.randint(75, 96)
    best_pract = random.randint(70, 92)
    mobile = max(10, perf - random.randint(3, 8)) # mobile is usually slightly lower than desktop/perf base

    # Core Web Vitals
    fcp_sec = round(random.uniform(1.2, 3.2), 1)
    lcp_sec = round(fcp_sec + random.uniform(0.6, 2.1), 1)
    cls_val = round(random.uniform(0.01, 0.28), 2)
    tbt_ms = random.choice([50, 110, 180, 240, 310, 420])
    speed_idx = round(fcp_sec + random.uniform(0.3, 1.2), 1)

    # Reset random seed
    random.seed()

    return {
        'performance_score': perf,
        'accessibility_score': access,
        'best_practices_score': best_pract,
        'mobile_score': mobile,
        'metrics': {
            'first_contentful_paint': f"{fcp_sec}s",
            'largest_contentful_paint': f"{lcp_sec}s",
            'cumulative_layout_shift': f"{cls_val}",
            'total_blocking_time': f"{tbt_ms}ms",
            'speed_index': f"{speed_idx}s"
        },
        'is_mock': True
    }
