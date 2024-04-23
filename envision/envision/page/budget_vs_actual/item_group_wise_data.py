from collections import defaultdict
from envision.api.utils import get_fiscal_year_quaters, get_in_currency_format, get_total
import frappe
from erpnext.accounts.utils import get_fiscal_year


temp_list = []
@frappe.whitelist()
def item_group_wise_data():
    temp_list.clear()
    
    fy_quaters = get_fiscal_year_quaters()
    for index, i in enumerate(fy_quaters):
        fy = frappe.db.get_value("Fiscal Year", filters={"year_start_date": i["quarter_start_date"]}, fieldname=["name"])
        b_name = frappe.db.get_value("Budget", filters={"fiscal_year": fy}, fieldname=["name"])
        if b_name:
            get_head_pi_items_data_with_budget(f"{index + 1}", b_name) # map data from budgets and purchase invoice

    agrigate_data_dict = get_head_aggregated_values(temp_list) # map if duplicate item and create a final list with inr currency
    total_dict= get_total(agrigate_data_dict)
    ach_data_dict= get_ach(total_dict)
    currency_data = get_in_currency_format(ach_data_dict)
    
    return currency_data


def get_head_pi_items_data_with_budget(budget_quater, name):
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
        temp_list.append({"category": b_item.item, budgeted: b_item.amount, "Head": "Expense"})
    
    # get pi details
    pi_list = frappe.db.get_list("Purchase Invoice", filters={"posting_date": ["between", [start_date, end_date]]}, fields=["name"])
    for pi in pi_list:
        pi_details = frappe.get_doc("Purchase Invoice", pi.name)
        for item in pi_details.items:
            if item.expense_account in budget_accounts:
                temp_pi_item.append({"category": item.item_code, "amount": item.amount})
                
    # Dictionary to store accumulated amounts for each item
    sum_dict = defaultdict(float)

    # Calculate sum for each item
    for item in temp_pi_item:
        sum_dict[item['category']] += item['amount']

    # Convert the accumulated sums into the desired format
    pi_list = [{"category": item, actual: amount, "Head": "Expense"} for item, amount in sum_dict.items()]
    for i in pi_list:
        temp_list.append(i)
    print('temp_list',temp_list)


def get_head_aggregated_values(temp_list):
    sums = {}
    for entry in temp_list:
        category = entry['category']
        head = entry['Head']
        if category not in sums:
            sums[category] = {}
        if head not in sums[category]:
            sums[category][head] = {'category': category, 'Head': head}
        
        for key, value in entry.items():
            if key not in ['category', 'Head']:
                if key in sums[category][head]:
                    sums[category][head][key] = sums[category][head].get(key, 0) + value
                else:
                    sums[category][head][key] = value
    data = []
    for category, heads in sums.items():
        for head, values in heads.items():
            data.append(values)
    return data

def get_ach(data):
    ach_list = data
    for i in ach_list:
        q1_budgeted = i.get('q1_budgeted', 0)  # Get q1_budgeted value or default to 0 if not found
        q1_actual = i.get('q1_actual', 0)  # Get q1_actual value or default to 0 if not found
        i['q1_ach'] = f"{(q1_actual * 100) / q1_budgeted}%" if q1_budgeted != 0 else "0%"

        q2_budgeted = i.get('q2_budgeted', 0)
        q2_actual = i.get('q2_actual', 0)
        i['q2_ach'] = f"{(q2_actual * 100) / q2_budgeted}%" if q2_budgeted != 0 else "0%"

        q3_budgeted = i.get('q3_budgeted', 0)
        q3_actual = i.get('q3_actual', 0)
        i['q3_ach'] = f"{(q3_actual * 100) / q3_budgeted}%" if q3_budgeted != 0 else "0%"

        q4_budgeted = i.get('q4_budgeted', 0)
        q4_actual = i.get('q4_actual', 0)
        i['q4_ach'] = f"{(q4_actual * 100) / q4_budgeted}%" if q4_budgeted != 0 else "0%"

        total_budgeted = i.get('total_budgeted', 0)
        total_actual = i.get('total_actual', 0)
        i['ytm_progression'] = f"{(total_actual * 100) / total_budgeted}%" if total_budgeted != 0 else "0%"
    return ach_list
