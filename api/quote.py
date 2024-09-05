import json
from flask import Flask, request, jsonify
from .sales_tax_rates import sales_tax_rates
from .zip_to_state import get_state_from_zip
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Function to calculate total cost with sales tax
def calculate_total_with_tax(zip_code, total_cost, tax_rates, get_state_from_zip):
    # Get the state from the zip code using the CSV lookup
    state = get_state_from_zip(zip_code)

    if state:
        # Calculate sales tax based on the state
        sales_tax = tax_rates.get(state, 0) * total_cost
        total_with_tax = total_cost + sales_tax
        return total_with_tax, sales_tax
    else:
        return total_cost, 0  # No tax if state is not found

# Flask route to handle the quote request
@app.route('/api/quote', methods=['POST'])
def quote():
    logging.debug("Received request with data: %s", request.data)
    try:
        # Parse request body as JSON
        body = request.get_json()
        logging.debug("Parsed body: %s", body)

        # Extract zip_code and total_cost from the body
        zip_code = body.get('zip_code')
        total_cost = body.get('total_cost', 0)
        logging.debug(f"Zip code: {zip_code}, Total cost: {total_cost}")
        
        # Calculate total cost with tax
        total_with_tax, sales_tax = calculate_total_with_tax(zip_code, total_cost, sales_tax_rates, get_state_from_zip)
        logging.debug(f"Total with tax: {total_with_tax}, Sales tax: {sales_tax}")

        # Return the result as a JSON response
        return jsonify({
            'total_cost_with_tax': total_with_tax,
            'sales_tax': sales_tax
        })
    except Exception as e:
        logging.error("Error occurred: %s", e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)