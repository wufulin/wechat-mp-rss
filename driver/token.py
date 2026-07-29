__package__ = "driver"
from core.config import Config,cfg
# 确保data目录和wx.lic文件存在
import os

import logging
logger = logging.getLogger(__name__)
lic_path="./data/wx.lic"
os.makedirs(os.path.dirname(lic_path), exist_ok=True)
if not os.path.exists(lic_path):
    with open(lic_path, "w") as f:
        f.write("{}")
wx_cfg = Config(lic_path)

def set_token(data:any,ext_data:any=None):

    """
    设置微信登录的Token和Cookie信息
    :param data: 包含Token和Cookie信息的字典
    """
    if data.get("token", "") == "":
        return
    wx_cfg.set("token", data.get("token", ""))
    wx_cfg.set("cookie", data.get("cookies_str", ""))
    wx_cfg.set("fingerprint", data.get("fingerprint", ""))
    wx_cfg.set("expiry", data.get("expiry", {}))
    logger.info(f"Token 已更新 ({str(data.get('token'))[:8]}...)，到期时间: {data.get('expiry')['expiry_time']}")
    if ext_data is not None:
        wx_cfg.set("ext_data", ext_data)
    wx_cfg.save_config()
    wx_cfg.reload()
    from jobs.notice import sys_notice
    
#     sys_notice(f"""WeRss授权成功
# - Token: {data.get("token")}
# - Expiry: {data.get("expiry")['expiry_time']}
# """, str(cfg.get("server.code_title","WeRss授权成功")))


def get(key:str,default:str="")->str:
    return str(wx_cfg.get(key, default))