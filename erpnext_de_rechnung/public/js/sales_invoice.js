// Client-side refinements for Sales Invoice form.
//
// Three UX fixes:
//
// (a) Duplicate leaves old payment_schedule with a stale due_date until Save.
//     The user should be able to eyeball the correct due_date BEFORE
//     committing.
// (b) Duplicate also carries contact_email / contact_person from the source
//     invoice. If the linked Contact record was edited later (different
//     manager, new email), the duplicate still shows the old snapshot — a
//     silent footgun for the auto-send toggle.
// (c) A brand-new invoice needs payment_terms_template auto-filled from the
//     Customer / Company so due_date can be computed immediately, not after
//     the first Save. Our server hook does this, but only at validate time —
//     too late for visual review.
frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		if (!frm.is_new()) return;
		refresh_stale_copies(frm);
		auto_fill_payment_terms(frm);
		reset_auto_send_from_company(frm);
	},

	customer(frm) {
		if (!frm.is_new()) return;
		auto_fill_payment_terms(frm);
	},

	company(frm) {
		if (!frm.is_new()) return;
		reset_auto_send_from_company(frm);
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

function reset_auto_send_from_company(frm) {
	// On any freshly-loaded new or duplicated invoice, overwrite the
	// auto-send flag with the Company's current default. This stops a
	// duplicate from silently inheriting an old per-invoice setting that
	// contradicts the company-wide policy.
	if (!frm.doc.company) return;
	frappe.db.get_value("Company", frm.doc.company, "default_auto_send_email").then((r) => {
		const target = (r.message && r.message.default_auto_send_email) ? 1 : 0;
		if (frm.doc.auto_send_email !== target) {
			frm.set_value("auto_send_email", target);
		}
	});
}

function auto_fill_payment_terms(frm) {
	if (!frm.doc.customer || frm.doc.payment_terms_template) return;

	// Prefer the Customer's default, fall back to the Company's default.
	frappe.db.get_value("Customer", frm.doc.customer, "payment_terms").then((r) => {
		const from_customer = r.message && r.message.payment_terms;
		if (from_customer) {
			frm.set_value("payment_terms_template", from_customer);
			return;
		}
		if (!frm.doc.company) return;
		frappe.db.get_value("Company", frm.doc.company, "payment_terms").then((r2) => {
			const from_company = r2.message && r2.message.payment_terms;
			if (from_company) {
				frm.set_value("payment_terms_template", from_company);
			}
		});
	});
}

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
