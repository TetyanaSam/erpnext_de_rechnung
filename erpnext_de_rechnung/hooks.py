app_name = "erpnext_de_rechnung"
app_title = "ERPNext DE Rechnung"
app_publisher = "Tetyana Samoylenko"
app_description = "German invoice print format and Leistungszeitraum field for ERPNext"
app_email = "info@samotet.de"
app_license = "mit"

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["dt", "=", "Sales Invoice"], ["fieldname", "like", "leistungszeitraum%"]]
    },
    {
        "dt": "Print Format",
        "filters": [["name", "=", "DE Rechnung"]]
    }
]

doc_events = {
    "Sales Invoice": {
        "before_validate": "erpnext_de_rechnung.custom.sales_invoice.before_validate",
        "validate": "erpnext_de_rechnung.custom.sales_invoice.set_leistungszeitraum_anzeige"
    }
}
