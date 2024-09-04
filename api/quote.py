import json
from .sales_tax_rates import sales_tax_rates
from .zip_to_state import get_state_from_zip

def calculate_total_with_tax(zip_code, total_cost, tax_rates, get_state_from_zip):
    # Get the state from the zip code using the CSV lookup
    state = get_state_from_zip(zip_code)
    
    if state:
        # Calculate sales tax based on the state
        sales_tax = tax_rates(state) * total_cost
        total_with_tax = total_cost + sales_tax
        return total_with_tax, sales_tax
    else:
        return total_cost, 0  # No tax if state is not found

def handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        
        # Extract parameters
        zip_code = body.get('zip_code')
        total_cost = body.get('total_cost')
        
        # Calculate total cost with tax
        total_with_tax, sales_tax = calculate_total_with_tax(zip_code, total_cost, sales_tax_rates)
        
        # Return response with total cost and sales tax
        return {
            'statusCode': 200,
            'body': json.dumps({
                'total_cost_with_tax': total_with_tax,
                'sales_tax': sales_tax
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
