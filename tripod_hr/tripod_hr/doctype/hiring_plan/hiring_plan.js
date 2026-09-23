frappe.ui.form.on('Hiring Plan', {
    monthly_salary(frm){ tp_ctc(frm); },
    accommodation(frm){ tp_ctc(frm); },
    visa(frm){ tp_ctc(frm); },
    medical(frm){ tp_ctc(frm); },
    ticket(frm){ tp_ctc(frm); },
    gosi(frm){ tp_ctc(frm); },

    refresh(frm){
        if (frm.is_new()) return;

        // Create Job Opening from this plan row (pre-filled).
        if (frm.doc.status !== 'Filled' && frm.doc.status !== 'Cancelled') {
            frm.add_custom_button(__('Job Opening'), function(){
                frappe.model.with_doctype('Job Opening', function(){
                    let jo = frappe.model.get_new_doc('Job Opening');
                    jo.job_title = frm.doc.designation || frm.doc.raw_designation;
                    jo.designation = frm.doc.designation;
                    jo.company = frm.doc.company;
                    jo.department = frm.doc.department;
                    jo.status = 'Open';
                    jo.custom_hiring_plan = frm.doc.name;
                    frappe.set_route('Form', 'Job Opening', jo.name);
                });
            }, __('Create'));
        }

        // Quick view of openings created from this plan row.
        frm.add_custom_button(__('View Job Openings'), function(){
            frappe.set_route('List', 'Job Opening', { custom_hiring_plan: frm.doc.name });
        }, __('View'));
    }
});

function tp_ctc(frm){
    const t = (frm.doc.monthly_salary||0) + (frm.doc.accommodation||0) +
              (frm.doc.visa||0) + (frm.doc.medical||0) +
              (frm.doc.ticket||0) + (frm.doc.gosi||0);
    frm.set_value('total_ctc', t);
}
