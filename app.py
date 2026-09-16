from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "tekin_almaz_super_secret_key"

# Admin Telegram ID (O'zingizning Telegram ID raqamingizni shu yerga yozing)
ADMIN_ID = 7849637859  # Misol uchun, o'zgartirishingiz mumkin

# Bazani sozlash
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            amount INTEGER,
            wallet TEXT,
            status TEXT DEFAULT 'Bajarildi',
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, admin_id=ADMIN_ID)

@app.route('/api/get_user', methods=['POST'])
def get_user():
    data = request.json
    user_id = data.get('user_id', 7849637859)
    username = data.get('username', 'foydalanuvchi')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance, referrals FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('INSERT INTO users (user_id, username, balance, referrals) VALUES (?, ?, 10, 0)', (user_id, username))
        conn.commit()
        balance, referrals = 10, 0
    else:
        balance, referrals = user
        
    # Tarixni olish
    cursor.execute('SELECT username, amount, wallet, date FROM withdrawals ORDER BY id DESC LIMIT 10')
    history = cursor.fetchall()
    conn.close()
    
    is_admin = (user_id == ADMIN_ID)
    
    return {
        "balance": balance,
        "referrals": referrals,
        "is_admin": is_admin,
        "history": [{"username": h[0], "amount": h[1], "wallet": h[2], "date": h[3]} for h in history]
    }

@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    user_id = data.get('user_id')
    amount = int(data.get('amount', 0))
    wallet = data.get('wallet')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance, username FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user or user[0] < amount or amount < 50:
        conn.close()
        return {"success": False, "message": "Balans yetarli emas yoki minimal miqdor 50 ta almaz!"}
        
    new_balance = user[0] - amount
    cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
    cursor.execute('INSERT INTO withdrawals (username, amount, wallet) VALUES (?, ?, ?)', (user[1], amount, wallet))
    conn.commit()
    conn.close()
    
    return {"success": True, "new_balance": new_balance, "message": "Muvaffaqiyatli ariza berildi!"}

@app.route('/api/admin/action', methods=['POST'])
def admin_action():
    data = request.json
    admin_id = data.get('admin_id')
    if admin_id != ADMIN_ID:
        return {"success": False, "message": "Ruxsat etilmagan!"}
        
    action = data.get('action')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if action == 'set_balance':
        target_user = data.get('username')
        amount = int(data.get('amount', 0))
        cursor.execute('UPDATE users SET balance = balance + ? WHERE username = ? OR user_id = ?', (amount, target_user, target_user))
        conn.commit()
    
    conn.close()
    return {"success": True, "message": "Admin amal bajarildi!"}

# HTML Template (Dahshatli Cyber-Glassmorphism Dizayn)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tekin Almaz UZ - Mini App</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: #030712;
            color: #ffffff;
            overflow-x: hidden;
        }
        .cyber-box {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 58, 138, 0.3) 100%);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(59, 130, 246, 0.3);
            box-shadow: 0 0 30px rgba(37, 99, 235, 0.15);
        }
        .cyber-btn {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            box-shadow: 0 0 25px rgba(59, 130, 246, 0.5);
            transition: all 0.3s ease;
        }
        .cyber-btn:active { transform: scale(0.97); }
        .bg-glow {
            position: fixed;
            width: 300px; height: 300px;
            background: radial-gradient(circle, rgba(37,99,235,0.2) 0%, transparent 70%);
            top: -100px; left: -100px; z-index: -1;
        }
    </style>
