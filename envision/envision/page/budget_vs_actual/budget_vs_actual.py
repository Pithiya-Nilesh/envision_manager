from collections import defaultdict
from envision.api.utils import get_fiscal_year_quaters, get_in_currency_format, get_total
from erpnext.accounts.utils import get_fiscal_year
import frappe, json

temp_list = []

@frappe.whitelist()
def get_data():
    temp_list.clear()
    
    final_departments = []
    
    departments = frappe.db.get_list("Department", fields=["name"])
    
    for department in departments:
        projects = frappe.db.get_list("Project", filters={"department": department.name}, fields=["name"], pluck="name")
        if projects:
            final_departments.append({department.name: projects})
    
    fy_quaters = get_fiscal_year_quaters() # get 4 quaters of 3 month from current fiscal year
    for index, i in enumerate(fy_quaters):
        fy = frappe.db.get_value("Fiscal Year", filters={"year_start_date": i["quarter_start_date"]}, fieldname=["name"])
        
        for department in final_departments:
            for key, projects in department.items():
                for project in projects:
                    b_name = frappe.db.get_value("Budget", filters={"fiscal_year": fy, "project": project, "docstatus": 1}, fieldname=["name"])
                    if b_name:
                        get_pi_data_with_budget(f"{index + 1}", b_name, project, key) # map data from budgets and purchase invoice
                        get_si_data_with_budget(f"{index + 1}", b_name, project, key)
                        
    agrigate_data = get_aggregated_values(temp_list) # map if duplicate item and create a final list with inr currency
    total_list = get_total(agrigate_data)
    ach_list = get_ach(total_list)
    sum_r_plus_exp = sum_revenue_plus_expense(ach_list)
    currency_data = get_in_currency_format(sum_r_plus_exp)
    final_list = remove_duplicate_departments(currency_data)
    return final_list
    
def get_pi_data_with_budget(budget_quater, name, project, department):
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
        temp_list.append({"department": department, "type": "Expense", budgeted: b_item.amount})
    
    
    # get pi details
    pi_list = frappe.db.get_list("Purchase Invoice", filters={"posting_date": ["between", [start_date, end_date]], "docstatus": 1}, fields=["name"])
    for pi in pi_list:
        pi_details = frappe.get_doc("Purchase Invoice", pi.name)
        for item in pi_details.items:
            if item.project == budget.project and item.expense_account in budget_accounts:
                temp_pi_item.append({"department": department, "amount": item.amount})
                
    # Dictionary to store accumulated amounts for each item
    sum_dict = defaultdict(float)

    # Calculate sum for each item
    for item in temp_pi_item:
        sum_dict[item['department']] += item['amount']

    # Convert the accumulated sums into the desired format
    pi_list = [{"department": item, "type": "Expense", actual: amount} for item, amount in sum_dict.items()]
    for i in pi_list:
        temp_list.append(i)
       
def get_si_data_with_budget(budget_quater, name, project, department):
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
        temp_list.append({"department": department, "type": "Revenue", budgeted: b_item.amount})
    
    
    # get pi details
    si_list = frappe.db.get_list("Sales Invoice", filters={"posting_date": ["between", [start_date, end_date]], "docstatus": 1}, fields=["name"])
    for si in si_list:
        si_details = frappe.get_doc("Sales Invoice", si.name)
        for item in si_details.items:
            if item.project == budget.project and item.income_account in budget_accounts:
                temp_pi_item.append({"department": department, "amount": item.amount})
                
    # Dictionary to store accumulated amounts for each item
    sum_dict = defaultdict(float)

    # Calculate sum for each item
    for item in temp_pi_item:
        sum_dict[item['department']] += item['amount']

    # Convert the accumulated sums into the desired format
    pi_list = [{"department": item, "type": "Revenue", actual: amount} for item, amount in sum_dict.items()]
    for i in pi_list:
        temp_list.append(i)
    print("\n\n temp list", temp_list)
               
def get_aggregated_values(temp_list):
    sums = {}

    for entry in temp_list:
        department = entry['department']
        expense_type = entry['type']
        if department not in sums:
            sums[department] = {}
        if expense_type not in sums[department]:
            sums[department][expense_type] = {'department': department, 'type': expense_type}
        
        for key, value in entry.items():
            if key not in ['department', 'type']:
                if key in sums[department][expense_type]:
                    sums[department][expense_type][key] += value
                else:
                    sums[department][expense_type][key] = value

    data = []
    for department, types in sums.items():
        for expense_type, values in types.items():
            data.append(values)
    return data 

def get_ach(data):
    ach_list = data
    for i in ach_list:
        if 'q1_actual' in i:
            i['q1_ach'] = f"{(i['q1_actual'] * 100) / i['q1_budgeted']}%"
        else:
            i['q1_ach'] = "0%"
            
        if 'q2_actual' in i:
            i['q2_ach'] = f"{(i['q2_actual'] * 100) / i['q2_budgeted']}%"
        else:
            i['q2_ach'] = "0%"
            
        if 'q3_actual' in i:
            i['q3_ach'] = f"{(i['q3_actual'] * 100) / i['q3_budgeted']}%"
        else:
            i['q3_ach'] = "0%"
            
        if 'q4_actual' in i:
            i['q4_ach'] = f"{(i['q4_actual'] * 100) / i['q4_budgeted']}%"
        else:
            i['q4_ach'] = "0%"
            
        if 'total_actual' in i and 'total_budgeted' in i:
            i['ytm_progression'] = f"{(i['total_actual'] * 100) / i['total_budgeted']}%"
        else:
            i['ytm_progression'] = "0%"
    return ach_list

def remove_duplicate_departments(data):
    dept = []
    for i in data:
        if i["department"] in dept:
            i["department"] = ""
        dept.append(i["department"])
    return data

def sum_revenue_plus_expense(data):
    # implement sum of this is panding
    return data
    
    

# final data list
"""
    [
        {
            "department": "", 
            "revenue_or_expense": "",
            "q1_b": "", 
            "q1_a": "", 
            "q1_ach": "",
            "q2_b": "", 
            "q2_a": "", 
            "q2_ach": "",
            "q3_b": "", 
            "q3_a": "", 
            "q3_ach": "",
            "q4_b": "", 
            "q4_a": "",
            "q4_ach": "",
            "total_budget: "",
            "progression_actual": "",
            "ytm_progressive": "",
            "fy": "",
            "growth": "",
        }
    ]

"""

"""
    "message": [
        {
            "Accounts": [
                "PROJ-0003",
                "PROJ-0001"
            ]
        },
        {
        "Customer Service": [
            "PROJ-0002"
            ]
        }
    ]
"""

