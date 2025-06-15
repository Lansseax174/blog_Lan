# from flask import Flask, render_template
# import markdown
# # Flask:框架核心
# # render_template: 加载.html文件模板的函数
# app = Flask(__name__)
#
# app.secret_key = '123456'
# # 创建Flask网站应用对象, __name__的作用是高数Flask当前文件是主程序
# # 博客文章存放目录
# CONTENT_DIR = './content'
#
# # 预设后台登录密码
# ADMIN_PASSWORD = '123456'
#
# @app.route('/')
# # 告诉Flask:当用户访问这个网站的根路径/（比如 http://127.0.0.1:5000/）
# # 就运行下面的index()函数，类似路由，当访问xx,就执行xx
# def index():
#     articles = []
#     # 原始文章内容，使用 Markdown 格式写
#     raw_articles = [
#         {
#             "title": "如何搭建个人博客",
#             "content": '''
#     ### 第一步：安装 Flask
#
#     你可以运行：
#
#         pip install flask
#
#     ### 第二步：创建项目结构
#
#     在你的编辑器中创建这些文件：
#
#     - app.py
#     - templates/index.html
#     '''
#         },
#         {
#             "title": "Flask 模板语法简介",
#             "content": '''
#     你可以使用 Jinja2 模板语法：
#
#     - \`\{\{ 变量 \}\}\` 显示变量
#     - \`\{\% for item in list \%\}\` 遍历循环
#
#     '''
#         }
#     ]
#
#     # 将 Markdown 转成 HTML
#
#     for article in raw_articles:
#         html = markdown.markdown(article["content"], extensions=["fenced_code"])
#         articles.append({
#             "title": article["title"],
#             "content": html
#         })
#     print(articles)
#     return render_template('index.html', articles=articles)
#     # 把 templates/index.html 文件渲染成网页，返回给浏览器显示
#
# @app.route('/model')
# def model_view():
#     return render_template('model.html')
#
# if __name__ == '__main__':
#     app.run(debug = True)
#     # 开启debug模式会显示错误信息


from flask import Flask, render_template, request, redirect, url_for, session, abort
import markdown
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 这里填一个复杂点的随机字符串，保证 session 安全

# 博客文章存放目录
CONTENT_DIR = './content'

# 预设后台登录密码
ADMIN_PASSWORD = '123456'

# -------------------- 前台主页 --------------------
@app.route('/')
def index():
    articles = []
    # 遍历 content 目录下的 md 文件，转换成 HTML，传给模板渲染
    for filename in os.listdir(CONTENT_DIR):
        if filename.endswith('.md'):
            filepath = os.path.join(CONTENT_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                md_text = f.read()
            html = markdown.markdown(md_text, extensions=['fenced_code'])
            articles.append({
                'title': filename[:-3],
                'content': html
            })
    # 按文件名排序，或者时间排序都行
    articles.sort(key=lambda x: x['title'])
    return render_template('index.html', articles=articles)

# -------------------- 登录 --------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pwd = request.form.get('password')
        if pwd == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='密码错误')
    else:
        return render_template('login.html')

# -------------------- 登出 --------------------
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# -------------------- 后台管理页 --------------------
@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    # 列出所有 Markdown 文件，方便选择编辑
    files = [f for f in os.listdir(CONTENT_DIR) if f.endswith('.md')]
    return render_template('admin.html', files=files)

# -------------------- 编辑或新建文章 --------------------
@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    filename = request.args.get('filename') or 'new_post.md'

    filepath = os.path.join(CONTENT_DIR, filename)

    if request.method == 'POST':
        content = request.form.get('content')
        new_filename = request.form.get('filename')
        if not new_filename.endswith('.md'):
            new_filename += '.md'
        new_filepath = os.path.join(CONTENT_DIR, new_filename)

        # 保存文件
        with open(new_filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        # 如果修改了文件名，删除旧文件
        if new_filepath != filepath and os.path.exists(filepath):
            os.remove(filepath)

        return redirect(url_for('admin'))

    # GET 请求，读取文件内容
    content = ''
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

    return render_template('edit.html', filename=filename, content=content)

# -------------------- 删除文章 --------------------
@app.route('/delete/<filename>')
def delete(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    filepath = os.path.join(CONTENT_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    if not os.path.exists(CONTENT_DIR):
        os.makedirs(CONTENT_DIR)
    app.run(debug=True)
