import frappe

def get_fiscal_year_quaters():
    import datetime
    from dateutil import relativedelta

    # Get the current date
    current_date = datetime.date.today()

    # Determine the fiscal year based on April start
    if current_date.month >= 4:
        fiscal_year_start = datetime.date(current_date.year, 4, 1)
    else:
        fiscal_year_start = datetime.date(current_date.year - 1, 4, 1)

    # Get the start and end dates of each quarter
    quarters = []
    for i in range(4):
        quarter_start = fiscal_year_start + relativedelta.relativedelta(months=i * 3)
        quarter_end = quarter_start + relativedelta.relativedelta(months=2, days=-1)
        quarters.append({
            # f"quarter{i + 1}_start_date": quarter_start.strftime("%Y-%m-%d"),
            "quarter_start_date": quarter_start.strftime("%Y-%m-%d"),
            "quarter_end_date": quarter_end.strftime("%Y-%m-%d")
        })
        
    return quarters


def get_in_currency_format(data):
    # Iterate through the data and format the amounts to Indian currency
    formatted_data = []
    for item in data:
        formatted_item = {}
        for key, value in item.items():
            if isinstance(value, (int, float)):
                formatted_item[key] = format_to_indian_currency(value)
            else:
                formatted_item[key] = value
        formatted_data.append(formatted_item)
    return formatted_data


# Function to format number to Indian currency format
def format_to_indian_currency(number):
    import locale
    # Set the locale to Indian English
    locale.setlocale(locale.LC_ALL, 'en_IN')
    return locale.currency(number, grouping=True)

def get_total(data):
    # Initialize total budgeted and total actual variables
    total_budgeted = 0.0
    total_actual = 0.0

    # Iterate through each dictionary in list1
    for item in data:
        item_total_budgeted = 0.0
        item_total_actual = 0.0
        
        # Iterate through keys of the dictionary
        for key, value in item.items():
            if key.endswith('d') and key.startswith('q'):
                item_total_budgeted += item[key]
            if key.endswith('l') and key.startswith('q'):
                item_total_actual += item[key]
        
        # Add item totals to the global totals
        total_budgeted += item_total_budgeted
        total_actual += item_total_actual
        
        # Add item totals as new keys in the dictionary
        item['total_budgeted'] = item_total_budgeted
        item['total_actual'] = item_total_actual
    return data