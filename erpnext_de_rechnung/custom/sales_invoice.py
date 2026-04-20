import frappe


# Desired visibility of Sales Invoice Item child-table columns.
# Keys are fieldnames on Sales Invoice Item; values are 1 (visible) or 0 (hidden).
# Re-asserted by ensure_invoice_item_columns() on every `bench migrate`.
INVOICE_ITEM_COLUMN_VISIBILITY = {
    "item_code": 1,
    "description": 1,
    "warehouse": 0,
}


def ensure_invoice_item_columns():
    """Idempotently enforce Property Setter values for Sales Invoice Item columns.

    Frappe fixtures create missing Property Setters but won't override values
    that a user later changed via Customize Form. We reapply the intended
    state on every migrate so the form layout stays predictable.
    """
    for fieldname, value in INVOICE_ITEM_COLUMN_VISIBILITY.items():
        name = f"Sales Invoice Item-{fieldname}-in_list_view"
        if frappe.db.exists("Property Setter", name):
            frappe.db.set_value("Property Setter", name, {
                "value": str(value),
                "module": "ERPNext DE Rechnung",
            })
        else:
            frappe.get_doc({
                "doctype": "Property Setter",
                "name": name,
                "doctype_or_field": "DocField",
                "doc_type": "Sales Invoice Item",
                "field_name": fieldname,
                "property": "in_list_view",
                "property_type": "Check",
                "value": str(value),
                "module": "ERPNext DE Rechnung",
            }).insert(ignore_permissions=True)
    frappe.clear_cache(doctype="Sales Invoice Item")
    frappe.db.commit()


GERMAN_MONTHS = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April",
    5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
    9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
}

def before_validate(doc, method=None):
    # On a freshly created (or duplicated) invoice, copy the auto-send flag
    # default from the Company so the user doesn't have to remember to set it
    # every time. They can still toggle it per-invoice before Submit.
    if doc.is_new() and not doc.get("auto_send_email"):
        try:
            company = frappe.get_cached_doc("Company", doc.company)
            if company.get("default_auto_send_email"):
                doc.auto_send_email = 1
        except Exception:
            pass

    # A duplicated Sales Invoice keeps the old payment_schedule rows, so the
    # due_date doesn't update to reflect the new posting_date. Clear both
    # when we detect a mismatch; ERPNext's set_payment_schedule() later in
    # validate() will rebuild them from payment_terms_template + new dates.
    try:
        from frappe.utils import getdate
        if doc.posting_date and doc.payment_terms_template and doc.get("payment_schedule"):
            ps0 = doc.payment_schedule[0]
            # If the first schedule entry's due_date was computed against an
            # old posting_date, force recalc.
            if ps0.due_date and ps0.get("credit_days"):
                expected = getdate(doc.posting_date)
                # ERPNext stores credit_days on each schedule row; we can
                # re-derive the due_date from posting_date + credit_days to
                # detect drift. If different, wipe and rebuild.
                from datetime import timedelta
                should_be = expected + timedelta(days=int(ps0.credit_days or 0))
                if getdate(ps0.due_date) != should_be:
                    doc.set("payment_schedule", [])
                    doc.due_date = None
    except Exception:
        pass

    # Auto-fill payment terms template from customer or company defaults so new
    # invoices don't need manual selection. Leave explicit due_date alone — if
    # the user typed a due date on the form, ERPNext may still recalculate it
    # from the payment schedule, which is standard behavior.
    if doc.payment_terms_template:
        return
    try:
        customer = frappe.get_cached_doc("Customer", doc.customer)
        if customer.payment_terms:
            doc.payment_terms_template = customer.payment_terms
            return
    except Exception:
        pass
    try:
        company = frappe.get_cached_doc("Company", doc.company)
        if company.payment_terms:
            doc.payment_terms_template = company.payment_terms
    except Exception:
        pass

def on_submit_summary(doc, method=None):
    """Produce a durable, user-visible summary of what happened at Submit:
    whether the PDF got attached, and whether the auto-send email was
    enqueued. Written as an Info-Comment on the document so it's always
    visible in Activity (msgprint can get lost in submit-response race
    conditions on mobile)."""

    # This hook runs BEFORE pdf_on_submit (which attaches the PDF) and
    # BEFORE Notification (which queues the email) because Frappe runs
    # doctype-specific hooks first, then wildcard ones. Defer the actual
    # status check + comment to after_commit, when those sibling hooks
    # have finished writing to the DB.
    frappe.db.after_commit.add(lambda: _write_submit_comment(doc.name))


def _write_submit_comment(name):
    try:
        pdfs = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Sales Invoice",
                "attached_to_name": name,
                "file_name": ["like", "%.pdf"],
            },
            fields=["file_name"],
        )

        doc = frappe.db.get_value(
            "Sales Invoice", name,
            ["auto_send_email", "contact_email"], as_dict=True,
        )

        lines = []
        if pdfs:
            lines.append(f"📎 PDF angehängt: <b>{pdfs[0].file_name}</b>")
        else:
            lines.append("⚠️ Kein PDF angehängt.")

        if doc.auto_send_email:
            queued = frappe.db.count(
                "Email Queue",
                {"reference_doctype": "Sales Invoice", "reference_name": name},
            )
            if queued:
                lines.append(
                    f"✉️ E-Mail an <b>{doc.contact_email or '?'}</b> in "
                    f"Warteschlange gestellt — Versand innerhalb von ~1 Minute."
                )
            else:
                lines.append(
                    "⚠️ Auto-Versand ist aktiviert, aber keine "
                    "E-Mail-Queue-Eintragung gefunden."
                )
        else:
            lines.append(
                "☐ Auto-Versand ausgeschaltet. Manueller Versand: Menu "
                "\"...\" → Email."
            )

        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Sales Invoice",
            "reference_name": name,
            "content": "<br>".join(lines),
        }).insert(ignore_permissions=True)

        # Also push a realtime toast so the user sees it without
        # refreshing the page.
        frappe.publish_realtime(
            "msgprint",
            {
                "message": "<br>".join(lines),
                "indicator": "green",
                "alert": 1,
            },
            user=frappe.session.user,
        )
    except Exception:
        # Never block the request path on summary-comment issues.
        frappe.log_error(frappe.get_traceback(), "on_submit_summary")


def set_leistungszeitraum_anzeige(doc, method=None):
    typ = doc.get("leistungszeitraum_typ")
    if typ == "Datumsbereich":
        von = doc.get("leistungszeitraum_von")
        bis = doc.get("leistungszeitraum_bis")
        if von and bis:
            from frappe.utils import formatdate
            doc.leistungszeitraum_anzeige = f"{formatdate(von, 'dd.MM.yyyy')} \u2013 {formatdate(bis, 'dd.MM.yyyy')}"
        else:
            doc.leistungszeitraum_anzeige = ""
    elif typ == "Monat/Jahr":
        von = doc.get("leistungszeitraum_von")
        doc.leistungszeitraum_bis = None
        if von:
            from frappe.utils import getdate
            d = getdate(von)
            doc.leistungszeitraum_anzeige = f"{GERMAN_MONTHS[d.month]} {d.year}"
        else:
            doc.leistungszeitraum_anzeige = ""
    elif typ == "Datum":
        von = doc.get("leistungszeitraum_von")
        doc.leistungszeitraum_bis = None
        if von:
            from frappe.utils import formatdate
            doc.leistungszeitraum_anzeige = formatdate(von, 'dd.MM.yyyy')
        else:
            doc.leistungszeitraum_anzeige = ""
    else:
        doc.leistungszeitraum_anzeige = ""
