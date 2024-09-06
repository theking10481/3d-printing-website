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

    // Client-side dimension checking
    const standard_max = 250;
    const full_volume_max = 256;
    
    let size_category = "standard";
    let directions_over = {};

    if (modelDimensions.some(dim => dim > full_volume_max)) {
        size_category = "too_large";
        directions_over = modelDimensions.reduce((acc, val, idx) => {
            if (val > full_volume_max) {
                acc[['X', 'Y', 'Z'][idx]] = val;
            }
            return acc;
        }, {});
    } else if (modelDimensions.some(dim => dim > standard_max)) {
        size_category = "full_volume";
        directions_over = modelDimensions.reduce((acc, val, idx) => {
            if (val > standard_max) {
                acc[['X', 'Y', 'Z'][idx]] = val - standard_max;
            }
            return acc;
        }, {});
    }

    // Display warnings if needed
    displayDimensionWarnings(size_category, directions_over);

    // Halt form submission if the model is too large
    if (size_category === "too_large") {
        return;
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
        if (data.error) {
            document.getElementById('quoteResult').innerHTML = `Error: ${data.error}`;
        } else {
            document.getElementById('quoteResult').innerHTML = `Estimated Quote: $${data.total_cost_with_tax}`;
        }
    } catch (error) {
        document.getElementById('quoteResult').innerHTML = `Failed to fetch quote: ${error.message}`;
    }
});

// Function to display warnings if dimensions are too large
function displayDimensionWarnings(size_category, directions_over) {
    const warningDiv = document.getElementById("quoteResult");
    warningDiv.innerHTML = ""; // Clear previous warnings

    if (size_category === "full_volume") {
        warningDiv.innerHTML = `Warning: Full-volume printing required due to exceeding standard size limits in dimensions: ${JSON.stringify(directions_over)}`;
    } else if (size_category === "too_large") {
        warningDiv.innerHTML = `Error: Model too large in dimensions: ${JSON.stringify(directions_over)}`;
    }
}
