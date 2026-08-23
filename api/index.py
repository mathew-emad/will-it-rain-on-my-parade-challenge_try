import sys
import os

# إضافة المجلد الرئيسي للـ path عشان يقدر يقرأ من مجلد backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app_moment import app
