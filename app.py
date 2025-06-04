import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from datetime import datetime

# 加载环境变量
load_dotenv()


class Config(object):
    # 定义定时任务
    # HOST = '0.0.0.0'
    # FLASK_RUN_PORT = 8081
    # DEBUG = True

    SQLALCHEMY_DATABASE_URI = 'sqlite:///comments.db'
    SCHEDULER_API_ENABLED = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JOBS = [
        # {
        #     'id': 'job1',  # 任务 ID
        #     'func': 'app:print_time',  # 执行任务的函数
        #     'args': ('job1',),  # 传递给函数的参数
        #     'trigger': 'interval',  # 触发类型
        #     'seconds': 10  # 时间间隔（秒）
        # },
        {
            'id': 'auto_audit',  # 任务 ID
            'func': 'app:auto_audit',  # 执行任务的函数
            'trigger': 'interval',  # 触发类型
            'seconds': 30,  # 时间间隔（秒）
            'max_instances': 1
        }
    ]


# 定时打印时间测试
def print_time(job_id):
    # 打印当前时间，按照年月日时分秒的格式
    nowstr = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{nowstr} :Task {job_id} executed.")

def extract_json(text):
    # 提取第一个大括号 {} 之间的内容
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    else:
        return text  # 没找到就原样返回，后面解析会失败

# 调用GPT大模型，自动审核评论
def auto_audit():
    with app.app_context():  # 确保在应用上下文中执行
        try:
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY 环境变量未设置")

            # 配置 OpenAI 服务
            client = OpenAI(
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                api_key=os.getenv("OPENAI_API_KEY")
            )
            # set the prompt
            prompt = '''
            # 评论内容审核指令

            ## 任务描述
            对用户提交的评论内容进行合规性评估，判断其是否适合在中国境内网络平台发布

            ## 评估维度
            1. **政治敏感性**
               - 是否包含不当政治表述
               - 是否涉及敏感政治人物/事件

            2. **宗教文化适配**
               - 是否含有宗教歧视内容
               - 是否符合社会主义核心价值观

            3. **法律合规性**
               - 是否违反网络安全法
               - 是否包含违法信息

            4. **社会文化规范**
               - 是否存在地域/民族歧视
               - 是否使用侮辱性语言
               - 是否包含低俗内容

            ## 返回格式要求
            返回一个 JSON 对象，如：
            {
            "passed": <0|1>,
            "reason": "该评论内容含有可能被视为不尊重的言辞"
            }
            '''

            # get all comments
            comments = Comment.query.filter_by(status=0).order_by(Comment.id).all()
            # 遍历 comments
            for comment in comments:
                userInput = comment.content
                # call the OpenAI API
                generation_response = client.chat.completions.create(
                    # model="gpt-4-1106-preview",
                    model="deepseek/deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": prompt
                        },
                        {
                            "role": "user",
                            "content": userInput
                        }
                    ],
                    response_format={"type": "json_object"},
                    stream=False
                )
                # ChatCompletion(id='chatcmpl-8cYEeiOrkM42OlMo40QlMDKQfqu0j', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='{\n  "passed": 0,\n  "reason": "[该评论内容含有可能被视为不尊重的言辞]"\n}', role='assistant', function_call=None, tool_calls=None))], created=1704198756, model='gpt-4-1106-preview', object='chat.completion', system_fingerprint='fp_3905aa4f79', usage=CompletionUsage(completion_tokens=33, prompt_tokens=207, total_tokens=240))
                resultContent = generation_response.choices[0].message.content.strip()
                print("返回内容：", resultContent)
                json_str = extract_json(resultContent)
                # 转化为json对象
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print("JSON解析失败:", e)
                    print("原始返回:", resultContent)
                    print("提取后的内容:", json_str)
                    continue
                # 判断评论的检查结果是否合规
                if result["passed"] == 1:
                    comment.status = 1
                    db.session.commit()
                    print(f"{comment.id} 自动审核通过！")
                else:
                    comment.status = 2
                    db.session.commit()
                    print(f"[{comment.id}] '{comment.content}' 有问题 : {result['reason']} .")


        except Exception as e:
            print(f"自动审核任务出错: {str(e)}")


# 把时间戳转为年月日的时间来展示
def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


# 自定义的timesense过滤器
def relative_time_from_timestamp(timestamp):
    # 将时间戳转换为 datetime 对象
    target_time = datetime.fromtimestamp(timestamp)
    now = datetime.now()

    # 计算时间差
    delta = now - target_time
    days = delta.days
    seconds = delta.seconds
    minutes = seconds // 60
    hours = minutes // 60

    # 根据时间差返回相对时间
    if days > 365:
        years = days // 365
        return "%i 年前" % years
    elif days > 30:
        months = days // 30
        return "%i 个月前" % months
    elif days > 7:
        weeks = days // 7
        return "%i 周前" % weeks
    elif days > 0:
        return "%i 天前" % days
    elif hours > 0:
        return "%i 小时前" % hours
    elif minutes > 0:
        return "%i 分钟前" % minutes
    elif seconds > 0:
        return "%i 秒前" % seconds
    else:
        return "刚刚"


app = Flask(__name__)
app.config.from_object(Config())

# 向 jinja_env 应用添加过滤器
app.jinja_env.filters['timesince'] = relative_time_from_timestamp

db = SQLAlchemy(app)

# 初始化调度器
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    # 评论状态 0:未审核 1:已审核
    status = db.Column(db.Integer, nullable=False, default=0)
    # 增加一个创建的时间，用created_at字段的时间戳，单位是秒
    created_at = db.Column(db.Integer, nullable=False, default=0)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form['content']
        new_comment = Comment(content=content, status=0)
        # 当前时间戳，秒 存入 created_at
        new_comment.created_at = int(datetime.now().timestamp())

        try:
            db.session.add(new_comment)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding your comment'
    else:
        comments = Comment.query.filter_by(status=1).order_by(Comment.id.desc()).all()
        return render_template('index.html', comments=comments)


@app.route('/delete/<int:id>')
def delete(id):
    comment_to_delete = Comment.query.get_or_404(id)

    try:
        db.session.delete(comment_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that comment'


# 评论管理，可以查看评论的列表，然后审核评论, 审核通过，设置status为1，否则设置为2
@app.route('/admin')
def admin():
    # 查询status为0的所有评论
    comments = Comment.query.filter_by(status=0).order_by(Comment.id).all()
    return render_template('admin.html', comments=comments)


# 通过审核的方法名pass，接受评论id，然后修改status为1
@app.route('/passone/<int:id>')
def passone(id):
    comment_to_pass = Comment.query.get_or_404(id)

    try:
        comment_to_pass.status = 1
        db.session.commit()
        return redirect('/admin')
    except:
        return 'There was a problem passing that comment'


@app.route('/new')
# 拒绝审核的方法名reject，接受评论id，然后修改status为2
@app.route('/reject/<int:id>')
def rejectone(id):
    comment_to_reject = Comment.query.get_or_404(id)

    try:
        comment_to_reject.status = 2
        db.session.commit()
        return redirect('/admin')
    except:
        return 'There was a problem rejecting that comment'


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not scheduler.running:  # 防止调试模式下的重复启动
            scheduler.start()
    app.run(port=5000, debug=True)
