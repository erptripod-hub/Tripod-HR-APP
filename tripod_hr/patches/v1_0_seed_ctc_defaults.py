"""
One-time patch: seed CTC Component Default for each existing branch.
Idempotent — safe to run multiple times.
"""
import frappe


def execute():
    branches = [
        # (branch_name, company, country, is_ksa_national,
        #  accommodation, visa, iqama, medical, ticket, transport,
        #  gratuity_1to5, gratuity_5plus, probation_yrs)
        ("Fit Out UAE", "Tripod Media", "UAE", 0, 650, 180, 0, 58, 62.5, 22, 21, 30, 1),
        ("Dubai Production", "Tripod Media", "UAE", 0, 650, 180, 0, 58, 62.5, 22, 21, 30, 1),
        ("Dubai Office Staff", "Tripod Media", "UAE", 0, 0, 180, 0, 200, 175, 0, 21, 30, 1),
        ("KSA Office Staff", "Tripod Global", "KSA", 0, 0, 0, 87, 282, 182, 0, 15, 30, 2),
        ("KSA National", "Tripod Global", "KSA", 1, 0, 0, 0, 0, 0, 0, 15, 30, 2),
        ("KSA Labour", "Tripod Global", "KSA", 0, 800, 0, 96, 55, 22, 63, 15, 30, 2),
        ("KSA Fit Out", "Tripod Global", "KSA", 0, 800, 0, 57, 54, 63, 22, 15, 30, 2),
        ("Luxxe Labour", "Luxxe", "UAE", 0, 650, 180, 0, 58, 62.5, 22, 21, 30, 1),
        ("Luxxe Office", "Luxxe", "UAE", 0, 0, 180, 0, 350, 142, 0, 21, 30, 1),
    ]
    
    for row in branches:
        (branch_name, company, country, is_ksa_nat,
         accom, visa, iqama, medical, ticket, transport,
         grat15, grat5p, probation) = row
        
        if not frappe.db.exists("Company", company):
            frappe.log_error(f"Skipping {branch_name}: Company {company} not found", "CTC Patch")
            continue
        
        if not frappe.db.exists("Branch", branch_name):
            branch_doc = frappe.new_doc("Branch")
            branch_doc.branch = branch_name
            try:
                branch_doc.insert(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(f"Branch create failed {branch_name}: {e}", "CTC Patch")
                continue
        
        if frappe.db.exists("CTC Component Default", branch_name):
            doc = frappe.get_doc("CTC Component Default", branch_name)
        else:
            doc = frappe.new_doc("CTC Component Default")
            doc.branch = branch_name
        
        doc.company = company
        doc.country = country
        doc.is_ksa_national_branch = is_ksa_nat
        doc.default_accommodation = accom
        doc.default_visa = visa
        doc.default_iqama = iqama
        doc.default_medical_insurance = medical
        doc.default_ticket_allowance = ticket
        doc.default_transport = transport
        doc.gratuity_days_year1to5 = grat15
        doc.gratuity_days_year5plus = grat5p
        doc.probation_years_no_gratuity = probation
        
        try:
            doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"CTC default save failed {branch_name}: {e}", "CTC Patch")
    
    frappe.db.commit()
    print(f"Seeded {len(branches)} CTC Component Defaults")
