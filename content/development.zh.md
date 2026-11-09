---
title: "开发指南"
linkTitle: "开发指南"
description: "构建与测试 pg_exporter、编写采集器、重建配置并理解发布流水线"
weight: 120
icon: fa-solid fa-code-branch
categories: [指南]
---

PG Exporter 将 SQL 和指标定义放在 YAML 中，由 Go 运行时加载定义、采集结果并提供 HTTP 服务。修改功能时，先确定行为由哪一层负责。

用户手册以稳定版 **v{{< param version >}}** 为准。独立的 `snort` 开发分支包含实验性的 Composite、Patroni、pgBackRest 和 PostgreSQL 日志功能，`main` 与 v1.6.0 不包含这些功能，其约定与状态见[设计归档](/zh/design/)。

## 仓库结构 {#repository-layout}

| 路径 | 用途 |
|:---|:---|
| `exporter/` | CLI 解析、URL/配置加载、规划、执行、指标、健康状态、HTTP Handler 与测试 |
| `config/` | 面向 PostgreSQL 10–19 与 PgBouncer 的 57 个采集器文件和 1 个配置参考文件 |
| `pg_exporter.yml` | 生成的默认单体配置（`make conf`） |
| `legacy/config/` | PostgreSQL 9.1-9.6 采集器定义 |
| `legacy/pg_exporter.yml` | 生成的 Legacy 单体配置（`make conf9`） |
| [设计归档](/zh/design/) | 权威设计理由、被否决方案、不变量与带日期的发布边界 |
| `monitor/` | Grafana 仪表盘与数据库初始化辅助脚本 |
| `package/` | systemd 环境/单元文件与软件包脚本 |
| `.goreleaser.yml` | 跨平台压缩包、RPM/DEB、校验和、Docker 镜像与 GitHub Release |
{.full-width}

## 工具链 {#toolchain}

v1.6.0 标签声明 Go **1.27.3**。按所构建版本的要求选择工具链。构建稳定标签：

```bash
git clone --branch v{{< param version >}} https://github.com/pgsty/pg_exporter.git
cd pg_exporter
go mod download
make build
./pg_exporter --version
```

`make build` 和 GoReleaser 都会注入版本、分支、提交和构建日期。发布产物关闭 CGO。分支构建可能保留默认发布版本号，因此识别二进制时需要同时检查提交号。

修改代码时，从选定的源版本建立工作分支。编辑前阅读 `AGENTS.md`，并检查 `git status --short --branch`。

## 改动前后运行测试 {#test-before-and-after-a-change}

```bash
go mod tidy -diff
go test -race -count=1 ./...
GODEBUG=httpmuxgo121=1 go test -count=1 ./...
go vet ./...
```

配置测试覆盖 PostgreSQL 与 PgBouncer 分支选择、旧版采集器、生成文件一致性、指标名、标签、谓词和快照直方图。运行时测试覆盖并发抓取、重载和 HTTP 处理器。SQL 兼容性还需要在每个受影响数据库版本上，以监控角色执行查询来验证。

修改运行时时，还应交叉构建六个发布目标：Linux amd64/arm64/ppc64le、Darwin amd64/arm64、Windows amd64。已有辅助命令：

```bash
make goreleaser-build
```

此命令会在需要时安装 GoReleaser，并重建 `dist/` 中的快照产物。二进制、软件包和发布压缩包不应加入 Git。

## 修改或新增采集器 {#change-or-add-a-collector}

1. 选择数字分组与唯一的顶层分支名。
2. 多个版本/角色分支需要输出同一指标族时，用 `name` 固定指标命名空间。
3. SQL 使用显式结果列清单。
4. 尽可能精确地添加 `min_version` / `max_version`、角色标签、事实标签与谓词。
5. 在 `metrics` 下准确声明每个返回列一次。
6. 根据运维开销与失败影响选择 `ttl`、`timeout`、`fatal`、`skip`。
7. 运行配置测试，重建合并文件并检查 Diff。
8. 以监控角色在每个相关服务器版本与角色上测试查询。
9. 公共指标变化时更新[内置采集器](/zh/collectors/)和相关手册，版本发布时再补充发布说明。

请阅读本次修改所基于版本中的 `config/0000-doc.yml`。当前[配置手册](/zh/config/)解释稳定版格式。

