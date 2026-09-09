import os

# Admin credentials
ADMIN_USERNAME = "password"
ADMIN_PASSWORD = "admin"

SECRET_KEY = "anothershit"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLES_DIR = os.path.join(BASE_DIR, "articles")

UPLOADS_DIR = os.path.join(BASE_DIR, "static", "uploads")