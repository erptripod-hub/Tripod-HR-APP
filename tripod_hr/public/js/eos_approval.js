// EOS (UAE / KSA): payment status indicator + Make Payment button for Finance
(function () {
	const PAY_COLORS = { 'Unpaid': 'red', 'Partly Paid': 'orange', 'Paid': 'green' };

	const handlers = {
		refresh(frm) {
			const status = frm.doc.custom_payment_status;
			if (frm.doc.docstatus === 1 && status) {
				frm.dashboard.add_indicator(__('Payment: {0}', [__(status)]), PAY_COLORS[status] || 'gray');
			}

			const can_pay = frappe.user.has_role('Accounts Manager') || frappe.user.has_role('Accounts User');
			if (frm.doc.docstatus !== 1 || status === 'Paid' || !can_pay) return;

			frm.add_custom_button(__('Journal Entry'), () => {
				const remaining = flt(frm.doc.net_payable) - flt(frm.doc.custom_paid_amount);
				frappe.model.with_doctype('Journal Entry', () => {
					const je = frappe.model.get_new_doc('Journal Entry');
					je.voucher_type = 'Bank Entry';
					je.company = frm.doc.company;
					je.posting_date = frappe.datetime.get_today();
					je.custom_eos_doctype = frm.doctype;
					je.custom_eos_reference = frm.doc.name;
					je.user_remark = `End of Service payment - ${frm.doc.employee} ${frm.doc.employee_name || ''} (${frm.doc.name})`;

					const dr = frappe.model.add_child(je, 'accounts');
					dr.party_type = 'Employee';
					dr.party = frm.doc.employee;
					dr.debit_in_account_currency = remaining;

					const cr = frappe.model.add_child(je, 'accounts');
					cr.credit_in_account_currency = remaining;

					frappe.set_route('Form', 'Journal Entry', je.name);
				});
			}, __('Create'));
		},
	};

	frappe.ui.form.on('UAE EOS Calculation', handlers);
	frappe.ui.form.on('KSA EOS Calculation', handlers);
})();
