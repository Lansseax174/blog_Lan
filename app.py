from flask import Flask, render_template
import markdown
# Flask:框架核心
# render_template: 加载.html文件模板的函数
app = Flask(__name__)
# 创建Flask网站应用对象, __name__的作用是高数Flask当前文件是主程序

@app.route('/')
# 告诉Flask:当用户访问这个网站的根路径/（比如 http://127.0.0.1:5000/）
# 就运行下面的index()函数，类似路由，当访问xx,就执行xx
def index():
    articles = []
    # 原始文章内容，使用 Markdown 格式写
    raw_articles = [
        {
            "title": "如何搭建个人博客",
            "content": '''
    ### 第一步：安装 Flask

    你可以运行：

        pip install flask

    ### 第二步：创建项目结构

    在你的编辑器中创建这些文件：

    - app.py
    - templates/index.html
    '''
        },
        {
            "title": "Flask 模板语法简介",
            "content": '''
    你可以使用 Jinja2 模板语法：

    - \`\{\{ 变量 \}\}\` 显示变量
    - \`\{\% for item in list \%\}\` 遍历循环

    '''
        }
    ]

    # 将 Markdown 转成 HTML

    for article in raw_articles:
        html = markdown.markdown(article["content"], extensions=["fenced_code"])
        articles.append({
            "title": article["title"],
            "content": html
        })
    print(articles)
    return render_template('index.html', articles=articles)
    # 把 templates/index.html 文件渲染成网页，返回给浏览器显示

@app.route('/model')
def model_view():
    return render_template('model.html')

if __name__ == '__main__':
    app.run(debug = True)
    # 开启debug模式会显示错误信息
