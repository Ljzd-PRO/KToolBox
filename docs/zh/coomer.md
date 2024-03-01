# Coomer

KToolBox 支持从 Coomer.su / Coomer.party 下载

Coomer.su 的文件可以从 Kemono.su / Kemono.party 服务器下载，所以 **无需编辑配置** 即可下载 Coomer 里的作品

如果无效，你可以通过 dotenv文件 `prod.env` 或系统环境变量来修改配置，然后再次尝试：
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
