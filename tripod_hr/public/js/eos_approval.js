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
				const remaining = flt(frm.doc.net_payable) - flt(frm.doc.custom_paid_amount);
				frappe.call({
					method: 'tripod_hr.tripod_hr.eos_approval.events.get_payment_defaults',
					args: { company: frm.doc.company },
				}).then((r) => {
					const acc = r.message || {};
					frappe.model.with_doctype('Journal Entry', () => {
						const je = frappe.model.get_new_doc('Journal Entry');
						je.voucher_type = 'Bank Entry';
						je.company = frm.doc.company;
						je.posting_date = frappe.datetime.get_today();
						je.custom_eos_doctype = frm.doctype;
						je.custom_eos_reference = frm.doc.name;
						je.user_remark = `End of Service payment - ${frm.doc.employee} ${frm.doc.employee_name || ''} (${frm.doc.name})`;

						const dr = frappe.model.add_child(je, 'accounts');
						dr.account = acc.payable_account;
						dr.party_type = 'Employee';
						dr.party = frm.doc.employee;
						dr.debit_in_account_currency = remaining;

						const cr = frappe.model.add_child(je, 'accounts');
						cr.account = acc.bank_account;
						cr.credit_in_account_currency = remaining;

						frappe.set_route('Form', 'Journal Entry', je.name);
					});
				});
			}, __('Create'));
		},
	};

	frappe.ui.form.on('UAE EOS Calculation', handlers);
	frappe.ui.form.on('KSA EOS Calculation', handlers);
})();
