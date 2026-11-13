# mindesk-monitor

MinDesk 的**外部**可用性拨测。每 5 分钟从 GitHub 访问一次 `https://mindesk.cn/api/health`，
连续 3 次失败就发企业微信群告警，恢复后发恢复通知（30 分钟内不重复告警）。

存在的理由：服务器上那个 `backup-watchdog.sh` 自己也跑在同一台机器上，
整机宕机时它跟着一起消失，必须有外部检测点。选 GitHub Actions 是因为免费、
不限次数；腾讯云轻量服务器的监控只有 CPU/内存/带宽这类指标，没有「实例失联」。

- 告警通道：仓库 Secrets 里的 `WECOM_WEBHOOK`（企业微信群机器人地址），代码里没有密钥。
- 手动测试：Actions → 外部可用性拨测 → Run workflow → 勾上 `force_fail`。
- 保活：每周自动提交一次 `.heartbeat`，防止 GitHub 因 60 天无活动停掉定时任务。

## 腾讯云 SCF 版本（现网）

`scf/index.py` 是同一拨测的腾讯云函数版本，现网由 SCF 每 5 分钟触发一次（定时触发器），
2026-11-13 复核当天全部返回 200。

- 入口：`main(event, context)`；`event.force_fail=true` 可手动制造失败验证告警。
- 环境变量：`WECOM_WEBHOOK`（企业微信机器人地址，只配在函数配置里，不入仓）。
- 行为：请求 `https://mindesk.cn/api/health`，最多 3 次、每次超时 10 秒；只有 HTTP 200 且响应含 `"success":true` 才算健康；失败推送企业微信并带上北京时间。
- 部署：在 SCF 控制台新建 Python 函数，上传 `scf/index.py`，配置定时触发器 `*/5 * * * *` 与 `WECOM_WEBHOOK` 环境变量。
- 与 GitHub Actions 的关系：两者可并存，互为补充；腾讯云 SCF 是 2026-11-13 核对时确认在用的外部检测点。
