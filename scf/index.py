import json, os, time, urllib.request

URL = "https://mindesk.cn/api/health"
WEBHOOK = os.environ.get("WECOM_WEBHOOK", "")
UA = "mindesk-monitor-scf/1.0"


def bj_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 8 * 3600))


def check():
    """访问健康检查，3 次重试。返回 (ok, code, err)。"""
    code, err = "000", ""
    for i in range(3):
        try:
            req = urllib.request.Request(URL, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=10) as r:
                code = str(r.status)
                body = r.read(4096).decode("utf-8", "ignore")
            if code == "200" and '"success":true' in body.replace(" ", ""):
                return True, code, ""
            err = "响应内容不含 success:true"
        except Exception as e:
            err = type(e).__name__ + ": " + str(e)[:120]
            code = "ERR"
        if i < 2:
            time.sleep(5)
    return False, code, err


def send(text):
    """推送企业微信，返回响应文本（便于调用方核验是否真的发出去了）。"""
    if not WEBHOOK:
        print("WEBHOOK 未配置，跳过推送")
        return "NO_WEBHOOK"
    data = json.dumps({"msgtype": "text", "text": {"content": text}},
                      ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(WEBHOOK, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read(200).decode("utf-8", "ignore")
            print("webhook ->", r.status, body)
            return body
    except Exception as e:
        msg = type(e).__name__ + ": " + str(e)[:120]
        print("webhook 失败:", msg)
        return "ERR " + msg


def main(event, context):
    force = isinstance(event, dict) and bool(event.get("force_fail"))
    ok, code, err = check()
    if force:
        ok, code, err = False, "FORCED", "手动测试"
    print("检查结果: ok=%s code=%s err=%s" % (ok, code, err))
    if ok:
        return {"ok": True, "code": code}
    msg = (
        "【紧急】mindesk.cn 外部访问不通\n"
        "时间: %s（北京时间）\n"
        "健康检查: %s → HTTP %s（3 次重试均失败）\n"
        "影响: 小程序 / 网页后台此刻应该都打不开\n"
        "说明: 这条是腾讯云函数的外部拨测（每 5 分钟一次）。服务器上那个巡检脚本也跑在同一台机器上，"
        "整机宕机时它不会告警，只有这条能发现。\n"
        "👉 请联系 WorkBuddy 处理，无需自行操作。"
    ) % (bj_time(), URL, code)
    resp = send(msg)
    return {"ok": False, "code": code, "webhook": resp}
