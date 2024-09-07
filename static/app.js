document.getElementById('quoteForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const fileInput = document.getElementById('model_file');
    const file = fileInput.files[0];  // Get the selected file
    if (!file) {
        alert('Please select a file.');
        return;
    }

    // Step 1: Get a pre-signed URL for S3 upload
    try {
        const response = await fetch('/generate-presigned-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_name: file.name
            })
        });

        if (!response.ok) {
            throw new Error('Failed to get a pre-signed URL.');
        }

        const data = await response.json();
        const presignedUrl = data.url;

        // Step 2: Upload the file to S3 using the pre-signed URL
        const uploadResponse = await fetch(presignedUrl, {
            method: 'PUT',
            headers: {
                'Content-Type': file.type  // Set the file type (MIME type)
            },
            body: file
        });

        if (!uploadResponse.ok) {
            throw new Error('Failed to upload the file to S3.');
        }

        // Step 3: After the file is uploaded, send the S3 file URL to the backend for quote calculation
        const formData = new FormData();
        formData.append('zip_code', document.getElementById('zip_code').value);
        formData.append('filament_type', document.getElementById('filament_type').value);
        formData.append('quantity', document.getElementById('quantity').value);
        formData.append('rush_order', document.getElementById('rush_order').checked ? 'true' : 'false');
        formData.append('use_usps_connect_local', document.getElementById('use_usps_connect_local').checked ? 'true' : 'false');
        formData.append('file_url', presignedUrl);  // Send the S3 file URL

        const quoteResponse = await fetch('/api/quote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                zip_code: document.getElementById('zip_code').value,
                filament_type: document.getElementById('filament_type').value,
                quantity: document.getElementById('quantity').value,
                rush_order: document.getElementById('rush_order').checked ? 'true' : 'false',
                use_usps_connect_local: document.getElementById('use_usps_connect_local').checked ? 'true' : 'false',
                file_url: presignedUrl
            })
        });

        if (!quoteResponse.ok) {
            throw new Error('Failed to get a quote.');
        }

        const quoteData = await quoteResponse.json();
        document.getElementById('quoteResult').innerHTML = `
            <p>Estimated Quote: ${quoteData.total_cost_with_tax}</p>
            <p>Base Cost: ${quoteData.base_cost}</p>
            <p>Material Cost: ${quoteData.material_cost}</p>
            <p>Shipping Cost: ${quoteData.shipping_cost}</p>
            <p>Rush Order Surcharge: ${quoteData.rush_order_surcharge}</p>
            <p>Sales Tax: ${quoteData.sales_tax}</p>
        `;
    } catch (error) {
        console.error('Error during process:', error);
        document.getElementById('quoteResult').innerHTML = `Failed to get a quote: ${error.message}`;
    }
});