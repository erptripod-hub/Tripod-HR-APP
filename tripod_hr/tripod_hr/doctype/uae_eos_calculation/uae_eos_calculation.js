// UAE EOS Calculation - Client Script
// Handles live UI calculations and auto-fetch on employee select

frappe.ui.form.on('UAE EOS Calculation', {
    refresh: function(frm) {
        // Status indicator color
        if (frm.doc.status === 'In Process') {
            frm.page.set_indicator(__('In Process'), 'orange');
        } else if (frm.doc.status === 'Cleared') {
            frm.page.set_indicator(__('Cleared - Ready to Submit'), 'blue');
        } else if (frm.doc.status === 'Completed') {
            frm.page.set_indicator(__('Completed'), 'green');
        } else if (frm.doc.status === 'Cancelled') {
            frm.page.set_indicator(__('Cancelled'), 'red');
        }

        // Recalculate button
        if (!frm.is_new()) {
            frm.add_custom_button(__('Recalculate All'), function() {
                frm.trigger('recalculate_all');
            });
        }

        // Hide "Mark as Cleared" button if already cleared/submitted
        if (frm.doc.status === 'Cleared' || frm.doc.docstatus === 1) {
            frm.set_df_property('mark_as_cleared', 'hidden', 1);
        } else {
            frm.set_df_property('mark_as_cleared', 'hidden', 0);
        }
    },

    mark_as_cleared: function(frm) {
        if (frm.is_new() || frm.is_dirty()) {
            frappe.msgprint(__('Please save the document first before marking as Cleared.'));
            return;
        }
        frappe.confirm(
            __('Are you sure all calculations are final and you want to mark this as Cleared? After this, only Submit will move it to Completed.'),
            function() {
                frappe.call({
                    method: 'tripod_hr.tripod_hr.doctype.uae_eos_calculation.uae_eos_calculation.mark_as_cleared',
                    // For Server Script API: use 'mark_as_cleared'
                    args: { docname: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Marking as Cleared...'),
                    callback: function(r) {
                        if (r.message) {
                            frm.reload_doc();
                        }
                    }
                });
            }
        );
    },

    employee: function(frm) {
        if (!frm.doc.employee) return;

        frappe.call({
            method: 'tripod_hr.tripod_hr.doctype.uae_eos_calculation.uae_eos_calculation.get_employee_details',
            // If you place the controller elsewhere, change the method path accordingly
            // For Server Script approach use: 'uae_eos_calculation.get_employee_details'
            args: { employee: frm.doc.employee },
            callback: function(r) {
                if (!r.message) return;
                const d = r.message;

                // Employee fields
                frm.set_value('employee_name', d.employee_name);
                frm.set_value('designation', d.designation);
                frm.set_value('department', d.department);
                frm.set_value('branch', d.branch);
                frm.set_value('company', d.company);
                frm.set_value('date_of_joining', d.date_of_joining);
                frm.set_value('nationality', d.nationality);
                frm.set_value('emirates_id', d.emirates_id);
                frm.set_value('passport_number', d.passport_number);
                frm.set_value('bank_account', d.bank_account);
                frm.set_value('iban', d.iban);

                // Salary fields
                frm.set_value('basic_salary', d.basic_salary || 0);
                frm.set_value('housing_allowance', d.housing_allowance || 0);
                frm.set_value('transportation_allowance', d.transportation_allowance || 0);
                frm.set_value('other_allowance', d.other_allowance || 0);

                // Leave & Loan
                if (d.leaves_balance !== undefined) {
                    frm.set_value('leaves_balance', d.leaves_balance);
                }
                if (d.loan_advance_recovery) {
                    frm.set_value('loan_advance_recovery', d.loan_advance_recovery);
                }

                // Trigger downstream calcs
                frm.trigger('recalculate_all');
                frappe.show_alert({
                    message: __('Employee details fetched successfully'),
                    indicator: 'green'
                });
            }
        });
    },

    // ------------------------------------------------------------------
    // Trigger recalc on relevant field changes
    // ------------------------------------------------------------------
    date_of_settlement: function(frm) { frm.trigger('recalculate_all'); },
    date_of_joining:    function(frm) { frm.trigger('recalculate_all'); },
    exit_status:        function(frm) { frm.trigger('set_leave_basis'); frm.trigger('recalculate_all'); },
    basic_salary:       function(frm) { frm.trigger('recalculate_all'); },
    housing_allowance:  function(frm) { frm.trigger('recalculate_all'); },
    transportation_allowance: function(frm) { frm.trigger('recalculate_all'); },
    other_allowance:    function(frm) { frm.trigger('recalculate_all'); },
    gratuity_base_type: function(frm) { frm.trigger('calc_gratuity'); frm.trigger('calc_summary'); },
    gratuity_reduction_percent: function(frm) { frm.trigger('calc_gratuity'); frm.trigger('calc_summary'); },
    override_gratuity:  function(frm) { frm.trigger('calc_gratuity'); frm.trigger('calc_summary'); },
    calculation_mode:   function(frm) { frm.trigger('recalculate_all'); },
    leave_calculation_basis: function(frm) { frm.trigger('calc_leave'); frm.trigger('calc_summary'); },
    leaves_balance:     function(frm) { frm.trigger('calc_leave'); frm.trigger('calc_summary'); },
    leave_salary_paid:  function(frm) { frm.trigger('calc_leave'); frm.trigger('calc_summary'); },
    leave_salary_held_visa_change: function(frm) { frm.trigger('calc_leave'); frm.trigger('calc_summary'); },
    override_leave:     function(frm) { frm.trigger('calc_leave'); frm.trigger('calc_summary'); },
    pending_overtime_hours: function(frm) { frm.trigger('calc_overtime'); frm.trigger('calc_summary'); },
    overtime_rate_per_hour: function(frm) { frm.trigger('calc_overtime'); frm.trigger('calc_summary'); },
    override_overtime:  function(frm) { frm.trigger('calc_overtime'); frm.trigger('calc_summary'); },
    days_worked_pending: function(frm) { frm.trigger('calc_pending_salary'); frm.trigger('calc_summary'); },
    unpaid_leaves_taken: function(frm) { frm.trigger('calc_pending_salary'); frm.trigger('calc_summary'); },
    air_ticket_allowance: function(frm) { frm.trigger('calc_pending_salary'); frm.trigger('calc_summary'); },
    override_salary_payable: function(frm) { frm.trigger('calc_pending_salary'); frm.trigger('calc_summary'); },
    visa_labour_card_expense: function(frm) { frm.trigger('calc_recovery'); frm.trigger('calc_summary'); },
    loan_advance_recovery: function(frm) { frm.trigger('calc_recovery'); frm.trigger('calc_summary'); },
    notice_period_shortfall: function(frm) { frm.trigger('calc_recovery'); frm.trigger('calc_summary'); },
    other_recovery:     function(frm) { frm.trigger('calc_recovery'); frm.trigger('calc_summary'); },

    // ------------------------------------------------------------------
    // Calculation triggers
    // ------------------------------------------------------------------
    set_leave_basis: function(frm) {
        if (frm.doc.exit_status === 'End of Contract') {
            frm.set_value('leave_calculation_basis', 'Full Month Salary (End of Contract)');
        } else if (frm.doc.exit_status) {
            frm.set_value('leave_calculation_basis', 'Basic Salary Only (Resignation/Termination)');
        }
    },

    recalculate_all: function(frm) {
        frm.trigger('calc_gross_pay');
        frm.trigger('calc_service_period');
        frm.trigger('calc_gratuity');
        frm.trigger('calc_leave');
        frm.trigger('calc_overtime');
        frm.trigger('calc_pending_salary');
        frm.trigger('calc_recovery');
        frm.trigger('calc_summary');
    },

    calc_gross_pay: function(frm) {
        const gross = (flt(frm.doc.basic_salary) + flt(frm.doc.housing_allowance)
            + flt(frm.doc.transportation_allowance) + flt(frm.doc.other_allowance));
        frm.set_value('gross_pay_per_month', gross);
    },

    calc_service_period: function(frm) {
        if (!frm.doc.date_of_joining || !frm.doc.date_of_settlement) return;
        const join = frappe.datetime.str_to_obj(frm.doc.date_of_joining);
        const sett = frappe.datetime.str_to_obj(frm.doc.date_of_settlement);
        const days = Math.round((sett - join) / (1000 * 60 * 60 * 24));
        if (days < 0) {
            frappe.msgprint(__('Settlement date cannot be earlier than joining date'));
            return;
        }
        frm.set_value('total_service_days', days);
        frm.set_value('employment_years', flt(days / 365.25, 4));
    },

    calc_gratuity: function(frm) {
        // Determine base
        let base = 0;
        const base_type = frm.doc.gratuity_base_type || 'Basic Only';
        if (base_type === 'Basic Only') {
            base = flt(frm.doc.basic_salary);
        } else if (base_type === 'Basic + Housing') {
            base = flt(frm.doc.basic_salary) + flt(frm.doc.housing_allowance);
        } else {
            base = flt(frm.doc.gross_pay_per_month);
        }
        frm.set_value('gratuity_base_amount', base);
        frm.set_value('daily_basic_wage', flt(base / 30, 2));

        const years = flt(frm.doc.employment_years);
        const days = flt(frm.doc.total_service_days);
        const daily = base / 30;

        // Set days_per_year display
        let dpy = 0;
        if (years < 1) dpy = 0;
        else if (years <= 5) dpy = 21;
        else dpy = 30;
        frm.set_value('gratuity_days_per_year', dpy);

        // Skip auto-calc if overridden
        if (frm.doc.override_gratuity || frm.doc.calculation_mode === 'Manual') return;

        let gratuity = 0;
        if (years < 1) {
            gratuity = 0;
        } else if (years <= 5) {
            gratuity = daily * 21 * (days / 365.25);
        } else {
            const first_five_days = 5 * 365.25;
            const remaining_days = days - first_five_days;
            gratuity = (daily * 21 * 5) + (daily * 30 * (remaining_days / 365.25));
        }

        // Reduction
        if (flt(frm.doc.gratuity_reduction_percent)) {
            gratuity = gratuity * (1 - flt(frm.doc.gratuity_reduction_percent) / 100);
        }

        // Cap: 24 months wage
        const cap = base * 24;
        if (cap && gratuity > cap) gratuity = cap;

        frm.set_value('gratuity_payable', flt(gratuity, 2));
    },

    calc_leave: function(frm) {
        let daily = 0;
        if (frm.doc.leave_calculation_basis === 'Full Month Salary (End of Contract)') {
            daily = flt(frm.doc.gross_pay_per_month) / 30;
        } else {
            daily = flt(frm.doc.basic_salary) / 30;
        }
        frm.set_value('leave_daily_rate', flt(daily, 2));

        if (frm.doc.override_leave || frm.doc.calculation_mode === 'Manual') return;

        let gross_leave = daily * flt(frm.doc.leaves_balance);
        let net = gross_leave - flt(frm.doc.leave_salary_paid)
                  - flt(frm.doc.leave_salary_held_visa_change);
        if (net < 0) net = 0;
        frm.set_value('leave_salary_payable', flt(net, 2));
    },

    calc_overtime: function(frm) {
        if (frm.doc.override_overtime || frm.doc.calculation_mode === 'Manual') return;
        const ot = flt(frm.doc.pending_overtime_hours) * flt(frm.doc.overtime_rate_per_hour);
        frm.set_value('overtime_payable', flt(ot, 2));
    },

    calc_pending_salary: function(frm) {
        const gross = flt(frm.doc.gross_pay_per_month);
        const days = flt(frm.doc.days_worked_pending);
        const unpaid = flt(frm.doc.unpaid_leaves_taken);
        let net_days = days - unpaid;
        if (net_days < 0) net_days = 0;
        const pending = gross ? (gross / 30) * net_days : 0;
        frm.set_value('pending_salary_last_month', flt(pending, 2));

        if (frm.doc.override_salary_payable || frm.doc.calculation_mode === 'Manual') return;
        const total = pending + flt(frm.doc.air_ticket_allowance);
        frm.set_value('salary_payable', flt(total, 2));
    },

    calc_recovery: function(frm) {
        const total = flt(frm.doc.visa_labour_card_expense)
                    + flt(frm.doc.loan_advance_recovery)
                    + flt(frm.doc.notice_period_shortfall)
                    + flt(frm.doc.other_recovery);
        frm.set_value('total_recovery', flt(total, 2));
    },

    calc_summary: function(frm) {
        const grat = flt(frm.doc.gratuity_payable);
        const leave = flt(frm.doc.leave_salary_payable);
        const ot = flt(frm.doc.overtime_payable);
        const sal = flt(frm.doc.salary_payable);
        const ded = flt(frm.doc.total_recovery);

        frm.set_value('total_gratuity', grat);
        frm.set_value('total_leave_salary', leave);
        frm.set_value('total_overtime', ot);
        frm.set_value('total_salary_payable', sal);

        const gross = grat + leave + ot + sal;
        frm.set_value('gross_total', flt(gross, 2));
        frm.set_value('total_deductions', flt(ded, 2));
        frm.set_value('net_payable', flt(gross - ded, 2));
    }
});

// Helper
function flt(value) {
    if (value === null || value === undefined || value === '') return 0;
    return parseFloat(value) || 0;
}
