from backend.app_moment import app
from a2wsgi import ASGIMiddleware

# تحويل تطبيق FastAPI ليعمل على Vercel Serverless Functions
app = ASGIMiddleware(app)