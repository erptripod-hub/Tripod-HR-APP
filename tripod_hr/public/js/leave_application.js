// Leave Application - Update Return Date Feature
// For workers who don't return on time

frappe.ui.form.on("Leave Application", {
    refresh: function(frm) {
        // Show button only on submitted Leave Applications
        if (frm.doc.docstatus === 1 && frm.doc.status === "Approved") {
            frm.add_custom_button(__('Update Return Date'), function() {
                show_update_return_date_dialog(frm);
            }, __('Actions'));
        }
        
        // Show extension history if exists
        if (frm.doc.custom_original_to_date) {
            frm.set_df_property('custom_extension_section', 'hidden', 0);
        }
    }
});

function show_update_return_date_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Update Return Date'),
        fields: [
            {
                label: __('Current To Date'),
                fieldname: 'current_to_date',
                fieldtype: 'Date',
                default: frm.doc.to_date,
                read_only: 1
            },
            {
                label: __('New Return Date'),
                fieldname: 'new_to_date',
                fieldtype: 'Date',
                reqd: 1,
                default: frm.doc.to_date
            },
            {
                label: __('Reason for Extension'),
                fieldname: 'reason',
                fieldtype: 'Small Text',
                reqd: 1
            }
        ],
        primary_action_label: __('Update'),
        primary_action: function(values) {
            if (values.new_to_date <= frm.doc.to_date) {
                frappe.msgprint(__('New return date must be after current to date'));
                return;
            }
            
            frappe.call({
                method: 'tripod_hr.events.leave_management.update_leave_return_date',
                args: {
                    leave_application: frm.doc.name,
                    new_to_date: values.new_to_date,
                    reason: values.reason
                },
                freeze: true,
                freeze_message: __('Updating Leave Application...'),
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint({
                            title: __('Success'),
                            indicator: 'green',
                            message: r.message.message
                        });
                        d.hide();
                        frm.reload_doc();
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            indicator: 'red',
                            message: r.message ? r.message.message : __('Failed to update')
                        });
                    }
                }
            });
        }
    });
    
    d.show();
}
