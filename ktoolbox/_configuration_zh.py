import ktoolbox.configuration


# noinspection SpellCheckingInspection,GrazieInspection
class APIConfiguration(ktoolbox.configuration.APIConfiguration):
    """
    Kemono API 配置

    :ivar scheme: Kemono API 的 URL 协议
    :ivar netloc: Kemono API 的主机地址
    :ivar statics_netloc: Kemono 服务器静态文件（如图片）的主机地址
    :ivar files_netloc: Kemono 服务器帖子文件的主机地址
    :ivar path: Kemono API 的根路径
    :ivar timeout: API 请求超时时间
    :ivar retry_times: API 请求失败时重试次数
    :ivar retry_interval: API 请求重试间隔秒数
    :ivar session_key: 登录成功后可在 Cookie 中找到的会话密钥
    """
    ...


class DownloaderConfiguration(ktoolbox.configuration.DownloaderConfiguration):
    """
    文件下载器配置

    :ivar scheme: 下载器的 URL 协议
    :ivar timeout: 下载器请求超时时间
    :ivar encoding: 文件名解析和帖子内容文本保存的字符集
    :ivar buffer_size: 每个下载文件的文件 I/O 缓冲区字节数
    :ivar chunk_size: 下载器流的分块字节数
    :ivar temp_suffix: 下载文件的临时文件名后缀
    :ivar retry_times: 下载失败时重试次数
    :ivar retry_stop_never: 永不停止下载器重试（启用时忽略 retry_times）
    :ivar retry_interval: 下载器重试间隔秒数
    :ivar tps_limit: 每秒最大连接数
    :ivar use_bucket: 启用本地存储桶模式
    :ivar bucket_path: 本地存储桶路径
    :ivar reverse_proxy: 下载 URL 的反向代理格式。通过插入空的 ``{}`` 自定义文件名格式以表示原始 URL。例如：``https://example.com/{}`` 会变成 ``https://example.com/https://n1.kemono.su/data/66/83/xxxxx.jpg``；``https://example.com/?url={}`` 会变成 ``https://example.com/?url=https://n1.kemono.su/data/66/83/xxxxx.jpg``
    """
    ...


class PostStructureConfiguration(ktoolbox.configuration.PostStructureConfiguration):
    # noinspection SpellCheckingInspection
    """
    帖子路径结构模型

    - 默认结构:
    ```
    ..
    ├─ content.txt
    ├─ external_links.txt
    ├─ {id}_{}.png (文件)
    ├─ post.json (元数据)
    ├─ attachments
    │    ├─ 1.png
    │    └─ 2.png
    └─ revisions
         ├─ <PostStructure>
         │    ├─ ...
         │    └─ ...
         └─ <PostStructure>
              ├─ ...
              └─ ...
    ```

    - ``file`` 可用属性

        | 属性         | 类型   |
        |--------------|--------|
        | ``id``       | 字符串 |
        | ``user``     | 字符串 |
        | ``service``  | 字符串 |
        | ``title``    | 字符串 |
        | ``added``    | 日期   |
        | ``published``| 日期   |
        | ``edited``   | 日期   |

    :ivar attachments: 附件目录的子路径
    :ivar content: 帖子内容文件的子路径
    :ivar external_links: 外部链接文件的子路径（用于保存内容中发现的云存储链接）
    :ivar file: 帖子 `file` 文件名的格式（`file` 不是 `attachment`，每个帖子只有一个 `file`，通常为封面图片）。通过插入空的 ``{}`` 自定义文件名格式。可使用 [属性][ktoolbox.configuration.JobConfiguration]。例如：``{title}_{}`` 可能生成 ``TheTitle_Stelle_lv5_logo.gif``、``TheTitle_ScxHjZIdxt5cnjaAwf3ql2p7.jpg`` 等文件名。
    :ivar revisions: 修订目录的子路径
    """
    ...


