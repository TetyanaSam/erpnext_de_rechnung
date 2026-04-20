// Client-side refinements for Sales Invoice form.
//
// Problem 1: Duplicate leaves old payment_schedule → due_date looks stale
// until the user saves. The user should be able to EYEBALL the correct
// due_date before committing.
//
// Problem 2: Duplicate also carries contact_email / contact_person from
// the source invoice. If the Contact record was edited later (different
// manager, new email), the duplicate still shows the old snapshot — a
// silent footgun for the auto-send toggle.
//
// Both are fixed on form refresh for a freshly-loaded new doc: clear the
// stale snapshots, re-trigger the standard handlers so ERPNext re-fetches
// current data from the linked records.
frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		if (!frm.is_new()) return;
		refresh_stale_copies(frm);
	},

	posting_date(frm) {
		// Posting date changed → payment schedule is stale. Clear it and
		// let the standard ERPNext handler recompute from the (unchanged)
		// payment_terms_template.
		if (frm.doc.payment_terms_template && frm.doc.posting_date) {
			frm.clear_table("payment_schedule");
			frm.set_value("due_date", null);
			frm.refresh_field("payment_schedule");
			frm.trigger("payment_terms_template");
		}
	},
});

function refresh_stale_copies(frm) {
	if (!frm.doc.customer) return;

	// If the payment_schedule carried a due_date that doesn't match the
	// current posting_date + credit_days, wipe it so the standard handler
	// rebuilds.
	const ps = frm.doc.payment_schedule;
	if (ps && ps.length && frm.doc.posting_date && ps[0].credit_days) {
		const expected = frappe.datetime.add_days(frm.doc.posting_date, ps[0].credit_days);
		if (frappe.datetime.get_diff(expected, ps[0].due_date) !== 0) {
			frm.clear_table("payment_schedule");
			frm.set_value("due_date", null);
			frm.refresh_field("payment_schedule");
			if (frm.doc.payment_terms_template) {
				frm.trigger("payment_terms_template");
			}
		}
	}

	// Re-fetch contact details from the Customer's current primary contact.
	// The duplicate copied a possibly-stale contact_email snapshot.
	if (frm.doc.customer && frm.doc.contact_person) {
		frappe.call({
			method: "frappe.client.get",
			args: { doctype: "Contact", name: frm.doc.contact_person },
			callback(r) {
				if (!r.message) return;
				const primary = (r.message.email_ids || []).find((e) => e.is_primary);
				const email = primary ? primary.email_id : null;
				if (email && email !== frm.doc.contact_email) {
					frm.set_value("contact_email", email);
				}
			},
		});
	}
}
