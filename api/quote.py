import json
import trimesh
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from .sales_tax_rates import sales_tax_rates
from .zip_to_state import get_state_from_zip
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Define the folder to store uploaded files temporarily
UPLOAD_FOLDER = '/path/to/upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Updated filament prices for Bambu Lab
filament_prices = {
    "PLA Basic": 19.99,
    "PLA Matte": 19.99,
    "PETG HF": 19.99,
    "PETG Basic": 19.99,
    # Add more filaments as needed...
}

# Material densities in g/cm³ (approximate values)
material_densities = {
    "PLA Basic": 1.24,
    "PLA Matte": 1.24,
    "PETG HF": 1.27,
    # Add more filament types and their densities as needed
}

# Function to calculate total cost with sales tax
def calculate_total_with_tax(zip_code, total_cost, tax_rates, get_state_from_zip):
    state = get_state_from_zip(zip_code)
    if state:
        sales_tax = tax_rates.get(state, 0) * total_cost
        total_with_tax = total_cost + sales_tax
        return total_with_tax, sales_tax
    else:
        return total_cost, 0

# Function to calculate the total material weight
def calculate_weight(volume_cm3, density_g_per_cm3):
    return volume_cm3 * density_g_per_cm3  # Weight in grams

# Function to estimate packaging weight
def estimate_packaging_weight(model_weight):
    return model_weight * 0.15

# Function to calculate total weight for shipping
def calculate_total_weight(volume_cm3, density_g_per_cm3):
    model_weight = calculate_weight(volume_cm3, density_g_per_cm3)
    packaging_weight = estimate_packaging_weight(model_weight)
    return (model_weight + packaging_weight) / 1000  # Convert to kg

# Function to check the size of the model
def check_model_size(model_dimensions):
    standard_max = 250  # Max size for standard builds
    full_volume_max = 256  # Max size for full-volume builds
    x, y, z = model_dimensions
    if x > full_volume_max or y > full_volume_max or z > full_volume_max:
        return "too_large", {}
    if x > standard_max or y > standard_max or z > standard_max:
        return "full_volume", {}
    return "standard", {}

# USPS shipping calculation function (simplified)
def calculate_usps_shipping(zip_code, weight_kg, express=False, connect_local=False):
    weight_lbs = weight_kg * 2.20462  # Convert kg to lbs
    return 7.90  # Example rate

@app.route('/api/quote', methods=['POST'])
def quote():
    try:
        # Extract form data from the request
        zip_code = request.form.get('zip_code')
        filament_type = request.form.get('filament_type')
        quantity = int(request.form.get('quantity', 1))
        rush_order = bool(request.form.get('rush_order', False))
        use_usps_connect_local = bool(request.form.get('use_usps_connect_local', False))

        # Handle file upload
        if 'model_file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files['model_file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Save the uploaded file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Load the 3D model using trimesh
        try:
            mesh = trimesh.load(file_path)
        except Exception as e:
            return jsonify({"error": f"Failed to load 3D model: {str(e)}"}), 400

        # Calculate the volume and bounding box
        volume_cm3 = mesh.volume / 1000  # Convert from mm³ to cm³
        bounding_box = mesh.bounding_box.extents  # Dimensions (x, y, z)

        # Ensure valid filament type and calculate costs
        if filament_type not in material_densities or filament_type not in filament_prices:
            return jsonify({"error": "Invalid filament type"}), 400

        # Get the density for the filament and calculate the total weight
        density = material_densities[filament_type]
        total_weight_g = calculate_weight(volume_cm3, density)
        total_weight_kg = total_weight_g / 1000

        # Check model size and print category
        size_category, _ = check_model_size(bounding_box)
        if size_category == "too_large":
            return jsonify({"error": "Model too large"}), 400

        # Calculate total material cost
        total_material_cost = total_weight_kg * filament_prices[filament_type] * quantity

        # Calculate shipping cost and other surcharges
        shipping_weight = calculate_total_weight(volume_cm3, density)
        shipping_cost = calculate_usps_shipping(zip_code, shipping_weight, express=rush_order, connect_local=use_usps_connect_local)
        rush_order_surcharge = 20 if rush_order else 0
        base_cost = 20  # Example base cost per item

        # Calculate total cost before tax
        total_cost_before_tax = (base_cost + total_material_cost) * quantity + shipping_cost + rush_order_surcharge

        # Calculate total cost with tax
        total_with_tax, sales_tax = calculate_total_with_tax(zip_code, total_cost_before_tax, sales_tax_rates, get_state_from_zip)

        # Prepare the response data
        response_data = {
            'total_cost_with_tax': f"${total_with_tax:.2f}",
            'sales_tax': f"${sales_tax:.2f}",
            'base_cost': f"${base_cost:.2f}",
            'material_cost': f"${total_material_cost:.2f}",
            'shipping_cost': f"${shipping_cost:.2f}",
            'rush_order_surcharge': f"${rush_order_surcharge:.2f}"
        }

        return jsonify(response_data)

    except Exception as e:
        logging.error("Error occurred: %s", e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)