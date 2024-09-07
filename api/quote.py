import io
import boto3
import json
import logging
import trimesh
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError
import os
import logging
from .sales_tax_rates import sales_tax_rates
from .zip_to_state import get_state_from_zip

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

MINIMUM_WEIGHT_G = 0.1  # Minimum weight in grams (adjust as needed)

BUCKET_NAME = '3d-printing-website-files'

base_cost = 20



# Define S3 client
s3_client = boto3.client(
    's3',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

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
    # Get the state based on the ZIP code
    state = get_state_from_zip(zip_code)
    
    # Ensure we have a valid state
    if state:
        # Look up the sales tax rate for the state
        sales_tax_rate = tax_rates.get(state, 0)
        
        # Calculate sales tax
        sales_tax = sales_tax_rate * total_cost
        
        # Add sales tax to the total cost
        total_with_tax = total_cost + sales_tax
        return total_with_tax, sales_tax
    else:
        # If no state is found, return the original cost with no tax
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
def upload_file_to_s3(file_buffer, bucket, object_name):
    """Upload a file buffer to an S3 bucket"""

    try:
        # Upload the file from memory directly to S3
        s3_client.upload_fileobj(file_buffer, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


@app.route('/api/quote', methods=['POST'])
def quote():
    try:
        # Get form data
        zip_code = request.form.get('zip_code')
        filament_type = request.form.get('filament_type')
        quantity = int(request.form.get('quantity', 1))
        rush_order = request.form.get('rush_order', 'false') == 'true'
        use_usps_connect_local = request.form.get('use_usps_connect_local', 'false') == 'true'

        # Handle file upload
        if 'model_file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files['model_file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Secure the filename and create S3 object name
        object_name = secure_filename(file.filename)
        
        # Upload file to S3
        file_buffer = io.BytesIO(file.read())
        upload_success = upload_file_to_s3(file_buffer, BUCKET_NAME, object_name)

        if not upload_success:
            return jsonify({"error": "Failed to upload file to S3"}), 500

        # Reset buffer position before reusing
        file_buffer.seek(0)

        # Load the 3D model directly from the in-memory buffer using trimesh
        try:
            mesh = trimesh.load(file_buffer, file.filename)
        except Exception as e:
            return jsonify({"error": f"Failed to load 3D model: {str(e)}"}), 400

        # Calculate the volume and bounding box
        volume_cm3 = mesh.volume / 1000  # Convert from mm³ to cm³
        bounding_box = mesh.bounding_box.extents  # Dimensions (x, y, z)

        # Check if the filament type is valid
        if filament_type not in material_densities or filament_type not in filament_prices:
            return jsonify({"error": "Invalid filament type"}), 400

        # Get the density for the filament
        density = material_densities[filament_type]

        # Calculate the total material weight (with minimum threshold)
        total_weight_g = max(calculate_weight(volume_cm3, density), MINIMUM_WEIGHT_G)
        total_weight_kg = total_weight_g / 1000  # Convert to kg

        # Calculate material cost
        total_material_cost = total_weight_kg * filament_prices[filament_type] * quantity

        # Base cost
        base_cost = 20

        # Rush order surcharge
        rush_order_surcharge = 20 if rush_order else 0

        # Shipping cost based on weight
        shipping_weight = calculate_total_weight(volume_cm3, density)
        shipping_cost = calculate_usps_shipping(zip_code, shipping_weight, express=rush_order, connect_local=use_usps_connect_local)

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
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    logging.error(f"File too large: {error}")
    return jsonify({'error': 'File too large. Maximum file size is 16MB.'}), 413

if __name__ == '__main__':
    app.run(debug=True)