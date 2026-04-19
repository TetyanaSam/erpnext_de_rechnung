# ERPNext DE Rechnung

> A Frappe/ERPNext app that turns a vanilla Sales Invoice into a clean,
> audit-safe German invoice — bilingual on demand, with everything the
> Finanzamt, your accountant and your client actually want to see.

[🇬🇧 English](#english) · [🇩🇪 Deutsch](#deutsch) · [✉️ Contact / Kontakt](#contact--kontakt)

---

## English

### What this app does

German invoicing has a lot of small rules that stock ERPNext doesn't handle out of the box: the service period (*Leistungszeitraum*), correct VAT labelling, the §14 UStG mandatory fields, sensible layout for small-business invoices (*Kleinunternehmer*), and — if your client is abroad — a second language column.

**ERPNext DE Rechnung** bundles all of that into one installable app:

- **A purpose-built Print Format `DE Rechnung`** that replaces the default Sales Invoice PDF. Everything is laid out for an A4 page with a running page header (`Company · Invoice-No · Seite 1 / 2`) and a three-column footer (contact / tax / bank).
- **Optional bilingual mode** (German + English) per invoice. One checkbox on the Sales Invoice form; labels, table headers, VAT rows, payment terms and month names all flip to two-language format. Months are properly localized (`März 2026 / March 2026`, not a date range).
- **Leistungszeitraum field group** on every Sales Invoice with three types: `Monat/Jahr`, `Datum`, `Datumsbereich`. Always rendered as *Month Year* on the PDF — if you want a date range on the document you write it explicitly in the item description, which is the clean way to do it.
- **Vorausrechnung detection**: if the posting date is before the service period starts, the document title automatically becomes `Vorausrechnung` (advance invoice) instead of `Rechnung`. Handy for recurring service contracts billed up-front.
- **Due-date protection**: Frappe's default `set_payment_schedule()` loves to overwrite the due date you just typed. This app restores the user-intended due date after validation.
- **Auto-fill payment terms** from the customer or company defaults, so you don't have to pick them manually on every new invoice.
- **Pinned form layout** for Sales Invoice items. The relevant columns (`Artikel`, `Bezeichnung`) stay visible in the line-item table through cache clears, migrations and Customize Form edits — no more hunting for the item code after an update.
- **Page-number safety**: no blank trailing page, no duplicate page-2 header, no garbled page counters — several wkhtmltopdf foot-guns are fixed in the layout.

### What's inside

| Component | Purpose |
|---|---|
| Print Format `DE Rechnung` | Main output — replaces default Sales Invoice PDF |
| Custom Field `zweisprachig` | Bilingual switch (Check) on Sales Invoice |
| Leistungszeitraum section | 7 custom fields grouping type, start/end, display text |
| Property Setters | Persistent column visibility on the item table |
| `before_validate` / `validate` hooks | Payment-terms auto-fill, due-date restore, Leistungszeitraum display text |
| `after_migrate` hook | Re-asserts pinned form layout after every upgrade |

### Requirements

- **ERPNext v15** / **Frappe v15**
- **wkhtmltopdf 0.12.6+** with patched Qt (the build Frappe Docker ships)
- A Company record with `phone_no`, `email`, `tax_id` and a Bank Account flagged as company account — these populate the invoice footer.

### Installation

From your bench root:

```bash
bench get-app https://github.com/TetyanaSam/erpnext_de_rechnung
bench --site your-site install-app erpnext_de_rechnung
bench --site your-site migrate
```

The install creates the custom fields and loads the print format. `bench migrate` triggers the `after_migrate` hook that pins the item-table layout.

To update after a `git pull`:

```bash
bench --site your-site migrate
bench restart
```

### How to use

#### Creating a normal German invoice

1. Open a new Sales Invoice, pick the customer, add items.
2. Scroll to the **Leistungszeitraum** section. Pick a type:
    - **Monat/Jahr** — most common. Pick any date in the month; the PDF prints just `April 2026`.
    - **Datum** — one-off service on a specific date.
    - **Datumsbereich** — a range. *The PDF still prints only the month*, so if you need "1.–15. April" literally, put that in the item description.
3. Save and submit.
4. **Print → DE Rechnung → Download PDF**.

#### Making it bilingual

Tick the **Zweisprachig** checkbox on the Sales Invoice. All German labels now have an English subtitle or inline translation (`Rechnungsnummer / Invoice No.`, `Umsatzsteuer 19 % / VAT 19%`, `März 2026 / March 2026`, etc.). Turn it off and the document stays purely German.

> **Heads up:** the checkbox currently does not have *Allow on Submit*. Toggle it before you submit the invoice, or amend.

#### Item lines

Each item row prints:
- **Pos.** — line number
- **Bezeichnung** — shows the item name, with the description as a smaller line underneath
- **Menge · Einheit · Einzelpreis · Netto · MwSt · Brutto**

The `item_code` and `description` columns are always visible in the form's line-item editor so you can pick items and tweak descriptions without fighting the layout.

#### Footer data

The footer pulls from your Company record and the first Bank Account marked "Is Company Account". Make sure these are filled in once:

- **Company**: `company_name`, address, `phone_no`, `email`, `tax_id`
- **Bank Account** (company): `iban`, `bank`, `branch_code` (BIC)

Kleinunternehmer notice (`§ 19 UStG`) is included by default in the footer style — edit the Print Format HTML if your status changes.

### Troubleshooting

- **"My bilingual checkbox is off but the PDF is still two-language"** — the form has unsaved changes. Hit **Save** before downloading the PDF; the Preview uses in-memory state, the PDF reads the database.
- **"Item column is missing in the invoice lines"** — run `bench --site your-site migrate`. The `after_migrate` hook reasserts the layout. This issue is fixed structurally, but a stale cache can still show the old layout until the next hard refresh.
- **"A blank second page appears after the invoice"** — this was a wkhtmltopdf margin-mismatch bug; it's fixed in the current print format. If it shows up again after edits, make sure the `.print-format { margin-top; margin-bottom }` rule in the style block is intact.

---

## Deutsch

### Was die App macht

Die Standard-ERPNext-Rechnung ist pragmatisch, aber deutschlandtauglich ist sie nicht: Leistungszeitraum fehlt, die Umsatzsteuerzeile ist nicht zweisprachig übersetzbar, Kleinunternehmer-Hinweise muss man manuell pflegen, und die Nummerierung auf Folgeseiten ist nicht sauber.

**ERPNext DE Rechnung** ist die Nachrüstung dafür:

- **Druckvorlage `DE Rechnung`** — saubere, A4-optimierte Rechnung mit laufendem Seitenkopf (`Firma · Rechnungs-Nr · Seite 1 / 2`) und dreispaltigem Fuß (Kontakt / Steuer / Bank).
- **Optionaler zweisprachiger Modus** (Deutsch + Englisch) pro Rechnung: ein Häkchen in der Rechnung und sämtliche Beschriftungen, Tabellenköpfe, MwSt-Zeilen, Zahlungsbedingungen und Monatsnamen erscheinen zweisprachig. Monate werden korrekt lokalisiert (`März 2026 / March 2026`).
- **Leistungszeitraum-Block** mit drei Typen: `Monat/Jahr`, `Datum`, `Datumsbereich`. Auf dem PDF wird immer *Monat Jahr* ausgegeben — wenn Du einen echten Zeitraum brauchst, schreibst Du ihn direkt in die Artikelbeschreibung. Das ist aufgeräumter und nie missverständlich.
- **Vorausrechnung automatisch**: Liegt das Rechnungsdatum vor dem Leistungszeitraum, wird aus der Rechnung automatisch eine *Vorausrechnung* — praktisch für Dauerschuldverhältnisse, die im Voraus abgerechnet werden.
- **Fälligkeitsschutz**: Frappe überschreibt gern das Fälligkeitsdatum beim Speichern. Die App stellt den von Dir eingetragenen Wert wieder her.
- **Zahlungsbedingungen vorbelegt** aus Kunde oder Firma — Du musst sie nicht bei jeder Rechnung neu auswählen.
- **Formularlayout bleibt stabil**: Die Spalten *Artikel* und *Bezeichnung* in der Positionstabelle überstehen Cache-Reset, Migration und Customize-Form-Änderungen — nach einem Update suchst Du die Artikelnummer nie wieder.
- **Leere Seite nach der Rechnung weg**, Seitenzählung korrekt, keine dupplizierten Kopfzeilen — mehrere klassische wkhtmltopdf-Stolpersteine sind sauber gelöst.

### Anforderungen

- **ERPNext v15** / **Frappe v15**
- **wkhtmltopdf 0.12.6+** mit patched Qt
- Eine Firma mit `phone_no`, `email`, `tax_id` und ein als Firmenkonto markiertes Bankkonto — daraus wird der Rechnungsfuß befüllt.

### Installation

```bash
bench get-app https://github.com/TetyanaSam/erpnext_de_rechnung
bench --site deine-site install-app erpnext_de_rechnung
bench --site deine-site migrate
```

### Kurzanleitung

1. Neue Sales Invoice anlegen, Kunde und Positionen eintragen.
2. Im Abschnitt **Leistungszeitraum** den Typ wählen (meist `Monat/Jahr`) und ein Datum im entsprechenden Monat eintragen — ausgegeben wird `April 2026`.
3. Für eine zweisprachige Rechnung **Zweisprachig** anhaken (vor dem Submit).
4. Speichern, submitten, **Drucken → DE Rechnung → PDF herunterladen**.

---

## Contact / Kontakt

**Tetyana Samoylenko** · Business Automation Engineer · Hamburg

📧 **info@samotet.de**

### Individuelle Entwicklung & ERPNext-Beratung

Diese App ist ein Nebenprodukt der täglichen Arbeit. Hauptsächlich mache ich für Kunden das hier:

- **ERPNext-Implementierung und -Anpassung** — Einführung, Datenmigration, eigene DocTypes, Workflows, Druckformate, Integrationen.
- **Mobile Apps** — native/hybride Apps, entweder als Aufsatz auf ein ERPNext-Backend oder komplett eigenständig. Mit Offline-Betrieb, Push, Update-Kanal.
- **Prozessautomatisierung** — alles, was Menschen davon befreit, Daten von A nach B zu tippen: API-Bridges, Background-Jobs, Berichte, Webhooks, Zahlungsabgleich, E-Mail-Verarbeitung, Benachrichtigungen.
- **Deutsche Compliance** — XRechnung, GoBD, sauberes MwSt-Handling, Datenexporte für Steuerberater.

### Custom development & ERPNext consulting

This app is a by-product of day-to-day client work. What I do most of the time:

- **ERPNext implementation and customization** — rollout, data migration, custom DocTypes, workflows, print formats, third-party integrations.
- **Mobile apps** — native / hybrid apps, either paired with an ERPNext backend or completely standalone. Offline mode, push, update channel — the full package.
- **Business process automation** — whatever removes the "human copy-pastes data from A to B" step: API bridges, background jobs, reports, webhooks, payment reconciliation, e-mail processing, notifications.
- **German compliance** — XRechnung, GoBD, clean VAT handling, data exports your Steuerberater won't complain about.

If any of that sounds like what you need, drop a line at **info@samotet.de** — happy to talk through the problem and tell you honestly whether I'm the right person to solve it.

---

## License

MIT — see [license.txt](license.txt). Use it, fork it, ship it. A mention is appreciated but not required.
