app_name = "erpnext_de_rechnung"
app_title = "ERPNext DE Rechnung"
app_publisher = "Tetyana Samoylenko"
app_description = "German invoice print format and Leistungszeitraum field for ERPNext"
app_email = "info@samotet.de"
app_license = "mit"

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["dt", "=", "Sales Invoice"], ["fieldname", "in",
            ["leistungszeitraum_section", "leistungszeitraum_typ",
             "leistungszeitraum_von", "leistungszeitraum_bis",
             "leistungszeitraum_col", "leistungszeitraum_col2",
             "leistungszeitraum_anzeige", "leistungszeitraum_datum",
             "leistungszeitraum_monat", "leistungszeitraum_jahr",
             "zweisprachig"]]]
    },
    {
        "dt": "Print Format",
        "filters": [["name", "=", "DE Rechnung"]]
    },
    {
        "dt": "Property Setter",
        "filters": [["doc_type", "=", "Sales Invoice Item"],
                    ["field_name", "in", ["description", "warehouse"]],
                    ["property", "=", "in_list_view"]]
    }
]

doc_events = {
    "Sales Invoice": {
        "before_validate": "erpnext_de_rechnung.custom.sales_invoice.before_validate",
        "validate": "erpnext_de_rechnung.custom.sales_invoice.set_leistungszeitraum_anzeige"
    }
}
