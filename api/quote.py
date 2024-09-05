import json
from flask import Flask, request, jsonify
from .sales_tax_rates import sales_tax_rates
from .zip_to_state import get_state_from_zip

import logging
from flask import Flask, request, jsonify
logging.basicConfig(level=logging.DEBUG)

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


def handler(event, context):
    logging.debug("Received event: %s", event)
    try:
        body = json.loads(event['body'])
        logging.debug("Parsed body: %s", body)
        zip_code = body.get('zip_code')
        total_cost = body.get('total_cost', 0)
        logging.debug(f"Zip code: {zip_code}, Total cost: {total_cost}")
        
        total_with_tax, sales_tax = calculate_total_with_tax(zip_code, total_cost, sales_tax_rates, get_state_from_zip)
        logging.debug(f"Total with tax: {total_with_tax}, Sales tax: {sales_tax}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'total_cost_with_tax': total_with_tax,
                'sales_tax': sales_tax
            })
        }
    except Exception as e:
        logging.error("Error occurred: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

if __name__ == '__main__':
    app.run(debug=True)
