from flask import Flask, render_template, request, redirect, url_for, session, abort
import markdown
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 这里填一个复杂点的随机字符串，保证 session 安全

# 博客文章存放目录
CONTENT_DIR = './content'

# 预设后台登录密码
ADMIN_PASSWORD = '123456'

# 前台主页
@app.route('/')
def index():
    articles = [] # 存储读到的文章数据
    for filename in os.listdir(CONTENT_DIR):
        if filename.endswith('.md'):
            filepath = os.path.join(CONTENT_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                md_text = file.read()
            file_html_version = markdown.markdown(md_text, extensions=['fenced_code'])
            # markdown库把md文本转换为html
            articles.append({
                'title': filename[:-3], # 文件名去掉.md当作文章名
                'content': file_html_version
            })
    # 按文件名(A到Z)排序
    articles.sort(key=lambda x: x['title'])
    return render_template('index.html', articles=articles)
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
    files = [f for f in os.listdir(CONTENT_DIR) if f.endswith('.md')]
    return render_template('admin.html', files=files)

# 编辑或新建文章
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

# 删除文章
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
