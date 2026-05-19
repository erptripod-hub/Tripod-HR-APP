frappe.ui.form.on('Idea Vault', {
	refresh: function(frm) {
		// Helpful intro message for employees
		if (frm.is_new()) {
			frm.set_intro(
				__('Share your idea to help us improve. Every voice matters — your suggestion will be reviewed by HR.'),
				'blue'
			);
		}

		// Show status as a status indicator on the form
		if (!frm.is_new() && frm.doc.status) {
			let color_map = {
				'Submitted': 'orange',
				'Under Review': 'blue',
				'Approved': 'green',
				'Implemented': 'green',
				'Rejected': 'red',
				'On Hold': 'gray'
			};
			frm.page.set_indicator(frm.doc.status, color_map[frm.doc.status] || 'gray');
		}

		// Hide HR Review section from non-HR users
		let user_roles = frappe.user_roles || [];
		let is_hr = user_roles.includes('HR User') || user_roles.includes('HR Manager') || user_roles.includes('System Manager');
		if (!is_hr) {
			frm.set_df_property('status', 'read_only', 1);
			frm.set_df_property('hr_comments', 'read_only', 1);
			frm.set_df_property('reviewed_by', 'read_only', 1);
			frm.set_df_property('reviewed_on', 'read_only', 1);
		}
	}
});
