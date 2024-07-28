# Encrypted Email Backup and Restore

This project provides a secure way to backup your emails to S3-compatible storage and restore them when needed. It uses encryption to ensure the privacy of your emails during storage.

## Features

- Backup emails from multiple IMAP accounts
- Encrypt emails before uploading to S3 storage
- Restore emails from S3 storage to IMAP accounts
- Rate-limited uploads to prevent overwhelming S3 storage or network
- Configuration via TOML file for easy setup

## Prerequisites

- Python 3.7+
- pip (Python package installer)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/encrypted-email-backup.git
   cd encrypted-email-backup
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the `config.toml.example` file to `config.toml`:
   ```
   cp config.toml.example config.toml
   ```

2. Edit `config.toml` with your specific settings:
   - Set the `action` to either "backup" or "restore"
   - Fill in your S3 credentials and settings
   - Add your email account details
   - Set the maximum upload rate (e.g., "5MB" or "1GB")

Example `config.toml`:

```toml
action = "backup"

[s3]
endpoint = "https://s3.eu-central-003.backblazeb2.com"
key = "your-access-key"
secret = "your-secret-key"
bucket_name = "your-bucket-name"
max_upload_rate = "5MB"

[[email_accounts]]
email_address = "your-email@example.com"
password = "your-email-password"
imap_server = "imap.example.com"
encryption_password = "your-encryption-password"
```

## Usage

To run the script, simply execute:

```
python main.py
```

The script will read the `config.toml` file and perform the specified action (backup or restore) for each configured email account.

## Security Considerations

- This script uses strong encryption (ChaCha20-Poly1305) to protect your emails.
- Encryption passwords are never stored; they're only used to derive encryption keys.
- Be sure to keep your `config.toml` file secure, as it contains sensitive information.
- It's recommended to use an app-specific password for your email account if your provider supports it.

## Limitations

- Currently, the script only backs up the inbox. Other folders are not included.
- Attachments are included in the backup but are not handled separately.
- The script doesn't handle incremental backups; it checks for new emails on each run.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is provided as-is, without any warranties. Always test thoroughly and use at your own risk.
