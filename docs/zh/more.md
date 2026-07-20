# 项目信息

## 开发分支

Pawchive v1 在成为默认发布线之前，维护于 [`pawchive`](https://github.com/Ljzd-PRO/KToolBox/tree/pawchive) 分支。

变更按契约、客户端、项目迁移、测试、文档和发布元数据拆分为独立提交。原始 Pawchive OpenAPI 文件保持不变，以便根据规范化契约审查生成代码的变更。

## 质量策略

默认测试套件完全离线，并阻止意外网络访问。手写 API 层必须保持 100% 行和分支覆盖率，生成模型不计入统计，全项目覆盖率不得低于 85%。

CI 还会在支持的 Python 版本上校验 OpenAPI、确定性模型生成、Ruff、API 层严格 Mypy、Python 字节码编译、包构建和严格 MkDocs 构建。

## 许可证

KToolBox 使用 [BSD 3-Clause License](https://github.com/Ljzd-PRO/KToolBox/blob/master/LICENSE)。

Copyright © 2023 by Ljzd-PRO.
