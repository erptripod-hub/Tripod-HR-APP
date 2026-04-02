// Client script for Appointment Guideline
// Hides the download button on the file attachment for Employee Self Service role

frappe.ui.form.on('Appointment Guideline', {
	refresh: function(frm) {
		// Check if current user has Employee Self Service role but NOT HR roles
		const hasHRAccess = frappe.user.has_role(['HR Manager', 'HR User', 'System Manager', 'Administrator']);
		const hasESSRole = frappe.user.has_role('Employee Self Service') || frappe.user.has_role('Employee');

		if (hasESSRole && !hasHRAccess) {
			// Make the entire form read-only
			frm.set_df_property('guideline_file', 'read_only', 1);

			// Hide download/clear buttons on the attachment field
			setTimeout(function() {
				frm.fields_dict['guideline_file'].$wrapper.find('.btn-attach, .attached-file .close, [data-action="clear_attachment"]').hide();

				// Override the attachment link to open in new tab (view only)
				frm.fields_dict['guideline_file'].$wrapper.find('.attached-file a').attr('target', '_blank');

				// Add read-only notice
				if (frm.fields_dict['guideline_file'].$wrapper.find('.ess-notice').length === 0) {
					frm.fields_dict['guideline_file'].$wrapper.append(
						'<div class="ess-notice" style="font-size:11px;color:#92400e;background:#fffbeb;border:1px solid #fde68a;border-radius:4px;padding:5px 10px;margin-top:6px;">' +
						'&#128274; View only — downloading is disabled for your role. Contact HR for a copy.' +
						'</div>'
					);
				}
			}, 500);

			// Remove save/edit buttons
			frm.disable_save();
		}
	}
});
