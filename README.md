# AI评论合规审核系统

## 项目简介
本项目基于 Python 3.9 + Flask + OpenAI API 实现，能够自动判断用户评论内容是否符合规范，适用于中国境内网络平台发布标准。系统支持评论提交、列表展示及后台审核功能。

---

## 技术栈
- Python 3.9
- Flask
- OpenAI API
- Flask-SQLAlchemy（数据库管理）
- Flask-APScheduler（定时任务调度）
- python-dotenv（环境变量管理）

---

## 功能描述
- 用户通过前端提交评论。
- 后台定时调用 OpenAI 模型自动审核评论内容。
- 审核通过的评论状态更新为“已审核”，不合规的标记为“审核失败”。
- 提供前端页面展示审核通过的评论列表。
- 提供后台管理页面查看所有待审核评论。

---

## 环境准备


1、创建新的虚拟环境：

    python3 -m venv venv

2、激活虚拟环境：

   source venv/bin/activate

3、安装依赖：

   pip install -r requirements.txt

注： 如果没有 requirements.txt，可执行以下命令生成：

pip install flask openai python-dotenv flask-sqlalchemy flask-apscheduler

pip freeze > requirements.txt

---

## 配置环境变量

在项目根目录下创建 .env 文件，内容示例如下：

OPENAI_BASE_URL=https://api.openai.com/v1

OPENAI_API_KEY=你的OpenAI_API_Key

请根据你自己的 OpenAI API 地址和密钥进行替换。

---

## 启动项目

通过 IDE 运行 app.py 文件，或命令行执行：python3 app.py

---

## 使用说明

### 访问评论提交及列表页面（只显示审核通过评论）：

http://127.0.0.1:5000/

### 访问后台评论管理页面（查看待审核评论，手动审核）：

http://127.0.0.1:5000/admin

---

## 备注

1）项目中启用了定时任务，每隔几秒自动调用 AI 审核新评论。

2）数据库存储在本地 SQLite 文件 comments.db 中。

3）请确保你的网络环境能够访问 OpenAI API。
