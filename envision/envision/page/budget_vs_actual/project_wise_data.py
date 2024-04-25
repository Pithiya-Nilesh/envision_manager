from collections import defaultdict
from envision.api.utils import get_fiscal_year_quaters, get_in_currency_format, get_total
import frappe
from erpnext.accounts.utils import get_fiscal_year


""" table_3_data: Project data"""
temp_list = []
@frappe.whitelist()
def project_wise_data():
    temp_list.clear()
    fy_quaters = get_fiscal_year_quaters()
    for index, i in enumerate(fy_quaters):
        fy = frappe.db.get_value("Fiscal Year", filters={"year_start_date": i["quarter_start_date"]}, fieldname=["name"])
        b_name = frappe.db.get_value("Budget", filters={"fiscal_year": fy}, fieldname=["name"])
        if b_name:
            get_pi_items_data_with_budget(f"{index + 1}", b_name ) # map data from budgets and purchase invoice

    agrigate_data_dict = get_project_aggregated_values(temp_list)
    get_total_calculations = get_calculations(agrigate_data_dict)

    return get_total_calculations


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
        # item_doc = frappe.get_doc("Item", b_item.item)
        project_doc= frappe.get_doc("Project", budget.project)
        temp_list.append({"Project_Name": budget.project, "Client_Name": project_doc.customer, budgeted: b_item.amount})
    
    # get pi details
    pi_list = frappe.db.get_list("Purchase Invoice", filters={"posting_date": ["between", [start_date, end_date]]}, fields=["name"]) # alternative, fetch data from Item-wise Purchase Register report
    for pi in pi_list:
        pi_details = frappe.get_doc("Purchase Invoice", pi.name)
        for item in pi_details.items:
            if item.project == budget.project and item.expense_account in budget_accounts:
                project_doc= frappe.get_doc("Project", item.project)
                temp_pi_item.append({"Project_Name": item.project, "Client_Name": project_doc.customer , "amount": item.amount})
                
    # Dictionary to store accumulated amounts for each item
    sum_dict = defaultdict(float)

    # Calculate sum for each item
    for item in temp_pi_item:
        sum_dict[item['Project_Name']] += item['amount']

    # Convert the accumulated sums into the desired format
    for project, amount in sum_dict.items():
        project_doc= frappe.get_doc("Project", project)
        temp_list.append({"Project_Name": project, "Client_Name": project_doc.customer, actual: amount})
   

# aggregated values based on same project
def get_project_aggregated_values(temp_list):
    sums = {}           
    for entry in temp_list:
        project_name = entry.get('Project_Name', None)
        client_name = entry.get('Client_Name', None)
        
        for key, value in entry.items():
            if key not in ['Project_Name', 'Client_Name']:
                if (project_name, client_name) not in sums:
                    sums[(project_name, client_name)] = {}
                if key not in sums[(project_name, client_name)]:
                    sums[(project_name, client_name)][key] = entry[key]
                else:
                    sums[(project_name, client_name)][key] += entry[key]
                    
    data = []
    for (project_name, client_name), values in sums.items():
        values['Project_Name'] = project_name
        values['Client_Name'] = client_name
        data.append(values)
    return data


def get_calculations(data):
    ach_list = data
    for i in ach_list:
        q1_budgeted = i.get('q1_budgeted', 0)  # Get q1_budgeted value or default to 0 if not found
        q1_actual = i.get('q1_actual', 0)  # Get q1_actual value or default to 0 if not found
        q2_budgeted = i.get('q2_budgeted', 0)
        q2_actual = i.get('q2_actual', 0)
        q3_budgeted = i.get('q3_budgeted', 0)
        q3_actual = i.get('q3_actual', 0)
        q4_budgeted = i.get('q4_budgeted', 0)
        q4_actual = i.get('q4_actual', 0)
        i['q1_q2_q3_budgeted'] = f"{(q1_budgeted + q2_budgeted + q3_budgeted)}"
        i['q1_q2_q3_actual'] = f"{(q1_actual + q2_actual + q3_actual)}"
        i['total_budgeted'] = f"{(q1_budgeted + q2_budgeted +q3_budgeted + q4_budgeted )}"
        i['total_actual'] = f"{(q1_actual + q2_actual + q3_actual + q4_actual)}"
    return ach_list