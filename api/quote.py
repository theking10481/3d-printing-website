from flask import Flask, request, jsonify
from .sales_tax_rates import sales_tax_rates
from .zip_to_state import get_state_from_zip

app = Flask(__name__)

def calculate_total_with_tax(zip_code, total_cost, tax_rates, get_state_from_zip):
    # Get the state from the zip code using the CSV lookup
    state = get_state_from_zip(zip_code)

    if state:
        # Calculate sales tax based on the state
        sales_tax = tax_rates[state] * total_cost
        total_with_tax = total_cost + sales_tax
        return total_with_tax, sales_tax
    else:
        return total_cost, 0  # No tax if state is not found

@app.route('/api/quote', methods=['POST'])
def quote_handler():
    try:
        # Parse request body
        body = request.get_json()
        
        # Extract parameters
        zip_code = body.get('zip_code')
        total_cost = body.get('total_cost')
        
        # Calculate total cost with tax
        total_with_tax, sales_tax = calculate_total_with_tax(zip_code, total_cost, sales_tax_rates, get_state_from_zip)
        
        # Return response with total cost and sales tax
        return jsonify({
            'total_cost_with_tax': total_with_tax,
            'sales_tax': sales_tax
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
