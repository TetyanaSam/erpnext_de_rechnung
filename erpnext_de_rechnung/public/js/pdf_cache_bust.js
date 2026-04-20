// Force a unique URL on every "PDF" / "Print" action so mobile browsers
// and PDF viewers cannot serve a stale cached response. Without this,
// the user (and their clients) would need to manually clear browser
// cache after every invoice re-render — unacceptable for a tool that
// produces invoices sent out to third parties.
//
// The server-side after_request hook sets `Cache-Control: no-store`
// on the response, but an already-cached PDF would never be re-fetched
// for the browser to discover the new headers. A timestamp query
// parameter guarantees a unique URL each click, forcing a real request.
frappe.after_ajax(() => {
	if (!frappe.urllib || typeof frappe.urllib.get_full_url !== "function") {
		return;
	}
	const original = frappe.urllib.get_full_url;
	frappe.urllib.get_full_url = function (url) {
		const full = original.apply(this, arguments);
		if (typeof full === "string" &&
			(full.indexOf("download_pdf") !== -1 || full.indexOf("/printview") !== -1)) {
			const sep = full.indexOf("?") !== -1 ? "&" : "?";
			return full + sep + "_cb=" + Date.now();
		}
		return full;
	};
});

// Redirect the "Drucken" / "Print" button on the Print view to the PDF
// download path instead of opening the browser-native print dialog on a
// preview HTML. The preview renders without the running page header/
// footer (wkhtmltopdf only injects those during real PDF generation) and
// without page numbers, so printing it produces a visually different
// document from the PDF the client actually receives. Users get confused
// seeing one layout on screen and another in the sent PDF. Route the
// button to render_pdf so "what you see is what the client gets".
//
// The PrintView class is defined in frappe's print.bundle.js which loads
// lazily when /app/print/... route opens, so we must patch AFTER that
// bundle is loaded. Re-check on every page change.
(function patch_drucken_button() {
	let patched = false;

	function patch_once() {
		if (patched) return true;
		const PV = frappe.ui && frappe.ui.form && frappe.ui.form.PrintView;
		if (!PV || !PV.prototype) return false;
		PV.prototype.printit = function () {
			// Delegate to the same code path as the "PDF" button: open a
			// freshly generated PDF in a new tab. Users print from the PDF
			// viewer if they still want a paper copy.
			this.render_pdf();
		};
		patched = true;
		return true;
	}

	// The PrintView class ships in frappe's print.bundle.js which is
	// lazy-loaded the first time the user navigates to /app/print/... —
	// and "first time" may be any moment during the user's session, not
	// just right after page load. Start a long-running, low-rate poll
	// that keeps checking until the class appears, then stops.
	function start_polling(max_ms) {
		const started = Date.now();
		const iv = setInterval(() => {
			if (patch_once() || Date.now() - started > max_ms) {
				clearInterval(iv);
			}
		}, 400);
	}

	if (typeof frappe !== "undefined") {
		if (!patch_once()) {
			// Poll for up to 10 minutes after initial load. Covers the
			// user opening print view well into their session.
			start_polling(10 * 60 * 1000);
			// Restart polling on every route change too — first-time
			// navigation to /app/print is when the bundle loads.
			if (frappe.router && typeof frappe.router.on === "function") {
				frappe.router.on("change", () => {
					if (!patched) start_polling(30 * 1000);
				});
			}
		}
	}
})();
