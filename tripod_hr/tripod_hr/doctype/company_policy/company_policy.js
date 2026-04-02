// Client script for Company Policy
// Hides the download button on the file attachment for Employee Self Service role

frappe.ui.form.on('Company Policy', {
	refresh: function(frm) {
		const hasHRAccess = frappe.user.has_role(['HR Manager', 'HR User', 'System Manager', 'Administrator']);
		const hasESSRole = frappe.user.has_role('Employee Self Service') || frappe.user.has_role('Employee');

		if (hasESSRole && !hasHRAccess) {
			// Make form read-only
			frm.set_df_property('policy_document', 'read_only', 1);

			setTimeout(function() {
				// Hide upload/clear controls
				frm.fields_dict['policy_document'].$wrapper.find('.btn-attach, .attached-file .close, [data-action="clear_attachment"]').hide();

				// Open attachment in new tab
				frm.fields_dict['policy_document'].$wrapper.find('.attached-file a').attr('target', '_blank');

				// Add read-only notice
				if (frm.fields_dict['policy_document'].$wrapper.find('.ess-notice').length === 0) {
					frm.fields_dict['policy_document'].$wrapper.append(
						'<div class="ess-notice" style="font-size:11px;color:#92400e;background:#fffbeb;border:1px solid #fde68a;border-radius:4px;padding:5px 10px;margin-top:6px;">' +
						'&#128274; View only — downloading is disabled for your role. Contact HR for a copy.' +
						'</div>'
					);
				}
			}, 500);

			frm.disable_save();
		}
	}
});
