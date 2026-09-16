from flask import Flask, render_template_string, request
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "tekin_almaz_super_secret_key"

ADMIN_ID = 7849637859  # Sizning Telegram ID'ingiz

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 10,
            referrals INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
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
    user_id = data.get('user_id')
    username = data.get('username', 'foydalanuvchi')
    
    if not user_id:
        return {"balance": 0, "referrals": 0, "is_admin": False, "history": []}
    
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
        
    cursor.execute('SELECT username, amount, wallet, status, date FROM withdrawals ORDER BY id DESC LIMIT 20')
    history = cursor.fetchall()
    conn.close()
    
    is_admin = (int(user_id) == ADMIN_ID)
    
    return {
        "balance": balance,
        "referrals": referrals,
        "is_admin": is_admin,
        "history": [{"username": h[0], "amount": h[1], "wallet": h[2], "status": h[3], "date": h[4]} for h in history]
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
    cursor.execute('INSERT INTO withdrawals (user_id, username, amount, wallet) VALUES (?, ?, ?, ?)', (user_id, user[1], amount, wallet))
    conn.commit()
    conn.close()
    
    return {"success": True, "new_balance": new_balance, "message": "Ariza muvaffaqiyatli qabul qilindi!"}

@app.route('/api/admin/action', methods=['POST'])
def admin_action():
    data = request.json
    admin_id = int(data.get('admin_id', 0))
    if admin_id != ADMIN_ID:
        return {"success": False, "message": "Ruxsat etilmagan!"}
        
    target = data.get('username')
    amount = int(data.get('amount', 0))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE username = ? OR user_id = ?', (amount, target, target))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Balans muvaffaqiyatli o'zgartirildi!"}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tekin Almaz UZ</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: #030712; color: #ffffff; overflow-x: hidden; }
        .cyber-box { background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 58, 138, 0.4) 100%); backdrop-filter: blur(20px); border: 1px solid rgba(59, 130, 246, 0.3); }
        .cyber-btn { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); transition: all 0.3s ease; }
        .cyber-btn:active { transform: scale(0.97); }
    </style>
