from frappe import _


def get_data():
	return {
		"fieldname": "custom_eos_reference",
		"transactions": [
			{"label": _("Payment"), "items": ["Journal Entry"]},
		],
	}
