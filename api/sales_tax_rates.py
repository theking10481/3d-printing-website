import csv

# Function to load sales tax rates from the CSV using built-in csv module
def load_sales_tax_rates():
    tax_rates = {}
    with open('path_to_your_csv/sales_tax_rates.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Remove the '%' and convert to a decimal
            combined_rate = float(row['Combined Rate'].strip('%')) / 100
            tax_rates[row['State']] = combined_rate
    return tax_rates

# Store the sales tax rates in memory
sales_tax_rates = load_sales_tax_rates()

# Function to get sales tax by state
def get_sales_tax_rate(state):
    return sales_tax_rates.get(state, 0)