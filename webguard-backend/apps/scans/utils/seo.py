"""
WebGuard Pro — SEO Analyzer
Audits metadata, structure, and configuration using BeautifulSoup.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, Any

def analyze_seo(html_content: str, base_url: str) -> Dict[str, Any]:
    """
    Analyzes page HTML and checks robots.txt/sitemap.xml on the target site.
    Returns:
        Dict containing:
            - score: int (0 to 100)
            - title: Dict details
            - meta_description: Dict details
            - h1_tags: Dict details
            - image_alts: Dict details
            - og_tags: Dict details
            - sitemap_robots: Dict details
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    seo_score = 0
    report = {}

    # 1. Title Audit (20 points max)
    title_tag = soup.find('title')
    title_text = title_tag.get_text().strip() if title_tag else None
    title_score = 0
    title_feedback = ""
    
    if not title_text:
        title_feedback = "Missing title tag. This is critical for search engine results indexing."
    else:
        title_len = len(title_text)
        if 10 <= title_len <= 60:
            title_score = 20
            title_feedback = f"Perfect title length ({title_len} characters) and tag presence."
        else:
            title_score = 10
            title_feedback = f"Title is set but length ({title_len} characters) is outside the optimal range of 10 to 60 characters."

    seo_score += title_score
    report['title'] = {
        'value': title_text,
        'score': title_score,
        'passed': title_score == 20,
        'feedback': title_feedback
    }

    # 2. Meta Description Audit (20 points max)
    meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
    meta_desc_text = meta_desc_tag.get('content', '').strip() if meta_desc_tag else None
    meta_desc_score = 0
    meta_desc_feedback = ""

    if not meta_desc_text:
        meta_desc_feedback = "Missing meta description. Search engines use this for search snippet descriptions."
    else:
        desc_len = len(meta_desc_text)
        if 50 <= desc_len <= 160:
            meta_desc_score = 20
            meta_desc_feedback = f"Perfect description length ({desc_len} characters)."
        else:
            meta_desc_score = 10
            meta_desc_feedback = f"Meta description is present but length ({desc_len} characters) is outside the optimal range of 50 to 160 characters."

    seo_score += meta_desc_score
    report['meta_description'] = {
        'value': meta_desc_text,
        'score': meta_desc_score,
        'passed': meta_desc_score == 20,
        'feedback': meta_desc_feedback
    }

    # 3. H1 Heading Audit (20 points max)
    h1_tags = soup.find_all('h1')
    h1_count = len(h1_tags)
    h1_score = 0
    h1_feedback = ""

    if h1_count == 0:
        h1_feedback = "No H1 headings found. Every page should have exactly one main H1 heading."
    elif h1_count == 1:
        h1_score = 20
        h1_feedback = "Exactly one H1 heading found. Perfect structure."
    else:
        h1_score = 10
        h1_feedback = f"Multiple H1 headings ({h1_count}) found. We recommend using only one H1 heading per page for SEO hierarchy."

    seo_score += h1_score
    report['h1_tags'] = {
        'count': h1_count,
        'headings': [h.get_text().strip() for h in h1_tags],
        'score': h1_score,
        'passed': h1_score == 20,
        'feedback': h1_feedback
    }

    # 4. Image Alt Attributes Audit (15 points max)
    images = soup.find_all('img')
    img_count = len(images)
    missing_alts = 0
    
    for img in images:
        alt = img.get('alt')
        if alt is None or alt.strip() == "":
            missing_alts += 1

    img_score = 15
    img_feedback = ""

    if img_count > 0:
        missing_percentage = (missing_alts / img_count) * 100
        if missing_alts == 0:
            img_feedback = "All image alt tags are present."
        else:
            deduction = int(15 * (missing_alts / img_count))
            img_score = max(0, 15 - deduction)
            img_feedback = f"{missing_alts} out of {img_count} images ({missing_percentage:.1f}%) are missing alt descriptive text."
    else:
        img_feedback = "No images found on this page."

    seo_score += img_score
    report['image_alts'] = {
        'total_images': img_count,
        'missing_alts': missing_alts,
        'score': img_score,
        'passed': missing_alts == 0,
        'feedback': img_feedback
    }

    # 5. Open Graph (OG) Tags Audit (15 points max)
    og_properties = ['og:title', 'og:description', 'og:image']
    found_og = []
    
    for prop in og_properties:
        tag = soup.find('meta', attrs={'property': prop})
        if tag and tag.get('content', '').strip():
            found_og.append(prop)

    og_score = len(found_og) * 5
    og_feedback = f"Found {len(found_og)} of {len(og_properties)} standard Open Graph tags: {', '.join(found_og)}."
    if len(found_og) < len(og_properties):
        missing_og = list(set(og_properties) - set(found_og))
        og_feedback += f" Missing: {', '.join(missing_og)} for social media previews."

    seo_score += og_score
    report['og_tags'] = {
        'found': found_og,
        'score': og_score,
        'passed': len(found_og) == len(og_properties),
        'feedback': og_feedback
    }

    # 6. robots.txt & sitemap.xml Audit (10 points max)
    # Check at the root of the domain
    parsed_url = urlparse(base_url)
    root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    robots_url = urljoin(root_url, '/robots.txt')
    sitemap_url = urljoin(root_url, '/sitemap.xml')

    robots_present = False
    sitemap_present = False
    
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 WebGuardPro/1.0'
    headers = {'User-Agent': user_agent}

    # Check robots.txt
    try:
        r = requests.get(robots_url, headers=headers, timeout=5)
        robots_present = (r.status_code == 200)
    except Exception:
        pass

    # Check sitemap.xml
    try:
        r = requests.get(sitemap_url, headers=headers, timeout=5)
        sitemap_present = (r.status_code == 200)
    except Exception:
        pass

    site_score = 0
    if robots_present:
        site_score += 5
    if sitemap_present:
        site_score += 5

    seo_score += site_score
    site_feedback = ""
    if robots_present and sitemap_present:
        site_feedback = "Both robots.txt and sitemap.xml were detected successfully at the root domain."
    elif robots_present:
        site_feedback = "robots.txt detected, but sitemap.xml was missing at the root."
    elif sitemap_present:
        site_feedback = "sitemap.xml detected, but robots.txt was missing at the root."
    else:
        site_feedback = "Both robots.txt and sitemap.xml are missing. These are key configurations for search crawlability."

    report['sitemap_robots'] = {
        'robots_present': robots_present,
        'sitemap_present': sitemap_present,
        'score': site_score,
        'passed': robots_present and sitemap_present,
        'feedback': site_feedback
    }

    return {
        'score': seo_score,
        'report': report
    }
