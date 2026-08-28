---
title: "开发指南"
linkTitle: "开发指南"
description: "构建与测试 pg_exporter、编写采集器、重建配置并理解发布流水线"
weight: 120
icon: fa-solid fa-code-branch
categories: [指南]
---

项目刻意把大部分监控逻辑放在 YAML 中，只用较小的 Go 引擎负责执行。因此改动分为两条路径：采集器改动与 exporter 运行时改动。无论哪一类，都要让合并配置、测试、文档与发布元数据保持一致。

## 仓库结构

| 路径 | 用途 |
|:---|:---|
| `exporter/` | CLI 解析、URL/配置加载、规划、执行、指标、健康状态、HTTP Handler 与测试 |
| `config/` | 面向 PostgreSQL 10-19+ 与 PgBouncer 的 58 个有序采集器定义文件 |
| `pg_exporter.yml` | 生成的默认单体配置（`make conf`） |
| `legacy/config/` | PostgreSQL 9.1-9.6 采集器定义 |
| `legacy/pg_exporter.yml` | 生成的 Legacy 单体配置（`make conf9`） |
| `docs/design/` | 快照直方图语义等权威设计说明 |
| `monitor/` | Grafana 仪表盘与数据库初始化辅助脚本 |
| `package/` | systemd 环境/单元文件与软件包脚本 |
| `.goreleaser.yml` | 跨平台压缩包、RPM/DEB、校验和、Docker 镜像与 GitHub Release |
{.full-width}

## 工具链

当前 `go.mod` 声明 Go **1.27.0**。常规开发构建：

```bash
git clone https://github.com/pgsty/pg_exporter.git
cd pg_exporter
go mod download
make build
./pg_exporter --version
```

正式产物关闭 CGO。`make build` 适合本地开发；官方产物由 GoReleaser 注入版本、分支、提交与构建日期元数据。

## 改动前后运行测试

```bash
go test ./...
go test -race ./...

# 确认 PostgreSQL / PgBouncer 各版本分支仍有覆盖，
# 并验证配置结构、指标名、Label 与直方图。
go test ./exporter/...
```

测试套件覆盖 PostgreSQL 19 配置、PostgreSQL 9 Legacy 配置、并发/重载、HTTP 路由校验、Label/指标名、谓词缓存与快照直方图验收。

修改运行时时，还应交叉构建支持的发布目标，或运行：

```bash
make goreleaser-build
```

## 修改或新增采集器

1. 选择数字分组与唯一的顶层分支名。
2. 多个版本/角色分支需要输出同一指标族时，用 `name` 固定指标命名空间。
3. SQL 使用显式结果列清单。
4. 尽可能精确地添加 `min_version` / `max_version`、角色标签、事实标签与谓词。
5. 在 `metrics` 下准确声明每个返回列一次。
6. 根据运维开销与失败影响选择 `ttl`、`timeout`、`fatal`、`skip`。
7. 运行配置测试，重建合并文件并检查 Diff。
8. 以监控角色在每个相关服务器版本与角色上测试查询。
9. 公共指标面变化时更新[内置采集器](/zh/collectors/)与发布注记。

可执行 Schema 参考为 [`config/0000-doc.yml`](https://github.com/pgsty/pg_exporter/blob/main/config/0000-doc.yml)。

### 列规则

- `LABEL` 变为 Prometheus 标签，应避免无边界或敏感值。
- `GAUGE` 用于可双向变化的值。
- `COUNTER` 用于源端单调递增值（服务器重启/统计重置仍会归零）。
- `HISTOGRAM` 从 SQL 行构建快照分布；其 `_bucket`、`_count`、`_sum` 序列是可下降的 Gauge，不能应用 `rate()` 或 `increase()`。
- `DISCARD` 校验并忽略结果列，不对外导出。
- `rename`、`default`、`scale` 会改变输出名称/值语义，需要兼容性审查。

采集器包含直方图时，`le` 是保留标签。指标名与标签名在加载配置时完成校验，非法名称会在抓取前失败。

## 重建配置

```bash
make conf     # config/*.yml -> pg_exporter.yml
make conf9    # legacy/config/*.yml -> legacy/pg_exporter.yml

git diff -- pg_exporter.yml legacy/pg_exporter.yml
```

生成文件是需要提交的产物。CI 会检查它们与有序源文件完全一致；不要只修改单体输出。

## 本地验证采集器

```bash
# 只验证语法/Schema，不需要目标
./pg_exporter --config=./config --dry-run

# 生成目标特定计划并退出
PG_EXPORTER_URL='postgres://monitor@localhost/postgres' \
  ./pg_exporter --config=./config --explain

# 运行并查看规划、耗时与错误
PG_EXPORTER_URL='postgres://monitor@localhost/postgres' \
  ./pg_exporter --config=./config --log.level=debug
curl localhost:9630/explain
curl localhost:9630/stat
```

既要测试有数据结果，也要测试零行结果。自 v1.4.1 起，缺失配置声明的 `LABEL` 列会原子拒绝整个采集器结果，即使查询恰好返回零行也一样。

## 发布流水线

GoReleaser 会生成：

- Linux、macOS、Windows 压缩包；
- RPM 与 DEB 软件包；
- SHA256 `checksums.txt`；
- amd64/arm64 Docker 镜像与多架构 Manifest；
- 对应标签的 GitHub Release。

发布版本注入 `exporter.Version`。打标签前要同步 fallback 版本、Makefile 版本、README 徽标、软件包元数据与文档参数。标签、Release 对象、校验和、软件包内容、容器 Manifest 与实际安装行为是不同验证层，必须分别核验。

## 文档工作流

独立文档仓库可以导入 Pigsty 权威模块页面，并拆分汇总发布历史：

```bash
python3 bin/sync_pg_exporter_content.py \
  --pigsty-io /path/to/pigsty.io \
  --pigsty-cc /path/to/pigsty.cc \
  --output ./content
```

生成的核心页面再由独立站专有的兼容性、安全、采集器、排障与本文等指南补充。发布前运行严格告警构建与链接检查。

贡献使用 [Apache 2.0](https://github.com/pgsty/pg_exporter/blob/main/LICENSE) 许可证。改动与 Issue 请提交到 [pgsty/pg_exporter](https://github.com/pgsty/pg_exporter)。
