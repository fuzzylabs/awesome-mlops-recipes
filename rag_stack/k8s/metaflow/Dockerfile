# Use Netflix's official Metaflow metadata service image
FROM netflixoss/metaflow_metadata_service:latest

# Install boto3 for AWS/S3 integration
RUN pip install --no-cache-dir boto3>=1.34.0

EXPOSE 8080

CMD ["python", "-m", "services.metadata_service.server"]
