from envision.envision.page.budget_vs_actual.department_wise_data import department_wise_data
from envision.envision.page.budget_vs_actual.item_group_wise_data import item_group_wise_data
import frappe

@frappe.whitelist()
def get_data():
    
    department_data = department_wise_data()
    item_group_data = item_group_wise_data()
    
    return department_data, item_group_data