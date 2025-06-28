import logging
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)

def generate_presigned_url(s3_client, client_method, method_parameters, expires_in):

    try:
        url = s3_client.generate_presigned_url(
            clientMethod=client_method,
            Params=method_parameters,
            ExpiresIn=expires_in
        )
        logger.info("Got presigned URL: %s", url)
    except ClientError:
        logger.exception("Couldn't get a presigned URL for client method '%s'.")
        raise

    return url

def rsa_signer(message):
    private_key=serialization.load_pem_private_key(
        settings.AWS_CLOUDFRONT_KEY,
        password=None,
        backend=default_backend()
    )

    signature=private_key.sign(
        message,
        padding.PKCS1v15(),
        hashes.SHA1()
    )

    return signature