class JobConfiguration(ktoolbox.configuration.JobConfiguration):
    """
    下载任务配置

    - ``post_dirname_format`` 和 ``filename_format`` 可用属性

        | 属性         | 类型   |
        |--------------|--------|
        | ``id``       | 字符串 |
        | ``user``     | 字符串 |
        | ``service``  | 字符串 |
        | ``title``    | 字符串 |
        | ``added``    | 日期   |
        | ``published``| 日期   |
        | ``edited``   | 日期   |

    - ``year_dirname_format`` 和 ``month_dirname_format`` 可用属性

        | 属性         | 类型   |
        |--------------|--------|
        | ``year``     | 字符串 |
        | ``month``    | 字符串 |

    :ivar count: 并发下载的协程数量
    :ivar include_revisions: 下载时包含修订帖子
    :ivar post_dirname_format: 自定义帖子目录名格式，可使用 [属性][ktoolbox.configuration.JobConfiguration]。例如：``[{published}]{id}`` > ``[2024-1-1]123123``，``{user}_{published}_{title}`` > ``234234_2024-1-1_TheTitle``
    :ivar post_structure: 帖子路径结构
    :ivar mix_posts: 在创作者目录下将不同帖子的所有文件保存到同一路径，不创建帖子目录，且不会记录 ``CreatorIndices``
    :ivar sequential_filename: 附件按数字顺序重命名，如 ``1.png``、``2.png`` 等
    :ivar sequential_filename_excludes: 启用 ``sequential_filename`` 时排除按顺序命名的文件扩展名，这些文件将保留原始名称。例如 ``[".psd", ".zip", ".mp4"]``
    :ivar filename_format: 通过插入空的 ``{}`` 自定义文件名格式，表示基本文件名。可使用 [属性][ktoolbox.configuration.JobConfiguration]。例如：``{title}_{}`` 可能生成 ``TheTitle_b4b41de2-8736-480d-b5c3-ebf0d917561b``、``TheTitle_af349b25-ac08-46d7-98fb-6ce99a237b90`` 等。也可与 ``sequential_filename`` 结合使用，如 ``[{published}]_{}`` 可能生成 ``[2024-1-1]_1.png``、``[2024-1-1]_2.png`` 等。
    :ivar allow_list: 下载匹配这些模式（Unix shell 风格）的文件，如 ``["*.png"]``
    :ivar block_list: 不下载匹配这些模式（Unix shell 风格）的文件，如 ``["*.psd","*.zip"]``
    :ivar extract_external_links: 从帖子内容中提取外部文件分享链接并保存到单独文件
    :ivar external_link_patterns: 用于提取外部链接的正则表达式模式
    :ivar group_by_year: 根据发布日期按年分组到不同目录
    :ivar group_by_month: 根据发布日期按月分组到不同目录（需要启用 group_by_year）
    :ivar year_dirname_format: 自定义年份目录名格式。可用属性：``year``。例如：``{year}`` > ``2024``，``Year_{year}`` > ``Year_2024``
    :ivar month_dirname_format: 自定义月份目录名格式。可用属性：``year``、``month``。例如：``{year}-{month}`` > ``2024-01``，``{year}_{month}`` > ``2024_01``
    """
    ...


class LoggerConfiguration(ktoolbox.configuration.LoggerConfiguration):
    """
    日志配置

    :ivar path: 日志保存路径，``None`` 表示不输出日志文件
    :ivar level: 日志过滤级别
    :ivar rotation: 日志轮换周期
    """
    ...


class Configuration(ktoolbox.configuration.Configuration):
    # noinspection SpellCheckingInspection,GrazieInspection
    """
    KToolBox 配置

    :ivar api: Kemono API 配置
    :ivar downloader: 文件下载器配置
    :ivar job: 下载任务配置
    :ivar logger: 日志配置
    :ivar webui: Web UI 配置
    :ivar ssl_verify: 对 Kemono API 服务器和下载服务器启用 SSL 证书验证
    :ivar json_dump_indent: JSON 文件保存时的缩进
    :ivar use_uvloop: 使用 uvloop/winloop 优化 asyncio 性能 \
    Windows 下使用 winloop，类 Unix 系统下使用 uvloop，提高并发性能。\
    Windows 下安装 winloop：`pip install ktoolbox[winloop]` \
    Unix 下安装 uvloop：`pip install ktoolbox[uvloop]`
    """
    ...
�下载服务器启用 SSL 证书验证
    :ivar json_dump_indent: JSON 文件保存时的缩进
    :ivar use_uvloop: 使用 uvloop/winloop 优化 asyncio 性能 \
    Windows 下使用 winloop，类 Unix 系统下使用 uvloop，提高并发性能。\
    Windows 下安装 winloop：`pip install ktoolbox[winloop]` \
    Unix 下安装 uvloop：`pip install ktoolbox[uvloop]`
    """
    ...
