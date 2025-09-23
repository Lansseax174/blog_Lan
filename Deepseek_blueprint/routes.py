from flask import Flask, render_template, request, jsonify, Response, Blueprint
import re
import dashscope
import random
import os
import datetime

from dotenv import load_dotenv
load_dotenv()
DeepSeekApi = os.getenv("DeepSeekApi")

deepseek_blueprint = Blueprint('DeepSeek', __name__,
                               template_folder='templates',
                               static_folder='static')

# 多用户对话映射：user_id -> [ { "role": "...", "content": "..." }, ...]
conversations = {}

# 记录每个 user_id 最近一次活动时间
last_activity = {}

def generate_user_id():
    """
    生成长度为 10^20 (共21位数字) 的随机ID字符串。
    这里做示例，实际上只是一串 21 位数字。
    """
    # 先生成第一位 [1-9]，避免出现开头'0'
    first_digit = str(random.randint(1, 9))
    # 再生成剩余 20 位 [0-9]
    other_digits = ''.join(str(random.randint(0, 9)) for _ in range(20))
    return first_digit + other_digits

def format_message(text):
    """
    简单的富文本处理示例：将 **粗体** 转成 <span class="bold-text">，
    并对某些符号做基础拆分，可根据项目需要自定义。
    """
    if not text:
        return ''

    # 把一段多行文本拆成行列表，并把每一行里 **粗体标记** 的内容替换为
    # <span class="bold-text">内容</span> 这种 HTML 标签，以便网页显示成自定义的粗体样式
    lines = text.split('\n')
    formatted_lines = [
        re.sub(r'\*\*(.*?)\*\*', r'<span class="bold-text">\1</span>', line)
        for line in lines
    ]

    processed_text = '\n'.join(formatted_lines)
    sections = [section for section in processed_text.split('###') if section.strip()]

    formatted_sections = []
    for section in sections:
        section_lines = [line.strip() for line in section.split('\n') if line.strip()]
        if not section_lines:
            continue
        result = ''
        for line in section_lines:
            # 匹配形如 "1." 的序号并加粗
            if re.match(r'^\d+\.', line):
                result += f'<p class="section-title">{line}</p>'
            # 匹配形如 "-" 的子段落加粗
            elif line.startswith('-'):
                clean_text = line.lstrip('-').strip()
                result += f'<p class="subsection"><span class="bold-text">{clean_text}</span></p>'
            # 匹配形如 "xxx: yyy"
            elif ':' in line:
                parts = line.split(':', 1)
                subtitle = parts[0].strip()
                content = parts[1].strip()
                result += f'<p><span class="subtitle">{subtitle}</span>: {content}</p>'
            else:
                result += f'<p>{line}</p>'
        formatted_sections.append(result)

    return ''.join(formatted_sections)

# 清理超过24小时未活动的user_id
def cleanup_old_users():
    now = datetime.datetime.now()
    # 建立一个24小时前是几点的时间点
    cutoff = now - datetime.timedelta(hours=24)
    remove_ids = []
    for uid, last_time in last_activity.items():
        if last_time < cutoff:
            remove_ids.append(uid)
    for uid in remove_ids:
        # 删除 last_activity 和 conversations 中的数据
        del last_activity[uid]
        if uid in conversations:
            del conversations[uid]

@deepseek_blueprint.route('/')
def index():
    """
    每次刷新页面时，随机生成一个新的 user_id 并传给前端。
    这样用户可以在本页面发消息时都带上该 user_id，用于区分对话历史。
    """
    user_id = generate_user_id()
    return render_template('deepseek.html', user_id=user_id)

@deepseek_blueprint.route('/chat', methods=['POST'])
def send_once():
    """
    一次性返回接口 (非流式)。
    不改变原有功能的同时，增加了多用户对话记忆。
    """
    user_id = request.args.get('user_id', '').strip()
    if not user_id:
        return jsonify({'error': '缺少 user_id 参数'}), 400

    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'error': '空消息'}), 400

    # 新增：更新用户最新活动时间
    last_activity[user_id] = datetime.datetime.now()

    # 取出或初始化对话历史
    conversation_history = conversations.get(user_id, [])
    # 在对话历史里追加用户消息
    conversation_history.append({"role": "user", "content": user_message})

    try:
        # 调用 DashScope 一次性生成
        response = dashscope.Generation.call(
            api_key="",
            model="deepseek-r1",  # deepseek-r1 仅示例
            messages=conversation_history,
            result_format='message'
            # 不带 stream=True，即一次性接口
        )

        # 打印日志，便于调试
        if response and response.output and response.output.choices:
            print("reasoning_content:", response.output.choices[0].message.reasoning_content)
            print("API Response:", response)
        else:
            print("response 或 choices 为空:", response)

        # 检查response是否有效
        if response and response.output and response.output.choices:
            bot_message = response.output.choices[0].message.content
            # 将模型回答存入对话历史
            conversation_history.append({"role": "assistant", "content": bot_message})
            # 更新回全局 conversations
            conversations[user_id] = conversation_history

            # 记录日志到 logs.txt (若不存在会自动创建)
            reasoning_content = response.output.choices[0].message.reasoning_content or ""
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logs_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs.txt')
            with open(logs_file, 'a', encoding='utf-8') as f:
                f.write(f"Time: {timestamp}, UserID: {user_id}, UserMsg: {user_message}, "
                        f"Reasoning: {reasoning_content}, Content: {bot_message}\n")

            formatted_bot_message = format_message(bot_message)
            # 调用清理函数
            cleanup_old_users()

            return jsonify({'reply': formatted_bot_message})
        else:
            # 这里在 response 无效时也写日志，确保一定能创建/写入 logs.txt
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logs_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs.txt')
            with open(logs_file, 'a', encoding='utf-8') as f:
                f.write(f"Time: {timestamp}, UserID: {user_id}, UserMsg: {user_message}, "
                        f"Reasoning: 无, Content: 出错了，请稍后再试。\n")

            # 调用清理函数
            cleanup_old_users()
            return jsonify({'reply': format_message('出错了，请稍后再试。')})

    except Exception as e:
        print("API 调用错误:", str(e))

        # 新增：异常时也写日志
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logs_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs.txt')
        with open(logs_file, 'a', encoding='utf-8') as f:
            f.write(f"Time: {timestamp}, UserID: {user_id}, UserMsg: {user_message}, "
                    f"Error: {str(e)}\n")

        # 调用清理函数
        cleanup_old_users()
        return jsonify({'reply': format_message('出错了，请稍后再试。')})

