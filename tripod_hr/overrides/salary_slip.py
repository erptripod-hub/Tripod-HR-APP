import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip


ALLOWED_COMPANIES = [
    "TRIPOD GLOBAL SHOPFIT MANUFACTURING COMPANY",
    "Sanctuaire Exotique Interior Decoration LLC",
    "Tripod Media FZ LLC",
]

ACTUAL_COMPONENTS = [
    "Basic",
    "HRA",
    "Transport Allowance",
    "Cost of Living Allowance",
    "Fuel Allowance",
    "Other Allowance",
    "Other Allowances",
    "Car Allowance",
    "Mobile Allowance",
]

ALLOWED_NON_BASIC = [
    "HRA",
    "Transport Allowance",
    "Cost of Living Allowance",
    "Fuel Allowance",
    "Other Allowance",
    "Other Allowances",
    "Car Allowance",
    "Mobile Allowance",
]


def get_deduction_amount(total_salary):
    """
    Slab logic:
    - 8000 and below     : No deduction
    - 8001 to 9999       : Deduct to make net = 8000
    - 10000 to 10999     : 20% deduction
    - 11000 and above    : 25% deduction
    """
    if total_salary <= 8000:
        return 0
    elif total_salary < 10000:
        return total_salary - 8000
    elif total_salary < 11000:
        return total_salary * 0.20
    else:
        return total_salary * 0.25


class CustomSalarySlip(SalarySlip):

    def calculate_net_pay(self):
        # First let ERPNext do its standard calculation
        super().calculate_net_pay()

        # Now apply our custom deduction on top
        self.apply_tripod_salary_deduction()

    def apply_tripod_salary_deduction(self):
        # Check company
        if self.company not in ALLOWED_COMPANIES:
            return

        # Get deduction percent from Salary Structure Assignment
        ssa = frappe.db.get_value(
            "Salary Structure Assignment",
            {
                "employee": self.employee,
                "salary_structure": self.salary_structure,
                "docstatus": 1,
            },
            ["name", "custom_deduction_percent"],
            as_dict=1,
        )

        if not ssa:
            return

        deduction_percent = ssa.custom_deduction_percent or 0

        if deduction_percent <= 0:
            return

        # Calculate actual total salary from actual components only (exclude provisions)
        total_salary = 0
        for row in self.earnings:
            if row.salary_component in ACTUAL_COMPONENTS:
                total_salary += row.amount

        # Calculate deduction based on slab
        deduction_amount = get_deduction_amount(total_salary)

        if deduction_amount <= 0:
            return

        # Collect non-basic rows with value
        non_basic_rows = []
        for row in self.earnings:
            if row.salary_component in ALLOWED_NON_BASIC and row.amount > 0:
                non_basic_rows.append(row)

        if not non_basic_rows:
            frappe.throw(
                "No non-basic components found for employee "
                + str(self.employee_name)
                + ". Cannot apply salary deduction."
            )

        # Sum total non-basic
        total_non_basic = sum(row.amount for row in non_basic_rows)

        if deduction_amount > total_non_basic:
            frappe.throw(
                "Salary deduction "
                + str(round(deduction_amount, 2))
                + " exceeds total non-basic components "
                + str(round(total_non_basic, 2))
                + " for employee "
                + str(self.employee_name)
                + ". Please review salary structure."
            )

        # Apply proportional deduction on non-basic components
        for row in non_basic_rows:
            proportion = row.amount / total_non_basic
            deduction_for_this = round(proportion * deduction_amount, 2)
            row.amount = round(row.amount - deduction_for_this, 2)

        # Recalculate gross pay from earnings (excluding provisions)
        new_actual_gross = 0
        for row in self.earnings:
            if row.salary_component in ACTUAL_COMPONENTS:
                new_actual_gross += row.amount

        # Recalculate total deductions
        total_deductions = 0
        for row in self.deductions:
            total_deductions += row.amount

        # Recalculate full gross including provisions for ERPNext consistency
        full_gross = 0
        for row in self.earnings:
            full_gross += row.amount

        # Set correct values
        self.gross_pay = round(full_gross, 2)
        self.net_pay = round(full_gross - total_deductions, 2)
        self.rounded_total = round(self.net_pay, 2)
        self.total_in_words = frappe.utils.money_in_words(self.rounded_total, self.currency)
