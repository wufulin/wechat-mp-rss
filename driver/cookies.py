import time
import logging
logger = logging.getLogger(__name__)
def expire(cookies:any) :
    """从 cookies 中提取 slave_sid 的过期时间
    兼容两种来源：dict 形式（Playwright 导出的 cookie）和 requests CookieJar 的 Cookie 对象
    """
    if not isinstance(cookies, list) and not isinstance(cookies, dict):
        raise TypeError("cookies参数必须是列表或字典类型")
    # 字典形式统一为列表处理
    if isinstance(cookies, dict):
        cookies = [cookies]

    cookie_expiry=None
    for cookie in cookies:
        # 按对象类型分别取 name 和 expires：
        # requests 的 Cookie 对象直接读 .name/.expires 属性；dict 形式检查键是否存在
        if isinstance(cookie, dict):
            name = cookie.get('name')
            expires = cookie.get('expires') if 'expires' in cookie else None
        else:
            name = getattr(cookie, 'name', None)
            expires = getattr(cookie, 'expires', None)
        if name != 'slave_sid' or expires in (None, ''):
            continue
        try:
            expiry_time = float(expires)
            remaining_time = expiry_time - time.time()
            if remaining_time > 0:
                cookie_expiry = {
                    'expiry_timestamp': expiry_time,
                    'remaining_seconds': int(remaining_time),
                    'expiry_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiry_time))
                }
            break
        except (TypeError, ValueError):
            logger.warning(f"slave_sid 的过期时间戳无效: {expires}")
            break
    return cookie_expiry


