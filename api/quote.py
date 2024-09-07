import json
import trimesh
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from .sales_tax_rates import sales_tax_rates
from .zip_to_state import get_state_from_zip
import logging
import os

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Define a valid path for storing uploaded files
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')  # This sets the upload folder to a "uploads" directory in your current working directory
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the directory exists before saving files
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
        # Handle file upload
        if 'model_file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files['model_file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Secure the filename and save the file to the UPLOAD_FOLDER
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Load the 3D model using trimesh
        try:
            mesh = trimesh.load(file_path)
        except Exception as e:
            return jsonify({"error": f"Failed to load 3D model: {str(e)}"}), 400

        # Continue with your existing logic for volume calculation and cost...
        volume_cm3 = mesh.volume / 1000  # Convert from mm³ to cm³
        bounding_box = mesh.bounding_box.extents  # Dimensions (x, y, z)

        # Your existing logic...
        return jsonify({'success': 'File processed successfully'})

    except Exception as e:
        logging.error("Error occurred: %s", e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)