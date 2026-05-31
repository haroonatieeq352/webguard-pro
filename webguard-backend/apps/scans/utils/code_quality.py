"""
WebGuard Pro — Code Quality Analyzer
Audits HTML structure for inline styles, script count, minification, deprecated tags, and SRI.
"""

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Dict, Any

def analyze_code_quality(html_content: str, base_url: str) -> Dict[str, Any]:
    """
    Analyzes page HTML for code quality issues.
    Returns:
        Dict containing:
            - score: int (0 to 100)
            - minification: Dict details
            - inline_styles: Dict details
            - inline_scripts: Dict details
            - deprecated_tags: Dict details
            - sri_check: Dict details
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    code_score = 0
    report = {}

    # ── 1. Minification check (25 points max) ────────────────
    # Check if external stylesheets or scripts are minified (.min.js / .min.css)
    scripts = soup.find_all('script', src=True)
    stylesheets = soup.find_all('link', rel=lambda x: x and 'stylesheet' in x.lower())
    
    total_assets = 0
    unminified_assets = []
    
    for s in scripts:
        src = s.get('src', '')
        if src:
            total_assets += 1
            if '.min.' not in src.lower() and 'node_modules' not in src.lower():
                unminified_assets.append(src)
                
    for css in stylesheets:
        href = css.get('href', '')
        if href:
            total_assets += 1
            if '.min.' not in href.lower():
                unminified_assets.append(href)

    min_score = 25
    min_feedback = ""
    
    if total_assets > 0:
        unminified_count = len(unminified_assets)
        if unminified_count == 0:
            min_feedback = "All external JavaScript and CSS files are minified."
        else:
            pct = (unminified_count / total_assets) * 100
            deduction = int(25 * (unminified_count / total_assets))
            min_score = max(0, 25 - deduction)
            min_feedback = f"{unminified_count} out of {total_assets} external assets ({pct:.1f}%) appear to be unminified (missing '.min.' extension)."
    else:
        min_feedback = "No external stylesheets or scripts found on this page."

    code_score += min_score
    report['minification'] = {
        'total_assets': total_assets,
        'unminified_count': len(unminified_assets),
        'unminified_list': unminified_assets[:10],  # limit list size
        'score': min_score,
        'passed': len(unminified_assets) == 0,
        'feedback': min_feedback
    }

    # ── 2. Inline Styles check (25 points max) ───────────────
    # Count elements with inline style attribute
    styled_elements = soup.find_all(style=True)
    inline_styles_count = len(styled_elements)
    
    styles_score = 25
    styles_feedback = ""
    
    if inline_styles_count == 0:
        styles_feedback = "Zero inline style attributes found. Excellent separation of concerns."
    else:
        # Deduct 2 points per inline style up to 25
        deduction = inline_styles_count * 2
        styles_score = max(0, 25 - deduction)
        styles_feedback = f"Found {inline_styles_count} elements using inline style attributes. Move styles to an external CSS stylesheet."

    code_score += styles_score
    report['inline_styles'] = {
        'count': inline_styles_count,
        'score': styles_score,
        'passed': inline_styles_count == 0,
        'feedback': styles_feedback
    }

    # ── 3. Inline Scripts check (20 points max) ──────────────
    # Count script tags without src attribute
    inline_scripts = soup.find_all('script', src=False)
    # Filter out JSON-LD schemas or other text types
    actual_inline_scripts = [
        s for s in inline_scripts 
        if not s.get('type') or 'javascript' in s.get('type', '').lower()
    ]
    inline_script_count = len(actual_inline_scripts)
    
    scripts_score = 20
    scripts_feedback = ""

    if inline_script_count == 0:
        scripts_feedback = "Zero inline JavaScript blocks found. Good CSP security compatibility."
    else:
        # Deduct 4 points per inline script up to 20
        deduction = inline_script_count * 4
        scripts_score = max(0, 20 - deduction)
        scripts_feedback = f"Found {inline_script_count} inline JavaScript blocks. We recommend moving script logic to external JS files."

    code_score += scripts_score
    report['inline_scripts'] = {
        'count': inline_script_count,
        'score': scripts_score,
        'passed': inline_script_count == 0,
        'feedback': scripts_feedback
    }

    # ── 4. Deprecated HTML tags check (15 points max) ────────
    deprecated_tags = ['font', 'center', 'marquee', 'big', 'dir', 'strike', 'tt', 'acronym', 'applet', 'basefont', 'frameset', 'frame', 'noframes', 'isindex']
    found_deprecated = {}
    
    for tag_name in deprecated_tags:
        found = soup.find_all(tag_name)
        if found:
            found_deprecated[tag_name] = len(found)

    dep_score = 15
    dep_feedback = ""

    if not found_deprecated:
        dep_feedback = "No deprecated HTML tags found. Code conforms to HTML5 standards."
    else:
        # Deduct 5 points per unique deprecated tag type found up to 15
        deduction = len(found_deprecated) * 5
        dep_score = max(0, 15 - deduction)
        list_str = ", ".join([f"<{t}> ({c} times)" for t, c in found_deprecated.items()])
        dep_feedback = f"Deprecated HTML tags found: {list_str}. Avoid using deprecated presentation tags."

    code_score += dep_score
    report['deprecated_tags'] = {
        'found': found_deprecated,
        'score': dep_score,
        'passed': len(found_deprecated) == 0,
        'feedback': dep_feedback
    }

    # ── 5. Subresource Integrity (SRI) check (15 points max) ─
    # Check external third-party CDN scripts for integrity attribute
    base_netloc = urlparse(base_url).netloc
    cdn_scripts = []
    missing_sri = []

    for s in scripts:
        src = s.get('src', '')
        if src:
            parsed_src = urlparse(src)
            # It's an external third-party script if scheme is set and domain doesn't match base_netloc
            if parsed_src.netloc and parsed_src.netloc != base_netloc:
                cdn_scripts.append(src)
                if not s.get('integrity'):
                    missing_sri.append(src)

    sri_score = 15
    sri_feedback = ""

    if len(cdn_scripts) > 0:
        missing_count = len(missing_sri)
        if missing_count == 0:
            sri_feedback = "All external third-party CDN script tags implement Subresource Integrity (SRI)."
        else:
            pct = (missing_count / len(cdn_scripts)) * 100
            deduction = int(15 * (missing_count / len(cdn_scripts)))
            sri_score = max(0, 15 - deduction)
            sri_feedback = f"{missing_count} out of {len(cdn_scripts)} external CDN scripts ({pct:.1f}%) are missing the 'integrity' attribute. SRI prevents CDN spoofing attacks."
    else:
        sri_feedback = "No external third-party CDN scripts detected on this page."

    code_score += sri_score
    report['sri_check'] = {
        'total_cdn_scripts': len(cdn_scripts),
        'missing_sri_count': len(missing_sri),
        'missing_sri_list': missing_sri[:10],
        'score': sri_score,
        'passed': len(missing_sri) == 0,
        'feedback': sri_feedback
    }

    return {
        'score': code_score,
        'report': report
    }
