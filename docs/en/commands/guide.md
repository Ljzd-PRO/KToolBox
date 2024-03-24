# Guide

Check [Reference](reference.md) for all commands and their flags / parameters.

## Get general help

- `--help`, `-h`

```bash
ktoolbox -h
```
  
## Get help of a command

- `--help`, `-h`

```bash
ktoolbox download-post -h
```

## Download a specific post

`download-post`

```bash
ktoolbox download-post https://kemono.su/fanbox/user/49494721/post/6608808
```
??? info "If some files failed to download"
    If some files failed to download, you can try to execute the command line again, 
    the downloaded files will be **skipped**.
  
## Download all posts from a creator

`sync-creator`

```bash
# Download all posts of the creator/artist
ktoolbox sync-creator https://kemono.su/fanbox/user/9016
```
??? info "About `creator-indices.ktoolbox` file"
    By default, you will get a `creator-indices.ktoolbox` file in the creator directory, 
    it contains the information and filepath of posts inside the directory.

??? tip "Update creator directory"
    You can rerun the command, files with the same filename will be skipped.

## Download posts that published within the specified time range

`sync-creator`

- `--start-time`: Start time of the published time range for posts downloading.
- `--end-time`: End time of the published time range for posts downloading.

```bash
# From 2023-8-5 to 2023-12-6
ktoolbox sync-creator https://kemono.su/fanbox/user/641955 --start-time=2023-8-5 --end-time=2023-12-6

# From 2023-8-5 to now
ktoolbox sync-creator https://kemono.su/fanbox/user/641955 --start-time=2023-8-5

# Before 2023-8-5
ktoolbox sync-creator https://kemono.su/fanbox/user/641955 --end-time=2023-8-5
```

### Time Format

The time value should match `%Y-%m-%d`, for example:

- `2023-12-7`
- `2023-12-07`
- `2023-12-31`
