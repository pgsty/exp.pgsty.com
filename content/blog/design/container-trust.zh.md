---
title: "容器信任根与发布检查"
linkTitle: "容器信任根"
date: "2026-11-08T00:00:00+08:00"
lastmod: "2026-11-09T00:00:00+08:00"
authors: [Vonng]
categories: [design]
tags: [Design, Security, Compatibility]
summary: "v1.6.0：为两条 scratch 镜像路径补齐 CA 根证书与许可证，并在发布验证中检查 TLS 连接和 DEB 产物。"
---

> **状态：** 已随 v1.6.0 发布。<br>
> **决策日期／最后核验：** 2026-11-08／2026-11-09。<br>
> **范围：** 基于 v1.5.0 源码 `1891254` 的容器与发布验证改动，吸收 `68c95ba` 的打包修正。不修改 exporter 运行时代码或数据库驱动。<br>
> **交付：** v1.6.0 标签指向 `6bee809`；GitHub Release、带版本号的压缩包、RPM／DEB 和校验和已发布。源码 CI、制品验收与 amd64／arm64 容器 TLS 验证通过。软件发布不等于生产部署或生产负载验证。

## 问题 {#problem}

v1.5.0 的两条 Docker 构建路径都以 `scratch` 为最终镜像，未携带系统 CA 证书包。普通 Dockerfile 还漏了 `LICENSE`；GoReleaser Dockerfile 已包含该文件。OCI 许可证标签只能标识许可证，不能携带许可证正文。

当前 `lib/pq` 驱动在省略 `sslrootcert` 时使用 Go 的系统信任根。容器没有这些根证书，便无法在 `verify-ca` 或 `verify-full` 模式下验证由公共 CA 签发的服务器证书。[v1.5.0 目标状态设计记录](/zh/design/target-state-contracts/) 已如实说明此前需要挂载 CA。

## 决策与不变量 {#decision-and-invariants}

最终镜像继续使用 `scratch`。将发行版 CA 证书包复制到 Go 标准信任库路径 `/etc/ssl/certs/ca-certificates.crt`，并让两条构建路径都包含 `/LICENSE`。源码构建从 Go 构建阶段取得证书包；发布构建在独立 Alpine 阶段安装 `ca-certificates`，只将证书包复制进最终镜像。Docker 构建上下文的白名单须允许 `LICENSE`。

补入公共信任根不会自动启用 TLS。省略 `sslmode` 时仍设为 `disable`；验证证书链与主机名应使用 `sslmode=verify-full`。私有 CA 仍需挂载，并通过 `sslrootcert` 指定。发布镜像不得包含私钥或组织私有信任根。

根证书在镜像构建时固定，更新 CA 需要重新构建和分发镜像。运行时安装软件包、加入 Shell、迁移驱动、调整双向 TLS 和改变默认 TLS 模式，均不在本次范围内。

## 备选方案 {#alternatives}

要求每个部署都挂载公共根证书会保留打包缺口，并增加普通证书验证连接的配置负担。将最终镜像改为完整 Linux 发行版，又会为静态二进制引入不必要的运行时文件。复制 CA 证书包可以沿用现有镜像结构，同时补齐缺失的运行时数据。

## 验收与发布边界 {#acceptance-and-release-boundaries}

CI 实际构建普通 Dockerfile。发布测试构建真实的 GoReleaser snapshot，包括 amd64 与 arm64 镜像，但不发布。两条路径共用以下镜像检查：

- 将镜像内的许可证和默认配置与源码文件逐字比较，解析 CA 证书包，并运行二进制。
- 用 `verify-ca` 和 `verify-full` 连接临时 PostgreSQL TLS 实例：未知私有 CA 必须失败，显式指定可信 CA 必须成功。
- 通过临时挂载将测试 CA 追加到镜像证书包，不指定 `sslrootcert`，验证系统信任库查找路径；`verify-full` 必须拒绝主机名不匹配。

TLS 用例使用本地服务与临时生成的证书，不依赖公共 TLS 服务。它们验证证书包解析和信任库查找路径，不声称覆盖每个公共 CA 或完整的双向 TLS 组合。

发布产物检查保留 RPM 兼容性断言，补充 DEB 元数据、文件内容、配置权限、conffiles 和安装检查。检查所有 DEB 架构的内容，在容器原生架构上安装软件包，并以 `prometheus` 身份运行二进制。校验和必须验证成功。

这些检查只验收构建候选。v1.6.0 手册与发布正文描述本次修正，在正式公开版本与制品可用时一同上线。
