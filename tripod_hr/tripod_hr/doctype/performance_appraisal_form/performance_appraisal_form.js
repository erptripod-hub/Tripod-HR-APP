// Copyright (c) 2026, Tripod and contributors
// For license information, please see license.txt

frappe.ui.form.on('Performance Appraisal Form', {
	refresh: function(frm) {
		// Add custom buttons based on workflow state
		if (frm.doc.docstatus === 0) {
			// Show helpful message
			if (!frm.doc.objectives || frm.doc.objectives.length === 0) {
				frm.dashboard.add_comment('Add objectives to start the appraisal', 'blue', true);
			}
		}
		
		// Calculate average rating on refresh
		calculate_average_rating(frm);
	},
	
	employee: function(frm) {
		// When employee is selected, fetch their line manager
		if (frm.doc.employee) {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'Employee',
					filters: { name: frm.doc.employee },
					fieldname: ['reports_to']
				},
				callback: function(r) {
					if (r.message && r.message.reports_to) {
						frm.set_value('line_manager', r.message.reports_to);
					}
				}
			});
		}
	}
});

frappe.ui.form.on('Performance Appraisal Objective', {
	rating: function(frm, cdt, cdn) {
		// Recalculate overall rating when any objective rating changes
		calculate_average_rating(frm);
	},
	
	objectives_remove: function(frm) {
		// Recalculate when objective is removed
		calculate_average_rating(frm);
	}
});

function calculate_average_rating(frm) {
	if (!frm.doc.objectives || frm.doc.objectives.length === 0) {
		return;
	}
	
	let total = 0;
	let count = 0;
	
	frm.doc.objectives.forEach(function(obj) {
		if (obj.rating) {
			total += parseInt(obj.rating);
			count++;
		}
	});
	
	if (count > 0) {
		let average = Math.round(total / count);
		frm.set_value('overall_rating', String(average));
	}
}
