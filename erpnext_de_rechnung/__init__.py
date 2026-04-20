__version__ = "0.0.1"

# Monkey-patch Frappe's PDF option preparer to always tell wkhtmltopdf to
# ignore resource-load errors (images, fonts, CSS imports). Without this,
# any transient network hiccup — or a broken image in a letterhead — makes
# wkhtmltopdf exit with code 1 and the whole PDF generation fails, which
# then breaks the Notification-with-attached-PDF flow on Submit.
#
# Frappe already has the fix in `frappe.utils.pdf.prepare_options`, but the
# line is commented out by default. We re-enable it at import time so every
# PDF request (pdf_on_submit, Notification, manual PDF button) uses the
# resilient option set.
try:
    from frappe.utils import pdf as _frappe_pdf

    if not getattr(_frappe_pdf, "_erpnext_de_rechnung_load_error_patched", False):
        _orig_prepare_options = _frappe_pdf.prepare_options

        def _prepare_options_resilient(html, options):
            html, options = _orig_prepare_options(html, options)
            options.setdefault("load-error-handling", "ignore")
            options.setdefault("load-media-error-handling", "ignore")
            return html, options

        _frappe_pdf.prepare_options = _prepare_options_resilient
        _frappe_pdf._erpnext_de_rechnung_load_error_patched = True
except Exception:
    # Don't ever block app import on a patch failure — worst case we fall
    # back to Frappe's default (stricter) behaviour.
    pass
