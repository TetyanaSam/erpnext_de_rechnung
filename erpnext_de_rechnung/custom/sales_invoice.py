import frappe

GERMAN_MONTHS = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April",
    5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
    9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
}

def before_validate(doc, method=None):
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
        if von:
            from frappe.utils import getdate
            d = getdate(von)
            doc.leistungszeitraum_anzeige = f"{GERMAN_MONTHS[d.month]} {d.year}"
        else:
            doc.leistungszeitraum_anzeige = ""
    else:
        doc.leistungszeitraum_anzeige = ""
