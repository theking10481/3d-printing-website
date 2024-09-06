document.getElementById('quoteForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const volume = parseFloat(document.getElementById('volume').value);
    const zipCode = document.getElementById('zip_code').value;
    const filamentType = document.getElementById('filament_type').value;
    const quantity = parseInt(document.getElementById('quantity').value);
    const rushOrder = document.getElementById('rush_order').checked;
    const useUspsConnectLocal = document.getElementById('use_usps_connect_local').checked;
    const modelDimensions = [
        parseFloat(document.getElementById('dimension_x').value),
        parseFloat(document.getElementById('dimension_y').value),
        parseFloat(document.getElementById('dimension_z').value)
    ];
    // Function to display warnings if dimensions are too large
function displayDimensionWarnings(size_category, size_info) {
    const warningDiv = document.getElementById("quoteResult");
    
    // Clear any existing warnings
    warningDiv.innerHTML = "";

    if (size_category === "full_volume") {
        warningDiv.innerHTML = "Warning: Full-volume printing required due to exceeding standard size limits.";
    }
    
    if (size_category === "too_large") {
        warningDiv.innerHTML = "Error: Model too large in the following dimensions: " + JSON.stringify(size_info);
    }
}

document.getElementById('quoteForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const volume = parseFloat(document.getElementById('volume').value);
    const zipCode = document.getElementById('zip_code').value;
    const filamentType = document.getElementById('filament_type').value;
    const quantity = parseInt(document.getElementById('quantity').value);
    const rushOrder = document.getElementById('rush_order').checked;
    const useUspsConnectLocal = document.getElementById('use_usps_connect_local').checked;
    const modelDimensions = [
        parseFloat(document.getElementById('dimension_x').value),
        parseFloat(document.getElementById('dimension_y').value),
        parseFloat(document.getElementById('dimension_z').value)
    ];

    // Here, call the size-checking logic to display warnings before submitting
    const size_category = checkModelSize(modelDimensions); // Replace with the actual logic that computes the size category
    displayDimensionWarnings(size_category, modelDimensions); // Call the function to display warnings if needed

    // Continue with the API request only if there is no "too_large" error
    if (size_category === "too_large") {
        return;  // Stop submission if the model is too large
    }

    try {
        const response = await fetch('/api/quote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                volume_cm3: volume,
                zip_code: zipCode,
                filament_type: filamentType,
                quantity: quantity,
                model_dimensions: modelDimensions,
                rush_order: rushOrder,
                use_usps_connect_local: useUspsConnectLocal
            })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        console.log('Response:', data);  // Log to see the response object
        
        if (data.error) {
            document.getElementById('quoteResult').innerHTML = `Error: ${data.error}`;
        } else {
            document.getElementById('quoteResult').innerHTML = `Estimated Quote: $${data.total_cost_with_tax}`;
        }
    } catch (error) {
        console.error('Error during fetch:', error);
        document.getElementById('quoteResult').innerHTML = `Failed to fetch quote: ${error.message}`;
    }
});

    try {
        const response = await fetch('/api/quote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                volume_cm3: volume,
                zip_code: zipCode,
                filament_type: filamentType,
                quantity: quantity,
                model_dimensions: modelDimensions,
                rush_order: rushOrder,
                use_usps_connect_local: useUspsConnectLocal
            })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        console.log('Response:', data);  // Log to see the response object
        
        if (data.error) {
            document.getElementById('quoteResult').innerHTML = `Error: ${data.error}`;
        } else {
            document.getElementById('quoteResult').innerHTML = `Estimated Quote: $${data.total_cost_with_tax}`;
        }
    } catch (error) {
        console.error('Error during fetch:', error);
        document.getElementById('quoteResult').innerHTML = `Failed to fetch quote: ${error.message}`;
    }
});
