import json
import os

import markdown

from flask import Flask, render_template, request, redirect, url_for, session

from Deepseek_blueprint import deepseek_blueprint

from dotenv import load_dotenv
load_dotenv()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 这里填一个复杂点的随机字符串，保证 session 安全
app.register_blueprint(deepseek_blueprint, url_prefix='/deepseek')
# 主页文章存放目录
Content_dir = './content'
BlogContent_dir = './BlogContent'

# 文章排序顺序文件
Content_Order = 'ContentOrder.json'
BlogContent_Order = 'BlogContentOrder.json'

# 计数文件路径
Click_Nums_File = os.path.join('JsonData', 'ClickMainNums.json')

# 前台主页
@app.route('/')
def index():
    os.makedirs(os.path.dirname(Click_Nums_File), exist_ok=True)

    count = 0
    if os.path.exists(Click_Nums_File):
        with open(Click_Nums_File, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                count = data.get('count',0)
            except json.JSONDecodeError:
                count = 0
    count += 1
    with open(Click_Nums_File, 'w', encoding='utf-8') as file:
        json.dump({'count': count}, file, ensure_ascii=False, indent = 1)

    # 读取自定义顺序
    custom_order = []
    if os.path.exists(Content_dir):
        with open(Content_Order, 'r', encoding='utf-8') as f:
            custom_order = json.load(f)

    articles = [] # 存储读到的文章数据
    for filename in os.listdir(Content_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(Content_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                md_text = file.read()
            file_html_version = markdown.markdown(md_text, extensions=['fenced_code'])
            # markdown库把md文本转换为html
            articles.append({
                'title': filename[:-3], # 文件名去掉.md当作文章名
                'content': file_html_version,
                'filename': filename
            })

    if custom_order:
        # 按自定义顺序排序，没有列出的放最后
        order_index = {name: i for i, name in enumerate(custom_order)}
        articles.sort(key=lambda x: order_index.get(x['filename'], 9999))

    return render_template('index.html', articles=articles, view_count = count)
    # 调用Flask的render_template模块渲染前端页面,使用index.html模板,传入articles

# 登录
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

# 登出
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# 后台管理页
@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    # 列出所有 Markdown 文件，方便选择编辑

    files = [f for f in os.listdir(Content_dir) if f.endswith('.md')]

    custom_order = []
    if os.path.exists(Content_Order):
        try:
            with open(Content_Order, 'r', encoding='utf-8') as file:
                custom_order = json.load(file)
        except Exception:
            custom_order = []

    if custom_order:
        # 按 order.json 里的顺序排；不在 order.json 里的放到后面并按名称排序
        idx = {name: i for i, name in enumerate(custom_order)}
        files.sort(key=lambda name: (0, idx[name]) if name in idx else (1, name.lower()))
    else:
        # 没有自定义顺序就按名称排
        files.sort(key=str.lower)

    files_blog = [f for f in os.listdir(BlogContent_dir) if f.endswith('.md')]

    custom_order_blog = []
    if os.path.exists(BlogContent_Order):
        try:
            with open(BlogContent_Order, 'r', encoding='utf-8') as file:
                custom_order_blog = json.load(file)
        except Exception:
            custom_order_blog = []

    if custom_order_blog:
        # 按 BlogContentOrder.json 里的顺序排；不在 order.json 里的放到后面并按名称排序
        idx = {name: i for i, name in enumerate(custom_order_blog)}
        files_blog.sort(key=lambda name: (0, idx[name]) if name in idx else (1, name.lower()))
    else:
        # 没有自定义顺序就按名称排
        files_blog.sort(key=str.lower)


    return render_template(
        'admin.html',
                           files=files,
                           files_blog=files_blog,
                            has_custom_order=bool(custom_order),
                            has_custom_order_blog = bool(custom_order_blog))


@app.route('/save_order', methods=['POST'])
def save_order():
    if not session.get('logged_in'):
        return '', 403
    data = request.get_json()
    with open(Content_Order, 'w', encoding='utf-8') as f:
        json.dump(data['order'], f, ensure_ascii=False, indent=2)
    return '', 200

@app.route('/save_order2', methods=['POST'])
def save_order2():
    if not session.get('logged_in'):
        return '', 403
    data = request.get_json()
    with open(BlogContent_Order, 'w', encoding='utf-8') as f:
        json.dump(data['order'], f, ensure_ascii=False, indent=2)
    return '', 200

# 编辑或新建主页/博客文章(两者复用一个edit函数)
@app.route('/<scope>/edit', methods=['GET', 'POST'])
def edit(scope):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    filename = request.args.get('filename') or 'new_post.md'

    # scope = "main" 或 "blog"
    base_dir = Content_dir if scope == 'main' else BlogContent_dir
    filepath = os.path.join(base_dir, filename)

    if request.method == 'POST':
        content = request.form.get('content')
        new_filename = request.form.get('filename')
        if not new_filename.endswith('.md'):
            new_filename += '.md'
        new_filepath = os.path.join(base_dir, new_filename)

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

# 删除主页/博客文章(两者复用一个delete函数)
@app.route('/delete/<scope>/<filename>')
def delete(scope, filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # scope = "main" 或 "blog"
    base_dir = Content_dir if scope == 'main' else BlogContent_dir
    filepath = os.path.join(base_dir, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('admin'))

@app.route('/blog')
def blog():
    # 读取自定义顺序
    custom_order = []
    if os.path.exists(BlogContent_dir):
        with open(BlogContent_Order, 'r', encoding='utf-8') as f:
            custom_order = json.load(f)

    articles2 = [] # 存储读到的文章数据
    for filename in os.listdir(BlogContent_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(BlogContent_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                md_text = file.read()
            file_html_version = markdown.markdown(md_text, extensions=['fenced_code'])
            # markdown库把md文本转换为html
            articles2.append({
                'title': filename[:-3], # 文件名去掉.md当作文章名
                'content': file_html_version,
                'filename': filename
            })

    if custom_order:
        # 按自定义顺序排序，没有列出的放最后
        order_index = {name: i for i, name in enumerate(custom_order)}
        articles2.sort(key=lambda x: order_index.get(x['filename'], 9999))


    return render_template('blog.html', articles2=articles2)
    # 调用Flask的render_template模块渲染前端页面,使用blog.html模板,传入articles

@app.route('/deepseek')
def about():
    return render_template('deepseek.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/Carbon_Silicon_Matrix')
def carbon_silicon_matrix():
    return render_template('Carbon_Silicon_Matrix.html')

if __name__ == '__main__':
    if not os.path.exists(Content_dir):
        os.makedirs(Content_dir)
    app.run(debug=True)

