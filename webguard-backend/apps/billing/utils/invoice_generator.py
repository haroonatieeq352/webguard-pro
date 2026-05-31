import io
import logging
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"WeasyPrint could not be imported: {str(e)}. Using fallback PDF generator.")
    WEASYPRINT_AVAILABLE = False
    class HTML:
        def __init__(self, *args, **kwargs):
            pass
        def write_pdf(self, *args, **kwargs):
            pass

logger = logging.getLogger(__name__)

def generate_invoice_pdf(invoice):
    """
    Renders an HTML receipt/invoice using Jinja2, compiles it into a PDF via WeasyPrint,
    saves the PDF to the Invoice model FileField, and sends a transactional email to the user.
    """
    # 1. Compile Render Context
    payment = invoice.payment
    context = {
        'invoice': invoice,
        'payment': payment,
        'user': invoice.user,
        'tier_name': payment.subscription.subscription_tier.upper() if payment.subscription else 'PRO',
        'frontend_url': settings.FRONTEND_URL,
    }
    
    # 2. Render Jinja2 Template to HTML String
    # Note: django-jinja or base Django jinja2 backend uses 'using="jinja2"'
    html_content = render_to_string('billing/invoice.html', context, using='jinja2')
    
    # 3. Compile HTML to PDF in Memory using WeasyPrint or fallback
    if WEASYPRINT_AVAILABLE:
        pdf_io = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_io)
        pdf_data = pdf_io.getvalue()
    else:
        pdf_data = b"%PDF-1.4 Mock PDF Invoice Content because WeasyPrint is unavailable on local Windows machine"
    
    # 4. Save to Django FileField
    filename = f"invoice_{invoice.invoice_number}.pdf"
    invoice.pdf_file.save(filename, ContentFile(pdf_data), save=True)
    
    # 5. Build Transactional Email
    subject = f"Your WebGuard Pro Receipt - {invoice.invoice_number}"
    
    html_email_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Inter, Arial, sans-serif; background: #0A0E1A; color: #E2E8F0; padding: 40px;">
      <div style="max-width: 600px; margin: 0 auto; background: #111827; border-radius: 12px; padding: 40px; border: 1px solid #1E2A3A;">
        <h1 style="color: #00D4FF; margin-bottom: 8px;">WebGuard Pro</h1>
        <p style="color: #94A3B8; margin-bottom: 32px;">Scan. Detect. Protect. Rank.</p>
    
        <h2 style="color: #E2E8F0;">Payment Receipt & Invoice</h2>
        <p style="color: #94A3B8;">Hi {invoice.user.full_name or invoice.user.email},</p>
        <p style="color: #94A3B8;">
          Thank you for your payment! Your transaction was processed successfully.
          We have generated your invoice <strong style="color: #E2E8F0;">{invoice.invoice_number}</strong>
          and attached the PDF copy to this email.
        </p>
    
        <div style="background: #1F2937; border-radius: 8px; padding: 20px; margin: 24px 0; border-left: 4px solid #00D4FF;">
          <table style="width: 100%; border-collapse: collapse; color: #E2E8F0;">
            <tr>
              <td style="padding: 6px 0; color: #94A3B8;">Invoice Number:</td>
              <td style="padding: 6px 0; font-weight: 700; text-align: right;">{invoice.invoice_number}</td>
            </tr>
            <tr>
              <td style="padding: 6px 0; color: #94A3B8;">Payment Gateway:</td>
              <td style="padding: 6px 0; text-align: right; text-transform: capitalize;">{payment.gateway}</td>
            </tr>
            <tr>
              <td style="padding: 6px 0; color: #94A3B8;">Transaction ID:</td>
              <td style="padding: 6px 0; text-align: right; font-family: monospace;">{payment.transaction_id}</td>
            </tr>
            <tr>
              <td style="padding: 6px 0; color: #94A3B8; font-weight: 700;">Total Amount:</td>
              <td style="padding: 6px 0; font-weight: 700; text-align: right; color: #00D4FF;">{payment.amount} {payment.currency}</td>
            </tr>
          </table>
        </div>
    
        <p style="color: #94A3B8; font-size: 14px;">
          You can also download this invoice from your WebGuard dashboard anytime.
        </p>
    
        <hr style="border: none; border-top: 1px solid #1E2A3A; margin: 32px 0;">
        <p style="color: #475569; font-size: 12px; margin-top: 24px;">
          &copy; 2025 WebGuard Pro. All rights reserved.
        </p>
      </div>
    </body>
    </html>
    """
    
    plain_email_body = strip_tags(html_email_body)
    
    # 6. Send Email with PDF Attachment
    try:
        email = EmailMessage(
            subject=subject,
            body=plain_email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invoice.user.email]
        )
        email.attach(filename, pdf_data, 'application/pdf')
        # Check if html alternative can be added
        email.extra_headers = {'Content-Type': 'text/html'} # Or send as multipart
        # Better: use EmailMessage's ability to send HTML content or attach HTML
        # In Django, to send HTML body in EmailMessage:
        email.content_subtype = 'html'
        email.body = html_email_body
        
        email.send(fail_silently=False)
        logger.info(f"Successfully emailed invoice {invoice.invoice_number} to {invoice.user.email}")
    except Exception as e:
        logger.error(f"Failed to email invoice {invoice.invoice_number} to {invoice.user.email}: {str(e)}", exc_info=True)
        # We don't raise here, so that we don't break payment flows if mail server has issues
        
    return invoice
