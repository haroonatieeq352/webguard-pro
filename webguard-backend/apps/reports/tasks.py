import io
import hmac
import hashlib
import logging
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from django.template.loader import render_to_string
from celery import shared_task

from apps.scans.models import ScanRequest, ScanResult, Vulnerability
from apps.reports.models import ScanReport

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    logging.getLogger(__name__).warning(f"WeasyPrint could not be imported in reports tasks: {str(e)}. Using fallback PDF generator.")
    WEASYPRINT_AVAILABLE = False
    class HTML:
        def __init__(self, *args, **kwargs):
            pass
        def write_pdf(self, *args, **kwargs):
            pass

logger = logging.getLogger('apps.reports')


def generate_reportlab_pdf(scan_request, scan_result, vulnerabilities, grade, risk_level, report_hash):
    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.graphics.shapes import Drawing, Rect, String, Line
    from django.utils import timezone

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#00b4d8'),
        alignment=1,
        spaceAfter=30
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=15,
        spaceAfter=15,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f1f5f9'),
        borderColor=colors.HexColor('#cbd5e1'),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=10
    )

    story = []

    # ── COVER PAGE ──
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("WebGuard Pro", title_style))
    story.append(Paragraph("SCAN. DETECT. PROTECT.", subtitle_style))
    
    # Divider line
    d_line = Drawing(doc.width, 10)
    d_line.add(Rect(doc.width/2 - 75, 4, 150, 4, fillColor=colors.HexColor('#00b4d8'), strokeColor=None))
    story.append(d_line)
    story.append(Spacer(1, 0.5 * inch))

    story.append(Paragraph("Security & Performance Audit", ParagraphStyle('SubText', parent=body_style, alignment=1, fontSize=12, textColor=colors.HexColor('#64748b'))))
    story.append(Paragraph(f"<b>{scan_request.url}</b>", ParagraphStyle('TargetURL', parent=body_style, alignment=1, fontSize=16, leading=20, textColor=colors.HexColor('#334155'))))
    story.append(Spacer(1, 0.3 * inch))

    # Health score card table
    score_data = [
        [Paragraph(f"<font size=44 color='#00b4d8'><b>{scan_result.health_score}%</b></font>", ParagraphStyle('ScoreVal', parent=body_style, alignment=1))],
        [Paragraph(f"<b>OVERALL HEALTH GRADE: {grade}</b>", ParagraphStyle('ScoreLabel', parent=body_style, alignment=1, fontSize=11, textColor=colors.HexColor('#64748b')))]
    ]
    t_score = Table(score_data, colWidths=[200])
    t_score.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('TOPPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(t_score)
    story.append(Spacer(1, 1 * inch))

    # Meta metadata
    date_str = (scan_request.completed_at or timezone.now()).strftime('%B %d, %Y')
    meta_text = f"<b>Report Date:</b> {date_str}<br/><b>Scan Type:</b> {scan_request.scan_type.capitalize()} Scan<br/><b>Report ID:</b> {scan_request.id}"
    story.append(Paragraph(meta_text, ParagraphStyle('MetaText', parent=body_style, alignment=1, fontSize=10, textColor=colors.HexColor('#64748b'))))
    
    story.append(PageBreak())

    # ── EXECUTIVE SUMMARY ──
    story.append(Paragraph("Executive Summary", h1_style))
    
    summary_text = (
        f"On <b>{date_str}</b>, WebGuard Pro conducted an automated website security, search engine optimization (SEO), "
        f"code quality, and performance audit on the target domain: <b>{scan_request.url}</b>.<br/><br/>"
        f"Based on our scoring criteria, the target site received an overall health rating of <b>{scan_result.health_score}%</b>, "
        f"achieving a grade of <b>{grade}</b>.<br/><br/>"
        f"The overall risk rating is classified as <b>{risk_level.upper()} RISK</b>."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Category Scoring Breakdown", h2_style))
    
    # Table showing category scores
    cat_data = [
        [
            Paragraph("<b>Category</b>", body_style), 
            Paragraph("<b>Score</b>", body_style), 
            Paragraph("<b>Weight</b>", body_style),
            Paragraph("<b>Rating Bar</b>", body_style)
        ],
        [Paragraph("Security", body_style), Paragraph(f"{scan_result.security_score}/100", body_style), Paragraph("25%", body_style), ""],
        [Paragraph("SEO Optimization", body_style), Paragraph(f"{scan_result.seo_score}/100", body_style), Paragraph("20%", body_style), ""],
        [Paragraph("Performance", body_style), Paragraph(f"{scan_result.performance_score}/100", body_style), Paragraph("20%", body_style), ""],
        [Paragraph("Code Quality", body_style), Paragraph(f"{scan_result.code_quality_score}/100", body_style), Paragraph("15%", body_style), ""],
        [Paragraph("Accessibility", body_style), Paragraph(f"{scan_result.accessibility_score}/100", body_style), Paragraph("10%", body_style), ""],
        [Paragraph("Mobile Usability", body_style), Paragraph(f"{scan_result.mobile_score}/100", body_style), Paragraph("10%", body_style), ""],
    ]
    
    for idx, score in enumerate([
        scan_result.security_score,
        scan_result.seo_score,
        scan_result.performance_score,
        scan_result.code_quality_score,
        scan_result.accessibility_score,
        scan_result.mobile_score
    ], start=1):
        bar_draw = Drawing(150, 12)
        # Background rect
        bar_draw.add(Rect(0, 2, 150, 8, fillColor=colors.HexColor('#e2e8f0'), strokeColor=None))
        # Fill rect
        fill_color = colors.HexColor('#2ed573') if score >= 80 else (colors.HexColor('#ffa502') if score >= 50 else colors.HexColor('#ff4757'))
        width_fill = (score / 100.0) * 150
        if width_fill > 0:
            bar_draw.add(Rect(0, 2, width_fill, 8, fillColor=fill_color, strokeColor=None))
        cat_data[idx][3] = bar_draw

    t_cat = Table(cat_data, colWidths=[150, 70, 70, 160])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_cat)
    story.append(Spacer(1, 20))

    # ── DETAILED AUDIT FINDINGS ──
    story.append(PageBreak())
    story.append(Paragraph("Detailed Audit Findings", h1_style))
    
    if not vulnerabilities:
        story.append(Paragraph("Congratulations! No major security vulnerabilities or header misconfigurations were identified during this scan.", body_style))
    else:
        for vuln in vulnerabilities:
            vuln_elements = []
            
            # Header line: Title + Severity badge
            v_title = Paragraph(f"<b>{vuln.title}</b>", ParagraphStyle('VT', parent=body_style, fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#0f172a')))
            v_sev_color = '#ff4757' if vuln.severity.lower() in ['critical', 'high'] else ('#ffa502' if vuln.severity.lower() == 'medium' else '#2ed573')
            v_sev = Paragraph(f"<font color='{v_sev_color}'><b>{vuln.severity.upper()}</b></font>", ParagraphStyle('VS', parent=body_style, alignment=2, fontSize=9, fontName='Helvetica-Bold'))
            
            t_header = Table([[v_title, v_sev]], colWidths=[380, 70])
            t_header.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ]))
            vuln_elements.append(t_header)
            vuln_elements.append(Spacer(1, 6))
            
            # Category
            vuln_elements.append(Paragraph(f"<b>Category:</b> {vuln.owasp_category or 'General Vulnerability'}", ParagraphStyle('VCat', parent=body_style, fontSize=9, textColor=colors.HexColor('#64748b'))))
            vuln_elements.append(Spacer(1, 4))
            
            # Description
            vuln_elements.append(Paragraph(f"<b>Description:</b> {vuln.description}", body_style))
            vuln_elements.append(Spacer(1, 4))
            
            # Evidence
            if vuln.evidence:
                vuln_elements.append(Paragraph("<b>Evidence:</b>", ParagraphStyle('VEvL', parent=body_style, fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#475569'))))
                vuln_elements.append(Paragraph(vuln.evidence, code_style))
                vuln_elements.append(Spacer(1, 4))
                
            # Remediation
            if vuln.remediation:
                vuln_elements.append(Paragraph(f"<b>Remediation / Solution:</b><br/>{vuln.remediation}", ParagraphStyle('VRem', parent=body_style, fontName='Helvetica', textColor=colors.HexColor('#1e293b'))))
            
            vuln_elements.append(Spacer(1, 20))
            story.append(KeepTogether(vuln_elements))

    # ── VERIFICATION BOX ──
    story.append(Spacer(1, 20))
    verify_elements = []
    verify_elements.append(Paragraph("<b>Verification of Report Authenticity</b>", ParagraphStyle('VTitle', parent=body_style, fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#0f172a'))))
    
    from django.conf import settings as django_settings
    verify_text = (
        f"To verify that this report was officially generated by WebGuard Pro and has not been altered or falsified, "
        f"you can upload this document or check its integrity signature hash on our verification portal at:<br/>"
        f"<font color='#00b4d8'><b>{django_settings.FRONTEND_URL}/reports/verify/{report_hash}/</b></font><br/><br/>"
        f"<b>Signature:</b> {report_hash}"
    )
    verify_elements.append(Paragraph(verify_text, ParagraphStyle('VText', parent=body_style, fontSize=9, textColor=colors.HexColor('#475569'))))
    
    t_verify = Table([[verify_elements]], colWidths=[450])
    t_verify.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#cbd5e1')),
        ('LINESTYLE', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 15),
        ('RIGHTPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(KeepTogether([t_verify]))

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


@shared_task(
    bind=True,
    name='apps.reports.tasks.compile_scan_report',
    max_retries=2,
    default_retry_delay=60
)
def compile_scan_report(self, scan_request_id: str):
    """
    Celery task that compiles the ScanResult into a professional PDF document,
    calculates an HMAC-SHA256 signature to guarantee authenticity, and stores the ScanReport record.
    """
    try:
        scan_request = ScanRequest.objects.get(id=scan_request_id)
        scan_result = ScanResult.objects.get(scan_request=scan_request)
    except (ScanRequest.DoesNotExist, ScanResult.DoesNotExist) as e:
        logger.error(f"[compile_scan_report] ScanRequest/Result {scan_request_id} not found: {e}")
        return {'status': 'skipped', 'reason': 'not_found'}

    logger.info(f"[compile_scan_report] Compiling report for {scan_request.url}")

    # 1. Fetch Vulnerabilities
    vulns = list(Vulnerability.objects.filter(scan_request=scan_request))

    # 2. Determine Risk Level
    # Classify risk based on severity of any vulnerabilities found
    risk_level = 'low'
    severities = [v.severity.lower() for v in vulns]
    if 'critical' in severities:
        risk_level = 'critical'
    elif 'high' in severities:
        risk_level = 'high'
    elif 'medium' in severities:
        risk_level = 'medium'

    # 3. Calculate Grade (A-F) based on health score
    health = scan_result.health_score
    if health >= 90:
        grade = 'A'
    elif health >= 80:
        grade = 'B'
    elif health >= 70:
        grade = 'C'
    elif health >= 60:
        grade = 'D'
    else:
        grade = 'F'

    # 4. Generate Cryptographic Hash Signature (HMAC-SHA256) of scan metadata
    # This cryptographically links the scan outcome to prevent tampering
    completed_time_str = scan_request.completed_at.isoformat() if scan_request.completed_at else timezone.now().isoformat()
    msg = f"{scan_request.id}:{health}:{completed_time_str}"
    
    hmac_secret = getattr(settings, 'REPORT_HMAC_SECRET', 'dev-report-hmac-secret')
    report_hash = hmac.new(
        hmac_secret.encode('utf-8'),
        msg.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # 5. Render Jinja2 HTML Template
    context = {
        'scan_request': scan_request,
        'result': scan_result,
        'vulnerabilities': vulns,
        'grade': grade,
        'risk_level': risk_level,
        'created_at': scan_request.completed_at or timezone.now(),
        'report_id': str(scan_request.id),
        'report_hash': report_hash,
        'frontend_url': settings.FRONTEND_URL,
    }
    
    html_content = render_to_string('reports/report.html', context, using='jinja2')

    # 6. Compile HTML to PDF via WeasyPrint or Native ReportLab Fallback
    if WEASYPRINT_AVAILABLE:
        try:
            pdf_io = io.BytesIO()
            HTML(string=html_content).write_pdf(pdf_io)
            pdf_data = pdf_io.getvalue()
        except Exception as e:
            logger.error(f"[compile_scan_report] WeasyPrint rendering failed: {str(e)}. Falling back to ReportLab.")
            pdf_data = generate_reportlab_pdf(scan_request, scan_result, vulns, grade, risk_level, report_hash)
    else:
        logger.info("[compile_scan_report] WeasyPrint not available on this environment. Utilizing ReportLab native fallback.")
        pdf_data = generate_reportlab_pdf(scan_request, scan_result, vulns, grade, risk_level, report_hash)

    # 7. Save ScanReport object (creates or updates)
    report, created = ScanReport.objects.get_or_create(
        scan_request=scan_request,
        defaults={'report_hash': report_hash}
    )
    
    if not created:
        report.report_hash = report_hash
        report.save(update_fields=['report_hash'])

    # Save the PDF file to FileField
    filename = f"report_{scan_request.id}.pdf"
    report.pdf_file.save(filename, ContentFile(pdf_data), save=True)

    logger.info(f"[compile_scan_report] Successfully compiled and saved report for {scan_request.url} (Hash: {report_hash})")
    return {'status': 'completed', 'report_id': str(report.id), 'hash': report_hash}
