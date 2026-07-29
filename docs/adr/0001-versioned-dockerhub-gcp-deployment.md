# ADR-0001：以语义化版本镜像部署 GCP

- 状态：已接受
- 日期：2026-07-30

## 背景

原有工作流分别向 Docker Hub 和 GHCR 构建镜像，触发路径没有覆盖多数应用源码，
生产 Compose 又在服务器本地执行构建。镜像产物、应用版本和服务器实际运行版本
缺少单一对应关系，也难以稳定回滚。

## 决策

1. 以 `vX.Y.Z` Git 标签作为正式发布入口，并校验源码中的所有版本声明。
2. 使用 GitHub Actions 构建 `linux/amd64`、`linux/arm64` 镜像，发布到
   `docker.io/franklin888/werss`。
3. 生产服务器部署精确 `X.Y.Z` 标签；`latest` 仅作为非生产便捷别名。
4. GitHub `production` environment 保存专用 SSH 凭据，部署用户仅维护
   `/opt/werss` 和对应 Docker Compose 项目。
5. 部署前备份 PostgreSQL，部署后检查健康端点与应用版本；失败时恢复上一镜像，
   但不自动恢复数据库。

## 结果

- 一个语义化版本对应一份不可变镜像和一个可审计的发布记录。
- GCP 不再依赖源代码、Node.js、Python 构建工具或 Docker build cache。
- 正式发布需要显式创建版本标签，普通 `main` push 不会直接修改生产。
- 多架构镜像构建时间高于单架构构建，但保留 ARM64 部署兼容性。
- 数据库迁移仍由应用启动逻辑负责；未来若引入破坏性迁移，需要扩展为独立迁移阶段。
