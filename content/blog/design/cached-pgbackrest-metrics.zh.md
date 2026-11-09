---
title: "把 pgBackRest 指标移出抓取路径"
linkTitle: "缓存 pgBackRest 指标"
date: "2026-08-23T19:34:09+08:00"
lastmod: "2026-10-13T00:00:00+08:00"
authors: [Vonng]
description: "在有界后台任务中执行 pgBackRest，并提供最后一份有效指标快照"
summary: "已实现，未发布。后台采集使命令和仓库延迟不进入 Prometheus 请求；刷新失败时保留最后一份有效备份状态。"
categories: [design]
tags: [设计, pgBackRest, Prometheus, 可靠性]
---

`pgbackrest info --output=json` 提供备份状态。命令可能访问远程仓库并等待存储响应。若在 Prometheus 请求中执行，数据库监控也要承担这段延迟。

> **状态：** 已实现，未发布。<br>
> **决策日期：** 2026-08-23。<br>
> **最后核验：** 2026-11-09。<br>
> **范围：** `snort` 开发分支提交 `c0ba58a` 的可选 `--pgbackrest` 组件；稳定版 `v1.6.0` 尚未包含。<br>
> **交付进度：** 本地测试通过；未合入 `main` 或发布标签；软件包、部署与生产运行未核验。

因此，PG Exporter 在后台执行 pgBackRest，验证结果后发布不可变快照。`/metrics` 读取最新快照，无需等待命令。

```text
后台任务
    -> 检测 pgBackRest 版本
    -> 执行 info --output=json
    -> 验证并构造指标
    -> 发布快照

/metrics 请求
    -> 读取快照
    -> 与其他来源合并
```

## 执行上限 {#bounded-execution}

后台任务直接执行配置的程序，不经过 shell。

| 控制项 | 默认值 | 规则 |
| --- | ---: | --- |
| 命令 | `pgbackrest` | 使用固定的版本与 info 参数 |
| 刷新间隔 | 2 分钟 | 最小 10 秒 |
| 刷新超时 | 30 秒 | 版本检测与 info 共用一个截止时间 |
| 标准输出 | 16 MiB | 超限取消命令 |
| 标准错误 | 64 KiB | 超限取消命令 |

后台先执行 `version --output=num`，旧版本回退到 `version`，随后执行 `info --output=json`。取消操作终止直接子进程；一秒的等待上限约束输出管道清理时间。

## 发布前验证 {#validation}

命令正常退出后，还要检查 JSON 结构、数值字段，以及 stanza 和仓库引用关系。输入最多包含 256 个 stanza 和 4,096 个备份；输出最多包含 20,000 个样本，Prometheus 文本不超过 4 MiB。

只有完整合法的结果才能替换快照。指标族在发布前完成验证，抓取路径只需检查元数据和所有权。

按 [Composite 所有权顺序](/zh/design/composite-exporter/#family-ownership)，pgBackRest 排在 PostgreSQL、进程自监控、Patroni 和 PgBouncer 之后。冲突指标族会被省略，组件标记为不可用；其他合法指标族仍可保留。

## 保留最后一次成功结果 {#last-good}

首次成功刷新后，命令、超时、解析或资源上限错误会保留上一份业务指标。组件报告 `up=0`，增加错误计数，并保留最后成功时间。

刷新失败时，后台仍会根据保留的 JSON 重算备份年龄，使其按刷新间隔反映经过的时间。`/metrics` 不解析 JSON，也不执行 pgBackRest。

首次成功前没有备份业务指标。PostgreSQL 与其他有效来源继续工作。

## 健康与并发请求 {#health}

组件健康使用 `component="pgbackrest"`。`up` 表示最近一次采集结果，最后成功时间说明备份数据有多旧。命令失败使用 `exec`；标准输出超限使用 `limit`；解析和合并错误使用各自原因。标准错误超限归类为执行错误。

重叠抓取可以读取同一份快照，不会启动第二条命令，也不会更新已保存的组件健康历史。指标冲突仍按 Composite 所有权规则处理。

## 备选方案与非目标 {#alternatives}

每次抓取都执行命令，会把 Prometheus 超时和并发请求绑定到仓库操作。后台任务使执行超时和刷新间隔独立于抓取。

独立 Exporter 提供进程隔离，但增加一个服务、端口、软件包和目标。集成组件提供另一种部署选择，不自动迁移现有部署。

通用 shell 命令插件不适合此处。pgBackRest 需要专用 JSON 校验、版本处理、指标定义与恢复规则。本组件接受 pgBackRest 可执行程序，不接受任意命令模板。

## 核验与运维 {#consequences}

`exporter/pgbackrest.go` 负责命令执行与快照发布，`exporter/pgbackrest_metrics.go` 负责 JSON 校验与指标构造。测试覆盖版本回退、畸形与过量输出、超时、保留最后成功结果、指标族冲突和关闭。

服务用户需要执行 pgBackRest、读取其配置和仓库凭据的权限。PG Exporter 软件包不捆绑 pgBackRest，使用主机上的备份软件安装。

对组件健康和最后成功时间设置告警。采集失败后，旧备份指标仍可能可见。替换独立 Exporter 前，使用预定服务用户，对同一个仓库比较两者的输出。
