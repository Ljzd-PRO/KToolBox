# 常见问题

## 如何解决 uvloop 安装失败的问题？

!!! info "这是可选的"
    uvloop 可以提高并发性能，但它是 **可选的**。如果你不想安装 uvloop，你可以跳过这个步骤。

uvloop 在 **Windows** 上 **不受支持**。如果你在 Linux 或 macOS 安装失败， 
你可以尝试用例如 **apt**、**yum**、**brew** 的系统包管理器安装，包管理器提供构建好的 uvloop 包。

- 使用 apt 安装
    ```bash
    sudo apt install python3-uvloop
    ```

## 我不需要作品目录下的 `attachments` 文件夹

你可以设置配置选项 `job.post_structure.attachments` 为 `./`

通过 dotenv文件 `prod.env` 或系统环境变量来设置配置：
```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

`./` 表示附件文件将会直接下载到作品目录下。

!!! info "提示"
    更多详情，请参考 [配置-向导](configuration/guide.md) 页面。

## 命令和标志（选项）应当使用 `-` 还是 `_` 作为分隔符？

两者都支持，推荐使用 `-`。