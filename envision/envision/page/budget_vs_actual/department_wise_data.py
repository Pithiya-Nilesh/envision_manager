from collections import defaultdict
from envision.api.utils import get_fiscal_year_quaters, get_in_currency_format, get_previous_fiscal_year_quaters, get_total
from erpnext.accounts.utils import get_fiscal_year
import frappe, json

temp_list = []
data_l = []


@frappe.whitelist()
def department_wise_data():
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
                        get_si_data_with_budget(f"{index + 1}", b_name, project, key)
                        get_pi_data_with_budget(f"{index + 1}", b_name, project, key) # map data from budgets and purchase invoice
                        
    final_list = get_final_list()
    
    return final_list
    
def get_final_list():
    agrigate_data = get_aggregated_values(temp_list) # map if duplicate item and create a final list with inr currency
    total_list = get_total(agrigate_data)
    ach_list = get_ach(total_list)
    current_year_data = sum_revenue_plus_expense(ach_list)
    previous_year_data = get_previous_year_data()
    maped_data = map_current_year_and_last_year_data(current_year_data, previous_year_data)
    currency_data = get_in_currency_format(maped_data)
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
    output = []

    for index, entry in enumerate(data):
        if entry['type'] == 'Expense':
            department_name = entry['department'] + " Margin"
            revenue_entry = next((x for x in data if x['department'] == entry['department'] and x['type'] == 'Revenue'), None)
            if revenue_entry:
                margin_entry = {
                    "department": department_name,
                    "type": "",
                    "q1_budgeted": "0",
                    "q1_actual": str(revenue_entry.get('q1_actual', 0 - entry.get('q1_actual', 0))),
                    "q2_budgeted": "0",
                    "q2_actual": str(revenue_entry.get('q2_actual', 0) - entry.get('q2_actual', 0)),
                    "q3_budgeted": "0",
                    "q4_budgeted": "0",
                    "total_budgeted": "0",
                    "total_actual": str(revenue_entry.get('total_actual', 0) - entry.get('total_actual', 0)),
                }
                output.append(margin_entry)
        if index == 0:
            output.append(entry)
        
        # Append the next entry if it exists
        if index < len(data) - 1:
            output.append(data[index + 1])
    return output
 
@frappe.whitelist()       
def get_previous_year_data():
    final_departments = []
    
    departments = frappe.db.get_list("Department", fields=["name"])
    
    for department in departments:
        projects = frappe.db.get_list("Project", filters={"department": department.name}, fields=["name"], pluck="name")
        if projects:
            final_departments.append({department.name: projects})
    
    pfy_quaters = get_previous_fiscal_year_quaters() # get 4 quaters of 3 month from current fiscal year
    
    # print("\n\n asdf pfy", pfy_quaters)
    
    for index, i in enumerate(pfy_quaters):
        fy = frappe.db.get_value("Fiscal Year", filters={"year_start_date": i["quarter_start_date"]}, fieldname=["name"])
        
        # print("\n\n final", final_departments)
        for department in final_departments:
            for key, projects in department.items():
                for project in projects:
                    # print("pro", project, fy)
                    b_name = frappe.db.get_value("Budget", filters={"fiscal_year": fy, "project": project, "docstatus": 1}, fieldname=["name"])
                    # print("\n\n bu name", b_name)
                    if b_name:
                        get_previous_year_si_data(f"{index + 1}", b_name, project, key)
                        # get_pi_data_with_budget(f"{index + 1}", b_name, project, key)
    
    pfy_revenue = defaultdict(float)

    # Iterate through the data and sum up the revenue for each department
    for entry in data_l:
        department = entry['department']
        revenue_q1 = entry.get('q1_actual', 0)
        revenue_q2 = entry.get('q2_actual', 0)
        revenue_q3 = entry.get('q3_actual', 0)
        revenue_q4 = entry.get('q4_actual', 0)
        pfy_revenue[department] += revenue_q1 + revenue_q2 + revenue_q3 + revenue_q4

    # Convert defaultdict to regular dictionary if needed
    pfy_revenue = dict(pfy_revenue)
    data_l.clear()
    data_l.append(pfy_revenue)
    return data_l

def get_previous_year_si_data(budget_quater, name, project, department):
    data_l.clear()
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
    
    # get pi details
    si_list = frappe.db.get_list("Sales Invoice", filters={"posting_date": ["between", [start_date, end_date]], "docstatus": 1}, fields=["name"])
    print("\n si", si_list)
    
    for si in si_list:
        si_details = frappe.get_doc("Sales Invoice", si.name)
        for item in si_details.items:
            if item.project == budget.project:
                temp_pi_item.append({"department": department, "amount": item.amount})
                
    # Dictionary to store accumulated amounts for each item
    sum_dict = defaultdict(float)

    # Calculate sum for each item
    for item in temp_pi_item:
        sum_dict[item['department']] += item['amount']

    # Convert the accumulated sums into the desired format
    pi_list = [{"department": item, "type": "Revenue", actual: amount} for item, amount in sum_dict.items()]
    for i in pi_list:
        data_l.append(i)
        
    return data_l

def map_current_year_and_last_year_data(current_year_data, previous_year_data):
    # Extract departments from previous list
    previous_departments = previous_year_data[0].keys()

    # Iterate through current list
    for item in current_year_data:
        department = item.get('department', None)
        if department and department in previous_departments and item.get('type') == "Revenue":
            # Add a new key 'previous_value' with corresponding value from previous list
            item['previous_year_data'] = previous_year_data[0][department]
            item["growth"] = f"{((float(item['total_actual']) * 100) / item['previous_year_data']) - 100:.2f}%"

    
    return current_year_data

