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
     

# def validate_budget_for_item(pi, method):
#     """ validate budget per item in purchase invoice """
#     is_cost_center = True if pi.cost_center else False
#     dimension = "Cost Center" if pi.cost_center else "Project" if pi.project else ""
    
#     gl = get_data_from_gl(pi.items, dimension, pi.company, is_cost_center)


#     fiscal_year = get_fiscal_year(date=pi.posting_date, company=pi.company)
    
#     budgets = frappe.db.get_list("Budget", filters={"fiscal_year": fiscal_year[0], "project": pi.project, "cost_center": pi.cost_center, "company": pi.company}, fields=["name"])
    
#     print("\n\n budgets", budgets)
    
#     budget = frappe.get_doc("Budget", budget)
   
#     # return if not applicable on bucking actual expenses in budget
#     # if not budget.applicable_on_booking_actual_expenses:
#     #     return
    

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
#             check_items_budget = check_items_budget(budget.custom_budget_for_items, pi.items, "Cost Center", pi.company, True)
            
        
#     # for b_item in b_budget_for_items:
#     print("\n\n b", budget.custom_budget_for_items.as_dict())
#     print("\n\n p", pi.items.as_dict())
    

# def check_items_budget(budget_items, pi_items, dimension, company, is_cost_center=False):
#     pass


# def get_data_from_gl(pi_items, dimention, company, is_cost_center):
#     accounts = []
#     filters = {}
    
#     for item in pi_items:
#         accounts.append("")
    
#     filters["company"] = company,
    
#     if is_cost_center: 
#         filters["cost_center"] = dimention
#     else:
#         filters["project"] = dimention
    
            
#     gl_entries = frappe.db.get_list("GL Entry", filters=filters, fields=[])



def validate_budget_for_item(pi, method):
    """Validate budget per item in purchase invoice."""
    # Get the fiscal year of the purchase invoice
    fiscal_year = frappe.get_cached_value('Fiscal Year', {'year_start_date': ('<=', pi.posting_date), 'year_end_date': ('>=', pi.posting_date)}, 'name')
    
    # Fetch the budget(s) based on fiscal year, project, cost center, and company
    budget_filters = {
        'fiscal_year': fiscal_year,
    }
    
    
    budgets = frappe.get_all('Budget', filters=budget_filters, fields=['name'])
    
    if not budgets:
        frappe.throw('No matching budget found for the fiscal year.')
    
    # Iterate through each budget and validate the purchase invoice items
    for budget in budgets:
        budget_doc = frappe.get_doc('Budget', budget.name)
        
        # Check if the budget fiscal year matches the invoice fiscal year
        if budget_doc.fiscal_year != fiscal_year :
            continue  # Skip this budget if fiscal year doesn't match
        
        # Validate items in the purchase invoice against the budget items
        validate_budget_items(budget_doc, pi.items, pi)
    
def validate_budget_items(budget_doc, pi_items, pi):
    """Validate the purchase invoice items against the budget items."""
    # Iterate over purchase invoice items
    for pi_item in pi_items:
        account_name = pi_item.expense_account
        
        # Check for matching budget accounts
        budget_account = next((bi for bi in budget_doc.accounts if bi.account == account_name), None)
        
        if budget_account:
            # Calculate remaining quantities and amounts
            for budget_item in budget_doc.custom_budget_for_items:
                item_code= budget_item.item

                # Define a query that converts `qty` to float and aggregates the results,:: and we can directly get qty and amount using this but here qty is in str, so first we have to convert it into float (item_wise_purchase_data = frappe.db.get_list('Purchase Invoice Item', filters=item_wise_purchase_filters, fields=['SUM(qty) AS total_qty', 'SUM(amount) AS total_amount)']))
                query = """
                    SELECT
                        SUM(CAST(CASE WHEN qty IS NOT NULL AND qty <> '' THEN qty ELSE 0 END AS FLOAT)) AS total_qty,
                        SUM(CAST(CASE WHEN amount IS NOT NULL THEN amount ELSE 0 END AS FLOAT)) AS total_amount
                    FROM
                        `tabPurchase Invoice Item`
                    JOIN
                        `tabPurchase Invoice` ON `tabPurchase Invoice Item`.parent = `tabPurchase Invoice`.name
                    WHERE
                        item_code = %(item_code)s
                        AND `tabPurchase Invoice`.status IN ('Submitted', 'Draft', 'Debit Note Issued')
                """

                # Pass the parameters as a dictionary
                query_params = {
                    'item_code': item_code,
                }
                # Execute the query using `frappe.db.sql`
                item_wise_purchase_data = frappe.db.sql(query,query_params, as_dict=True)

                # Check if the query result contains data
                if item_wise_purchase_data:
                    # Access the first item in the list
                    data = item_wise_purchase_data[0]

                    # Get the total quantity and total amount from the dictionary
                    # Use .get() method with a default value of 0 to handle None values
                    previously_used_qty = float(data.get('total_qty') or 0)
                    previously_used_amount = float(data.get('total_amount') or 0)
                else:
                    # If there is no data, set the quantities and amounts to 0
                    previously_used_qty = 0
                    previously_used_amount = 0


                if budget_item.item == pi_item.item_code:
                    # Calculate remaining quantities and amounts
                    remaining_qty = float(budget_item.qty) - float(previously_used_qty)
                    remaining_amount = budget_item.amount - previously_used_amount
                    
                    # Check if the purchase invoice item exceeds the budget limits
                    if remaining_qty < 0:
                        frappe.throw(f'Item quantity exceeds the remaining budgeted quantity for account {account_name}.')
                    if remaining_amount < 0:
                        frappe.throw(f'Item amount exceeds the remaining budgeted amount for account {account_name}.')
                    
        else:
            # No matching budget item found for the purchase invoice item
            frappe.throw(f'No budget found for account {account_name}, {budget_item.item}')

