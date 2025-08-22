# FAQ

## How to solve the failure of uvloop/winloop installation?

!!! info "It's optional"
    Event loop optimization (uvloop/winloop) can improve concurrent performance, but it's **optional**. 
    If you don't want to install these packages, you can ignore this step.

KToolBox now supports platform-specific event loop optimization:

- **Windows**: Uses `winloop` for improved performance
- **Linux/macOS**: Uses `uvloop` for improved performance

### Installing event loop optimizations

=== "Windows"
    ```bash
    pip install ktoolbox[winloop]
    ```

=== "Linux/macOS"
    ```bash
    pip install ktoolbox[uvloop]
    ```

If you failed installing uvloop on Linux or macOS, you can try to install it with system package manager like **apt**, **yum** or **brew**, as package managers provide prebuilt wheels for uvloop.

- Install with apt
    ```bash
    sudo apt install python3-uvloop
    ```

## `attachments` folder inside post directory is no need for me

You can set configuration option `job.post_structure.attachments` to `./`

Set the configuration by `prod.env` dotenv file or system environment variables:
```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

`./` means attachments will be downloaded directly into the post directory.

!!! info "Notice"
    For more information, please visit [Configuration-Guide](configuration/guide.md) page.

## How to disable cover image download?

You can set configuration option `job.download_file` to `False` to disable cover image (file) download functionality.

Set the configuration by `prod.env` dotenv file or system environment variables:
```dotenv
# Disable cover image download
KTOOLBOX_JOB__DOWNLOAD_FILE=False

# If you also want to disable attachment downloads, you can set
#KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

With this setting, KToolBox will only download attachments and skip file downloads. This is useful when some authors have garbled image names that require renaming functionality to sort by webpage order.

!!! info "Notice"
    - `download_file`: Controls whether to download post file (usually cover image)
    - `download_attachments`: Controls whether to download post attachments  
    - Both options default to `True` for backward compatibility

## Commands and flags should use `-` or `_` as seperator?

Both is support, `-` is suggested.

## Filename too long

In some cases, the filename or the post directory name can be too long and caused download failure.
To solve this issue, you can set **sequential filename** or use **custom post directory name**

Set the configuration by `prod.env` dotenv file or system environment variables:
```dotenv
# Rename attachments in numerical order, e.g. `1.png`, `2.png`, ...
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True

# Set the post directory name to its release/publish date and ID, e.g. `[2024-1-1]11223344`
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{id}
```

## How to Configure a Proxy?

You can set the `HTTPS_PROXY`, `HTTP_PROXY`, and `ALL_PROXY` environment variables to achieve this.

Refer to: [HTTPX - Environment Variables](https://www.python-httpx.org/environment_variables/#http_proxy-https_proxy-all_proxy)

For example, set it like this:

```shell
# Unix Shell
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897
export ALL_PROXY=socks5://127.0.0.1:7897
```

```powershell
# Windows PowerShell
$env:HTTP_PROXY="http://127.0.0.1:7897"; $env:HTTPS_PROXY="http://127.0.0.1:7897"
```

## GUI Configuration Editor Cannot Be Opened

!!! warning "Note"
    [`ktoolbox-pure-py`](https://pypi.org/project/ktoolbox-pure-py/) does not support the graphical configuration editor.

By default, the dependencies for the graphical configuration editor are not installed. You can install them using the following command:

```shell
pip3 install ktoolbox[urwid]
```

If you are using pipx:

```shell
pipx install ktoolbox[urwid] --force
```

## Kemono API Call Failed

For example:

```
ktoolbox sync-creator "https://coomer.su/onlyfans/user/hollyharper11" --start-time="2020-05-01" --end-time="2025-01-01"

2024-05-12 12:52:51.477 | INFO     | ktoolbox.cli:sync_creator:271 - Got creator information - {'name': 'hollyharper11', 'id': 'hollyharper11'}
2024-05-12 12:52:51.479 | INFO     | ktoolbox.action.job:create_job_from_creator:148 - Start fetching posts from creator hollyharper11
2024-05-12 12:52:56.477 | ERROR    | ktoolbox.api.base:_retry_error_callback:37 - Kemono API call failed - {'ret': APIRet(code=1002, message="1 validation error for Response\n  Invalid JSON: expected value at line 1 column 1 [type=json_invalid, input_value='<!DOCTYPE html>\\n<html>\\...>\\n  </body>\\n</html>\\n', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.7/v/json_invalid", exception=1 validation error for Response
  Invalid JSON: expected value at line 1 column 1 [type=json_invalid, input_value='<!DOCTYPE html>\n<html>\...>\n  </body>\n</html>\n', input_type=str]
    For further information visit https://errors.pydantic.dev/2.7/v/json_invalid, data=None)}
1 validation error for Response
  Invalid JSON: expected value at line 1 column 1 [type=json_invalid, input_value='<!DOCTYPE html>\n<html>\...>\n  </body>\n</html>\n', input_type=str]
    For further information visit https://errors.pydantic.dev/2.7/v/json_invalid
```

1. This is generally caused by frequent requests, so you can try setting a higher number of API retry attempts.
    ```dotenv
    # .env / prod.env
    KTOOLBOX_API__RETRY_TIMES=10
    ```

2. You can set **session key** (can be found in cookies after a successful login) for download
    ```dotenv
    # .env / prod.env
    KTOOLBOX_API__SESSION_KEY="xxxxxxx"
    ```

You can also set these through the graphical configuration editor: `API - retry_times` and `API -> session_key`.

## Frequently encounter **403** errors during downloads

The solution is the same as above.

## Antivirus software flags the executable as a virus/threat

This is a **false positive**. KToolBox is completely safe and open-source software.

**Why this happens:**
- PyInstaller executables are commonly flagged by antivirus engines due to their packing method
- Downloaded executables from the internet are often treated with suspicion
- Some heuristic engines flag any "download manager" type software

**Solutions:**
1. **Add an exception** in your antivirus software for the KToolBox executable
2. **Use pipx or pip installation** instead
3. **Build from source** if you're still concerned:
   ```bash
   git clone https://github.com/Ljzd-PRO/KToolBox.git
   cd KToolBox
   poetry install --with pyinstaller
   poetry run pyinstaller ktoolbox.spec
   ```

**Security assurance:**
- All releases are built automatically using GitHub Actions (publicly visible)
- Source code is completely open and auditable
- No malicious code exists in this project

## Where can I find more information about KToolBox?

- Guide: Use **AI(Copilot Spaces)** for command params and configuration help: [#304](https://github.com/Ljzd-PRO/KToolBox/issues/304)
- A community-shared usage guide: [#141](https://github.com/Ljzd-PRO/KToolBox/issues/141)
