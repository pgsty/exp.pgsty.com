---
title: "把 pgBackRest 指标移出抓取路径"
linkTitle: "缓存 pgBackRest 指标"
date: "2026-08-23T19:34:09+08:00"
lastmod: "2026-08-28T00:00:00+08:00"
authors: [Vonng]
description: "为什么 PG Exporter 在有界后台 worker 中执行 pgBackRest，并提供不可变的 last-good 快照"
summary: "已实现但未发布。有界后台 worker 验证 pgBackRest 输出并原子发布 last-good 快照，使命令与仓库时延不进入 Prometheus 请求。"
categories: [design]
tags: [设计, pgBackRest, Prometheus, 可靠性]
---

> **决策状态：** 已在开发线实现；截至 2026-08-28，尚未进入 `main`、tag 或公开软件包。<br>
> **决策日期：** 2026-08-23。<br>
> **适用范围：** Composite Exporter 内可选的 `--pgbackrest` 缓存组件。<br>
> **发布边界：** 源码行为已经实现并测试；公开版本、软件包、部署和独立 exporter 退役尚未验证。

pgBackRest 通过 `pgbackrest info --output=json` 暴露丰富的备份状态，但它提供的是命令，不是低延迟 metrics endpoint。命令可能检查本地配置、访问远程仓库、等待存储、输出大量 JSON，或因为与 PostgreSQL SQL 指标无关的原因失败。

如果每次 Prometheus 请求都执行命令，主数据库抓取的可用性与延迟就会绑定到备份基础设施。最终设计因此把 pgBackRest 当作缓存组件：

```text
background worker
    -> pgbackrest version
    -> pgbackrest info --output=json
    -> 严格校验并构造指标
    -> 原子发布不可变快照

/metrics request
    -> 读取当前快照
    -> 在 PostgreSQL、Patroni、PgBouncer 之后合并
```

命令路径与抓取路径不会互相等待。

## 有界命令执行 {#bounded-execution}

Collector 直接执行配置的 binary，不经过 shell。生产默认值如下：

| 控制项 | 默认值 | 契约 |
| --- | ---: | --- |
| 命令 | `pgbackrest` | 以固定参数直接执行 |
| 刷新间隔 | 2 分钟 | 最小 10 秒 |
| 刷新超时 | 30 秒 | 覆盖一轮后台刷新 |
| 标准输出 | 16 MiB | 硬上限；溢出立即取消命令 |
| 标准错误 | 64 KiB | 有界诊断输出 |

Worker 先检测 pgBackRest 版本，优先使用数字输出；必要时回退到旧版文本形式。随后执行 `info --output=json`。版本与 JSON shape 一起校验，因为不同 pgBackRest 版本的可用字段和已知兼容情况并不相同。

这些上限是安全和可靠性契约。损坏仓库、意外命令或恶意 wrapper 都不能无限分配内存，也不能在溢出后留下长期运行的子进程。Runner 在取消后还设置了很短的 wait delay，避免进程清理无限阻塞。

## 发布前完成全部验证 {#validation}

命令退出成功并不代表刷新成功。JSON 还必须满足预期文档结构、对象数量上限、数值约束、stanza 与 repository 关系，以及 metric name 和 label 规则。最终 Prometheus family 在发布前完成 normalize。

只有完整合法的 candidate 才会替换当前快照。这样 Prometheus 请求可以走更便宜的合并路径：缓存 family 已经经过完整客户端校验，每次数据库抓取只需检查所有权和 header，不再重新验证整份备份数据。

Composite 所有权顺序仍然是：

```text
PostgreSQL > Patroni > PgBouncer > pgBackRest > PostgreSQL Log
```

与高优先级来源冲突的 pgBackRest family 会被省略，并把组件标为 down；它不能往既有 family 添加样本，也不能让 PostgreSQL gather 变成 fatal。

## Last-good 语义 {#last-good}

至少成功刷新一次后，后续命令、超时、解析或资源上限故障会保留上一份业务 family。组件报告 `up=0`，增加有限错误原因，并保留最后成功时间。

这并不是“假装备份来源健康”，而是有意分开两个事实：

- 最新刷新失败；
- 如果年龄可见，上一份合法备份状态仍有价值。

相对备份年龄 Gauge 在故障期间继续增长。Worker 保存上一份合法 JSON 与版本，并可在后台只重算与当前时间相关的值。`/metrics` 本身永远不重新解析 JSON，也不执行 pgBackRest。

第一次成功之前没有 last-good 业务快照。健康保持 down，端点仍会返回 PostgreSQL 和其他合法组件。

## 健康与重叠抓取 {#health}

缓存组件通过 `component="pgbackrest"` 进入统一健康面。除了 parse、gather 等原因，它还包含命令执行与资源上限错误。

重叠 Prometheus 请求不会排队等待完整 Composite scrape。它读取同一个原子 pgBackRest 快照，并在 family 不冲突时纳入结果。因此 overlap 期间仍可使用缓存数据，不会启动第二条命令，也不会由请求路径修改组件健康状态。

## 为什么不能每次抓取都执行 {#alternatives}

按需执行看似能提供更“新”的数据，却会产生多个不良契约：

- Prometheus timeout 变成备份命令 timeout；
- 并发抓取可能并发检查仓库；
- repository 延迟可能隐藏 PostgreSQL 指标；
- scrape storm 会放大本地与远程存储负载；
- 命令输出大小与进程清理变成 HTTP handler 职责。

独立 exporter 进程提供更强的进程隔离，但会保留额外端口、target、软件包和健康模型。Composite 模式提供迁移选择，并不声称所有环境必须立即退役独立进程。

通用命令 plugin framework 同样被拒绝。pgBackRest 的 JSON、版本兼容、安全、指标与 last-good 语义都具有领域特性。把它当任意 shell 输出会削弱验证，并让尚未稳定的 plugin API 进入产品表面。

## 运维结果 {#consequences}

启用组件意味着 PG Exporter service 获得执行 pgBackRest 和读取其配置的权限。官方 PG Exporter 软件包无需捆绑 pgBackRest binary；可执行文件与 repository credential 继续由主机备份安装负责。

运维人员必须对组件健康和最后成功年龄告警，不能只看备份指标仍然存在。替换独立 exporter 前，还必须用最终软件包和真实 service user 验证实际仓库。源码测试、tag、打包、Pigsty target 修改与生产等价性是独立验收门槛。

外层协调器与失败规则见[一个端点，多种来源](/zh/design/composite-exporter/)。