</head>
<body class="min-h-screen flex flex-col justify-between pb-24">
    <div class="bg-glow"></div>

    <!-- MAJBURIY OBUNA MODALI -->
    <div id="sub-modal" class="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 hidden">
        <div class="cyber-box p-6 rounded-3xl max-w-sm w-full text-center space-y-4">
            <div class="w-16 h-16 mx-auto bg-blue-600/20 border border-blue-500 rounded-2xl flex items-center justify-center text-3xl animate-bounce">
                📢
            </div>
            <h3 class="text-lg font-extrabold text-white">Majburiy Obuna</h3>
            <p class="text-xs text-slate-300">Botdan to'liq foydalanish uchun homiy kanallarga obuna bo'ling!</p>
            <div class="space-y-2">
                <a href="https://t.me/Tekkin_olmos_bot" target="_blank" class="block w-full py-3 bg-slate-900 border border-blue-500/40 rounded-xl text-xs font-bold text-blue-400">1-Kanalga Obuna Bo'lish</a>
            </div>
            <button onclick="checkSubscription()" class="cyber-btn w-full py-3 rounded-xl font-bold text-white text-sm">A'zo bo'ldim ✅</button>
        </div>
    </div>

    <!-- HEADER -->
    <header class="p-4 flex items-center justify-between border-b border-blue-900/40 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/50 flex items-center justify-center text-lg shadow-inner">💎</div>
            <div>
                <h1 class="text-xs font-extrabold text-blue-400 tracking-wider">TEKIN ALMAZ</h1>
                <p class="text-[11px] text-slate-400" id="username-display">@foydalanuvchi</p>
            </div>
        </div>
        <div class="cyber-box px-3.5 py-1.5 rounded-full flex items-center space-x-2">
            <span class="text-blue-400">💎</span>
            <span class="font-extrabold text-sm text-white" id="balance-display">0</span>
            <span class="text-[10px] text-slate-400">Almaz</span>
        </div>
    </header>

    <!-- MAIN VIEWS -->
    <main class="flex-1 max-w-md w-full mx-auto p-4 space-y-5">
        
        <!-- HOME TAB -->
        <div id="tab-home" class="space-y-5">
            <div class="cyber-box rounded-3xl p-6 text-center relative overflow-hidden">
                <div class="w-16 h-16 mx-auto mb-3 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-3xl shadow-lg shadow-blue-500/30 animate-pulse">💎</div>
                <h2 class="text-xl font-extrabold text-white mb-1">Bepul Almazlar Yig'ing!</h2>
                <p class="text-xs text-slate-300 mb-5 leading-relaxed">Do'stlaringizni taklif qiling va har bir taklif uchun <span class="text-blue-400 font-bold">+10 Almaz</span> oling!</p>
                <button onclick="shareLink()" class="cyber-btn w-full py-3.5 rounded-2xl font-bold text-white flex items-center justify-center space-x-2">
                    <i class="fa-solid fa-share-nodes"></i>
                    <span>Do'stlarga Ulashish</span>
                </button>
            </div>

            <div class="grid grid-cols-2 gap-3">
                <div class="cyber-box p-4 rounded-2xl flex flex-col justify-between">
                    <div class="text-slate-400 text-xs font-medium mb-2 flex items-center justify-between">
                        <span>Takliflar</span>
                        <i class="fa-solid fa-users text-blue-400"></i>
                    </div>
                    <div class="text-2xl font-extrabold text-white" id="referral-count">0 <span class="text-xs font-normal text-slate-400">ta</span></div>
                </div>
                <div class="cyber-box p-4 rounded-2xl flex flex-col justify-between">
                    <div class="text-slate-400 text-xs font-medium mb-2 flex items-center justify-between">
                        <span>Status</span>
                        <i class="fa-solid fa-shield-halved text-emerald-400"></i>
                    </div>
                    <div class="text-sm font-bold text-emerald-400 mt-1">Faol 🚀</div>
                </div>
            </div>

            <div class="cyber-box p-4 rounded-2xl space-y-2">
                <label class="text-xs font-semibold text-slate-300 block">Sizning taklif havolangiz:</label>
                <div class="flex items-center space-x-2 bg-slate-900/80 border border-slate-800 rounded-xl p-2">
                    <input type="text" id="ref-link" readonly value="https://t.me/Tekkin_olmos_bot?start=7849637859" class="bg-transparent text-xs text-slate-300 w-full outline-none px-1">
                    <button onclick="copyLink()" class="bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded-lg text-xs font-bold transition">
                        <i class="fa-regular fa-copy"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- WITHDRAW TAB -->
        <div id="tab-withdraw" class="space-y-4 hidden">
            <div class="cyber-box p-6 rounded-3xl space-y-4">
                <h3 class="text-base font-extrabold text-white flex items-center space-x-2">
                    <i class="fa-solid fa-gem text-blue-400"></i>
                    <span>Almaz Yechish Shartlari</span>
                </h3>
                <p class="text-xs text-slate-300 leading-relaxed">
                    Balansingizdagi olmoslarni o'yin hisobingizga (Free Fire / PUBG) yoki kartaga yechib oling. Minimal yechish miqdori: <span class="text-blue-400 font-bold">50 ta almaz</span>.
                </p>
                <div class="space-y-3 pt-2">
                    <div>
                        <label class="text-[11px] font-semibold text-slate-400 block mb-1">Miqdor (Almaz):</label>
                        <input type="number" id="withdraw-amount" placeholder="Masalan: 50" class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none focus:border-blue-500">
                    </div>
                    <div>
                        <label class="text-[11px] font-semibold text-slate-400 block mb-1">ID yoki Hamyon raqami:</label>
                        <input type="text" id="withdraw-wallet" placeholder="Free Fire ID / Payeer / Click" class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none focus:border-blue-500">
                    </div>
                    <button onclick="requestWithdraw()" class="cyber-btn w-full py-3.5 rounded-xl font-bold text-white text-xs mt-2">Ariza Berish 🚀</button>
                </div>
            </div>
        </div>

        <!-- HISTORY TAB -->
        <div id="tab-history" class="space-y-3 hidden">
            <h3 class="text-sm font-extrabold text-white mb-2 flex items-center space-x-2">
                <i class="fa-solid fa-clock-rotate-left text-blue-400"></i>
                <span>Oxirgi yechib olingan almazlar</span>
            </h3>
            <div id="history-list" class="space-y-2">
                <!-- Dinamik to'ldiriladi -->
            </div>
        </div>

        <!-- SUPPORT TAB -->
        <div id="tab-support" class="space-y-4 hidden">
            <div class="cyber-box p-6 rounded-3xl text-center space-y-4">
                <div class="w-16 h-16 mx-auto bg-blue-600/20 border border-blue-500/40 rounded-2xl flex items-center justify-center text-3xl">🎧</div>
                <h3 class="text-base font-extrabold text-white">Yordam va Murojaat</h3>
                <p class="text-xs text-slate-300">Savollar yoki muammolar bo'yicha to'g'ridan-to'g'ri administratorga murojaat qiling:</p>
                <a href="https://t.me/ruzvix" target="_blank" class="cyber-btn block w-full py-3.5 rounded-2xl font-bold text-white text-sm">
                    Admin: @ruzvix 💬
                </a>
            </div>
        </div>

        <!-- ADMIN PANEL TAB -->
        <div id="tab-admin" class="space-y-4 hidden">
            <div class="cyber-box p-6 rounded-3xl space-y-4 border-amber-500/40">
                <h3 class="text-base font-extrabold text-amber-400 flex items-center space-x-2">
                    <i class="fa-solid fa-shield-halved"></i>
                    <span>Admin Boshqaruv Paneli</span>
                </h3>
                <div class="space-y-3">
                    <div>
                        <label class="text-[11px] font-semibold text-slate-400 block mb-1">Foydalanuvchi Username yoki ID:</label>
                        <input type="text" id="admin-target" placeholder="@username yoki ID" class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none focus:border-amber-500">
                    </div>
                    <div>
                        <label class="text-[11px] font-semibold text-slate-400 block mb-1">Qo'shish / Ayirish miqdori (+ yoki -):</label>
                        <input type="number" id="admin-amount" placeholder="Masalan: 100 yoki -50" class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none focus:border-amber-500">
                    </div>
                    <button onclick="adminSetBalance()" class="w-full py-3.5 bg-amber-600 hover:bg-amber-500 text-white rounded-xl font-bold text-xs transition shadow-lg shadow-amber-600/30">Balansni O'zgartirish ⚡</button>
                </div>
            </div>
        </div>

    </main>

    <!-- BOTTOM NAV -->
    <nav class="fixed bottom-0 left-0 right-0 bg-slate-950/90 backdrop-blur-lg border-t border-blue-900/40 p-2 z-40">
        <div class="max-w-md mx-auto grid grid-cols-5 gap-1 text-center" id="nav-bar-container">
            <button onclick="switchTab('home')" id="nav-home" class="py-2 rounded-xl text-blue-400 flex flex-col items-center transition">
                <i class="fa-solid fa-house text-base mb-0.5"></i>
                <span class="text-[9px] font-medium">Asosiy</span>
            </button>
            <button onclick="switchTab('withdraw')" id="nav-withdraw" class="py-2 rounded-xl text-slate-400 flex flex-col items-center transition">
                <i class="fa-solid fa-gem text-base mb-0.5"></i>
                <span class="text-[9px] font-medium">Yechish</span>
            </button>
            <button onclick="switchTab('history')" id="nav-history" class="py-2 rounded-xl text-slate-400 flex flex-col items-center transition">
                <i class="fa-solid fa-clock-rotate-left text-base mb-0.5"></i>
                <span class="text-[9px] font-medium">Tarix</span>
            </button>
            <button onclick="switchTab('support')" id="nav-support" class="py-2 rounded-xl text-slate-400 flex flex-col items-center transition">
                <i class="fa-solid fa-headset text-base mb-0.5"></i>
                <span class="text-[9px] font-medium">Murojaat</span>
            </button>
            <!-- Admin tugma dinamik qo'shiladi -->
        </div>
    </nav>

    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();

        let userData = {
            user_id: 7849637859,
            username: "foydalanuvchi"
        };

        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            userData.user_id = tg.initDataUnsafe.user.id;
            userData.username = tg.initDataUnsafe.user.username || tg.initDataUnsafe.user.first_name;
        }

        document.getElementById('username-display').innerText = '@' + userData.username;
        document.getElementById('ref-link').value = `https://t.me/Tekkin_olmos_bot?start=${userData.user_id}`;

        let isAdmin = false;

        function loadUserData() {
            fetch('/api/get_user', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(userData)
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('balance-display').innerText = data.balance;
                document.getElementById('referral-count').innerText = data.referrals + " ta";
                isAdmin = data.is_admin;

                if (isAdmin) {
                    let navContainer = document.getElementById('nav-bar-container');
                    if (!document.getElementById('nav-admin')) {
                        let btn = document.createElement('button');
                        btn.id = 'nav-admin';
                        btn.className = 'py-2 rounded-xl text-amber-400 flex flex-col items-center transition';
                        btn.onclick = () => switchTab('admin');
                        btn.innerHTML = `<i class="fa-solid fa-shield-halved text-base mb-0.5"></i><span class="text-[9px] font-medium">Admin</span>`;
                        navContainer.appendChild(btn);
                    }
                }

                let historyHTML = '';
                if(data.history.length === 0) {
                    historyHTML = '<div class="cyber-box p-4 rounded-2xl text-center text-xs text-slate-400">Hozircha tranzaksiyalar yo\'q.</div>';
                } else {
                    data.history.forEach(item => {
                        historyHTML += `
                            <div class="cyber-box p-3 rounded-2xl flex items-center justify-between text-xs">
                                <div>
                                    <span class="font-bold text-white">@${item.username}</span>
                                    <div class="text-[10px] text-slate-400">Hamyon: ${item.wallet}</div>
                                </div>
                                <div class="text-right">
                                    <span class="font-extrabold text-blue-400">-${item.amount} 💎</span>
                                    <div class="text-[9px] text-emerald-400">${item.status}</div>
                                </div>
                            </div>
                        `;
                    });
                }
                document.getElementById('history-list').innerHTML = historyHTML;
            });
        }

        loadUserData();

        function switchTab(tabName) {
            tg.HapticFeedback.impactOccurred('light');
            ['home', 'withdraw', 'history', 'support', 'admin'].forEach(t => {
                let el = document.getElementById('tab-' + t);
                if(el) el.classList.add('hidden');
                let nav = document.getElementById('nav-' + t);
                if(nav) nav.className = 'py-2 rounded-xl text-slate-400 flex flex-col items-center transition';
            });
            document.getElementById('tab-' + tabName).classList.remove('hidden');
            let activeNav = document.getElementById('nav-' + tabName);
            if(activeNav) {
                activeNav.className = tabName === 'admin' 
                    ? 'py-2 rounded-xl text-amber-400 flex flex-col items-center transition' 
                    : 'py-2 rounded-xl text-blue-400 flex flex-col items-center transition';
            }
        }

        function copyLink() {
            let copyText = document.getElementById("ref-link");
            copyText.select();
            navigator.clipboard.writeText(copyText.value);
            tg.showAlert("Havola nusxalandi! Do'stlaringizga yuboring.");
        }

        function shareLink() {
            let text = encodeURIComponent("💎 Tekin Almaz yig'ish va o'yinlarga bepul almoslar olish uchun ushbu botga kiring!");
            window.open(`https://t.me/share/url?url=${encodeURIComponent(document.getElementById("ref-link").value)}&text=${text}`, '_blank');
        }

        function requestWithdraw() {
            let amount = document.getElementById('withdraw-amount').value;
            let wallet = document.getElementById('withdraw-wallet').value;
            if(!amount || !wallet) {
                tg.showAlert("Barcha maydonlarni to'ldiring!");
                return;
            }
            fetch('/api/withdraw', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_id: userData.user_id, amount: parseInt(amount), wallet: wallet})
            })
            .then(res => res.json())
            .then(data => {
                tg.showAlert(data.message);
                if(data.success) {
                    document.getElementById('withdraw-amount').value = '';
                    document.getElementById('withdraw-wallet').value = '';
                    loadUserData();
                    switchTab('history');
                }
            });
        }

        function adminSetBalance() {
            let target = document.getElementById('admin-target').value;
            let amount = document.getElementById('admin-amount').value;
            if(!target || !amount) {
                alert("Ma'lumotlarni kiriting!");
                return;
            }
            fetch('/api/admin/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({admin_id: userData.user_id, action: 'set_balance', username: target, amount: parseInt(amount)})
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                loadUserData();
            });
        }

        function checkSubscription() {
            document.getElementById('sub-modal').classList.add('hidden');
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
