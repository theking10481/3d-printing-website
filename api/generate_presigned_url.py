import boto3
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

BUCKET_NAME = 'your-bucket-name'

# AWS S3 client (credentials are picked up automatically from environment variables in Vercel)
s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION'))

@app.route('/api/generate-presigned-url', methods=['POST'])
def generate_presigned_url():
    try:
        # Get the file name from the request
        data = request.get_json()
        file_name = data.get('file_name')

        # Generate a pre-signed URL for uploading the file to S3
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET_NAME, 'Key': file_name},
            ExpiresIn=3600  # URL will expire in 1 hour
        )

        return jsonify({'url': presigned_url}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)