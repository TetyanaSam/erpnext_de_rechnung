app_name = "erpnext_de_rechnung"
app_title = "ERPNext DE Rechnung"
app_publisher = "Tetyana Samoylenko"
app_description = "German invoice print format and Leistungszeitraum field for ERPNext"
app_email = "info@samotet.de"
app_license = "mit"

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["name", "in",
            ["Sales Invoice-leistungszeitraum_section",
             "Sales Invoice-leistungszeitraum_typ",
             "Sales Invoice-leistungszeitraum_von",
             "Sales Invoice-leistungszeitraum_bis",
             "Sales Invoice-leistungszeitraum_col",
             "Sales Invoice-leistungszeitraum_col2",
             "Sales Invoice-leistungszeitraum_anzeige",
             "Sales Invoice-leistungszeitraum_datum",
             "Sales Invoice-leistungszeitraum_monat",
             "Sales Invoice-leistungszeitraum_jahr",
             "Sales Invoice-zweisprachig",
             "Sales Invoice-absender_im_anschriftenfeld",
             "Company-is_kleinunternehmer"]]]
    },
    {
        "dt": "Print Format",
        "filters": [["name", "=", "DE Rechnung"]]
    },
    {
        "dt": "Property Setter",
        "filters": [["doc_type", "=", "Sales Invoice Item"],
                    ["field_name", "in", ["description", "warehouse", "item_code"]],
                    ["property", "=", "in_list_view"]]
    }
]

doc_events = {
    "Sales Invoice": {
        "before_validate": "erpnext_de_rechnung.custom.sales_invoice.before_validate",
        "validate": "erpnext_de_rechnung.custom.sales_invoice.set_leistungszeitraum_anzeige"
    }
}

# Append a cache-buster query param to PDF download URLs from the Desk.
# Works together with the after_request no-store headers: fresh URL forces
# the mobile browser to issue a real request, where it then sees and honors
# the no-cache headers for future loads.
app_include_js = [
    "/assets/erpnext_de_rechnung/js/pdf_cache_bust.js"
]

# Force our Sales Invoice Item column visibility after every migrate.
# Fixtures alone only create missing rows; they don't overwrite values edited
# via Customize Form. This hook re-asserts the desired state on each migrate.
after_migrate = [
    "erpnext_de_rechnung.custom.sales_invoice.ensure_invoice_item_columns"
]

# Disable browser caching for PDF responses. Without this, mobile browsers and
# PDF viewers keep serving a stale cached PDF after the source invoice has been
# re-rendered, which forces users to clear their cache manually.
after_request = [
    "erpnext_de_rechnung.custom.pdf_cache.no_cache_pdf"
]
