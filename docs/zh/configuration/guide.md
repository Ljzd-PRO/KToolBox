# 向导

- KToolBox 读取工作目录下的 **`prod.env` 文件** 或 **环境变量** 来设定配置
- 前往 [参考](./reference.md) 查看所有配置选项
- 用 `__` 来指定子选项, 例如 `KTOOLBOX_API__SCHEME` 相当于 `api.scheme`
- 所有配置选项都是可选的

## `prod.env` 文件示例

```dotenv
# 可同时下载10个文件
KTOOLBOX_JOB__COUNT=10

# 为每个下载任务分配 102400 字节内存作为缓冲区
KTOOLBOX_DOWNLOADER__BUFFER_SIZE=102400

# 设置作品附件目录为 `./`, 这意味着所有附件将直接保存在作品目录下
# 而不会创建一个子目录来储存
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./

# 为Kemono API服务器和下载服务器禁用SSL证书检查
# 在Kemono服务器的证书过期时很有用 （SSL: CERTIFICATE_VERIFY_FAILED）
KTOOLBOX_SSL_VERIFY=False

# 按照数字顺序重命名附件, 例如 `1.png`, `2.png`, ...
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True
```
