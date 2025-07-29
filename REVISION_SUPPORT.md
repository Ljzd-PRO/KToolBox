# KToolBox Revision Support

This document describes the revision support feature added to KToolBox.

## Overview

KToolBox now supports downloading revision posts from Kemono. Revision posts are updated versions of original posts that artists sometimes publish.

## Revision URL Format

Revision URLs follow this pattern:
```
https://kemono.su/{service}/user/{user_id}/post/{post_id}/revision/{revision_id}
```

Examples:
- Normal post: `https://kemono.su/fanbox/user/123/post/456`
- Revision post: `https://kemono.su/fanbox/user/123/post/456/revision/789`

## Features

### URL Parsing

The `parse_webpage_url()` function now returns 4 values instead of 3:
```python
service, user_id, post_id, revision_id = parse_webpage_url(url)
```

- For normal posts: `revision_id` will be `None`
- For revision posts: `revision_id` will contain the revision ID

### download-post Support

The `download-post` command now supports revision URLs:

```bash
# Download a revision post
ktoolbox download-post https://kemono.su/fanbox/user/123/post/456/revision/789

# Or specify parameters manually
ktoolbox download-post --service=fanbox --creator-id=123 --post-id=456 --revision-id=789
```

### Folder Structure

Revision posts are downloaded to a subfolder structure:
```
download_path/
└── {post_title}/
    ├── (normal post content - if downloading the main post)
    └── revision/
        └── {revision_id}/
            ├── attachments/
            ├── content.txt
            └── post.json
```

### API Support

The `get_post` API function now accepts an optional `revision_id` parameter:
```python
# Normal post
result = await get_post(service="fanbox", creator_id="123", post_id="456")

# Revision post  
result = await get_post(service="fanbox", creator_id="123", post_id="456", revision_id="789")
```

## sync-creator Considerations

The `sync-creator` command will work with revision posts if:
1. The Kemono API returns revision posts when fetching creator posts
2. You have a way to specify specific revision URLs

However, automatic discovery of revisions during sync-creator may be limited by the API's capabilities.

## Implementation Details

### Changes Made

1. **URL Parsing**: Extended `parse_webpage_url()` to handle revision URLs
2. **API Layer**: Updated `get_post` to construct revision endpoints
3. **CLI Layer**: Added `revision_id` parameter to `download_post` and `get_post`
4. **Job Creation**: Fixed directory creation to support nested revision folders
5. **Tests**: Added comprehensive tests for revision functionality

### Backward Compatibility

All existing functionality is preserved:
- Normal post URLs continue to work exactly as before
- All existing CLI commands and parameters work unchanged
- The API returns the same data structures

### Error Handling

The revision support includes proper error handling:
- Invalid URLs are handled gracefully
- Missing parameters show helpful error messages
- Network errors are handled the same as before

## Testing

The revision support has been tested with:
- Unit tests for URL parsing
- Integration tests for CLI functions
- Mock tests for API calls
- Manual testing of folder structure creation

## Usage Examples

```bash
# Download a normal post (unchanged)
ktoolbox download-post https://kemono.su/fanbox/user/123/post/456

# Download a revision post (new)
ktoolbox download-post https://kemono.su/fanbox/user/123/post/456/revision/789

# Get post data for a revision (new)
ktoolbox get-post --service=fanbox --creator-id=123 --post-id=456 --revision-id=789

# Sync creator (works with revisions if API provides them)
ktoolbox sync-creator https://kemono.su/fanbox/user/123
```

This implementation fulfills the main requirements from issue #240 for revision post support in KToolBox.