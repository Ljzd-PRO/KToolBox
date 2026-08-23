# 项目信息

## 发布状态

KToolBox v1 是基于 Pawchive 的全新发布线。它与 v0 不兼容，且尚未经过充分的真实使用验证；在依赖大规模同步前，请先执行有范围限制的下载。升级已有安装时，请从[迁移至 v1](migration-v1.md)开始。

Kemono 已不可用，Pawchive 是唯一支持的后端。原始 Pawchive OpenAPI 文件保持不变，以便将生成客户端的变更与规范化契约对照审查。

## 支持与资源

离开文档站前，请先使用站内搜索和[常见问题](faq.md)。若仍未找到答案，可使用下列明确的项目外部链接：

- 通过 [Issue 跟踪器](https://github.com/Ljzd-PRO/KToolBox/issues)报告可复现缺陷；
- 在 [Discussions](https://github.com/Ljzd-PRO/KToolBox/discussions)中提出问题和建议；
- 从 [Releases](https://github.com/Ljzd-PRO/KToolBox/releases)查看发布说明和产物；
- 在[源代码仓库](https://github.com/Ljzd-PRO/KToolBox)查看代码和贡献历史。

## 质量与许可证

默认测试套件完全离线，并阻止意外网络访问。CI 会校验 OpenAPI 契约、确定性生成、测试、Ruff、Mypy、Python 字节码编译、包产物、WebUI 构建和严格 MkDocs 构建。

KToolBox 使用 [BSD 3-Clause License](https://opensource.org/license/bsd-3-clause)。Copyright © 2023 by Ljzd-PRO。
