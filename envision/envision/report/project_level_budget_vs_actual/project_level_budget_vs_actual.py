
import frappe

def execute(filters=None):

    columns = [
        {'label': 'Project Name', 'fieldname': 'project', 'fieldtype': 'Link', 'options': 'Project'},
        {'label': 'Client', 'fieldname': 'customer', 'fieldtype': 'Link', 'options': 'Customer'},
        {'label': 'Revenue/Expense', 'fieldname': 're', 'fieldtype': 'Data'},
        {'label': 'Particulars', 'fieldname': 'item', 'fieldtype': 'Link', 'options': 'Item'},
        {'label': 'Unit', 'fieldname': 'uom', 'fieldtype': 'Data'},
        {'label': 'Budgeted Qty', 'fieldname': 'qty', 'fieldtype': 'Float'},
        {'label': 'Budgeted Unit price', 'fieldname': 'unit_price', 'fieldtype': 'Currency'},
        {'label': 'Budgeted Amount', 'fieldname': 'amount', 'fieldtype': 'Currency'},
        {'label': 'Actual Qty', 'fieldname': 'pqty', 'fieldtype': 'Float'},
        {'label': 'Actual Unit price', 'fieldname': 'prate', 'fieldtype': 'Currency'},
        {'label': 'Actual Amount', 'fieldname': 'pamount', 'fieldtype': 'Currency'}
    ]
    sql = """
		SELECT 
			B.project,
			P.customer,
			'Expense' AS re,
			IB.item,
			IB.qty,
			IB.unit_price,
			IB.amount,
			PII.uom,
			SUM(PII.qty) AS pqty,
			AVG(PII.rate) AS prate,
			SUM(PII.amount) AS pamount
		FROM `tabBudget` AS B
		JOIN `tabProject` AS P ON B.project = P.name AND B.docstatus = 1
		JOIN `tabPurchase Invoice Item` AS PII ON PII.project = P.name
		JOIN `tabPurchase Invoice` AS PI ON PII.parent = PI.name AND PI.docstatus = 1
		JOIN `tabItem Budget` AS IB ON B.name = IB.parent AND IB.item = PII.item_code
		JOIN `tabBudget Account` AS BA ON BA.parent = B.name AND BA.account = PII.expense_account AND BA.custom_budget_against = 'Expense'
		GROUP BY B.project, IB.item
    """

		# UNION

		# SELECT 
		# 	B.project,
		# 	P.customer,
		# 	'Revenue' AS re,
		# 	IB.item,
		# 	IB.qty,
		# 	IB.unit_price,
		# 	IB.amount,
		# 	SII.uom,
		# 	SUM(SII.qty) AS pqty,
		# 	AVG(SII.rate) AS prate,
		# 	SUM(SII.amount) AS pamount
		# FROM `tabBudget` AS B
		# JOIN `tabProject` AS P ON B.project = P.name
		# JOIN `tabSales Invoice Item` AS SII ON SII.project = P.name
		# JOIN `tabSales Invoice` AS SI ON SII.parent = SI.name AND SI.docstatus = 1
		# JOIN `tabItem Budget` AS IB ON B.name = IB.parent AND IB.item = SII.item_code
		# JOIN `tabBudget Account` AS BA ON BA.parent = B.name AND BA.account = SII.income_account AND BA.custom_budget_against = 'Revenue'
		# GROUP BY B.project, IB.item
		# ORDER BY project, item;
    data = frappe.db.sql(sql, filters, as_dict=True)
    return columns, data