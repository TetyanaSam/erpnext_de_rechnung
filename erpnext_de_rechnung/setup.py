"""Idempotent setup of the defaults this app expects.

Runs on `bench install-app erpnext_de_rechnung` and on every `bench migrate`.
Every function here is safe to re-run — it only writes if the current value
differs from the desired one.
"""

import frappe


def ensure_defaults():
    _ensure_email_queue_scheduler()
    _ensure_e_invoice_settings()
    _ensure_pdf_on_submit_settings()
    _ensure_rechnung_notification()


def _ensure_email_queue_scheduler():
    """Run email queue flush + retry every minute, not every 4 (the default
    "All" frequency). Otherwise Submit → Send delay is up to 4 min which
    makes the workflow feel broken."""
    methods = (
        "frappe.email.queue.flush",
        "frappe.email.queue.retry_sending_emails",
    )
    for method in methods:
        name = frappe.db.get_value("Scheduled Job Type", {"method": method}, "name")
        if not name:
            continue
        doc = frappe.get_doc("Scheduled Job Type", name)
        if doc.frequency != "Cron" or doc.cron_format != "* * * * *":
            doc.frequency = "Cron"
            doc.cron_format = "* * * * *"
            doc.save(ignore_permissions=True)


def _ensure_e_invoice_settings():
    """Make sure eu_einvoice warns on save but blocks on submit.
    Otherwise users can submit invalid e-invoices silently."""
    if not frappe.db.exists("DocType", "E Invoice Settings"):
        return
    s = frappe.get_single("E Invoice Settings")
    changed = False
    if s.validate_sales_invoice_on_save != 1:
        s.validate_sales_invoice_on_save = 1
        changed = True
    if s.validate_sales_invoice_on_submit != 1:
        s.validate_sales_invoice_on_submit = 1
        changed = True
    if (s.error_action_on_save or "") != "Warning Message":
        s.error_action_on_save = "Warning Message"
        changed = True
    if (s.error_action_on_submit or "") != "Error Message":
        s.error_action_on_submit = "Error Message"
        changed = True
    if changed:
        s.save(ignore_permissions=True)


def _ensure_pdf_on_submit_settings():
    """Turn on PDF generation on Submit for Sales Invoice using our print
    format. Synchronous mode so Notification sees the attached PDF."""
    if not frappe.db.exists("DocType", "PDF on Submit Settings"):
        return
    s = frappe.get_single("PDF on Submit Settings")
    changed = False

    if s.create_pdf_in_background:
        s.create_pdf_in_background = 0
        changed = True

    has_si = any(r.document_type == "Sales Invoice" for r in (s.enabled_for or []))
    if not has_si:
        s.append(
            "enabled_for",
            {
                "document_type": "Sales Invoice",
                "print_format": "DE Rechnung",
            },
        )
        changed = True
    else:
        # Make sure the row points to OUR print format
        for r in s.enabled_for:
            if r.document_type == "Sales Invoice" and r.print_format != "DE Rechnung":
                r.print_format = "DE Rechnung"
                changed = True

    if changed:
        s.save(ignore_permissions=True)


# The notification is shipped as a fixture so we don't rewrite it on every
# migrate (the user may have edited the template). But if it's completely
# missing — create from scratch.
_NOTIFICATION_NAME = "Rechnung an Kunden senden"

_MESSAGE = """{%- set contact = frappe.get_doc("Contact", doc.contact_person) if doc.contact_person else None -%}
{%- set gender = (contact.gender or "") if contact else "" -%}
{%- set last = (contact.last_name or "") if contact else "" -%}

<p>
{%- if gender == "Male" and last -%}Sehr geehrter Herr {{ last }},
{%- elif gender == "Female" and last -%}Sehr geehrte Frau {{ last }},
{%- else -%}Sehr geehrte Damen und Herren,
{%- endif -%}
</p>

<p>anbei erhalten Sie unsere Rechnung <strong>{{ doc.name }}</strong>
vom {{ frappe.utils.formatdate(doc.posting_date, "dd.MM.yyyy") }}
über einen Gesamtbetrag von
<strong>{{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</strong>.</p>

<p>Für Rückfragen stehe ich Ihnen gerne zur Verfügung.</p>

<p>Mit freundlichen Grüßen<br>
{{ frappe.db.get_value("Company", doc.company, "company_name") }}</p>

<hr>

<p>
{%- if gender == "Male" and last -%}Dear Mr. {{ last }},
{%- elif gender == "Female" and last -%}Dear Ms. {{ last }},
{%- else -%}Dear Sir or Madam,
{%- endif -%}
</p>

<p>Please find attached our invoice <strong>{{ doc.name }}</strong>
dated {{ frappe.utils.formatdate(doc.posting_date, "dd.MM.yyyy") }}
for a total amount of
<strong>{{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</strong>.</p>

<p>If you have any questions, please do not hesitate to contact us.</p>

<p>Kind regards,<br>
{{ frappe.db.get_value("Company", doc.company, "company_name") }}</p>
"""


def _ensure_rechnung_notification():
    """Create the Notification that emails the invoice PDF on submit.
    Guarded by auto_send_email check — only fires if the user ticked
    that per-invoice. Uses the already-attached PDF (attach_files=All)
    so it doesn't re-render via wkhtmltopdf."""
    if frappe.db.exists("Notification", _NOTIFICATION_NAME):
        return

    doc = frappe.new_doc("Notification")
    doc.name = _NOTIFICATION_NAME
    doc.subject = "Rechnung {{ doc.name }} / Invoice {{ doc.name }}"
    doc.document_type = "Sales Invoice"
    doc.event = "Submit"
    doc.channel = "Email"
    doc.send_system_notification = 0
    doc.attach_print = 0
    doc.attach_files = "All"
    # Enabled by default — the real on/off control is the per-invoice
    # `auto_send_email` flag (see `condition` below). Notification-level
    # enabled is just the "worker" toggle; keeping it on and gating
    # sending through the flag on each document gives the user a
    # single, obvious lever.
    doc.enabled = 1
    doc.condition = "doc.auto_send_email"
    doc.send_to_all_assignees = 0
    doc.append(
        "recipients",
        {"receiver_by_document_field": "contact_email"},
    )
    doc.message = _MESSAGE
    doc.insert(ignore_permissions=True)
