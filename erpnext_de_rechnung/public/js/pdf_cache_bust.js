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
