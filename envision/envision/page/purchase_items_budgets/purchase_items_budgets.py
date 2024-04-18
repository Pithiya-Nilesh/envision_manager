from erpnext.accounts.utils import get_fiscal_year
import frappe 
from collections import defaultdict


final_list = []
@frappe.whitelist()
def get_data():
    # needed this list [{
    #     "item": "abc",
    #     "q1_budgeted": 6, "q1_actual": 7,
    #     "q2_budgeted": 6, "q2_actual": 7,
    #     "q3_budgeted": 6, "q3_actual": 7,
    #     "q4_budgeted": 6, "q4_actual": 7,
    #     "total_budgeted": 6, "total_actual": 7
    # }]

    get_q1_pi_items_data()
    get_q2_pi_items_data()
    get_q3_pi_items_data()
    get_q4_pi_items_data()
    
    print("\n\n final list", final_list)
    return final_list
    
    
def get_q1_pi_items_data():
    budget = frappe.get_doc("Budget", "PROJ-0001/q1/001")
    fiscal = get_fiscal_year(fiscal_year=budget.fiscal_year)
    
    start_date = str(fiscal[1])
    end_date = str(fiscal[2])

    budget_accounts = []
    temp_pi_item = []
    
    for a in budget.accounts:
        budget_accounts.append(a.account)
        
    for b_item in budget.custom_budget_for_items:
        final_list.append({"item": b_item.item, "q1_budgeted": b_item.amount})
    
    pi_list = frappe.db.get_list("Purchase Invoice", filters={"posting_date": ["between", [start_date, end_date]], "docstatus": 1}, fields=["name"])
    for pi in pi_list:
        pi_details = frappe.get_doc("Purchase Invoice", pi.name)
        for item in pi_details.items:
            if item.project == budget.project and item.expense_account in budget_accounts:
                temp_pi_item.append({"item": item.item_code, "amount": item.amount})
                
    # Dictionary to store accumulated amounts for each item
    sum_dict = defaultdict(float)

    # Calculate sum for each item
    for item in temp_pi_item:
        sum_dict[item['item']] += item['amount']

    # Convert the accumulated sums into the desired format
    pi_list = [{"item": item, "q1_actual": amount} for item, amount in sum_dict.items()]
    for i in pi_list:
        final_list.append(i)
            
def get_q2_pi_items_data():
    pass
    
def get_q3_pi_items_data():
    pass
    
def get_q4_pi_items_data():
    pass