# 向导

- KToolBox 读取工作目录下的 **`prod.env` 文件** 或 **环境变量** 来设定配置
- 前往 [参考](./reference.md) 查看所有配置选项
- 用 `__` 来指定子选项, 例如 `KTOOLBOX_API__SCHEME` 相当于 `api.scheme`
- 所有配置选项都是可选的

## `prod.env` 文件示例

```dotenv
# 可同时下载10个文件
KTOOLBOX_JOB__COUNT=10

# 设置作品附件目录为 `./`, 这意味着所有附件将直接保存在作品目录下
# 而不会创建一个子目录来储存
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./

# 按照数字顺序重命名附件, 例如 `1.png`, `2.png`, ...
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True

# 通过插入一个代表了基本文件名的空白的 `{}` 以自定义文件名格式 
# 与 `post_dirname_format` 类似，你可以使用一些 `Post` 类里的属性
# 例如 `{title}_{}` > `HelloWorld_b4b41de2-8736-480d-b5c3-ebf0d917561b`
# 你也可以和 `sequential_filename` 搭配使用
# 例如 `[{published}]_{}` > `[2024-1-1]_1.png`, `[2024-1-1]_2.png`
KTOOLBOX_JOB__FILENAME_FORMAT=[{published}]_{}

# 将发布日期作为作品目录名的开头，例如 `[2024-1-1]HelloWorld`
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{title}

# 为每个下载任务分配 102400 字节内存作为缓冲区
KTOOLBOX_DOWNLOADER__BUFFER_SIZE=102400

# 为Kemono API服务器和下载服务器禁用SSL证书检查
# 在Kemono服务器的证书过期时很有用 （SSL: CERTIFICATE_VERIFY_FAILED）
KTOOLBOX_SSL_VERIFY=False
```
