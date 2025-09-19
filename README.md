# 🌌 个人博客

一个基于 **Flask**
框架开发的个人博客网站，采用未来科技风格的全屏星空背景与霓虹 UI。\
支持 **Markdown
文章管理**、后台登录、文件排序、以及可定制的动态前端效果。\
**已部署在京东云服务器作为个人博客：`https://www.lansseax.icu`**

## ✨ 功能特性

-   **前端动效**
    -   全屏 Canvas 星空背景，使用 JavaScript 实现星点透视动画
    -   首页加载时的「双光束遮罩」动画与发光导航菜单
    -   头像自动旋转、鼠标悬停暂停等细节交互
-   **Markdown 博客系统**
    -   所有文章存放于 `content/` 目录，支持 `fenced_code` 语法
    -   首页自动加载并渲染 Markdown 为 HTML
    -   支持自定义排序：可在后台拖拽文章顺序，保存到 `order.json`
-   **后台管理**
    -   `/admin` 页面提供文章的新增、编辑、删除与排序功能
    -   简单的密码登录系统，基于 `session` 保存登录状态
    -   密码可通过 `.env` 文件安全配置（避免明文硬编码）
-   **多页面结构**
    -   预置 `/blog`、`/about`、`/contact`、`/settings`
        等路由，方便扩展
    -   所有页面继承同一星空与导航样式，保持一致的视觉体验

## 🏗️ 技术栈

  层级       技术选型
  ---------- -----------------------------------------
  **后端**   Python 3.x + Flask
  **前端**   HTML5 + CSS3 + JavaScript (原生 Canvas)
  **模板**   Jinja2 模板引擎 (Flask 内置)
  **依赖**   `markdown` 用于渲染 Markdown 为 HTML
  **部署**   uWSGI + Nginx (推荐)

## 📂 项目结构

    .
    ├─ app.py               # Flask 主程序入口
    ├─ templates/           # HTML 模板文件
    │  ├─ index.html        # 首页
    │  ├─ admin.html        # 后台管理
    │  ├─ edit.html         # 编辑页面
    │  ├─ login.html        # 登录页面
    │  └─ ... 其他扩展页面
    ├─ content/             # Markdown 文章存放目录
    ├─ order.json           # 自定义排序文件（自动生成）
    ├─ static/              # 静态资源 (CSS/JS/图片/头像)
    └─ .env                 # 环境变量 (存放后台密码等)

## ⚙️ 安装与运行

1.  **克隆项目**

    ``` bash
    git clone https://github.com/Lansseax174/blog_Lan.git
    上传到云服务器
    ```

2.  **安装依赖**

    ``` bash
    Flask
    markdown
    python-dotenv
    json
    os
    ```

3.  **配置环境变量** 新建 `.env` 文件（与 `app.py` 同级）：

    ``` bash
    ADMIN_PASSWORD=后台密码
    ```
    
4.  **生产部署 (Nginx + uWSGI)**

    -   使用宝塔面板或 Linux 服务器：
        -   安装 uWSGI：`pip install uwsgi`\
        -   配置 Nginx 反向代理到 uWSGI (监听 `127.0.0.1:8000`)\
        -   使用 `uwsgi --http 0.0.0.0:8000 --wsgi-file app.py --callable app` 启动服务\
    -   推荐使用 HTTPS (Let's Encrypt) 证书。

## 🔑 关键实现说明

-   **路由与装饰器**

    -   `@app.route('/')`：渲染首页，读取 `content/` 下所有 `.md`
        文件。\
    -   `@app.route('/admin')`：后台管理，需 `session['logged_in']`
        校验。\
    -   `@app.route('/edit', methods=['GET','POST'])`：支持文章的新增与编辑。\
    -   `@app.route('/save_order', methods=['POST'])`：保存前端拖拽后的顺序到
        `order.json`。

-   **Markdown 渲染**

    ``` python
    html = markdown.markdown(md_text, extensions=['fenced_code'])
    ```

-   **自定义排序**\
    前端使用拖拽 (Sortable.js) 改变顺序，后端写入 `order.json`，\
    首页加载时按 `order_index` 排序渲染。

-   **安全措施**

    -   使用 `.env` + `python-dotenv` 加载敏感信息：

        ``` python
        from dotenv import load_dotenv
        load_dotenv()
        ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
        ```


## 📝 License

MIT License © 2025 [Lansseax](https://github.com/Lansseax174)

**欢迎 Star ⭐ 和 Fork，本项目仅供个人学习与展示使用。**