公共接口或架构决策写入伴生仓库的双语[设计归档](/zh/design/)，说明源代码版本、决策、备选方案和交付状态。标签和产物发布前，将新行为标为未发布。小型代码修复补充测试和相关手册即可，无需新建设计文章。

### 列规则 {#column-rules}

- `LABEL` 变为 Prometheus 标签，应避免无边界或敏感值。
- `GAUGE` 用于可双向变化的值。
- `COUNTER` 用于源端单调递增值（服务器重启/统计重置仍会归零）。
- `HISTOGRAM` 从 SQL 行构建快照分布；其 `_bucket`、`_count`、`_sum` 序列是可下降的 Gauge，不能应用 `rate()` 或 `increase()`。
- `DISCARD` 忽略结果列，不对外导出。
- `rename`、`default`、`scale` 会改变输出名称/值语义，需要兼容性审查。

采集器包含直方图时，`le` 是保留标签。指标名与标签名在加载配置时完成校验，非法名称会在抓取前失败。

## 重建配置 {#regenerate-configs}

```bash
make conf     # config/*.yml -> pg_exporter.yml
make conf9    # legacy/config/*.yml -> legacy/pg_exporter.yml

git diff -- pg_exporter.yml legacy/pg_exporter.yml
```

这两个生成的 YAML 文件已由 Git 跟踪。CI 会检查它们与有序源文件是否一致。修改配置片段后重新生成 YAML，并将两者一起纳入改动。

## 本地验证采集器 {#exercise-a-collector-locally}

```bash
# 只验证语法/Schema，不需要目标
./pg_exporter --config=./config --dry-run

# 生成目标特定计划并退出
PG_EXPORTER_URL='postgres://monitor@localhost/postgres' \
  ./pg_exporter --config=./config --explain --fail-fast

# 运行并查看规划、耗时与错误
PG_EXPORTER_URL='postgres://monitor@localhost/postgres' \
  ./pg_exporter --config=./config --log.level=debug
# 在另一个终端中执行
curl -fsS localhost:9630/metrics >/dev/null
curl -fsS localhost:9630/explain
curl -fsS localhost:9630/stat
```

`--explain` 只选择采集器，不执行 SQL。通过指标端点测试结果和权限，既测试有数据结果，也测试零行结果。缺少配置声明的 `LABEL` 或 `HISTOGRAM` 列时，无论是否有结果行，都会拒绝整个采集器结果。

缓存或可选组件还应测试禁用路径、故障隔离、重载和关闭。日志持久化状态还需覆盖重启、轮转、截断、半条记录和状态文件权限。

## 发布流水线 {#release-pipeline}

GoReleaser 会生成：

- Linux、macOS、Windows 压缩包；
- RPM 与 DEB 软件包；
- SHA256 `checksums.txt`；
- amd64/arm64 Docker 镜像与多架构 Manifest；
- 对应标签的 GitHub Release。

打标签前，对齐 `exporter.Version`、Makefile 版本、软件包元数据和发布文档。发布工作流完成后，核验压缩包和软件包校验和、容器清单、二进制构建提交。随后更新本站 `params.version`、下载校验和、落地页版本数据、手册及相关设计记录。

本地快照构建用于检查打包，不会发布版本。带标签产物通过发布工作流交付；部署后另行验证实际安装的版本。

## 文档工作流 {#documentation-workflow}

在伴生仓库 `exp.pgsty.com` 中编辑本站文档。同步修改中英文页面后运行：

```bash
make check
```

该命令执行严格告警构建，并检查 Markdown 和内部链接。还应查看两种语言的渲染结果，重点检查命令、表格和窄屏溢出。

导入脚本可从 Pigsty 手册更新 `install`、`deploy`、`config`、`api` 和发布历史。先生成到临时目录，避免覆盖本站已有编辑：

```bash
preview_dir=$(mktemp -d)
python3 bin/sync_pg_exporter_content.py \
  --pigsty-io ../pigsty.io \
  --pigsty-cc ../pigsty.cc \
  --output "$preview_dir"
```

对照 `content/` 检查导入结果，只应用相关变更。本站扩展指南和设计归档在本仓库直接维护。

PG Exporter 源码贡献使用 [Apache 2.0](https://github.com/pgsty/pg_exporter/blob/v1.6.0/LICENSE)，本站原创文档使用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。软件改动提交到 [pgsty/pg_exporter](https://github.com/pgsty/pg_exporter)，文档改动提交到 [pgsty/exp.pgsty.com](https://github.com/pgsty/exp.pgsty.com)。
