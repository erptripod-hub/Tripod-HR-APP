// Forces office staff to read + acknowledge their company's Appointment Guideline
// when they open the Employee Self Service workspace.
(function () {
	var API = 'tripod_hr.tripod_hr.page.ess_guidelines.ess_guidelines.';
	var open_dialog = null;
	var last_check = 0;

	function on_ess_workspace() {
		var path = window.location.pathname.replace(/\/+$/, '').toLowerCase();
		return path.endsWith('/app/employee-self-service');
	}

	function check() {
		if (!on_ess_workspace() || open_dialog) return;
		var now = Date.now();
		if (now - last_check < 1500) return;   // debounce route events
		last_check = now;

		frappe.call({
			method: API + 'get_pending_guideline',
			callback: function (r) {
				if (r && r.message && on_ess_workspace() && !open_dialog) {
					show_popup(r.message);
				}
			}
		});
	}

	function viewer_html(file) {
		var ext = file.split('.').pop().toLowerCase();
		var full = window.location.origin + file;
		var src = ext === 'pdf'
			? full + '#toolbar=0&navpanes=0&scrollbar=1'
			: 'https://view.officeapps.live.com/op/embed.aspx?src=' + encodeURIComponent(full);
		return '<div style="font-size:12px;color:#92400e;background:#fffbeb;border:1px solid #fde68a;' +
			'border-radius:6px;padding:8px 12px;margin-bottom:10px">' +
			'&#128274; Please read the full document below, then click <b>I Acknowledge</b> to continue.</div>' +
			'<div oncontextmenu="return false" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">' +
			'<iframe src="' + src + '" style="width:100%;height:68vh;border:none;display:block" ' +
			'sandbox="allow-same-origin allow-scripts allow-forms"></iframe></div>';
	}

	function show_popup(p) {
		var acknowledged = false;

		var d = new frappe.ui.Dialog({
			title: 'HR Handbook — ' + frappe.utils.escape_html(p.company),
			size: 'extra-large',
			static: true,
			fields: [{ fieldtype: 'HTML', fieldname: 'viewer' }],
			primary_action_label: 'I Acknowledge',
			primary_action: function () {
				d.get_primary_btn().prop('disabled', true).text('Submitting...');
				frappe.call({
					method: API + 'acknowledge',
					args: { employee: p.employee, guideline: p.guideline },
					callback: function () {
						acknowledged = true;
						d.hide();
						open_dialog = null;
						frappe.show_alert({ message: 'Thank you — guideline acknowledged', indicator: 'green' });
					},
					error: function () {
						d.get_primary_btn().prop('disabled', false).text('I Acknowledge');
					}
				});
			}
		});

		d.fields_dict.viewer.$wrapper.html(viewer_html(p.file));

		// Cannot be dismissed until acknowledged
		d.$wrapper.on('hide.bs.modal', function (e) {
			if (!acknowledged) e.preventDefault();
		});
		d.$wrapper.find('.modal-header .modal-actions, .modal-header .close').hide();
		d.$wrapper.find('.modal-dialog').css('max-width', '1100px');

		open_dialog = d;
		d.show();
	}

	$(document).on('page-change', check);
	if (frappe.router && frappe.router.on) frappe.router.on('change', check);
	$(document).ready(function () { setTimeout(check, 1500); });
})();
