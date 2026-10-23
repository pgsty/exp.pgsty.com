---
title: "命令参考"
linkTitle: "命令参考"
description: "PG Exporter 命令行参数、环境变量、默认值与优先级"
weight: 105
icon: fa-solid fa-terminal
categories: [参考]
---

本页记录最新稳定版 PG Exporter **v{{< param version >}}** 的命令行选项。进程参数与
环境变量以本页为准；指标 YAML 与 SQL Schema 请查阅[采集器配置](/zh/config/)。

```bash
pg_exporter [flags]
pg_exporter --help       # 简要帮助
pg_exporter --help-long  # 完整帮助
pg_exporter --help-man   # man page 形式
```

布尔参数用 `--flag` 开启、`--no-flag` 关闭；`--flag=true` 与
`--flag=false` 形式也会在解析前被规范化。

## 目标与配置优先级

PG Exporter 按以下顺序选择连接 URL：

1. `--url` 或 `-u`
2. `PG_EXPORTER_URL`
3. `PGURL`
4. `PG_EXPORTER_URL_FILE` 指向文件中去除首尾空白后的内容
5. `postgresql:///?sslmode=disable`

高优先级 URL 会覆盖 URL 文件。选择 URL 文件时，该文件必须可读并包含非空的有效 URL。URL 语法、转义或查询参数名错误会阻止启动，诊断不会输出连接串。

显式数据库身份按 `lib/pq` 解析，包括 `dbname` 与 `database` 查询参数别名。自动发现会替换路径并清除这两个别名，再连接各发现数据库，同时保留凭据、TLS 选项与库名中的特殊字符。

URL 未指定 `sslmode` 时，PG Exporter 会补上 `sslmode=disable`。采集器配置独立解析：
先取 `--config`，再取 `PG_EXPORTER_CONFIG`，最后依次查找
`pg_exporter.yml`、`/etc/pg_exporter.yml` 与 `/etc/pg_exporter` 中第一个存在的路径。显式指定的路径加载失败时，程序会报错，不会回退到其他路径。

URL 中省略的字段可由驱动支持的环境变量补齐，例如 `PGHOST`、`PGPORT`、`PGUSER`、
`PGDATABASE` 与 `PGPASSFILE`。PG Exporter 会清除 `PGSERVICE` 和 `PGSERVICEFILE`，
避免服务文件覆盖连接目标。凭据文件的设置方法见[生产部署](/zh/deploy/)。

## 采集参数

| 参数 | 环境变量 | 默认值 | 用途 |
|:---|:---|:---|:---|
| `-u`, `--url=URL` | 见上方特殊优先级 | 本机 libpq URL | PostgreSQL 或 PgBouncer 目标 |
| `-c`, `--config=PATH` | `PG_EXPORTER_CONFIG` | 第一个存在的标准路径 | 采集器 YAML 文件或目录 |
| `-l`, `--label=KEY=VALUE,...` | `PG_EXPORTER_LABEL` | 空 | 固定 Prometheus 标签 |
| `-t`, `--tag=TAG,...` | `PG_EXPORTER_TAG` | 空 | 参与采集器规划的服务器标签 |
| `-C`, `--[no-]disable-cache` | `PG_EXPORTER_DISABLE_CACHE` | `false` | 绕过主查询结果缓存 |
| `-m`, `--[no-]disable-intro` | `PG_EXPORTER_DISABLE_INTRO` | `false` | 隐藏内置目标状态与 exporter 自监控指标 |
| `-a`, `--[no-]auto-discovery` | `PG_EXPORTER_AUTO_DISCOVERY` | `true` | 发现并抓取目标服务器上的数据库 |
| `-x`, `--exclude-database=LIST` | `PG_EXPORTER_EXCLUDE_DATABASE` | `template0,template1,postgres` | 自动发现时排除数据库 |
| `-i`, `--include-database=LIST` | `PG_EXPORTER_INCLUDE_DATABASE` | 空 | 自动发现时仅包含指定数据库 |
| `-n`, `--namespace=NAME` | `PG_EXPORTER_NAMESPACE` | 自动 | 覆盖内置 `pg` 或 `pgbouncer` 指标前缀 |
| `-f`, `--[no-]fail-fast` | `PG_EXPORTER_FAIL_FAST` | `false` | 首次目标探测失败时退出 |
| `-T`, `--connect-timeout=MS` | `PG_EXPORTER_CONNECT_TIMEOUT` | `100` | 目标预检查与健康探测超时，单位毫秒 |

