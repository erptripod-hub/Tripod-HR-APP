// Copyright (c) 2026, Tripod and contributors
// For license information, please see license.txt

const RATING_FIELDS = [
	"rate_quality_of_work",
	"rate_communication",
	"rate_takes_initiative",
	"rate_collaboration",
	"rate_problem_solving",
	"rate_client_relations",
];

function calculate_total_score(frm) {
	let total = 0;
	RATING_FIELDS.forEach(function (field) {
		let val = frm.doc[field];
		if (val) {
			let num = parseInt(String(val).split("-")[0].trim());
			if (!isNaN(num)) {
				total += num;
			}
		}
	});
	frm.set_value("total_score", total);
}

let handlers = {
	refresh: function (frm) {
		calculate_total_score(frm);
	},
};

RATING_FIELDS.forEach(function (field) {
	handlers[field] = function (frm) {
		calculate_total_score(frm);
	};
});

frappe.ui.form.on("Project Team Appraisal", handlers);
