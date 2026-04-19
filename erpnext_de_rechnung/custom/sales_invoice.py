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
    # Capture the due_date as submitted from the form before ERPNext recalculates it
    doc.flags.intended_due_date = doc.due_date

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

def set_leistungszeitraum_anzeige(doc, method=None):
    # Restore due_date if ERPNext's set_payment_schedule() changed it
    intended = doc.flags.get("intended_due_date")
    if intended and doc.due_date != intended:
        doc.due_date = intended
        for row in doc.get("payment_schedule", []):
            row.due_date = intended

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
