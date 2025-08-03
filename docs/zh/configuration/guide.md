# 向导

!!! tip "图形化配置编辑器"

    === "用法"

        运行 `ktoolbox config-editor` 来启动，这会使配置编辑变得简单方便。

        - 按下 `<Esc>` 来返回，按 `<Enter>` 来选择 
        - 你也可以通过鼠标使用这个 GUI

!!! tip "生成示例 `.env` 文件"

    运行 `ktoolbox example-env` 来生成完整的配置文件样例。

- KToolBox 读取 **工作目录** 下的 **`.env` 或 `prod.env` 文件** 或 **环境变量** 来设定配置
  - 工作目录指的是你执行 `ktoolbox` 命令的目录位置，**不一定是 `ktoolbox` 可执行文件所在的目录**。在哪里执行就在哪里读取。
- 前往 [参考](./reference.md) 查看所有配置选项
- 用 `__` 来指定子选项, 例如 `KTOOLBOX_API__SCHEME` 相当于 `api.scheme`
- 所有配置选项都是可选的

## `.env` / `prod.env` 文件示例

```dotenv
##############################################################################
#  推荐使用图形化配置编辑器进行编辑。                                         #
#  运行 `ktoolbox config-editor` 启动编辑器。                                #
##############################################################################

# （可选）会话密钥，可在成功登录后的 cookies 中找到
# 403 错误时使用
#KTOOLBOX_API__SESSION_KEY=xxxxx

# 同时下载 10 个文件。
KTOOLBOX_JOB__COUNT=10

# 设置帖子附件目录路径为 `./`，表示将所有附件文件保存在帖子目录下
# 不会为附件单独创建子目录
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./

# 附件按数字顺序重命名，例如 `1.png`、`2.png`、……
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True

# 通过插入空的 `{}` 自定义文件名格式，表示基础文件名。
# 类似于 `post_dirname_format`，可以使用 `Post` 中的一些属性。
# 例如：`{title}_{}` > `HelloWorld_b4b41de2-8736-480d-b5c3-ebf0d917561b` 等。
# 也可以与 `sequential_filename` 一起使用。例如，
# `[{published}]_{}` > `[2024-1-1]_1.png`、`[2024-1-1]_2.png` 等。
KTOOLBOX_JOB__FILENAME_FORMAT=[{published}]_{title}_{id}_{}

# 帖子目录名以发布时间作为前缀，例如 `[2024-1-1]HelloWorld`
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{title}
```
