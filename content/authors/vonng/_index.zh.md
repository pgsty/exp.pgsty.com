---
title: 冯若航
linkTitle: Vonng
description: PG Exporter 与 Pigsty 的作者；PostgreSQL 基础设施、监控，以及夹在两者中间的那些工具。
---

冯若航（[@Vonng](https://github.com/Vonng)）编写 **PG Exporter**，以及它最初服务的
PostgreSQL 发行版 [Pigsty](https://pigsty.cc/)。

PG Exporter 起于一个很实际的抱怨：对数据库工程师真正重要的那些指标定义，被锁在导出器的
二进制里——懂数据库的人既读不到，也改不了。把它们挪进 YAML 与 SQL，指标契约就变成了可以
评审的东西；版本、角色与扩展之间的差异，也从「发布说明里的一句致歉」变成了导出器在运行时
自己做出的判断。

- [pigsty.cc](https://pigsty.cc/) — 这个导出器随之交付的 PostgreSQL 发行版
- [GitHub 上的 @Vonng](https://github.com/Vonng) — 这些项目背后的仓库
- [vonng.com](https://vonng.com/) — 长文