@deepseek_blueprint.route('/chat_stream')
def chat_stream():
    """
    流式(SSE)接口。
    会在返回数据里加前缀:
      - 'REASONING:' 表示“思考过程”
      - 'ANSWER:'    表示“正式回答内容”
    """
    user_id = request.args.get('user_id', '').strip()
    if not user_id:
        def error_stream():
            yield "data: 出错了: 缺少 user_id 参数\n\n"
            yield "event: end\ndata: \n\n"
        return Response(error_stream(), mimetype='text/event-stream')

    user_message = request.args.get('message', '').strip()

    def generate_stream():
        if not user_message:
            yield "data: 出错了: 空消息\n\n"
            yield "event: end\ndata: \n\n"
            return

        # ★★★ 新增：更新用户最新活动时间
        last_activity[user_id] = datetime.datetime.now()

        # 取出或初始化对话历史
        conversation_history = conversations.get(user_id, [])
        # 追加用户消息
        conversation_history.append({"role": "user", "content": user_message})

        try:
            # 调用 DashScope，流式输出
            chunk_generator = dashscope.Generation.call(
                api_key=DeepSeekApi,
                model="deepseek-v3.1",
                messages=conversation_history,
                result_format='message',
                enable_thinking=True,
                stream=True,
                incremental_output=True
            )

            if chunk_generator is None:
                yield "data: 出错了: 该模型不支持流式或返回为空\n\n"
                yield "event: end\ndata: \n\n"
                return

            first_chunk = next(chunk_generator, None)
            if (not first_chunk or not first_chunk.output or
                not first_chunk.output.choices):
                yield "data: 出错了: 该模型不支持流式或流式内容为空\n\n"
                yield "event: end\ndata: \n\n"
                return

            yield "data: ================思考过程===============\n\n"
            is_answering = False
            full_answer = ""
            accumulated_reasoning = ""

            # 处理第一帧
            rc = first_chunk.output.choices[0].message.reasoning_content
            ac = first_chunk.output.choices[0].message.content or ""

            if rc:
                yield f"data: REASONING:{rc}\n\n"
                accumulated_reasoning += rc
            if ac:
                if not is_answering:
                    yield "data: ================完整回复===============\n\n"
                    is_answering = True
                yield f"data: ANSWER:{ac}\n\n"
                full_answer += ac

            # 后续帧
            for chunk in chunk_generator:
                rc = chunk.output.choices[0].message.reasoning_content
                ac = chunk.output.choices[0].message.content or ""

                if rc:
                    yield f"data: REASONING:{rc}\n\n"
                    accumulated_reasoning += rc

                if ac:
                    if not is_answering:
                        yield "data: ================完整回复===============\n\n"
                        is_answering = True
                    yield f"data: ANSWER:{ac}\n\n"
                    full_answer += ac

            yield "event: end\ndata: \n\n"

            # 将完整回答存入对话历史
            conversation_history.append({"role": "assistant", "content": full_answer})
            conversations[user_id] = conversation_history

            # 记录日志到 logs.txt (若不存在会自动创建)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logs_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs.txt')
            with open(logs_file, 'a', encoding='utf-8') as f:
                f.write(f"Time: {timestamp}, UserID: {user_id}, UserMsg: {user_message}, "
                        f"Reasoning: {accumulated_reasoning}, Content: {full_answer}\n")

            # 调用清理函数
            cleanup_old_users()

        except Exception as e:
            err_msg = f"出错了: {str(e)}"
            yield f"data: {err_msg}\n\n"
            yield "event: end\ndata: \n\n"

            # ★★★ 新增：异常时也写日志
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logs_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs.txt')
            with open(logs_file, 'a', encoding='utf-8') as f:
                f.write(f"Time: {timestamp}, UserID: {user_id}, UserMsg: {user_message}, "
                        f"Error: {str(e)}\n")

            # 调用清理函数
            cleanup_old_users()

    return Response(generate_stream(), mimetype='text/event-stream')


