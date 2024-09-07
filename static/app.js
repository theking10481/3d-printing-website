document.getElementById('quoteForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData();
    formData.append('zip_code', document.getElementById('zip_code').value);
    formData.append('filament_type', document.getElementById('filament_type').value);
    formData.append('quantity', document.getElementById('quantity').value);
    formData.append('rush_order', document.getElementById('rush_order').checked);
    formData.append('use_usps_connect_local', document.getElementById('use_usps_connect_local').checked);
    formData.append('model_file', document.getElementById('model_file').files[0]);  // Attach the 3D model file

    try {
        const response = await fetch('/api/quote', {
            method: 'POST',
            body: formData
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
                <p>Estimated Quote: ${data.total_cost_with_tax}</p>
                <p>Base Cost: ${data.base_cost}</p>
                <p>Material Cost: ${data.material_cost}</p>
                <p>Shipping Cost: ${data.shipping_cost}</p>
                <p>Rush Order Surcharge: ${data.rush_order_surcharge}</p>
                <p>Sales Tax: ${data.sales_tax}</p>
            `;
        }
    } catch (error) {
        console.error('Error during fetch:', error);
        document.getElementById('quoteResult').innerHTML = `Failed to fetch quote: ${error.message}`;
    }
});