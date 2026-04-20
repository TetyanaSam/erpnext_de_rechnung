import frappe


def no_cache_pdf(response=None, request=None):
    """Force browsers to always fetch a freshly generated PDF.

    Mobile browsers (iOS Safari, Android Chrome) and PDF viewers cache PDF
    responses aggressively by URL. When a Sales Invoice is edited and
    re-rendered, the user still sees the previously cached PDF until the
    browser cache is manually cleared. We set explicit no-store headers on
    PDF responses so every tap on the PDF button delivers the current file.
    """
    if response is None or request is None:
        return
    try:
        path = (request.path or "") if hasattr(request, "path") else ""
        content_type = response.headers.get("Content-Type", "") if hasattr(response, "headers") else ""
        is_pdf_endpoint = "download_pdf" in path or "print" in path
        is_pdf_payload = "pdf" in content_type.lower()
        if is_pdf_endpoint or is_pdf_payload:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
    except Exception:
        frappe.log_error(frappe.get_traceback(), "erpnext_de_rechnung.no_cache_pdf")
