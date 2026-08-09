---
title: "项目简介"
linkTitle: "项目简介"
description: "pg_exporter 做什么、一次抓取如何完成动态规划，以及它的运维边界"
weight: 10
icon: fas fa-lightbulb
categories: [概念]
---

`pg_exporter` 将 PostgreSQL 与 pgBouncer 的运行状态转换为 Prometheus 指标。与把所有查询固化在代码里的 exporter 不同，它的大部分指标面由 YAML 声明：一个采集器定义 SQL、结果列、标签、指标类型、准入条件、超时与缓存策略。

这种设计同时带来两点好处：

- 发布版本自带覆盖广泛、经过测试的默认指标集；
- 本地团队无需重建二进制，就能新增、删除或特化指标。

## 数据路径

一次常规抓取会经过六个阶段：

1. **选择目标**：PostgreSQL URL 来自 `--url`、环境变量、密钥文件或本地优先默认值。
2. **发现事实**：exporter 获取服务器版本、恢复角色、数据库清单、扩展、Schema 与运维人员提供的标签。
3. **动态规划**：对每个指标命名空间，选择版本范围、角色标签、自定义标签与谓词都匹配目标的采集器分支。
4. **执行查询**：按每个采集器的超时与可选结果缓存策略执行 SQL。
5. **转换指标**：将结果列转换为 Label、Gauge、Counter 或快照直方图指标族。
6. **暴露结果**：通过可配置的 Prometheus 端点（默认 `/metrics`）返回内置指标与查询驱动指标。

健康检查与角色路由端点读取后台探测缓存，不会为每个 HTTP 请求重新查询数据库。因此，健康检查风暴不会转化为数据库连接风暴。

## 两层指标

### 内置 exporter 指标

Go 二进制始终能够暴露核心可用性与自监控指标，例如：

- `pg_up`、`pg_version` 与 `pg_in_recovery`；
- `pg_exporter_build_info` 与 exporter 运行时间；
- 抓取次数、失败、耗时、缓存 TTL 与逐查询统计。

只有在明确希望隐藏 exporter 自监控指标时才使用 `--disable-intro`；它不会删除 YAML 定义的业务指标。

### 声明式采集器指标

其余指标都来自 [`pg_exporter.yml`](https://github.com/pgsty/pg_exporter/blob/main/pg_exporter.yml)。该文件由 [`config/`](https://github.com/pgsty/pg_exporter/tree/main/config) 下 58 个有序定义文件生成，默认覆盖复制、WAL、检查点、活动、锁、事务、数据库/对象统计、进度视图、pgBouncer 与部分扩展。

完整清单参见[内置采集器](/zh/collectors/)，配置模型参见[采集器配置](/zh/config/)。

## 失败语义

失败行为同时受采集器级与进程级策略控制：

- `fatal: true` 的采集器失败可以使整次抓取失败，并将目标的 `*_up` 指标重置为 0。
- 非致命采集器失败只增加错误统计，其他采集器继续执行。
- 未配置时查询超时默认为 100 ms；显式配置为负值可以关闭查询超时。
- 默认采用非阻塞启动：即使数据库暂时不可达，HTTP 端点仍会启动；`--fail-fast` 会改为启动立即失败。
- 合法热重载会原子替换活动查询集；被拒绝的重载不会破坏当前运行配置。

`/explain` 回答“这个采集器为什么被选择或跳过”，`/stat` 回答“已选择的采集器表现如何”。遇到指标缺失、缓慢或报错时，应优先查看这两个端点。

## pg_exporter 不是什么

- 它不是 PostgreSQL 代理，不承载应用流量。
- 它不保存时序数据；存储由 Prometheus、VictoriaMetrics 或其他兼容系统完成。
- 它不会安装可选采集器所需的扩展。
- SQL 写进 YAML 并不会自动变得安全；查询审查、权限、TTL、超时与基数仍由运维人员负责。
- 角色端点报告观测到的 PostgreSQL 状态，而不是分布式共识结论。它们可作为路由输入，但 HA 策略仍属于 Patroni、负载均衡器与运维人员。

## 项目状态

最新稳定版本为 **v{{< param version >}}**。默认采集器包覆盖 PostgreSQL 10 至 PostgreSQL 19 分支，独立 legacy 配置包覆盖 PostgreSQL 9.1-9.6；pgBouncer 采集器覆盖支持 `SHOW` 命令的 1.8+ 至当前 1.25+ Schema。

接下来可以通过[快速上手](/zh/start/)完成最小部署，或直接阅读[生产部署](/zh/deploy/)了解完整运维面。
