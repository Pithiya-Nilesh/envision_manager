import frappe

"""Validate budget per item in purchase invoice."""
def validate_budget_for_item(pi, method):
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
    
    
"""Validate the purchase invoice items against the budget items."""
def validate_budget_items(budget_doc, pi_items, pi):
    # Iterate over purchase invoice items
    for pi_item in pi_items:
        account_name = pi_item.expense_account
        
        # checking match budget
        matching_budgets = False
        
        # Check for matching budget accounts, project, cost center
        for budget_account in budget_doc.accounts:
            if budget_account.account == account_name:
                if (pi_item.project and budget_doc.project and pi_item.project == budget_doc.project) \
                        or (pi_item.cost_center and budget_doc.cost_center and pi_item.cost_center == budget_doc.cost_center):
                    matching_budgets = True
            else:
                frappe.msgprint(f"Warning: Account for item {pi_item.item_code} and {budget_doc.name} does not match.")
                    
        # Check if project or cost center mismatch
        if pi_item.project and budget_doc.project and pi_item.project != budget_doc.project:
            # frappe.msgprint(f"Warning: Project for item {pi_item.item_code} does not match.")
            pass
        elif pi_item.cost_center and budget_doc.cost_center and pi_item.cost_center != budget_doc.cost_center:
            # frappe.msgprint(f"Warning: Cost center for item {pi_item.item_code} does not match.")
            pass

        # Check if any matching budget accounts are found
        if not matching_budgets:
            continue  # Skip this item if no matching budget accounts found

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
                    AND `tabPurchase Invoice`.status = 'Unpaid'
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