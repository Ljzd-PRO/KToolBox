# 常见问题

## 如何解决 uvloop/winloop 安装失败的问题？

!!! info "这是可选的"
    事件循环优化（uvloop/winloop）可以提高并发性能，但它是 **可选的**。如果你不想安装这些包，你可以跳过这个步骤。

KToolBox 现在支持平台特定的事件循环优化：

- **Windows**: 使用 `winloop` 来提升性能
- **Linux/macOS**: 使用 `uvloop` 来提升性能

### 安装事件循环优化

=== "Windows"
    ```bash
    pip install ktoolbox[winloop]
    ```

=== "Linux/macOS"
    ```bash
    pip install ktoolbox[uvloop]
    ```

如果你在 Linux 或 macOS 安装 uvloop 失败， 
你可以尝试用例如 **apt**、**yum**、**brew** 的系统包管理器安装，包管理器提供构建好的 uvloop 包。

- 使用 apt 安装
    ```bash
    sudo apt install python3-uvloop
    ```

## 我不需要帖子目录下的 `attachments` 文件夹

你可以设置配置选项 `job.post_structure.attachments` 为 `./`

通过 dotenv 文件 `prod.env` 或系统环境变量来设置配置：
```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

`./` 表示附件文件将会直接下载到帖子目录下。

!!! info "提示"
    更多详情，请参考 [配置-向导](configuration/guide.md) 页面。

## 命令和标志（选项）应当使用 `-` 还是 `_` 作为分隔符？

两者都支持，推荐使用 `-`。

## 文件名过长

在一些情况下，文件名或帖子目录名过长而导致下载失败。为了解决这个问题，你可以设置 **序列化文件名** 或使用 **自定义帖子目录名**

通过 dotenv 文件 `prod.env` 或系统环境变量来设置配置：
```dotenv
# 按照数字顺序重命名附件, 例如 `1.png`, `2.png`, ...
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True

# 设置帖子目录名为其发布日期和ID，例如 `[2024-1-1]11223344`
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{id}
```

## 如何配置代理？

可以通过设置 `HTTPS_PROXY`, `HTTP_PROXY`, `ALL_PROXY` 环境变量实现

参考：[HTTPX - Environment Variables](https://www.python-httpx.org/environment_variables/#http_proxy-https_proxy-all_proxy)

例如这样设置：

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

## 图形化配置编辑器无法打开

!!! warning "注意"
    [`ktoolbox-pure-py`](https://pypi.org/project/ktoolbox-pure-py/) 不支持图形化配置编辑器

默认情况下，图形化配置编辑器的相关依赖不会被安装，可使用以下命令附带安装：

```shell
pip3 install ktoolbox[urwid]
```

如果你用的是 pipx：

```shell
pipx install ktoolbox[urwid] --force
```

## Kemono API 调用失败

例如：

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

1. 确保更新到了 [v0.14.0](https://github.com/Ljzd-PRO/KToolBox/releases/tag/v0.14.0) 或以上版本

2. 一般可能是因为请求频繁导致，你可以尝试设置更多的 API 重试次数
    ```dotenv
    # .env / prod.env
    KTOOLBOX_API__RETRY_TIMES=10
    ```

3. 你可以尝试设置下载所用的 **session key** （登录成功后可在 Cookies 中查看）
    ```dotenv
    # .env / prod.env
    KTOOLBOX_API__SESSION_KEY="xxxxxxx"
    ```

你也可以通过图形化配置编辑器设置：`API - retry_times` 和 `API -> session_key`.

## 下载时频繁出现 403 错误

解决方法同上

## 我在哪里可以找到更多帮助？

- 向导：用 **AI（Copilot Spaces）** 获取命令参数和配置帮助：[#304](https://github.com/Ljzd-PRO/KToolBox/issues/304)
- 一个社区分享的使用向导：[#141](https://github.com/Ljzd-PRO/KToolBox/issues/141)
