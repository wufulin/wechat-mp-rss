import requests
import json
from core.log import logger

def send_feishu_message(webhook_url, title, text):
    """
    发送飞书消息（支持多种格式，自动降级）
    
    参数:
    - webhook_url: 飞书机器人 Webhook 地址
    - title: 消息标题
    - text: 消息内容（支持 Markdown 格式）
    """
    logger.info(f'【飞书消息】开始发送消息，webhook_url: {webhook_url[:50]}...')
    logger.info(f'【飞书消息】title: {title}')
    logger.info(f'【飞书消息】text长度: {len(text) if text else 0} 字符')
    
    # 首先尝试使用富文本 post 格式（支持 Markdown 渲染）
    logger.info('【飞书消息】尝试发送 post 格式消息...')
    success = send_feishu_post_message(webhook_url, title, text)
    if success:
        logger.info('【飞书消息】post 格式消息发送成功')
        return True
    
    # 如果失败，降级使用文本格式
    logger.info('【飞书消息】post 格式失败，降级使用 text 格式...')
    result = send_feishu_text_message(webhook_url, title, text)
    if result:
        logger.info('【飞书消息】text 格式消息发送成功')
    else:
        logger.warning('【飞书消息】text 格式消息也发送失败')
    return result


def send_feishu_post_message(webhook_url, title, text):
    """
    发送飞书富文本 post 格式消息（支持 Markdown 渲染）
    
    参数:
    - webhook_url: 飞书机器人 Webhook 地址
    - title: 消息标题
    - text: 消息内容（Markdown 格式）
    
    根据飞书官方文档格式：
    {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "标题",
                    "content": [
                        [{"tag": "text", "text": "文本"}, {"tag": "a", "text": "链接", "href": "url"}]
                    ]
                }
            }
        }
    }
    """
    headers = {'Content-Type': 'application/json'}
    import re
    
    # 将文本内容按行分割，每行作为一个段落（content 数组中的一个元素）
    lines = text.split('\n')
    content_blocks = []
    prev_was_title = False  # 跟踪上一行是否是标题
    
    for i, line in enumerate(lines):
        original_line = line
        line = line.strip()
        
        # 处理分隔线 ---
        if line.startswith('---') or line == '---':
            # 添加分隔线（使用空行和特殊字符，让分隔更明显）
            if content_blocks:
                content_blocks.append([{"tag": "text", "text": ""}])
                # 使用多个元素组合，让分隔线更美观
                content_blocks.append([
                    {"tag": "text", "text": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"}
                ])
                content_blocks.append([{"tag": "text", "text": ""}])
            continue
        
        # 跳过空行（但保留标题后的空行效果）
        if not line:
            if prev_was_title:
                # 标题后的空行，添加一个空段落
                content_blocks.append([{"tag": "text", "text": ""}])
                prev_was_title = False
            continue
        
        # 处理三级标题 ###
        if line.startswith('###'):
            title_text = line.replace('###', '').strip()
            title_text = title_text.replace('**', '')
            if content_blocks:  # 如果已有内容，先添加空行
                content_blocks.append([{"tag": "text", "text": ""}])
            # 使用特殊符号美化标题，将图标和文本分开为不同元素
            content_blocks.append([
                {"tag": "text", "text": "📌 "},
                {"tag": "text", "text": title_text}
            ])
            prev_was_title = True
        # 处理二级标题 ##（公众号名称）
        elif line.startswith('##') and not line.startswith('###'):
            title_text = line.replace('##', '').strip()
            title_text = title_text.replace('**', '')
            if content_blocks:  # 如果已有内容，先添加空行
                content_blocks.append([{"tag": "text", "text": ""}])
            # 使用特殊符号美化公众号标题，将图标和文本分开为不同元素
            content_blocks.append([
                {"tag": "text", "text": "✅ "},
                {"tag": "text", "text": title_text}
            ])
            prev_was_title = True
        # 处理一级标题 #
        elif line.startswith('#') and not line.startswith('##'):
            title_text = line.replace('#', '').strip()
            title_text = title_text.replace('**', '')
            if content_blocks:  # 如果已有内容，先添加空行
                content_blocks.append([{"tag": "text", "text": ""}])
            # 使用特殊符号美化主标题，将图标和文本分开为不同元素
            content_blocks.append([
                {"tag": "text", "text": "📋 "},
                {"tag": "text", "text": title_text}
            ])
            prev_was_title = True
        # 处理日期开头的行（例如：2025-12-22 每日科技聚合资讯）
        elif re.match(r'^\d{4}-\d{2}-\d{2}', line):
            # 这是一个日期开头的行，作为主标题处理
            if content_blocks:  # 如果已有内容，先添加空行
                content_blocks.append([{"tag": "text", "text": ""}])
            content_blocks.append([
                {"tag": "text", "text": "📅 "},
                {"tag": "text", "text": line}
            ])
            prev_was_title = True
        # 处理列表项（以 - 或 * 开头，通常包含链接）
        elif line.startswith('-') or line.startswith('*'):
            prev_was_title = False
            # 移除列表标记
            list_text = line.lstrip('-* ').strip()
            # 处理这一行的内容，可能包含链接和加粗文本
            block_content = parse_line_with_links(list_text)
            if block_content:
                # 在列表项前添加一个小圆点符号，美化列表
                # 使用独立的 text 元素，让格式更清晰
                if block_content and len(block_content) > 0:
                    # 检查是否已经有符号，避免重复
                    first_element = block_content[0]
                    if first_element.get("tag") == "text":
                        if not first_element["text"].startswith("•"):
                            block_content[0] = {"tag": "text", "text": f"• {first_element['text']}"}
                    else:
                        # 如果第一个是链接，在前面添加文本符号
                        block_content.insert(0, {"tag": "text", "text": "• "})
                content_blocks.append(block_content)
            else:
                content_blocks.append([
                    {"tag": "text", "text": "• "},
                    {"tag": "text", "text": list_text.replace('**', '')}
                ])
        # 处理包含链接的行
        elif '](' in line:
            prev_was_title = False
            block_content = parse_line_with_links(line)
            if block_content:
                content_blocks.append(block_content)
            else:
                content_blocks.append([{
                    "tag": "text",
                    "text": line.replace('**', '')
                }])
        else:
            prev_was_title = False
            # 普通文本，移除加粗标记
            text_content = line.replace('**', '')
            if text_content:
                # 检查是否是统计信息（包含"共"、"来自"等关键词）
                if '共' in text_content and '篇文章' in text_content:
                    # 美化统计信息，使用多个元素让格式更清晰
                    content_blocks.append([{"tag": "text", "text": ""}])
                    content_blocks.append([
                        {"tag": "text", "text": "📊 "},
                        {"tag": "text", "text": text_content}
                    ])
                else:
                    content_blocks.append([{
                        "tag": "text",
                        "text": text_content
                    }])
    
    # 如果没有内容块，使用原始文本
    if not content_blocks:
        content_blocks = [[{"tag": "text", "text": text.replace('**', '')}]]
    
    # 构建符合飞书 API 格式的数据
    # 注意：飞书支持 zh_cn 和 zh-CN，使用 zh_cn 更通用
    data = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": content_blocks
                }
            }
        }
    }
    
    # 打印发送的数据以便调试（使用多种方式确保输出可见）
    import sys
    output = '=' * 80 + '\n'
    output += '【发送给飞书的数据结构】\n'
    output += '=' * 80 + '\n'
    output += f'msg_type: {data["msg_type"]}\n'
    output += f'title: {data["content"]["post"]["zh_cn"]["title"]}\n'
    output += f'content_blocks数量: {len(data["content"]["post"]["zh_cn"]["content"])}\n'
    output += '\n【完整的JSON数据】\n'
    output += json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    output += '=' * 80 + '\n'
    
    # 输出到日志
    logger.debug(output)
    
    try:
        response = requests.post(
            url=webhook_url,
            headers=headers,
            json=data,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        # 打印完整响应以便调试
        logger.debug(f'【飞书API响应】{json.dumps(result, ensure_ascii=False, indent=2)}')
        
        # 检查飞书返回的错误码
        if result.get('code') != 0:
            error_msg = result.get('msg', '未知错误')
            logger.error(f'【飞书错误】富文本消息发送失败: {error_msg} (code: {result.get("code")})')
            return False
        else:
            logger.info('【飞书成功】富文本消息发送成功')
            return True
    except requests.exceptions.RequestException as e:
        logger.error(f'【飞书错误】富文本消息发送失败 (网络错误): {e}')
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                logger.error(f'【飞书错误详情】{json.dumps(error_detail, ensure_ascii=False, indent=2)}')
            except:
                logger.error(f'【飞书错误响应】{e.response.text}')
        return False
    except Exception as e:
        logger.exception(f'【飞书错误】富文本消息发送失败: {e}')
        return False


def parse_line_with_links(line):
    """
    解析包含链接的行，返回飞书 post 格式的内容块
    
    参数:
        line: 包含 Markdown 链接的文本行
        
    返回:
        内容块列表，格式如：[{"tag": "text", "text": "文本"}, {"tag": "a", "text": "链接", "href": "url"}]
    """
    import re
    block_content = []
    
    # 查找所有链接 [text](url)
    links = list(re.finditer(r'\[([^\]]+)\]\(([^\)]+)\)', line))
    
    if not links:
        # 没有链接，返回普通文本
        return [{"tag": "text", "text": line.replace('**', '')}]
    
    last_pos = 0
    for match in links:
        # 添加链接前的文本
        if match.start() > last_pos:
            text_before = line[last_pos:match.start()].strip()
            if text_before:
                # 移除加粗标记
                text_before = text_before.replace('**', '')
                if text_before:
                    block_content.append({
                        "tag": "text",
                        "text": text_before
                    })
        
        # 添加链接
        link_text = match.group(1)
        link_url = match.group(2)
        # 移除链接文本中的加粗标记 **text** -> text
        # 支持多种加粗格式：**text**, **text, text**
        link_text = link_text.replace('**', '')
        # 确保链接URL不为空
        if not link_url or link_url.strip() == '':
            link_url = '#'
        block_content.append({
            "tag": "a",
            "text": link_text.strip(),
            "href": link_url.strip()
        })
        last_pos = match.end()
    
    # 添加链接后的文本（通常是时间、标签等）
    if last_pos < len(line):
        text_after = line[last_pos:].strip()
        if text_after:
            # 移除加粗标记
            text_after = text_after.replace('**', '')
            if text_after:
                # 检查是否包含标签（🏷️ 开头的部分）
                if '🏷️' in text_after:
                    # 只保留标签部分，移除时间部分
                    parts = text_after.split('🏷️', 1)
                    tags_part = parts[1].strip() if len(parts) > 1 else ''
                    
                    # 添加标签部分，使用标签emoji
                    if tags_part:
                        block_content.append({
                            "tag": "text",
                            "text": f" 🏷️ {tags_part}"
                        })
                # 如果没有标签，不添加任何内容（因为时间已经被移除了）
    
    return block_content if block_content else [{"tag": "text", "text": line.replace('**', '')}]


def send_feishu_text_message(webhook_url, title, text):
    """
    发送飞书文本格式消息
    
    参数:
    - webhook_url: 飞书机器人 Webhook 地址
    - title: 消息标题
    - text: 消息内容
    """
    headers = {'Content-Type': 'application/json'}
    
    # 组合标题和内容
    full_text = f"{title}\n\n{text}" if title else text
    
    # 限制文本长度（飞书文本消息最大长度约 4096 字符）
    if len(full_text) > 4000:
        full_text = full_text[:4000] + "\n\n...(内容过长已截断)"
    
    # 根据飞书官方文档，使用正确的格式
    data = {
        "msg_type": "text",
        "content": {
            "text": full_text
        }
    }
    
    # 打印发送的数据以便调试
    logger.debug(f'【飞书文本消息】发送数据: msg_type={data["msg_type"]}, text长度={len(data["content"]["text"])}')
    
    try:
        response = requests.post(
            url=webhook_url,
            headers=headers,
            json=data,  # 使用 json 参数而不是 data，确保正确编码
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        # 打印完整响应以便调试
        logger.debug(f'【飞书API响应】{json.dumps(result, ensure_ascii=False, indent=2)}')
        
        if result.get('code') != 0:
            error_msg = result.get('msg', '未知错误')
            logger.error(f'【飞书错误】文本消息发送失败: {error_msg} (code: {result.get("code")})')
            return False
        else:
            logger.info('【飞书成功】文本消息发送成功')
            return True
    except requests.exceptions.RequestException as e:
        logger.error(f'【飞书错误】文本消息发送失败 (网络错误): {e}')
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                logger.error(f'【飞书错误详情】{json.dumps(error_detail, ensure_ascii=False, indent=2)}')
            except:
                logger.error(f'【飞书错误响应】{e.response.text}')
        return False
    except Exception as e:
        logger.exception(f'【飞书错误】文本消息发送失败: {e}')
        return False