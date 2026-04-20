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
	function patch() {
		const PV = frappe.ui?.form?.PrintView;
		if (!PV || !PV.prototype || PV.prototype._drucken_patched) {
			return;
		}
		PV.prototype._drucken_patched = true;
		PV.prototype.printit = function () {
			// Delegate to the same code path as the "PDF" button: open a
			// freshly generated PDF in a new tab. Users print from the PDF
			// viewer if they still want a paper copy.
			this.render_pdf();
		};
	}
	frappe.after_ajax(patch);
	$(document).on("page-change app_ready", patch);
})();
