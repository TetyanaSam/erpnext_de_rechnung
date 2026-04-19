MONATE = {
    "Januar": 1, "Februar": 2, "März": 3, "April": 4,
    "Mai": 5, "Juni": 6, "Juli": 7, "August": 8,
    "September": 9, "Oktober": 10, "November": 11, "Dezember": 12
}

def set_leistungszeitraum_anzeige(doc, method=None):
    typ = doc.get("leistungszeitraum_typ")
    if typ == "Datumsbereich":
        von = doc.get("leistungszeitraum_von")
        bis = doc.get("leistungszeitraum_bis")
        if von and bis:
            from frappe.utils import formatdate
            doc.leistungszeitraum_anzeige = f"{formatdate(von, 'dd.MM.yyyy')} – {formatdate(bis, 'dd.MM.yyyy')}"
    elif typ == "Monat/Jahr":
        monat = doc.get("leistungszeitraum_monat")
        jahr = doc.get("leistungszeitraum_jahr")
        if monat and jahr:
            doc.leistungszeitraum_anzeige = f"{monat} {jahr}"
