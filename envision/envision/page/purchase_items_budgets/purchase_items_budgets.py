from envision.api.utils import get_fiscal_year_quaters, get_in_currency_format, get_total
from erpnext.accounts.utils import get_fiscal_year
import frappe 
from collections import defaultdict


temp_list = []
@frappe.whitelist()
def get_data():
    temp_list.clear()
    # needed this list [{
    #     "item": "abc",
    #     "q1_budgeted": 6, "q1_actual": 7,
    #     "q2_budgeted": 6, "q2_actual": 7,
    #     "q3_budgeted": 6, "q3_actual": 7,
    #     "q4_budgeted": 6, "q4_actual": 7,
    #     "total_budgeted": 6, "total_actual": 7
    # }]
        
    fy_quaters = get_fiscal_year_quaters() # get 4 quaters of 3 month from current fiscal year
    for index, i in enumerate(fy_quaters):
        fy = frappe.db.get_value("Fiscal Year", filters={"year_start_date": i["quarter_start_date"]}, fieldname=["name"])
        name = frappe.db.get_value("Budget", filters={"fiscal_year": fy, "docstatus": 1}, fieldname=["name"])
        get_pi_items_data_with_budget(f"{index + 1}", name) # map data from budgets and purchase invoice
        
    # get a dictionary to store the aggregated values        
    final_list = get_aggregated_values(temp_list) # map if duplicate item and create a final list with inr currency
    
    print("\n\n final list", final_list)
  
    return final_list
    
def get_pi_items_data_with_budget(budget_quater, name):
    from frappe.utils import today
    budget = ""
    budget_accounts = []
    temp_pi_item = []
        
    # budget_quater wise key
    budgeted = ""
    actual = ""
    
    if budget_quater == "1":
        budgeted = "q1_budgeted"
        actual = "q1_actual"
        budget = frappe.get_doc("Budget", name)

    if budget_quater == "2":
        budgeted = "q2_budgeted"
        actual = "q2_actual"
        budget = frappe.get_doc("Budget", name)

    if budget_quater == "3":
        budgeted = "q3_budgeted"
        actual = "q3_actual"
        budget = frappe.get_doc("Budget", name)

    if budget_quater == "4":
        budgeted = "q4_budgeted"
        actual = "q4_actual"
        budget = frappe.get_doc("Budget", name)
    
    fiscal = get_fiscal_year(fiscal_year=budget.fiscal_year)
    
    start_date = str(fiscal[1])
    end_date = str(fiscal[2])
        
    # get budget details  
    for a in budget.accounts:
        budget_accounts.append(a.account)
        
    for b_item in budget.custom_budget_for_items:
        temp_list.append({"item": b_item.item, budgeted: b_item.amount})
    
    # get pi details
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
    pi_list = [{"item": item, actual: amount} for item, amount in sum_dict.items()]
    for i in pi_list:
        temp_list.append(i)
        
def get_aggregated_values(temp_list):
    sums = {}

    for entry in temp_list:
        item = entry['item']
        if item not in sums:
            sums[item] = {}
        
        for key, value in entry.items():
            if key != 'item':
                if key in sums[item]:
                    sums[item][key] += value
                else:
                    sums[item][key] = value
    print("\n\nsdfaa", sums.items())
    data = [{'item': item, **values} for item, values in sums.items()]
    data = get_total(data)
    data = get_in_currency_format(data)
    return data

