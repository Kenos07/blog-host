import os, re

import frontmatter
from datetime import date
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for, session, flash, abort)

from werkzeug.utils import secure_filename

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# HELPERS

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text

def article_path(slug: str) -> str:
    return os.path.join(config.ARTICLES_DIR, f"{slug}.md")

def load_article(slug: str) -> dict | None:
    path = article_path(slug)
    if not os.path.exists(path):
        return None
    post = frontmatter.load(path)
    
    return {
        "title": post.metadata.get("title", ""),
        "slug": post.metadata.get("slug", slug),
        "published_at": str(post.metadata.get("published_at", "")),
        "thumbnail": post.metadata.get("thumbnail", ""),
        "content": post.content,
    }

def save_article(data: dict) -> None:
    post = frontmatter.Post(
        content=data["content"],
        title=data["title"],
        slug=data["slug"],
        published_at=data["published_at"],
        thumbnail=data.get("thumbnail", "")
    )
    path = article_path(data["slug"])
    with open(path, "w", encoding="utf-8") as f:
        frontmatter.dump(post, f)

def delete_article(slug: str) -> None:
    path = article_path(slug)
    if os.path.exists(path):
        os.remove(path)

def list_articles() -> list[dict]:
    articles = []
    for fname in os.listdir(config.ARTICLES_DIR):
        if fname.endswith(".md"):
            slug = fname[:-3]
            article = load_article(slug)
            if article:
                articles.append(article)
    articles.sort(key=lambda a: a.get("published_at", ""), reverse=True)
    return articles

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS

def save_thumbnail(file) -> str | None:
    if not file or file.filename == "":
        return None
    if not allowed_file(file.filename):
        return None
    filename = secure_filename(file.filename)
    os.makedirs(config.UPLOADS_DIR, exist_ok=True)
    file.save(os.path.join(config.UPLOADS_DIR, filename))
    return filename


# GUEST ROUTE

@app.route("/")
def home():
    articles = list_articles()
    return render_template("guest/home.html", articles=articles)

@app.route("/article/<slug>")
def article(slug):
    art = load_article(slug)
    if art is None:
        abort(404)
    return render_template("guest/article.html", article=art)

# ADMIN ROUTES

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("admin_dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid username or password."
    return render_template("admin/login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    articles = list_articles()
    return render_template("admin/dashboard.html", articles=articles)

@app.route("/admin/add", methods=["GET", "POST"])
@login_required
def admin_add():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        published_at = request.form.get("published_at", str(date.today()))
        if not title or not content:
            flash("Title and content are required.", "error")
            return render_template(
                "admin/add.html",
                title=title,
                content=content,
                published_at=published_at,
                thumbnail="",
            )
        slug = slugify(title)
        base_slug = slug
        counter = 1
        while os.path.exists(article_path(slug)):
            slug = f"{base_slug}-{counter}"
            counter += 1
        thumbnail = save_thumbnail(request.files.get("thumbnail")) or ""
        save_article(
            {
                "title": title,
                "slug": slug,
                "content": content,
                "published_at": published_at,
                "thumbnail": thumbnail
            }
        )
        flash(f'Article "{title}" published successfully.', "success")
        return redirect(url_for("admin_dashboard"))
    
    return render_template(
        "admin/add.html",
        title="",
        content="",
        published_at=str(date.today()),
        thumbnail="",
    )

@app.route("/admin/edit/<slug>", methods=["GET", "POST"])
@login_required
def admin_edit(slug):
    art = load_article(slug)
    if art is None:
        abort(404)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        published_at = request.form.get("published_at", art["published_at"])
        if not title or not content:
            flash("Title and content are required.", "error")
            return render_template(
                "admin/edit.html",
                article=art,
                title=title,
                content=content,
                published_at=published_at,
            )

        new_thumb = save_thumbnail(request.files.get("thumbnail"))
        art["title"] = title
        art["content"] = content
        art["published_at"] = published_at
        art["thumbnail"] = new_thumb if new_thumb is not None else art.get("thumbnail", "")
        save_article(art)
        flash(f'Article "{title}" updated successfully.', "success")
        return redirect(url_for("admin_dashboard"))
    return render_template(
        "admin/edit.html",
        article=art,
        title=art["title"],
        content=art["content"],
        published_at=art["published_at"],
        thumbnail=art.get("thumbnail", "")
    )

@app.route("/admin/delete/<slug>", methods=["POST"])
@login_required
def admin_delete(slug):
    art = load_article(slug)
    if art:
        delete_article(slug)
        flash(f'Article "{art["title"]}" deleted.', "success")
    return redirect(url_for("admin_dashboard"))

# 404

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# MAIN APP

if __name__ == "__main__":
    os.makedirs(config.ARTICLES_DIR, exist_ok=True)
    app.run(debug=True)