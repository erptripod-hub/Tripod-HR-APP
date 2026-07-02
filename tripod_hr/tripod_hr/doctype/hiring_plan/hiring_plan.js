frappe.ui.form.on('Hiring Plan', {
    monthly_salary(frm){ tp_ctc(frm); },
    accommodation(frm){ tp_ctc(frm); },
    visa(frm){ tp_ctc(frm); },
    medical(frm){ tp_ctc(frm); },
    ticket(frm){ tp_ctc(frm); },
    gosi(frm){ tp_ctc(frm); },
});

function tp_ctc(frm){
    const t = (frm.doc.monthly_salary||0) + (frm.doc.accommodation||0) +
              (frm.doc.visa||0) + (frm.doc.medical||0) +
              (frm.doc.ticket||0) + (frm.doc.gosi||0);
    frm.set_value('total_ctc', t);
}
