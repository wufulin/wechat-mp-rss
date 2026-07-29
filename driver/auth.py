import threading
from driver.base import WX_InterFace
import os
from core.task import TaskScheduler
from driver.success import Success
from core.config import cfg
from core.print import print_info

def auth_cron_enabled() -> bool:
    """免扫码自动续期开关：环境变量 WERSS_AUTH_CRON 优先，其次 config.yaml 的 server.auth_cron，缺省默认 True"""
    env = os.getenv("WERSS_AUTH_CRON")
    if env is not None and str(env).strip() != "":
        return str(env).strip().lower() in ("1", "true", "yes", "on")
    return bool(cfg.get("server.auth_cron", True))

def auth():
    def run_auth():
        try:
            wx=WX_InterFace()
            # wx.Token(callback=Success)
            wx.switch_account()
        except Exception as e:
            # 定时续期失败只记日志，不影响其他任务（失效交由 failauth 兜底链路）
            print_info(f"免扫码自动续期执行失败: {e}")
    
    thread = threading.Thread(target=run_auth)
    thread.start()
    thread.join()  # 可选：等待完成
# 配置关闭时完全不启动调度；缺省默认开启（每小时用已保存凭证免扫码续期）
if auth_cron_enabled():
    auth_task=TaskScheduler()
    if os.getenv('DEBUG',False):
        auth_task.add_cron_job(auth, "*/1 * * * *",tag="授权定时更新")
    else:
        auth_task.add_cron_job(auth, "0 */1 * * *",tag="授权定时更新")
    auth_task.start()
    print_info("免扫码自动续期定时任务已启动（server.auth_cron）")