</head>
<body class="min-h-screen flex flex-col justify-between pb-24">

    <!-- HEADER -->
    <header class="p-4 flex items-center justify-between border-b border-blue-900/40 bg-slate-950/80 sticky top-0 z-40">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/50 flex items-center justify-center text-lg">💎</div>
            <div>
                <h1 class="text-xs font-extrabold text-blue-400">TEKIN ALMAZ</h1>
                <p class="text-[11px] text-slate-400" id="username-display">@foydalanuvchi</p>
            </div>
        </div>
        <div class="cyber-box px-3.5 py-1.5 rounded-full flex items-center space-x-2">
            <span class="text-blue-400">💎</span>
            <span class="font-extrabold text-sm text-white" id="balance-display">0</span>
            <span class="text-[10px] text-slate-400">Almaz</span>
        </div>
    </header>

    <!-- CONTENT -->
    <main class="flex-1 max-w-md w-full mx-auto p-4 space-y-5">
        
        <!-- HOME TAB -->
        <div id="tab-home" class="space-y-5">
            <div class="cyber-box rounded-3xl p-6 text-center">
                <div class="w-16 h-16 mx-auto mb-3 rounded-2xl bg-blue-600 flex items-center justify-center text-3xl shadow-lg shadow-blue-500/30">💎</div>
                <h2 class="text-xl font-extrabold text-white mb-1">Bepul Almazlar Yig'ing!</h2>
                <p class="text-xs text-slate-300 mb-5">Do'stlaringizni taklif qiling va har bir taklif uchun <span class="text-blue-400 font-bold">+10 Almaz</span> oling!</p>
                <button onclick="shareLink()" class="cyber-btn w-full py-3.5 rounded-2xl font-bold text-white flex items-center justify-center space-x-2">
                    <i class="fa-solid fa-share-nodes"></i>
                    <span>Do'stlarga Ulashish</span>
                </button>
            </div>

            <div class="grid grid-cols-2 gap-3">
                <div class="cyber-box p-4 rounded-2xl">
                    <div class="text-slate-400 text-xs mb-2 flex justify-between"><span>Takliflar</span><i class="fa-solid fa-users text-blue-400"></i></div>
                    <div class="text-2xl font-extrabold text-white" id="referral-count">0 ta</div>
                </div>
                <div class="cyber-box p-4 rounded-2xl">
                    <div class="text-slate-400 text-xs mb-2 flex justify-between"><span>Status</span><i class="fa-solid fa-shield-halved text-emerald-400"></i></div>
                    <div class="text-sm font-bold text-emerald-400 mt-1">Faol 🚀</div>
                </div>
            </div>

            <div class="cyber-box p-4 rounded-2xl space-y-2">
                <label class="text-xs font-semibold text-slate-300 block">Sizning taklif havolangiz:</label>
                <div class="flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-xl p-2">
                    <input type="text" id="ref-link" readonly class="bg-transparent text-xs text-slate-300 w-full outline-none px-1">
                    <button onclick="copyLink()" class="bg-blue-600 text-white px-3 py-2 rounded-lg text-xs font-bold"><i class="fa-regular fa-copy"></i></button>
                </div>
            </div>
        </div>

        <!-- WITHDRAW TAB -->
        <div id="tab-withdraw" class="space-y-4 hidden">
            <div class="cyber-box p-6 rounded-3xl space-y-4">
                <h3 class="text-base font-extrabold text-white flex items-center space-x-2">
                    <i class="fa-solid fa-gem text-blue-400"></i><span>Almaz Yechish</span>
                </h3>
                <p class="text-xs text-slate-300">Minimal yechish miqdori: <span class="text-blue-400 font-bold">50 ta almaz</span>.</p>
                <div class="bg-slate-900/60 p-3 rounded-xl border border-blue-500/20 text-xs">
                    <div>Sizning balansingiz: <span id="withdraw-user-bal" class="font-bold text-blue-400">0</span> 💎</div>
                </div>
                <div class="space-y-3">
                    <input type="number" id="withdraw-amount" placeholder="Miqdor (Masalan: 50)" class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none">
                    <input type="text" id="withdraw-wallet" placeholder="Free Fire ID / Hamyon raqami" class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none">
                    <button onclick="requestWithdraw()" class="cyber-btn w-full py-3.5 rounded-xl font-bold text-white text-xs">Ariza Berish 🚀</button>
                </div>
            </div>
        </div>

        <!-- HISTORY TAB -->
        <div id="tab-history" class="space-y-3 hidden">
            <h3 class="text-sm font-extrabold text-white mb-2"><i class="fa-solid fa-clock-rotate-left text-blue-400"></i> Tarix</h3>
            <div id="history-list" class="space-y-2"></div>
        </div>

        <!-- SUPPORT TAB -->
        <div id="tab-support" class="space-y-4 hidden">
            <div class="cyber-box p-6 rounded-3xl text-center space-y-4">
                <div class="w-16 h-16 mx-auto bg-blue-600/20 rounded-2xl flex items-center justify-center text-3xl">🎧</div>
                <h3 class="text-base font-extrabold text-white">Yordam</h3>
                <a href="https://t.me/ruzvix" target="_blank" class="cyber-btn block w-full py-3.5 rounded-2xl font-bold text-white text-sm">Admin: @ruzvix 💬</a>
            </div>
        </div>

        <!-- ADMIN TAB -->
        <div id="tab-admin" class="space-y-4 hidden">
            <div class="cyber-box p-6 rounded-3xl space-y-4 border-amber-500/40">
                <h3 class="text-base font-extrabold text-amber-400"><i class="fa-solid fa-shield-halved"></i> Admin Panel</h3>
                <input type="text" id="admin-target" placeholder="Username yoki ID" class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none">
                <input type="number" id="admin-amount" placeholder="Miqdor (+ yoki -)" class="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white outline-none">
                <button onclick="adminSetBalance()" class="w-full py-3.5 bg-amber-600 text-white rounded-xl font-bold text-xs">O'zgartirish ⚡</button>
            </div>
        </div>

    </main>

    <!-- BOTTOM NAV -->
    <nav class="fixed bottom-0 left-0 right-0 bg-slate-950/90 border-t border-blue-900/40 p-2 z-40">
        <div class="max-w-md mx-auto grid grid-cols-4 gap-1 text-center" id="nav-bar-container">
            <button onclick="switchTab('home')" id="nav-home" class="py-2 rounded-xl text-blue-400 flex flex-col items-center">
                <i class="fa-solid fa-house text-base mb-0.5"></i><span class="text-[9px]">Asosiy</span>
            </button>
            <button onclick="switchTab('withdraw')" id="nav-withdraw" class="py-2 rounded-xl text-slate-400 flex flex-col items-center">
                <i class="fa-solid fa-gem text-base mb-0.5"></i><span class="text-[9px]">Yechish</span>
            </button>
            <button onclick="switchTab('history')" id="nav-history" class="py-2 rounded-xl text-slate-400 flex flex-col items-center">
                <i class="fa-solid fa-clock-rotate-left text-base mb-0.5"></i><span class="text-[9px]">Tarix</span>
            </button>
            <button onclick="switchTab('support')" id="nav-support" class="py-2 rounded-xl text-slate-400 flex flex-col items-center">
                <i class="fa-solid fa-headset text-base mb-0.5"></i><span class="text-[9px]">Murojaat</span>
            </button>
        </div>
    </nav>

    <script>
        let tg = window.Telegram.WebApp;
        try { tg.expand(); } catch(e){}

        let userData = { user_id: 7849637859, username: "ruzvix" };
        if (tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.id) {
            userData.user_id = tg.initDataUnsafe.user.id;
            userData.username = tg.initDataUnsafe.user.username || tg.initDataUnsafe.user.first_name;
        }

        document.getElementById('username-display').innerText = '@' + userData.username;
        document.getElementById('ref-link').value = `https://t.me/Tekkin_olmos_bot?start=${userData.user_id}`;

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
                document.getElementById('withdraw-user-bal').innerText = data.balance;

                if (data.is_admin) {
                    let navContainer = document.getElementById('nav-bar-container');
                    navContainer.className = "max-w-md mx-auto grid grid-cols-5 gap-1 text-center";
                    if (!document.getElementById('nav-admin')) {
                        let btn = document.createElement('button');
                        btn.id = 'nav-admin';
                        btn.className = 'py-2 rounded-xl text-slate-400 flex flex-col items-center';
                        btn.onclick = () => switchTab('admin');
                        btn.innerHTML = `<i class="fa-solid fa-shield-halved text-base mb-0.5"></i><span class="text-[9px]">Admin</span>`;
                        navContainer.appendChild(btn);
                    }
                }

                let historyHTML = '';
                if(data.history.length === 0) {
                    historyHTML = '<div class="cyber-box p-4 rounded-2xl text-center text-xs text-slate-400">Tranzaksiyalar yo\'q.</div>';
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
            ['home', 'withdraw', 'history', 'support', 'admin'].forEach(t => {
                let el = document.getElementById('tab-' + t);
                if(el) el.classList.add('hidden');
                let nav = document.getElementById('nav-' + t);
                if(nav) nav.className = 'py-2 rounded-xl text-slate-400 flex flex-col items-center';
            });
            
            let targetTab = document.getElementById('tab-' + tabName);
            if(targetTab) targetTab.classList.remove('hidden');
            
            let activeNav = document.getElementById('nav-' + tabName);
            if(activeNav) {
                activeNav.className = tabName === 'admin' 
                    ? 'py-2 rounded-xl text-amber-400 flex flex-col items-center' 
                    : 'py-2 rounded-xl text-blue-400 flex flex-col items-center';
            }
        }

        function copyLink() {
            let copyText = document.getElementById("ref-link");
            copyText.select();
            navigator.clipboard.writeText(copyText.value);
            alert("Havola nusxalandi!");
        }

        function shareLink() {
            let text = encodeURIComponent("💎 Tekin Almaz yig'ish uchun botga kiring!");
            window.open(`https://t.me/share/url?url=${encodeURIComponent(document.getElementById("ref-link").value)}&text=${text}`, '_blank');
        }

        function requestWithdraw() {
            let amount = document.getElementById('withdraw-amount').value;
            let wallet = document.getElementById('withdraw-wallet').value;
            if(!amount || !wallet) { alert("Maydonlarni to'ldiring!"); return; }
            
            fetch('/api/withdraw', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_id: userData.user_id, amount: parseInt(amount), wallet: wallet})
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
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
            if(!target || !amount) { alert("Ma'lumotlarni kiriting!"); return; }
            
            fetch('/api/admin/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({admin_id: userData.user_id, username: target, amount: parseInt(amount)})
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                loadUserData();
            });
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
