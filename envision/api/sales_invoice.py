import frappe, json
# from erpnext.accounts.utils import get_fiscal_year



def validate_budget_for_item(si, method):
    """Validate budget per item in sales invoice."""
    # Determine if cost center or project is used for budgeting
    is_cost_center = True if si.cost_center else False
    dimension = "Cost Center" if is_cost_center else "Project" if si.project else ""
    
    # Get the fiscal year of the sales invoice
    fiscal_year = frappe.get_cached_value('Fiscal Year', {'year_start_date': ('<=', si.posting_date), 'year_end_date': ('>=', si.posting_date)}, 'name')
    
    # Fetch the budget(s) based on fiscal year, project, cost center, and company
    budget_filters = {
        'fiscal_year': fiscal_year,
    }
    
    
    budgets = frappe.get_all('Budget', filters=budget_filters, fields=['name'])
    
    if not budgets:
        pass
        # frappe.throw('No matching budget found for the fiscal year and dimension.')
        
    
    # Iterate through each budget and validate the sales invoice items
    for budget in budgets:
        budget_doc = frappe.get_doc('Budget', budget.name)
        
        # Check if the budget fiscal year matches the invoice fiscal year
        if budget_doc.fiscal_year != fiscal_year:
            continue  # Skip this budget if fiscal year doesn't match
        
        # Validate items in the sales invoice against the budget items
        validate_budget_items(budget_doc, si.items, si, dimension)
    
def validate_budget_items(budget_doc, si_items, si, dimension):
    """Validate the sales invoice items against the budget items."""
    # Create a dictionary to track used quantities and amounts in the invoice
    
    # Iterate over sales invoice items
    for si_item in si_items:
        account_name = si_item.expense_account
        
        # Check for matching budget item
        budget_account = next((bi for bi in budget_doc.accounts if bi.account == account_name), None)
        
        if budget_account:
            # Calculate remaining quantities and amounts
            print(budget_doc.project)
            for si_item in si_items:
                if si_item.project:
                    if si_item.project != budget_doc.project:
                        # frappe.throw(f"Project mismatch for account {account_name} at item {si_item.item_code}.")
                        continue
                elif si_item.cost_center:
                    if si_item.cost_center != budget_doc.cost_center:
                        # frappe.throw(f"Cost Center mismatch for account {account_name} at item {si_item.item_code}.")
                        continue

                  
                
       
            
            for budget_item in budget_doc.custom_budget_for_items:
                item_code= budget_item.item

                # Define a query that converts `qty` to float and aggregates the results,:: and we can directly get qty and amount using this but here qty is in str, so first we have to convert it into float (item_wise_sales_data = frappe.db.get_list('Sales Invoice Item', filters=item_wise_sales_filters, fields=['SUM(qty) AS total_qty', 'SUM(amount) AS total_amount)']))
                query = """
                    SELECT
                        SUM(CAST(CASE WHEN qty IS NOT NULL AND qty <> '' THEN qty ELSE 0 END AS FLOAT)) AS total_qty,
                        SUM(CAST(CASE WHEN amount IS NOT NULL THEN amount ELSE 0 END AS FLOAT)) AS total_amount
                    FROM
                        `tabSales Invoice Item`
                    JOIN
                        `tabSales Invoice` ON `tabSales Invoice Item`.parent = `tabSales Invoice`.name
                    WHERE
                        item_code = %(item_code)s
                        AND `tabSales Invoice`.status = 'Unpaid'
                """

                # Pass the parameters as a dictionary
                query_params = {
                    'item_code': item_code,
                }
                # Execute the query using `frappe.db.sql`
                item_wise_sales_data = frappe.db.sql(query,query_params, as_dict=True)

                # Check if the query result contains data
                if item_wise_sales_data:
                    # Access the first item in the list
                    data = item_wise_sales_data[0]

                    # Get the total quantity and total amount from the dictionary
                    # Use .get() method with a default value of 0 to handle None values
                    previously_used_qty = float(data.get('total_qty') or 0)
                    previously_used_amount = float(data.get('total_amount') or 0)
                else:
                    # If there is no data, set the quantities and amounts to 0
                    previously_used_qty = 0
                    previously_used_amount = 0


                if budget_item.item == si_item.item_code:
                    # Calculate remaining quantities and amounts
                    remaining_qty = float(budget_item.qty) - float(previously_used_qty)
                    remaining_amount = budget_item.amount - previously_used_amount
                    
                    
                    # Check if the sales invoice item exceeds the budget limits
                    if remaining_qty < 0:
                        frappe.throw(f'Item quantity exceeds the remaining budgeted quantity for account {account_name}.')
                    if remaining_amount < 0:
                        frappe.throw(f'Item amount exceeds the remaining budgeted amount for account {account_name}.')
                    
                # else:
                #     frappe.throw(f'items not matching {account_name}')
        
        else:
            # No matching budget item found for the sales invoice item
            # frappe.throw(f'No budget found for account {account_name}, {budget_item.item}')
            pass
    