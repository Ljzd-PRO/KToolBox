# File Integrity Verification

KToolBox now includes robust file integrity verification features to prevent corrupted downloads and provide better reliability.

## Overview

The integrity verification system addresses common issues with incomplete downloads, including:
- Files that appear to download successfully but are actually corrupted (e.g., half-black images)
- `PermissionError(13)` issues during file operations
- Downloads that complete without proper size verification

## Features

### 1. File Size Verification

**Default: Enabled**

KToolBox automatically verifies that downloaded files match the expected size from HTTP headers:

- Checks `Content-Range` header first (for resumable downloads)  
- Falls back to `Content-Length` header if `Content-Range` is not available
- Fails the download and cleans up temporary files if sizes don't match

```bash
# Enable/disable via environment variable
KTOOLBOX_DOWNLOADER__VERIFY_FILE_INTEGRITY=true  # Default: true
```

### 2. SHA-256 Checksum Verification

**Default: Disabled**

Optional checksum calculation provides additional integrity verification:

- Calculates SHA-256 hash during download
- Logs the checksum for each completed file
- Enables detection of data corruption beyond size mismatches

```bash
# Enable checksum verification
KTOOLBOX_DOWNLOADER__CHECKSUM_VERIFICATION=true  # Default: false
```

### 3. Improved Error Handling

The downloader now includes:

- **PermissionError Retry**: Automatic retry up to 3 times with exponential backoff when file rename operations fail
- **Atomic Operations**: Better cleanup of temporary files when operations fail
- **Enhanced Logging**: More detailed error messages with context

## Configuration

### Via Environment Variables

```bash
# File integrity verification (recommended: keep enabled)
KTOOLBOX_DOWNLOADER__VERIFY_FILE_INTEGRITY=true

# Checksum verification (optional, adds logging overhead)
KTOOLBOX_DOWNLOADER__CHECKSUM_VERIFICATION=false
```

### Via Configuration File

```python
# In your configuration
downloader:
  verify_file_integrity: true      # Enable size verification
  checksum_verification: false     # Enable SHA-256 checksums
```

## When to Use

### File Integrity Verification
- **Always recommended** - should remain enabled (default)
- Prevents corrupted files from being saved
- Minimal performance impact
- Essential for reliability

### Checksum Verification  
- **Optional** - enable when you need extra verification
- Useful for archival purposes or when data integrity is critical
- Adds computational overhead during downloads
- Provides SHA-256 hash logging for each file

## Troubleshooting

### Common Issues

**Issue**: Downloads fail with "File integrity check failed: size mismatch"
- **Cause**: Server provided incorrect `Content-Length` or download was interrupted
- **Solution**: This is working correctly - the system prevented a corrupted file from being saved

**Issue**: PermissionError during downloads  
- **Cause**: File is being accessed by another process (antivirus, file explorer, etc.)
- **Solution**: The system now automatically retries with exponential backoff

**Issue**: Performance impact with checksum verification
- **Cause**: SHA-256 calculation adds CPU overhead
- **Solution**: Disable checksum verification if not needed: `KTOOLBOX_DOWNLOADER__CHECKSUM_VERIFICATION=false`

### Logs

With integrity verification enabled, you'll see logs like:

```
INFO - Download completed with checksum - file: image.jpg, sha256: a7b86d4635b0a3e10df870a604a1a811c01a7943c34e5bfb3759d9827473507b
```

With size mismatch detection:

```
ERROR - File integrity check failed: size mismatch - expected_size: 1024, actual_size: 512, filename: corrupted.jpg
```

## Migration

These features are designed to be backward compatible:

- **Existing downloads**: No configuration changes required
- **Default behavior**: File integrity verification is automatically enabled
- **Optional features**: Checksum verification remains disabled by default

The integrity verification system helps ensure reliable downloads while maintaining compatibility with existing configurations and workflows.