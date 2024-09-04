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

    const data = await response.json();
    document.getElementById('quoteResult').innerHTML = `Estimated Quote: $${data.total_cost_with_tax}`;
});