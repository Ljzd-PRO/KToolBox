# Coomer

KToolBox 支持从 Coomer.su / Coomer.party 下载，但目前在它能够使用之前需要进行 **配置**。

你需要通过 dotenv文件 `prod.env` 或系统环境变量来设置配置：
```dotenv
# Coomer API
KTOOLBOX_API__NETLOC=coomer.su

# 用于从 Coomer 服务器下载文件
KTOOLBOX_API__FILES_NETLOC=coomer.su
```

## 关于 Coomer

官网 [https://coomer.su](https://coomer.su) 的介绍：

> Coomer is a public archiver for:
> 
> - OnlyFans
> - Fansly
> 
> Contributors here upload content and share it here for easy searching and organization. To get started viewing content, either search for creators on the creators page, or search for content on the posts page. If you want to contribute content, head over to the import page.
