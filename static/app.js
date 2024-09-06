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
            document.getElementById('quoteResult').innerHTML = `
                <p>Estimated Quote: $${data.total_cost_with_tax}</p>
                <p>Base Cost: $${data.base_cost}</p>
                <p>Material Cost: $${data.material_cost}</p>
                <p>Full Volume Surcharge: $${data.full_volume_surcharge}</p>
                <p>Shipping Cost: $${data.shipping_cost}</p>
                <p>Rush Order Surcharge: $${data.rush_order_surcharge}</p>
                <p>Sales Tax: $${data.sales_tax}</p>
            `;
        }
    } catch (error) {
        console.error('Error during fetch:', error);
        document.getElementById('quoteResult').innerHTML = `Failed to fetch quote: ${error.message}`;
    }
});
