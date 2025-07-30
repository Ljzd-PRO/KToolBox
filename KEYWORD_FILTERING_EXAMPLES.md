# Keyword Filtering Usage Examples

The KToolBox now supports keyword filtering for the `sync_creator` command, allowing you to download only posts that contain specific keywords in their title.

## Basic Usage

```bash
# Filter posts containing "python" in title
ktoolbox sync_creator --service patreon --creator_id 12345 --keywords "python"

# Filter posts containing multiple keywords (OR logic)
ktoolbox sync_creator --service patreon --creator_id 12345 --keywords "python,tutorial,programming"

# Combine with time filtering
ktoolbox sync_creator --service patreon --creator_id 12345 --keywords "python" --start_time "2024-01-01" --end_time "2024-12-31"

# Combine with post count limiting
ktoolbox sync_creator --service patreon --creator_id 12345 --keywords "python" --length 50
```

## Features

- **Case-insensitive matching**: Keywords match regardless of case
- **Substring matching**: "python" matches "Python", "python", "pythonic", etc.
- **Multiple keywords**: Use comma-separated values for OR logic
- **Content and title search**: Keywords are searched in post title only
- **Combines with existing filters**: Works alongside time range and post count limits

## Examples by Use Case

### Art Creator with Mixed Content
```bash
# Only download digital art posts
ktoolbox sync_creator --url "https://kemono.su/patreon/user/12345" --keywords "digital,artwork,illustration"
```

### Tutorial Creator
```bash
# Only download Python tutorials
ktoolbox sync_creator --service patreon --creator_id 12345 --keywords "python,tutorial"
```

### Game Developer
```bash
# Only download Unity-related posts
ktoolbox sync_creator --service patreon --creator_id 12345 --keywords "unity,game development,gamedev"
```

### Mixed Creator with Time + Keyword Filtering
```bash
# Download recent Python content only
ktoolbox sync_creator --service patreon --creator_id 12345 \
  --keywords "python,programming" \
  --start_time "2024-01-01" \
  --length 20
```