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
			const can_sign = ['EOS Creator', 'HR Manager', 'System Manager'].some((r) => frappe.user.has_role(r));
			if (frm.doc.docstatus === 1 && can_sign) {
				frm.add_custom_button(__('Add Employee Signature'), () => employee_signature_dialog(frm));
			}

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

	function employee_signature_dialog(frm) {
		let signature_url = null;
		const d = new frappe.ui.Dialog({
			title: __('Add Employee Signature'),
			fields: [
				{ fieldname: 'signed_copy', fieldtype: 'Attach', label: __('Signed Copy (scanned PDF or image)'),
				  description: __('The signature is cut automatically from the Employee box.') },
				{ fieldname: 'or_manual', fieldtype: 'Attach Image', label: __('Or upload the signature image directly') },
				{ fieldname: 'preview', fieldtype: 'HTML' },
			],
			primary_action_label: __('Extract Signature'),
			primary_action(values) {
				if (signature_url) {
					frappe.call({
						method: 'tripod_hr.tripod_hr.eos_approval.events.save_employee_signature',
						args: { doctype: frm.doctype, name: frm.doc.name, signature_url, signed_copy_url: values.signed_copy },
						freeze: true,
					}).then(() => { d.hide(); frm.reload_doc(); frappe.show_alert({ message: __('Employee signature saved'), indicator: 'green' }); });
					return;
				}
				const show = (url) => {
					signature_url = url;
					d.fields_dict.preview.$wrapper.html(
						`<div style="margin-top:10px;padding:12px;border:1px solid var(--border-color);border-radius:6px;text-align:center">
							<div class="text-muted small" style="margin-bottom:6px">${__('Preview')}</div>
							<img src="${url}" style="max-height:110px;max-width:100%">
						</div>`);
					d.set_primary_action(__('Save'), d.primary_action);
				};
				if (values.or_manual) return show(values.or_manual);
				if (!values.signed_copy) return frappe.msgprint(__('Attach the signed copy first.'));
				frappe.call({
					method: 'tripod_hr.tripod_hr.eos_approval.events.extract_employee_signature',
					args: { doctype: frm.doctype, name: frm.doc.name, file_url: values.signed_copy },
					freeze: true, freeze_message: __('Reading signature...'),
				}).then((r) => r.message && show(r.message));
			},
		});
		d.show();
	}

	frappe.ui.form.on('UAE EOS Calculation', handlers);
	frappe.ui.form.on('KSA EOS Calculation', handlers);
})();
