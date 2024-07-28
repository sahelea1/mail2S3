import imaplib
import email
import os
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import boto3
from botocore.client import Config
import base64
import json
import toml
import hashlib
import time

def derive_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def encrypt_message(message, key):
    chacha = ChaCha20Poly1305(key)
    nonce = os.urandom(12)
    ciphertext = chacha.encrypt(nonce, message.as_bytes(), None)
    return nonce + ciphertext

def decrypt_message(encrypted_data, key):
    chacha = ChaCha20Poly1305(key)
    nonce, ciphertext = encrypted_data[:12], encrypted_data[12:]
    return chacha.decrypt(nonce, ciphertext, None)

def connect_to_email(email_address, password, imap_server):
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email_address, password)
    return mail

def fetch_all_emails(mail):
    mail.select('inbox')
    _, message_numbers = mail.search(None, 'ALL')
    for num in message_numbers[0].split():
        _, msg = mail.fetch(num, '(RFC822)')
        yield email.message_from_bytes(msg[0][1])

def upload_to_s3(s3_client, bucket_name, file_name, data):
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=data)

def download_from_s3(s3_client, bucket_name, file_name):
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
        return response['Body'].read()
    except s3_client.exceptions.NoSuchKey:
        return None

def get_email_hash(email_message):
    return hashlib.md5(email_message.as_bytes()).hexdigest()

def parse_size(size_str):
    size = float(size_str[:-2])
    unit = size_str[-2:].upper()
    if unit == 'MB':
        return size * 1024 * 1024
    elif unit == 'GB':
        return size * 1024 * 1024 * 1024
    else:
        raise ValueError(f"Invalid size unit: {unit}. Use 'MB' or 'GB'.")

class RateLimitedS3:
    def __init__(self, s3_client, max_rate_bytes):
        self.s3_client = s3_client
        self.max_rate_bytes = max_rate_bytes
        self.last_upload_time = time.time()
        self.bytes_uploaded = 0

    def put_object(self, **kwargs):
        data_size = len(kwargs['Body'])
        self._wait_for_rate_limit(data_size)
        self.s3_client.put_object(**kwargs)
        self.bytes_uploaded += data_size
        self.last_upload_time = time.time()

    def _wait_for_rate_limit(self, data_size):
        if self.max_rate_bytes > 0:
            elapsed_time = time.time() - self.last_upload_time
            required_time = self.bytes_uploaded / self.max_rate_bytes
            if required_time > elapsed_time:
                time.sleep(required_time - elapsed_time)
            self.bytes_uploaded = 0

    def get_object(self, **kwargs):
        return self.s3_client.get_object(**kwargs)

    def exceptions(self):
        return self.s3_client.exceptions

def backup_emails(email_config, s3_config):
    # Generate salt and derive key
    salt = os.urandom(16)
    key = derive_key(email_config['encryption_password'], salt)
    
    # Connect to email
    mail = connect_to_email(email_config['email_address'], email_config['password'], email_config['imap_server'])
    
    # Create a rate-limited S3 client
    max_rate = parse_size(s3_config['max_upload_rate'])
    s3_client = RateLimitedS3(boto3.client('s3',
        endpoint_url=s3_config['endpoint'],
        aws_access_key_id=s3_config['key'],
        aws_secret_access_key=s3_config['secret'],
        config=Config(signature_version='s3v4')
    ), max_rate)
    
    # Create a folder for this email account
    folder_name = email_config['email_address'].replace('@', '_at_')
    
    # Load existing email hashes
    existing_hashes = download_from_s3(s3_client, s3_config['bucket_name'], f'{folder_name}/email_hashes.json')
    if existing_hashes:
        existing_hashes = json.loads(existing_hashes.decode())
    else:
        existing_hashes = {}
    
    new_hashes = {}
    
    # Fetch, encrypt, and upload new emails
    for i, msg in enumerate(fetch_all_emails(mail)):
        email_hash = get_email_hash(msg)
        if email_hash not in existing_hashes:
            encrypted_msg = encrypt_message(msg, key)
            file_name = f'{folder_name}/email_{i}_{email_hash}.enc'
            upload_to_s3(s3_client, s3_config['bucket_name'], file_name, encrypted_msg)
            new_hashes[email_hash] = file_name
    
    # Update and upload email hashes
    existing_hashes.update(new_hashes)
    upload_to_s3(s3_client, s3_config['bucket_name'], f'{folder_name}/email_hashes.json', json.dumps(existing_hashes).encode())
    
    # Upload salt (only if it's the first backup)
    if not download_from_s3(s3_client, s3_config['bucket_name'], f'{folder_name}/salt.bin'):
        upload_to_s3(s3_client, s3_config['bucket_name'], f'{folder_name}/salt.bin', salt)
    
    mail.logout()
    
    print(f"Backed up {len(new_hashes)} new emails for {email_config['email_address']}")

def restore_emails(email_config, s3_config):
    # Connect to S3
    s3_client = boto3.client('s3',
        endpoint_url=s3_config['endpoint'],
        aws_access_key_id=s3_config['key'],
        aws_secret_access_key=s3_config['secret'],
        config=Config(signature_version='s3v4')
    )
    
    folder_name = email_config['email_address'].replace('@', '_at_')
    
    # Download salt and derive key
    salt = download_from_s3(s3_client, s3_config['bucket_name'], f'{folder_name}/salt.bin')
    if not salt:
        print(f"No backup found for {email_config['email_address']}")
        return
    key = derive_key(email_config['encryption_password'], salt)
    
    # Connect to email
    mail = connect_to_email(email_config['email_address'], email_config['password'], email_config['imap_server'])
    
    # Load email hashes
    email_hashes = json.loads(download_from_s3(s3_client, s3_config['bucket_name'], f'{folder_name}/email_hashes.json').decode())
    
    # Download, decrypt, and restore emails
    for file_name in email_hashes.values():
        encrypted_msg = download_from_s3(s3_client, s3_config['bucket_name'], file_name)
        decrypted_msg = decrypt_message(encrypted_msg, key)
        mail.append('INBOX', None, None, decrypted_msg)
    
    mail.logout()
    
    print(f"Restored {len(email_hashes)} emails for {email_config['email_address']}")

def main():
    # Load configuration
    with open('config.toml', 'r') as f:
        config = toml.load(f)
    
    s3_config = config['s3']
    
    for email_account in config['email_accounts']:
        print(f"Processing account: {email_account['email_address']}")
        if config['action'] == 'backup':
            backup_emails(email_account, s3_config)
        elif config['action'] == 'restore':
            restore_emails(email_account, s3_config)
        else:
            print(f"Unknown action: {config['action']}")

if __name__ == "__main__":
    main()