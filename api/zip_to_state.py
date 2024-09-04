import csv

# Function to load the ZIP code data from CSV using built-in csv module
def load_zip_data():
    zip_data = {}
    with open('path_to_your_csv/us-zip-code-latitude-and-longitude.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            zip_data[row['zip']] = row['state_name']
    return zip_data

# Store the loaded ZIP data in memory
zip_data = load_zip_data()

# Function to get state from ZIP code
def get_state_from_zip(zip_code):
    return zip_data.get(str(zip_code), None)  # Convert to string for consistency