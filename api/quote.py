import json
from flask import Flask, request, jsonify
from .sales_tax_rates import sales_tax_rates
from .zip_to_state import get_state_from_zip
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Updated filament prices for Bambu Lab
filament_prices = {
    "PLA Basic": 19.99,
    "PLA Matte": 19.99,
    "PETG HF": 19.99,
    "PETG Basic": 19.99,
    "ABS": 19.99,
    "PETG Translucent": 19.99,
    "PLA Galaxy": 24.99,
    "PLA Metal": 24.99,
    "PLA Glow": 24.99,
    "PLA Silk Dual Color": 24.99,
    "PLA Marble": 24.99,
    "PLA Silk": 24.99,
    "PLA Sparkle": 24.99,
    "PLA-CF": 28.99,
    "PETG-CF": 28.99,
    "ASA": 29.99,
    "PC": 39.99,
    "PA6-GF": 45.99,
    "ABS-GF": 27.99,
    "PAHT-CF": 39.99,
    "TPU 95A HF": 41.99,
    "Support for PLA/PETG": 34.99,
    "Support for ABS": 14.99,
    "Support for PA/PET": 39.99,
    "PVA": 39.99,
    "PLA Aero": 44.99,
    "ASA Aero": 49.99,
    "PET-CF": 35.99,
    "PA6-CF": 32.99,
}

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

# Function to calculate the total material weight based on volume and density
def calculate_weight(volume_cm3, density_g_per_cm3):
    return volume_cm3 * density_g_per_cm3  # Weight in grams

# Function to estimate packaging weight as a percentage of the model weight
def estimate_packaging_weight(model_weight):
    return model_weight * 0.15  # Packaging weight is 15% of model weight

# Function to calculate the total weight for shipping
def calculate_total_weight(volume_cm3, density_g_per_cm3):
    model_weight = calculate_weight(volume_cm3, density_g_per_cm3)
    packaging_weight = estimate_packaging_weight(model_weight)
    return (model_weight + packaging_weight) / 1000  # Convert to kg for shipping

# Function to check the size and determine the print category
def check_model_size(model_dimensions):
    standard_max = 250  # Maximum for standard build
    full_volume_max = 256  # Maximum for full-volume build
    directions_over = {}  # Dictionary to store directions and mm over

    x, y, z = model_dimensions

    # Check if any dimension exceeds full volume
    if x > full_volume_max or y > full_volume_max or z > full_volume_max:
        directions_over = {dim: val for dim, val in zip(["X", "Y", "Z"], [x, y, z]) if val > full_volume_max}
        return "too_large", directions_over

    # Check if the model requires full-volume printing
    if x > standard_max or y > standard_max or z > standard_max:
        directions_over = {dim: val - standard_max for dim, val in zip(["X", "Y", "Z"], [x, y, z]) if val > standard_max}
        return "full_volume", directions_over

    # If the model fits within standard size
    return "standard", {}

@app.route('/api/quote', methods=['POST'])
def quote():
    logging.debug("Received request with data: %s", request.data)
    try:
        # Parse request body as JSON
        body = request.get_json()
        logging.debug("Parsed body: %s", body)

        # Extract necessary fields from the body
        zip_code = body.get('zip_code')
        volume_cm3 = body.get('volume_cm3', 0)
        filament_type = body.get('filament_type')
        quantity = body.get('quantity', 1)
        model_dimensions = body.get('model_dimensions')
        rush_order = body.get('rush_order', False)
        use_usps_connect_local = body.get('use_usps_connect_local', False)

        base_cost = 20  # Example base cost per item

        # Material densities in g/cm³ (approximate values)
        material_densities = {
            "PLA Basic": 1.24,
            "PLA Matte": 1.24,
            "PETG HF": 1.27,
            # Add more filament types and their densities as needed
        }

        # Check if the filament type is valid
        if filament_type not in material_densities or filament_type not in filament_prices:
            raise ValueError("Invalid filament type")

        # Get the density and price for the selected filament
        density = material_densities[filament_type]
        filament_cost_per_kg = filament_prices[filament_type]

        # Calculate total material weight in grams
        total_weight_g = calculate_weight(volume_cm3, density)

        # Convert grams to kg
        total_weight_kg = total_weight_g / 1000

        # Calculate total material cost based on filament cost
        total_material_cost = total_weight_kg * filament_cost_per_kg * quantity

        # Check model size and determine whether it needs full-volume printing
        size_category, size_info = check_model_size(model_dimensions)

        if size_category == "too_large":
            return jsonify({"error": "Model too large", "size_info": size_info}), 400

        # Full-volume surcharge (if applicable)
        full_volume_surcharge = base_cost * 0.15 if size_category == "full_volume" else 0

        # Calculate shipping cost (use your USPS shipping logic here)
        shipping_cost = 7.90  # Simplified for now

        # Rush order surcharge
        rush_order_surcharge = 20 if rush_order else 0

        # Total cost before tax
        total_cost_before_tax = (base_cost + total_material_cost + full_volume_surcharge) * quantity + shipping_cost + rush_order_surcharge

        # Calculate total cost with tax
        total_with_tax, sales_tax = calculate_total_with_tax(zip_code, total_cost_before_tax, sales_tax_rates)

        # Return the result as a JSON response
        return jsonify({
            'total_cost_with_tax': total_with_tax,
            'sales_tax': sales_tax,
            'base_cost': base_cost,
            'material_cost': total_material_cost,
            'full_volume_surcharge': full_volume_surcharge,
            'shipping_cost': shipping_cost,
            'rush_order_surcharge': rush_order_surcharge
        })
    except Exception as e:
        logging.error("Error occurred: %s", e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)