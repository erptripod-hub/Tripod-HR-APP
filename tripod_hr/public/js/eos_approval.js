// EOS (UAE / KSA): payment status indicator + Make Payment button for Finance
(function () {
	const PAY_COLORS = { 'Unpaid': 'red', 'Partly Paid': 'orange', 'Paid': 'green' };

	const handlers = {
		onload(frm) {
			// New EOS: show the exit checklist straight away
			if (!frm.is_new() || (frm.doc.custom_exit_checklist || []).length) return;
			frappe.call('tripod_hr.tripod_hr.eos_approval.events.get_checklist_items').then((r) => {
				(r.message || []).forEach((item) => {
					frm.add_child('custom_exit_checklist', { checklist_item: item });
				});
				frm.refresh_field('custom_exit_checklist');
			});
		},
		refresh(frm) {
			const status = frm.doc.custom_payment_status;
			if (frm.doc.docstatus === 1 && status) {
				frm.dashboard.add_indicator(__('Payment: {0}', [__(status)]), PAY_COLORS[status] || 'gray');
			}

			const can_pay = ['Finance Approval', 'Accounts Manager', 'Accounts User'].some((r) => frappe.user.has_role(r));
			if (frm.doc.docstatus !== 1 || status === 'Paid' || !can_pay) return;

			frm.add_custom_button(__('Bank Entry'), () => {
				frappe.call({
					method: 'tripod_hr.tripod_hr.eos_approval.events.make_eos_bank_entry',
					args: { eos_doctype: frm.doctype, eos_name: frm.doc.name },
				}).then((r) => {
					if (!r.message) return;
					const doc = frappe.model.sync(r.message)[0];
					frappe.set_route('Form', doc.doctype, doc.name);
				});
			}, __('Create'));
		},
	};

	frappe.ui.form.on('UAE EOS Calculation', handlers);
	frappe.ui.form.on('KSA EOS Calculation', handlers);
})();
