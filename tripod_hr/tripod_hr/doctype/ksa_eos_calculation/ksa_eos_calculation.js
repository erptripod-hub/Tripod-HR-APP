// Copyright (c) 2026, Tripod HR
// KSA End of Service Calculation - Client Script

frappe.ui.form.on('KSA EOS Calculation', {
    refresh: function(frm) {
        // Mark as Cleared button
        if (frm.doc.docstatus === 0 && frm.doc.status === 'In Process') {
            frm.add_custom_button(__('Mark as Cleared'), function() {
                frappe.call({
                    method: 'tripod_hr.tripod_hr.doctype.ksa_eos_calculation.ksa_eos_calculation.mark_as_cleared',
                    args: { docname: frm.doc.name },
                    callback: function(r) {
                        if (r.message) {
                            frm.reload_doc();
                        }
                    }
                });
            }, __('Actions'));
        }

        // Set currency for display
        frm.set_currency_labels(['gross_salary', 'daily_wage', 'gratuity_payable', 
            'leave_salary_payable', 'overtime_payable', 'salary_payable',
            'net_payable', 'total_recovery', 'gross_total'], 'SAR');
    },

    employee: function(frm) {
        if (frm.doc.employee) {
            frappe.call({
                method: 'tripod_hr.tripod_hr.doctype.ksa_eos_calculation.ksa_eos_calculation.get_employee_details',
                args: { employee: frm.doc.employee },
                callback: function(r) {
                    if (r.message) {
                        let data = r.message;
                        frm.set_value('employee_name', data.employee_name);
                        frm.set_value('designation', data.designation);
                        frm.set_value('department', data.department);
                        frm.set_value('branch', data.branch);
                        frm.set_value('company', data.company);
                        frm.set_value('date_of_joining', data.date_of_joining);
                        frm.set_value('nationality', data.nationality);
                        frm.set_value('iqama_no', data.iqama_no);
                        frm.set_value('gosi_no', data.gosi_no);
                        frm.set_value('passport_number', data.passport_number);
                        frm.set_value('bank_name', data.bank_name);
                        frm.set_value('bank_account', data.bank_account);
                        frm.set_value('iban', data.iban);
                        frm.set_value('gross_salary', data.gross_salary);
                        frm.set_value('leaves_accrued', data.leaves_accrued);
                        frm.set_value('leaves_utilized', data.leaves_utilized);
                        frm.set_value('leaves_balance', data.leaves_balance);
                        if (data.loan_advance_recovery) {
                            frm.set_value('loan_advance_recovery', data.loan_advance_recovery);
                        }
                        // Trigger service period calculation after employee fetch
                        setTimeout(() => {
                            frm.trigger('calculate_service_period');
                        }, 500);
                    }
                }
            });
        }
    },

    date_of_joining: function(frm) {
        frm.trigger('calculate_service_period');
    },

    date_of_settlement: function(frm) {
        frm.trigger('calculate_service_period');
        frm.trigger('calculate_gratuity_preview');
    },

    unpaid_leaves_taken: function(frm) {
        frm.trigger('calculate_service_period');
    },

    // ============ SERVICE PERIOD CALCULATION ============
    calculate_service_period: function(frm) {
        if (frm.doc.calculation_mode === 'Manual') return;
        
        if (frm.doc.date_of_joining && frm.doc.date_of_settlement) {
            let joining = frappe.datetime.str_to_obj(frm.doc.date_of_joining);
            let settlement = frappe.datetime.str_to_obj(frm.doc.date_of_settlement);
            
            // Calculate days
            let days = frappe.datetime.get_diff(settlement, joining);
            
            if (days > 0) {
                let years = days / 365.25;
                let unpaid = flt(frm.doc.unpaid_leaves_taken) || 0;
                let eligible = days - unpaid;
                
                frm.set_value('total_service_days', days);
                frm.set_value('employment_years', flt(years, 4));
                frm.set_value('days_eligible_for_gratuity', Math.round(eligible));
                
                // Trigger gratuity calculation
                frm.trigger('calculate_gratuity');
            }
        }
    },

    // ============ GRATUITY CALCULATION ============
    calculate_gratuity: function(frm) {
        if (frm.doc.calculation_mode === 'Manual') return;
        if (frm.doc.override_gratuity) return;
        
        let years = flt(frm.doc.employment_years) || 0;
        let daily = flt(frm.doc.daily_wage) || 0;
        
        // Calculate gratuity days (KSA: 15 days for first 5 yrs, 30 days after)
        let days_first_five = 0;
        let days_after_five = 0;
        
        if (years <= 5) {
            days_first_five = years * 15;
        } else {
            days_first_five = 5 * 15; // 75 days
            days_after_five = (years - 5) * 30;
        }
        
        let total_days = days_first_five + days_after_five;
        let gratuity_before = daily * total_days;
        
        // Get percentage
        let percentage = frm.doc.gratuity_percentage || 100;
        let gratuity_payable = gratuity_before * (percentage / 100);
        
        frm.set_value('gratuity_days_first_five_years', flt(days_first_five, 2));
        frm.set_value('gratuity_days_after_five_years', flt(days_after_five, 2));
        frm.set_value('total_gratuity_days', flt(total_days, 2));
        frm.set_value('gratuity_before_percentage', flt(gratuity_before, 2));
        frm.set_value('gratuity_payable', flt(gratuity_payable, 2));
        
        frm.trigger('calculate_summary');
    },

    separation_type: function(frm) {
        // Clear termination reason if not termination
        if (frm.doc.separation_type !== 'Termination by Employer') {
            frm.set_value('termination_reason', '');
        }
        // Trigger recalculation
        frm.trigger('calculate_gratuity_preview');
    },

    termination_reason: function(frm) {
        frm.trigger('calculate_gratuity_preview');
    },

    calculate_gratuity_preview: function(frm) {
        // Calculate gratuity percentage based on separation type
        if (frm.doc.calculation_mode === 'Manual') return;
        
        let separation = frm.doc.separation_type;
        let years = frm.doc.employment_years || 0;
        let percentage = 100;

        if (separation === 'Termination by Employer' && 
            frm.doc.termination_reason === 'Article 80 (Gross Misconduct)') {
            percentage = 0;
        } else if (separation === 'Resignation') {
            if (years < 2) percentage = 0;
            else if (years < 5) percentage = 33.33;
            else if (years < 10) percentage = 66.67;
            else percentage = 100;
        }

        frm.set_value('gratuity_percentage', percentage);
        frm.trigger('calculate_gratuity');
    },

    // ============ SALARY CALCULATIONS ============
    gross_salary: function(frm) {
        if (frm.doc.calculation_mode === 'Manual') return;
        if (frm.doc.gross_salary) {
            frm.set_value('daily_wage', flt(frm.doc.gross_salary / 30, 2));
            frm.set_value('leave_daily_rate', flt(frm.doc.gross_salary / 30, 2));
            frm.trigger('calculate_gratuity');
            frm.trigger('calculate_leave_salary');
        }
    },

    daily_wage: function(frm) {
        frm.trigger('calculate_gratuity');
    },

    // ============ LEAVE SALARY CALCULATION ============
    leaves_balance: function(frm) {
        frm.trigger('calculate_leave_salary');
    },

    leave_salary_paid: function(frm) {
        frm.trigger('calculate_leave_salary');
    },

    calculate_leave_salary: function(frm) {
        if (frm.doc.calculation_mode === 'Manual') return;
        if (frm.doc.override_leave) return;
        
        let daily = flt(frm.doc.leave_daily_rate) || flt(frm.doc.daily_wage) || 0;
        let balance = flt(frm.doc.leaves_balance) || 0;
        let already_paid = flt(frm.doc.leave_salary_paid) || 0;
        
        let leave_payable = (daily * balance) - already_paid;
        if (leave_payable < 0) leave_payable = 0;
        
        frm.set_value('leave_salary_payable', flt(leave_payable, 2));
        frm.trigger('calculate_summary');
    },

    // ============ OVERTIME CALCULATION ============
    pending_overtime_hours: function(frm) {
        frm.trigger('calculate_overtime');
    },

    overtime_rate_per_hour: function(frm) {
        frm.trigger('calculate_overtime');
    },

    calculate_overtime: function(frm) {
        if (frm.doc.calculation_mode === 'Manual') return;
        if (frm.doc.override_overtime) return;
        
        let hours = flt(frm.doc.pending_overtime_hours) || 0;
        let rate = flt(frm.doc.overtime_rate_per_hour) || 0;
        
        frm.set_value('overtime_payable', flt(hours * rate, 2));
        frm.trigger('calculate_summary');
    },

    // ============ PENDING SALARY CALCULATION ============
    days_worked_pending: function(frm) {
        frm.trigger('calculate_pending_salary');
    },

    current_month_payment: function(frm) {
        frm.trigger('calculate_salary_payable');
    },

    pending_salary_last_month: function(frm) {
        frm.trigger('calculate_salary_payable');
    },

    air_ticket_allowance: function(frm) {
        frm.trigger('calculate_salary_payable');
    },

    other_dues: function(frm) {
        frm.trigger('calculate_salary_payable');
    },

    calculate_pending_salary: function(frm) {
        if (frm.doc.calculation_mode === 'Manual') return;
        
        let gross = flt(frm.doc.gross_salary) || 0;
        let days = frm.doc.days_worked_pending || 0;
        
        // Use actual days in month if settlement date is set
        let days_in_month = 30;
        if (frm.doc.date_of_settlement) {
            let d = frappe.datetime.str_to_obj(frm.doc.date_of_settlement);
            days_in_month = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
        }
        
        if (gross && days) {
            frm.set_value('current_month_payment', flt((gross / days_in_month) * days, 2));
        }
        
        frm.trigger('calculate_salary_payable');
    },

    calculate_salary_payable: function(frm) {
        if (frm.doc.calculation_mode === 'Manual') return;
        if (frm.doc.override_salary_payable) return;
        
        let salary = flt(frm.doc.current_month_payment) + 
                     flt(frm.doc.pending_salary_last_month) + 
                     flt(frm.doc.air_ticket_allowance) + 
                     flt(frm.doc.other_dues);
        
        frm.set_value('salary_payable', flt(salary, 2));
        frm.trigger('calculate_summary');
    },

    // ============ RECOVERY CALCULATION ============
    visa_iqama_expense: function(frm) {
        frm.trigger('calculate_recovery');
    },

    loan_advance_recovery: function(frm) {
        frm.trigger('calculate_recovery');
    },

    notice_period_shortfall: function(frm) {
        frm.trigger('calculate_recovery');
    },

    other_recovery: function(frm) {
        frm.trigger('calculate_recovery');
    },

    calculate_recovery: function(frm) {
        if (frm.doc.calculation_mode === 'Manual') return;
        
        let total = flt(frm.doc.visa_iqama_expense) + 
                    flt(frm.doc.loan_advance_recovery) + 
                    flt(frm.doc.notice_period_shortfall) + 
                    flt(frm.doc.other_recovery);
        
        frm.set_value('total_recovery', flt(total, 2));
        frm.trigger('calculate_summary');
    },

    // ============ FINAL SUMMARY ============
    calculate_summary: function(frm) {
        if (frm.doc.calculation_mode === 'Manual') return;
        
        let gratuity = flt(frm.doc.gratuity_payable) || 0;
        let leave = flt(frm.doc.leave_salary_payable) || 0;
        let overtime = flt(frm.doc.overtime_payable) || 0;
        let salary = flt(frm.doc.salary_payable) || 0;
        let recovery = flt(frm.doc.total_recovery) || 0;
        
        let gross_total = gratuity + leave + overtime + salary;
        let net = gross_total - recovery;
        
        frm.set_value('total_gratuity', flt(gratuity, 2));
        frm.set_value('total_leave_salary', flt(leave, 2));
        frm.set_value('total_overtime', flt(overtime, 2));
        frm.set_value('total_salary_payable', flt(salary, 2));
        frm.set_value('gross_total', flt(gross_total, 2));
        frm.set_value('total_deductions', flt(recovery, 2));
        frm.set_value('net_payable', flt(net, 2));
    },

    calculation_mode: function(frm) {
        // When switching to Manual, stop auto-calculations
        if (frm.doc.calculation_mode === 'Manual') {
            frappe.show_alert({
                message: __('Manual mode: Auto-calculations disabled. You can edit all fields directly.'),
                indicator: 'orange'
            }, 5);
        } else {
            frappe.show_alert({
                message: __('Auto mode: Calculations will be performed automatically.'),
                indicator: 'green'
            }, 5);
            // Recalculate everything
            frm.trigger('calculate_service_period');
        }
    }
});
