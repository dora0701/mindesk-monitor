# mindesk-monitor

MinDesk 的**外部**可用性拨测。每 5 分钟从 GitHub 访问一次 `https://mindesk.cn/api/health`，
连续 3 次失败就发企业微信群告警，恢复后发恢复通知（30 分钟内不重复告警）。

存在的理由：服务器上那个 `backup-watchdog.sh` 自己也跑在同一台机器上，
整机宕机时它跟着一起消失，必须有外部检测点。选 GitHub Actions 是因为免费、
不限次数；腾讯云轻量服务器的监控只有 CPU/内存/带宽这类指标，没有「实例失联」。

- 告警通道：仓库 Secrets 里的 `WECOM_WEBHOOK`（企业微信群机器人地址），代码里没有密钥。
- 手动测试：Actions → 外部可用性拨测 → Run workflow → 勾上 `force_fail`。
- 保活：每周自动提交一次 `.heartbeat`，防止 GitHub 因 60 天无活动停掉定时任务。
