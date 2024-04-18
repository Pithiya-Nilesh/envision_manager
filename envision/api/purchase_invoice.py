import frappe, json
from erpnext.accounts.utils import get_fiscal_year


# def validate_budget_for_item(pi, method):
#     """ validate budget per item in purchase invoice """

#     fiscal_year = get_fiscal_year(date=pi.posting_date, company=pi.company)
    
#     budget = frappe.db.get_value("Budget", filters={"fiscal_year": fiscal_year[0]}, fieldname=["name"])
#     budget = frappe.get_doc("Budget", budget)
   
#     # return if not applicable on bucking actual expenses in budget
#     # if not budget.applicable_on_booking_actual_expenses:
#     #     return
    
#     # b_enable_budget = budget.applicable_on_booking_actual_expenses
#     b_anual_action = budget.action_if_annual_budget_exceeded
#     b_monthly_action = budget.action_if_accumulated_monthly_budget_exceeded
    
#     b_budget_against = budget.budget_against
#     # b_company = budget.company
#     # b_project = budget.project
#     # b_cost_center = budget.cost_center
#     b_fiscal_year = budget.fiscal_year
#     b_budget_for_items = budget.custom_budget_for_items

#     # print("\n\n budget", budget.as_dict())

#     if pi.company != budget.company:
#         return 
    
#     # return if not project or cost center in Purchase Invoice
#     if budget.budget_against == "Project":
#         if pi.project != budget.project:
#             return
#         else:
#             check_items_budget = check_items_budget(budget.custom_budget_for_items, pi.items, "Project", pi.company)
    
#     if budget.budget_against == "Cost Center":
#         if pi.cost_center != budget.cost_center:
#             return
#         else:
#             check_items_budget = check_items_budget(budget.custom_budget_for_items, pi.items, "Cost Center", pi.company)
            
        
#     # for b_item in b_budget_for_items:
#     print("\n\n b", budget.custom_budget_for_items.as_dict())
#     print("\n\n p", pi.items.as_dict())
     

def validate_budget_for_item(pi, method):
    """ validate budget per item in purchase invoice """
    is_cost_center = True if pi.cost_center else False
    dimension = "Cost Center" if pi.cost_center else "Project" if pi.project else ""
    
    gl = get_data_from_gl(pi.items, dimension, pi.company, is_cost_center)


    fiscal_year = get_fiscal_year(date=pi.posting_date, company=pi.company)
    
    budgets = frappe.db.get_list("Budget", filters={"fiscal_year": fiscal_year[0], "project": pi.project, "cost_center": pi.cost_center, "company": pi.company}, fields=["name"])
    
    print("\n\n budgets", budgets)
    
    budget = frappe.get_doc("Budget", budget)
   
    # return if not applicable on bucking actual expenses in budget
    # if not budget.applicable_on_booking_actual_expenses:
    #     return
    

    # print("\n\n budget", budget.as_dict())

    if pi.company != budget.company:
        return 
    
    # return if not project or cost center in Purchase Invoice
    if budget.budget_against == "Project":
        if pi.project != budget.project:
            return
        else:
            check_items_budget = check_items_budget(budget.custom_budget_for_items, pi.items, "Project", pi.company)
    
    if budget.budget_against == "Cost Center":
        if pi.cost_center != budget.cost_center:
            return
        else:
            check_items_budget = check_items_budget(budget.custom_budget_for_items, pi.items, "Cost Center", pi.company, True)
            
        
    # for b_item in b_budget_for_items:
    print("\n\n b", budget.custom_budget_for_items.as_dict())
    print("\n\n p", pi.items.as_dict())
    

def check_items_budget(budget_items, pi_items, dimension, company, is_cost_center=False):
    pass


def get_data_from_gl(pi_items, dimention, company, is_cost_center):
    accounts = []
    filters = {}
    
    for item in pi_items:
        accounts.append("")
    
    filters["company"] = company,
    
    if is_cost_center: 
        filters["cost_center"] = dimention
    else:
        filters["project"] = dimention
    
            
    gl_entries = frappe.db.get_list("GL Entry", filters=filters, fields=[])