`--include-database` 与 `--exclude-database` 只筛选自动发现的额外连接。`--url`
指定的数据库始终会被抓取。排除列表优先于包含列表。

`--namespace` 只修改 `pg_up` 等内置指标名称，不会修改 YAML 指标。
`--disable-intro` 也会隐藏 `pg_up`、`pg_version` 和 `pg_in_recovery`，
Go/进程指标与健康端点仍然可用。`--disable-cache` 绕过主查询结果缓存，
谓词查询仍使用各自配置的缓存。

将 `--connect-timeout` 设为高于目标正常往返耗时的值。零值或负值仍使用 100 ms。
采集器 SQL 使用独立的 YAML `timeout`。固定标签附加到指标序列上，Tag 用来选择采集器。

## HTTP 参数

| 参数 | 环境变量 | 默认值 | 用途 |
|:---|:---|:---|:---|
| `--web.listen-address=ADDR` | — | `:9630` | 监听地址；可重复指定多个地址 |
| `--[no-]web.systemd-socket` | — | `false` | 在 Linux 上使用 systemd 套接字激活 |
| `--web.config.file=PATH` | — | 空 | exporter-toolkit TLS 与认证配置 |
| `-P`, `--web.telemetry-path=PATH` | `PG_EXPORTER_TELEMETRY_PATH` | `/metrics` | Prometheus 指标暴露路径 |

指标路径必须以 `/` 开头，不能包含查询参数、片段、通配符、重复斜线或 `..` 路径段，且不能与 `/up`、`/primary`、`/replica`、`/reload`、
`/explain`、`/stat`、`/version` 等内置路由冲突。启动还会验证该路径实际进入指标处理器，而非重定向或其他处理器。转义路径必须兼容当前 HTTP mux；优先使用 `/metrics` 这样的普通路径。各端点的方法与响应语义参见
[HTTP API](/zh/api/)。

## 动作与日志

| 参数 | 默认值 | 用途 |
|:---|:---|:---|
| `-D`, `--[no-]dry-run` | `false` | 校验并打印采集器定义，无需连接目标 |
| `-E`, `--[no-]explain` | `false` | 连接目标，打印主连接已选采集器后退出 |
| `--log.level=LEVEL` | `info` | `debug`、`info`、`warn` 或 `error` |
| `--log.format=FORMAT` | `logfmt` | `logfmt` 或 `json` |
| `--version` | — | 打印版本、Go 版本、系统与架构 |
| `-h`, `--help` | — | 打印命令帮助 |

这些动作、日志与 exporter-toolkit Web 参数在稳定版中仅提供命令行形式，没有对应的
`PG_EXPORTER_*` 环境变量。用 `--explain --fail-fast` 要求目标预检查成功。
`--dry-run` 校验采集器定义；实际抓取还会检查权限、结果列和输出值。启动和重载时还会检查固定标签冲突。日志写入标准错误。

## 示例

```bash
# 同机 PostgreSQL，使用 libpq 默认连接参数
pg_exporter --config=/etc/pg_exporter.yml

# 远程目标，避免把密码放入命令行
export PG_EXPORTER_URL='postgres://monitor@db.example.com:5432/postgres?sslmode=verify-full'
pg_exporter --web.listen-address=:9630

# 不启动服务，只检查采集器定义
pg_exporter --config=./pg_exporter.yml --dry-run

# 除主目标外，只增加这两个自动发现数据库
pg_exporter --auto-discovery --include-database=app,analytics
```

systemd、容器、凭据与 Prometheus 接入请继续阅读[生产部署](/zh/deploy/)。
