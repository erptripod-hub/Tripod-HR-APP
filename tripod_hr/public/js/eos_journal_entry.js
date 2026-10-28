// EOS liability JV -> Make Bank Entry (payable team, no EOS access needed)
frappe.ui.form.on('Journal Entry', {
	refresh(frm) {
		if (frm.doc.docstatus !== 1 || !frm.doc.custom_eos_reference) return;
		if (frm.doc.voucher_type === 'Bank Entry' || frm.doc.voucher_type === 'Cash Entry') return;

		frm.add_custom_button(__('Make Bank Entry'), () => {
			frappe.model.open_mapped_doc({
				method: 'tripod_hr.tripod_hr.eos_approval.events.make_eos_bank_entry',
				frm: frm,
			});
		}).addClass('btn-primary');
	},
});
