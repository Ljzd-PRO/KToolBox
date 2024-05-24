# Guide

- KToolBox read **`prod.env` file** in the work folder or **environment variables** to store configuration
- Check [Reference](reference.md) for all configuration options
- Use `__` to specify the sub option, like `KTOOLBOX_API__SCHEME` means `api.scheme`
- All configuration options are optional

## `prod.env` file example

```dotenv
# Download 10 files at the same time.
KTOOLBOX_JOB__COUNT=10

# Set post attachments directory path as `./`, it means to save all attachments files in post directory
# without making a new sub directory to storage them
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./

# Rename attachments in numerical order, e.g. `1.png`, `2.png`, ...
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True

# Customize the filename format by inserting an empty `{}` to represent the basic filename.
# Similar to `post_dirname_format`, you can use some of the properties in `Post`.
# For example: `{title}_{}` > `HelloWorld_b4b41de2-8736-480d-b5c3-ebf0d917561b`, etc.
# You can also use it with `sequential_filename`. For instance,
# `[{published}]_{}` > `[2024-1-1]_1.png`, `[2024-1-1]_2.png`, etc.
KTOOLBOX_JOB__FILENAME_FORMAT=[{published}]_{}

# Prefix the post directory name with its release/publish date, e.g. `[2024-1-1]HelloWorld`
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{title}

# Allocate 102400 Bytes as buffer for each download job
KTOOLBOX_DOWNLOADER__BUFFER_SIZE=102400

# Disable SSL certificate verification for Kemono API server and download server
# It's useful when certificate on Kemono server expired. (SSL: CERTIFICATE_VERIFY_FAILED)
KTOOLBOX_SSL_VERIFY=False
```
