# Guide

!!! tip "Graphical Configuration Editor"

    === "Usage"

        Run `ktoolbox config-editor` to launch, 
        it will make configuration editing simple and convenient.

        - Press `<Esc>` for back, `<Enter>` for select
        - You can also use the GUI with the mouse

!!! tip "Generate Example `.env` File"

    Run `ktoolbox example-env` to generate a complete sample configuration file.

- KToolBox load **`.env` or `prod.env` file** in the **working directory** or **environment variables** to store configuration
  - The working directory refers to the directory where you execute the `ktoolbox` command, **it is not necessarily the directory where the `ktoolbox` executable is located**. It reads from where you execute it.
- Check [Reference](reference.md) for all configuration options
- Use `__` to specify the sub option, like `KTOOLBOX_API__SCHEME` means `api.scheme`
- All configuration options are optional

## `.env` / `prod.env` file example

```dotenv
##############################################################################
#  It is recommended to use the graphical configuration editor for editing.  #
#  Run `ktoolbox config-editor` to launch it.                                #
##############################################################################

# (Optional) Session key that can be found in cookies after a successful login
# Use when 403 Error
#KTOOLBOX_API__SESSION_KEY=xxxxx

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
KTOOLBOX_JOB__FILENAME_FORMAT=[{published}]_{title}_{id}_{}

# Prefix the post directory name with its release/publish date, e.g. `[2024-1-1]HelloWorld`
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{title}
```
