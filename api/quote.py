import json
from .sales_tax_rates import sales_tax_rates
from .zip_to_state import get_state_from_zip

def calculate_total_with_tax(zip_code, total_cost, tax_rates, get_state_from_zip):
    state = get_state_from_zip(zip_code)
    if state:
        sales_tax = tax_rates(state) * total_cost
        total_with_tax = total_cost + sales_tax
        return total_with_tax, sales_tax
    else:
        return total_cost, 0

def calculate_total_cost(volume_cm3, filament_type, quantity, rush_order):
    # Example base pricing logic - adjust according to your logic
    base_cost_per_cm3 = {
        'PLA': 0.05,
        'ABS': 0.07,
        'PETG': 0.06
    }
    base_cost = base_cost_per_cm3.get(filament_type, 0.05) * volume_cm3 * quantity

    # Add rush order surcharge
    if rush_order:
        base_cost *= 1.5  # 50% rush order surcharge

    return base_cost

def handler(event, context):
    try:
        body = json.loads(event['body'])
        
        zip_code = body.get('zip_code')
        volume_cm3 = body.get('volume_cm3')
        filament_type = body.get('filament_type')
        quantity = body.get('quantity')
        rush_order = body.get('rush_order')
        
        # Calculate total cost
        total_cost = calculate_total_cost(volume_cm3, filament_type, quantity, rush_order)
        
        # Calculate total cost with tax
        total_with_tax, sales_tax = calculate_total_with_tax(zip_code, total_cost, sales_tax_rates, get_state_from_zip)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'total_cost_with_tax': total_with_tax,
                'sales_tax': sales_tax,
                'total_cost': total_cost
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
