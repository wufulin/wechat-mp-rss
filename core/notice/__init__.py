from .wechat import send_wechat_message
from .dingtalk import send_dingtalk_message
from .feishu import send_feishu_message
from .custom import send_custom_message
from core.log import logger

def notice( webhook_url, title, text,notice_type: str=None):
    """
    公用通知方法，根据类型判断调用哪种通知
    
    参数:
    - notice_type: 通知类型，'wechat' 或 'dingtalk'
    - webhook_url: 对应机器人的Webhook地址
    - title: 消息标题
    - text: 消息内容
    """
    if  len(str(webhook_url)) == 0:
        logger.warning('未提供webhook_url')
        return False
    
    # 打印调试信息
    logger.info(f'【通知发送】webhook_url: {webhook_url[:50]}...')
    logger.info(f'【通知发送】title: {title}')
    logger.info(f'【通知发送】text长度: {len(text) if text else 0} 字符')
    
    if 'qyapi.weixin.qq.com' in webhook_url:
        notice_type = 'wechat'
    elif 'oapi.dingtalk.com' in webhook_url:
        notice_type = 'dingtalk'
    # 检测飞书 Webhook URL（标准格式：open.feishu.cn 或企业本地化部署：open.feishu.xxxx.com）
    elif 'open.feishu.' in webhook_url or 'feishu.cn' in webhook_url:  
        notice_type = 'feishu'
        logger.info('【通知发送】检测到飞书 Webhook URL')
    else:
        notice_type = 'custom'
        logger.info(f'【通知发送】未识别的 Webhook URL，使用 custom 类型')
    
    logger.info(f'【通知发送】通知类型: {notice_type}')
    
    try:
        if notice_type == 'wechat':
            result = send_wechat_message(webhook_url, title, text)
        elif notice_type == 'dingtalk':
            result = send_dingtalk_message(webhook_url, title, text)
        elif notice_type == 'feishu':
            result = send_feishu_message(webhook_url, title, text)
            logger.info(f'【通知发送】飞书消息发送结果: {result}')
        elif notice_type == 'custom':
            result = send_custom_message(webhook_url, title, text)
        else:
            logger.warning('不支持的通知类型')
            return False
        
        if result:
            logger.info(f'【通知发送】{notice_type} 消息发送成功')
        else:
            logger.warning(f'【通知发送】{notice_type} 消息发送失败')
        
        return result
    except Exception as e:
        logger.exception(f'【通知发送】发送消息时出错: {e}')
        return False