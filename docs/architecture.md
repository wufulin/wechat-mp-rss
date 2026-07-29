# WeRSS 架构与运行边界

业务模块的详细分层见
[开发架构概览](./dev/architecture-overview.md)。本文记录影响运行、发布和外部系统的
稳定边界。

## 运行结构

```text
浏览器
  -> Traefik :80/:443
  -> WeRSS (FastAPI + React 静态资源) :8001
       -> PostgreSQL
       -> MinIO
       -> 微信、AI API、Webhook 等外部服务
```

完整栈由 `docker-compose.yml` 定义；GCP 生产 `.env` 将 `DB` 指向栈内 PostgreSQL，
本地示例仍可使用 SQLite。已有外部数据库、对象存储或反向代理时使用
`docker-compose.app-only.yml`。持久化数据位于宿主机挂载目录，不写入应用镜像。

## 配置边界

- 应用运行配置由服务器 `.env`、镜像内 `config.yaml` 和数据库配置覆盖层共同决定。
- 生产发布版本单独保存在 `.release.env`，只有 `WERSS_IMAGE_TAG=X.Y.Z`。
- GitHub Actions 不传输生产 `.env`，也不持有数据库和应用管理员密码。
- Docker Hub 写令牌只用于镜像发布；GCP 只拉取公开镜像。

配置优先级和运行时覆盖规则见
[配置与优先级](./dev/configuration-and-precedence.md)。

## 发布数据流

```text
vX.Y.Z Git 标签
  -> 版本一致性校验
  -> 后端 / 前端 / 文档质量检查
  -> Docker Buildx 多架构构建
  -> docker.io/franklin888/werss:X.Y.Z
  -> GitHub production environment
  -> SSH /opt/werss
  -> PostgreSQL 备份
  -> Compose 拉取、启动、健康与版本检查
```

生产 Compose 使用语义化版本号，不使用 Git SHA 或 `latest`。镜像 digest 保留在
GitHub Actions 发布记录中，用于审计构建产物，但不作为服务器配置接口。

## 故障与回滚边界

- 容器启动或版本检查失败时，部署脚本自动恢复上一镜像版本。
- 应用启动会执行数据库结构同步，因此每次替换应用容器前生成 PostgreSQL 备份。
- 数据库不会自动回滚；恢复备份是可能覆盖数据的独立运维操作，必须人工确认。
- 生产部署通过 GitHub concurrency 串行化，避免两个版本同时修改同一 Compose 栈。

这一决策的背景与取舍记录在
[ADR-0001](./adr/0001-versioned-dockerhub-gcp-deployment.md)。
