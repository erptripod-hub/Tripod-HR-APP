// Auto-generate a shareable application link on Job Opening.
// HR just creates the opening and saves; the link fills itself and can be
// copied straight to LinkedIn. No route setup needed per opening.

frappe.ui.form.on('Job Opening', {
	refresh: function (frm) {
		set_application_link(frm);
	},
	after_save: function (frm) {
		set_application_link(frm);
	}
});

function set_application_link(frm) {
	if (frm.is_new() || !frm.doc.name) {
		return;
	}
	// Base URL: uses the site's own host, so it works on any domain automatically.
	var base = window.location.origin;
	var link = base + '/new-job-application?new=1&job_title=' +
		encodeURIComponent(frm.doc.name);

	if (frm.doc.custom_application_link !== link) {
		frm.set_value('custom_application_link', link);
	}
}
