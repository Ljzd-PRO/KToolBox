# Guide

- KToolBox read **`prod.env` file** in the work folder or **environment variables** to store configuration
- Check [Reference](reference.md) for all configuration options
- Use `__` to specify the sub option, like `KTOOLBOX_API__SCHEME` means `api.scheme`
- All configuration options are optional

## `prod.env` file example

```dotenv
# Download 10 files at the same time.
KTOOLBOX_JOB__COUNT=10

# Allocate 102400 Bytes as buffer for each download job
KTOOLBOX_DOWNLOADER__BUFFER_SIZE=102400

# Set post attachments directory path as `./`, it means to save all attachments files in post directory
# without making a new sub directory to storage them
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./

# Disable SSL certificate verification for Kemono API server and download server
# It's useful when certificate on Kemono server expired. (SSL: CERTIFICATE_VERIFY_FAILED)
KTOOLBOX_SSL_VERIFY=False

# Rename attachments in numerical order, e.g. `1.png`, `2.png`, ...
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True
```
