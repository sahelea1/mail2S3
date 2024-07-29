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
- [Poetry](https://python-poetry.org/) (Python package and dependency manager)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/encrypted-email-backup.git
   cd encrypted-email-backup
   ```

2. Install the project dependencies using Poetry:
   ```
   poetry install
   ```

   This command creates a virtual environment and installs all the required dependencies specified in the `pyproject.toml` file.

## Configuration

1. Copy the `config.toml.example` file to `config.toml`:
   ```
   cp config.toml.example config.toml
   ```

2. Edit `config.toml` with your specific settings:
   - Set the `action` to either "backup" or "restore"
   - Fill in your S3 credentialremove commit completely from historsys and settings
   - Add your email account details (just duplicate the whole section to backup more than one account.)
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

[[email_accounts]]
email_address = "your-email2@example2.com"
password = "your-email-password"
imap_server = "imap.example2.com"
encryption_password = "your-encryption-password"

.
.
.
```

## Usage

To run the script, use Poetry to ensure you're in the correct virtual environment:

```
poetry run python main.py
```

The script will read the `config.toml` file and perform the specified action (backup or restore) for each configured email account.

## Development

If you want to work on the project, you can use Poetry to spawn a shell within the virtual environment:

```
poetry shell
```

Then you can run the script directly:

```
python main.py
```

To add new dependencies to the project:

```
poetry add package-name
```

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

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

When contributing, please note that this project is released with an Apache License 2.0. Any code you submit will be under this license.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Key points of the Apache License 2.0:
- You can freely use, modify, distribute, and sell this software.
- You must include the original copyright notice and license in any copy of the software/source.
- You must state significant changes made to the software.
- You must include a copy of the Apache License 2.0 if you redistribute the code.
- This software comes with no warranties or conditions of any kind.

## Disclaimer

This software is provided as-is, without any warranties. Always test thoroughly and use at your own risk.
