# GitHub Actions 工作流

## 工作流概览

| 文件 | 触发条件 | 职责 |
| --- | --- | --- |
| `pr-checks.yaml` | `main` push、PR、手动或 reusable call | 后端、前端、文档、Compose 与 amd64 镜像构建检查 |
| `release-deploy.yaml` | 推送 `vX.Y.Z` 标签 | 校验版本、发布 Docker Hub 镜像、部署 GCP、创建 GitHub Release |
| `docs-site-pages.yaml` | 文档相关变更 | 发布文档站 |
| `base_os.yaml` | 基础镜像文件变更 | 维护历史 Python 基础镜像 |
| `buidweb.yaml` | reusable call | 维护历史前端 Pages 构建 |
| `issues.yaml` | Issue 事件 | Issue 自动回复 |

Docker Hub 与 GHCR 的重复发布工作流已合并为 `release-deploy.yaml`。生产发布只由
版本标签触发，不再依赖容易漏掉源码变更的路径过滤。

## 发布约定

版本必须在以下位置保持一致：

- `core/ver.py`
- `pyproject.toml`
- `web_ui/package.json`
- `README.md` 版本徽章

本地检查：

```bash
python scripts/check-release-version.py
```

发布新版本：

```bash
git tag -a v1.1.7 -m "release: v1.1.7"
git push origin v1.1.7
```

工作流会发布以下 Docker Hub 标签：

- `franklin888/werss:1.1.7`：生产部署使用，不覆盖。
- `franklin888/werss:1.1`：最新兼容补丁版本。
- `franklin888/werss:1`：最新兼容小版本。
- `franklin888/werss:latest`：便捷别名，不用于生产部署。

同名版本镜像视为不可变。工作流失败时使用 GitHub Actions 的 **Re-run failed
jobs**，不要删除并重建同名 Git 标签。

## GitHub 配置

Repository Actions 配置：

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `DOCKERHUB_USERNAME` | Variable | Docker Hub 用户名 |
| `DOCKERHUB_TOKEN` | Secret | Docker Hub Read & Write access token |

`franklin888/werss` 必须是公开仓库，GCP 才能使用匿名只读拉取。发布工作流会在
部署前通过 Docker Registry V2 匿名拉取接口验证该版本与目标架构可用，不会把写
令牌复制到服务器。

`production` environment 配置：

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `GCP_HOST` | Variable | GCP 主机名或固定 IP |
| `GCP_PORT` | Variable | SSH 端口，通常为 `22` |
| `GCP_USER` | Variable | 专用部署用户 |
| `GCP_SSH_PRIVATE_KEY` | Secret | 专用部署私钥 |
| `GCP_KNOWN_HOSTS` | Secret | 经过可信连接确认的 SSH host key |

生产部署串行执行。`production` secrets 只对部署 job 可见；PR job 不读取 Docker
Hub 或 GCP 凭据。

## GCP 目录

部署用户必须能够使用 Docker，并拥有 `/opt/werss`：

```text
/opt/werss/
├── .env
├── .release.env
├── docker-compose.yml
├── deploy-production.sh
├── backups/
├── .rollback/
└── .incoming/
```

`.env` 由服务器管理员一次性创建，包含数据库、管理员账号、MinIO、域名等配置。
工作流只传输 Compose 定义与部署脚本，不复制或覆盖 `.env`。

部署脚本执行顺序：

1. 校验目标版本与 Compose。
2. 如果 PostgreSQL 正在运行，先生成 `pg_dump` 压缩备份。
3. 拉取精确版本镜像。
4. `docker compose up --no-build --wait`。
5. 检查 `/api/health` 和 `/api/v1/sys/version`。
6. 健康检查失败时恢复上一 Compose 定义与镜像版本。

数据库恢复不会自动执行，避免覆盖失败部署期间可能产生的新数据；备份保存在
`/opt/werss/backups`，需要时由管理员确认后恢复。
