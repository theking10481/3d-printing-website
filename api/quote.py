import io
import json
import trimesh
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import logging
from .sales_tax_rates import sales_tax_rates
from .zip_to_state import get_state_from_zip

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Set the maximum file size (e.g., 16 MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB file size limit

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

# Flask route to handle the quote request
@app.route('/api/quote', methods=['POST'])
def quote():
    logging.debug("Received request with data: %s", request.form)
    try:
        # Parse form data instead of JSON
        zip_code = request.form.get('zip_code')
        filament_type = request.form.get('filament_type')
        quantity = int(request.form.get('quantity', 1))
        
        # Debug: print key form inputs
        print(f"ZIP Code: {zip_code}, Filament Type: {filament_type}, Quantity: {quantity}")

        # Correct rush order logic: check for presence of 'rush_order'
        rush_order = request.form.get('rush_order', 'false') == 'true'
        use_usps_connect_local = request.form.get('use_usps_connect_local', 'false') == 'true'

        # Debug: print checkbox values
        print(f"Rush Order: {rush_order}, USPS Connect Local: {use_usps_connect_local}")

        # Handle file upload (no saving to disk, use in-memory handling)
        if 'model_file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files['model_file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Read the uploaded file into an in-memory buffer
        file_buffer = io.BytesIO(file.read())

        # Load the 3D model directly from the in-memory buffer using trimesh
        try:
            mesh = trimesh.load(file_buffer, file.filename)
        except Exception as e:
            return jsonify({"error": f"Failed to load 3D model: {str(e)}"}), 400

        # Calculate the volume and bounding box
        volume_cm3 = mesh.volume / 1000  # Convert from mm³ to cm³
        print(f"Model volume (cm³): {volume_cm3}")  # Debug volume

        bounding_box = mesh.bounding_box.extents  # Dimensions (x, y, z)

        # Check if the filament type is valid
        if filament_type not in material_densities or filament_type not in filament_prices:
            return jsonify({"error": "Invalid filament type"}), 400

        # Get the density for the filament
        density = material_densities[filament_type]
        print(f"Filament type: {filament_type}, Density: {density} g/cm³")  # Debug filament

        # Calculate the total material weight
        total_weight_g = calculate_weight(volume_cm3, density)  # Weight in grams
        total_weight_kg = total_weight_g / 1000  # Convert to kg
        print(f"Material weight (g): {total_weight_g}, Material weight (kg): {total_weight_kg}")  # Debug weight

        # Check model size and determine print category
        size_category, _ = check_model_size(bounding_box)

        if size_category == "too_large":
            return jsonify({"error": "Model too large"}), 400

        # Calculate material cost (only if the volume is non-zero)
        if volume_cm3 > 0:
            total_material_cost = total_weight_kg * filament_prices[filament_type] * quantity
        else:
            total_material_cost = 0.0

        logging.debug(f"Material cost: {total_material_cost}")  # Debug material cost

        # Shipping cost based on weight
        shipping_weight = calculate_total_weight(volume_cm3, density)
        shipping_cost = calculate_usps_shipping(zip_code, shipping_weight, express=rush_order, connect_local=use_usps_connect_local)

        # Rush order surcharge (apply only if rush order is checked)
        rush_order_surcharge = 20 if rush_order else 0

        # Base cost
        base_cost = 20  # Example base cost per item

        # Total cost before tax
        total_cost_before_tax = (base_cost + total_material_cost) * quantity + shipping_cost + rush_order_surcharge

        # Calculate total cost with tax
        total_with_tax, sales_tax = calculate_total_with_tax(zip_code, total_cost_before_tax, sales_tax_rates, get_state_from_zip)

        # Prepare the response
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

@app.errorhandler(413)
def request_entity_too_large(error):
    logging.error(f"File too large: {error}")
    return jsonify({'error': 'File too large. Maximum file size is 16MB.'}), 413

if __name__ == '__main__':
    app.run(debug=True)