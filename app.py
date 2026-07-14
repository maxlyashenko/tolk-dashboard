import os, sqlite3, json, uuid
from datetime import datetime
from functools import wraps
from flask import (Flask, request, jsonify, render_template,
                   session, redirect, url_for, g)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Maxon")
DB_PATH      = os.environ.get("DB_PATH", "tolk.db")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "tolk2026")

# ─── DB ───────────────────────────────────────────────────────────────────────

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                year TEXT NOT NULL,
                month TEXT NOT NULL,
                name TEXT NOT NULL,
                svc TEXT NOT NULL,
                src TEXT NOT NULL,
                grn REAL NOT NULL DEFAULT 0,
                usd REAL NOT NULL DEFAULT 0,
                rate REAL NOT NULL DEFAULT 0,
                comm REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'paid',
                comment TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS months (
                key TEXT PRIMARY KEY,
                year TEXT NOT NULL,
                month TEXT NOT NULL,
                label TEXT NOT NULL,
                plan REAL NOT NULL DEFAULT 150000,
                partial INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                year TEXT NOT NULL,
                month TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                who TEXT NOT NULL DEFAULT 'me',
                amt REAL NOT NULL DEFAULT 0,
                comment TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS pipeline (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                value REAL NOT NULL DEFAULT 0,
                svc TEXT NOT NULL DEFAULT 'meta',
                stage TEXT NOT NULL DEFAULT 'new',
                src TEXT NOT NULL DEFAULT 'baza',
                mgr TEXT DEFAULT 'Макс',
                created_at INTEGER,
                updated_at INTEGER
            );
        """)
        db.commit()
        # Seed defaults if months table is empty
        if not db.execute("SELECT COUNT(*) FROM months").fetchone()[0]:
            _seed_defaults(db)

def _seed_defaults(db):
    months = [
        ("2025-09","2025","09","Вер '25",100000,0),
        ("2025-10","2025","10","Жов '25",100000,0),
        ("2025-11","2025","11","Лис '25",100000,0),
        ("2025-12","2025","12","Гру '25",100000,0),
        ("2026-01","2026","01","Січ '26",100000,0),
        ("2026-02","2026","02","Лют '26",150000,0),
        ("2026-03","2026","03","Бер '26",150000,0),
        ("2026-04","2026","04","Кві '26",150000,0),
        ("2026-05","2026","05","Тра '26",150000,0),
        ("2026-06","2026","06","Чер '26",150000,1),
    ]
    db.executemany(
        "INSERT OR IGNORE INTO months(key,year,month,label,plan,partial) VALUES(?,?,?,?,?,?)",
        months
    )
    pays = [
        ("h01","2025-09-25","2025","09","Hanert.com.ua","google","baza",20775,500,0.10,2078,"paid",""),
        ("h02","2025-10-01","2025","10","Вироби майстрів","meta_google","baza",29064,700,0.10,2906,"paid",""),
        ("h03","2025-10-17","2025","10","nezabuvay.com.ua","google","baza",16752,400,0.10,1675,"paid",""),
        ("h04","2025-10-17","2025","10","myfish.com.ua","google","baza",16776,400,0.10,1678,"paid",""),
        ("h05","2025-11-18","2025","11","58mile.com.ua","seo","baza",29554,700,0.10,2955,"paid","Без бюджету на посилання ($250)"),
        ("h06","2025-11-22","2025","11","Kleo","meta","baza",28000,0,0.10,2800,"paid","Meta+TikTok Ads"),
        ("h07","2025-11-26","2025","11","gsl.com.ua","google","baza",12744,300,0.10,1274,"paid",""),
        ("h08","2025-11-28","2025","11","dokamebel.com.ua","google","baza",17000,400,0.10,1700,"paid",""),
        ("h09","2025-12-22","2025","12","sanmarine.ua","smm","networking",25470,600,0.10,2547,"paid","Нетворкінг 6.12.25"),
        ("h10","2026-01-06","2026","01","vista-health.com.ua","smm","baza",46805,1100,0.50,23403,"paid","SMM+Meta"),
        ("h11","2026-01-20","2026","01","kodvody.com.ua","google","fb_viktor",45465,1050,0.50,22733,"paid","3 місяці Google Ads"),
        ("h12","2026-01-20","2026","01","keepcul.com","meta","ilia",17280,400,0.50,8640,"paid","Ілія — TikTok Ads"),
        ("h13","2026-02-26","2026","02","avtopan.ua","complex","baza",29968,700,0.20,5994,"part","50% оплата — Сайт+Google+Maps"),
        ("h14","2026-02-13","2026","02","clipnjoy.ca","meta","fb_viktor",13766,315,0.50,6883,"paid",""),
        ("h15","2026-02-20","2026","02","matras.kiev.ua","web","baza",1000,0,0.10,100,"paid","Завдання по сайту"),
        ("h16","2026-03-13","2026","03","hq.dp.ua","google","networking",17240,400,0.50,8620,"paid",""),
        ("h17","2026-03-15","2026","03","turhouse.com.ua","google","fb_viktor",21604,500,0.50,10802,"paid",""),
        ("h18","2026-03-20","2026","03","matras.kiev.ua (сайт)","web","baza",6732,154,0.10,673,"paid",""),
        ("h19","2026-03-28","2026","03","autoon.kiev.ua","complex","baza",30914,700,0.20,7176,"paid","Сайт+Google Ads+Maps"),
        ("h20","2026-04-13","2026","04","Bedoin","meta","networking",21950,500,0.50,10975,"paid",""),
        ("h21","2026-04-20","2026","04","Malva","meta_google","baza",54293,1080,0.50,27147,"paid","Google+Meta"),
        ("h22","2026-04-27","2026","04","Vegera (1-а оплата)","meta","baza",8700,200,0.50,4350,"part","2-а оплата в травні"),
        ("h23","2026-04-16","2026","04","repobona.com.ua","web","baza",13166,300,0.15,2015,"paid","20% від маржі"),
        ("h24","2026-04-21","2026","04","Tep.ua","meta","baza",19774,450,0.50,9887,"paid","В рахунку 21036 (6% ФОП)"),
        ("h25","2026-05-06","2026","05","Vegera (2-а оплата)","meta","baza",8700,200,0.50,4350,"paid",""),
        ("h26","2026-05-07","2026","05","Svitson.com.ua","google","biz_club",31376,600,0.50,15688,"paid",""),
        ("h27","2026-05-08","2026","05","Maxcryptobybit","tg","ilia",31376,600,0.45,14119,"paid","600 EUR / 702 USDT"),
        ("h28","2026-05-17","2026","05","blue chip","google","biz_club",20532,400,0.50,10266,"paid",""),
        ("h29","2026-05-21","2026","05","ektabud.pro","web","baza",35864,810,0.10,3586,"paid","З ПДВ 43037"),
        ("h30","2026-06-04","2026","06","Light Factory","meta","networking",17937,400,0.50,8969,"paid",""),
    ]
    db.executemany(
        "INSERT OR IGNORE INTO payments(id,date,year,month,name,svc,src,grn,usd,rate,comm,status,comment) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        pays
    )
    db.commit()

# ─── AUTH ─────────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "unauthorized"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == APP_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Невірний пароль"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ─── PAGES ────────────────────────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    return render_template("index.html")

# ─── API HELPERS ──────────────────────────────────────────────────────────────

def row2dict(row):
    return dict(row)

def rows2list(rows):
    return [dict(r) for r in rows]

# ─── PAYMENTS API ─────────────────────────────────────────────────────────────

@app.route("/api/pays", methods=["GET"])
@login_required
def get_pays():
    db = get_db()
    rows = db.execute("SELECT * FROM payments ORDER BY date DESC").fetchall()
    return jsonify(rows2list(rows))

@app.route("/api/pays", methods=["POST"])
@login_required
def create_pay():
    d = request.json
    if not d.get("name") or not d.get("grn"):
        return jsonify({"error": "name and grn required"}), 400
    pid = d.get("id") or str(uuid.uuid4())[:8]
    parts = d["date"].split("-")
    db = get_db()
    db.execute(
        "INSERT INTO payments(id,date,year,month,name,svc,src,grn,usd,rate,comm,status,comment) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (pid, d["date"], parts[0], parts[1], d["name"], d.get("svc","meta"),
         d.get("src","baza"), float(d.get("grn",0)), float(d.get("usd",0)),
         float(d.get("rate",0.5)), float(d.get("comm",0)),
         d.get("status","paid"), d.get("comment",""))
    )
    db.commit()
    row = db.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    return jsonify(row2dict(row)), 201

@app.route("/api/pays/<pid>", methods=["PUT"])
@login_required
def update_pay(pid):
    d = request.json
    parts = d["date"].split("-")
    db = get_db()
    db.execute(
        "UPDATE payments SET date=?,year=?,month=?,name=?,svc=?,src=?,grn=?,usd=?,rate=?,comm=?,status=?,comment=? WHERE id=?",
        (d["date"], parts[0], parts[1], d["name"], d.get("svc","meta"),
         d.get("src","baza"), float(d.get("grn",0)), float(d.get("usd",0)),
         float(d.get("rate",0.5)), float(d.get("comm",0)),
         d.get("status","paid"), d.get("comment",""), pid)
    )
    db.commit()
    row = db.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    return jsonify(row2dict(row))

@app.route("/api/pays/<pid>", methods=["DELETE"])
@login_required
def delete_pay(pid):
    db = get_db()
    db.execute("DELETE FROM payments WHERE id=?", (pid,))
    db.commit()
    return jsonify({"ok": True})

# ─── MONTHS API ───────────────────────────────────────────────────────────────

@app.route("/api/months", methods=["GET"])
@login_required
def get_months():
    db = get_db()
    rows = db.execute("SELECT * FROM months ORDER BY key").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["partial"] = bool(d["partial"])
        result.append(d)
    return jsonify(result)

@app.route("/api/months", methods=["POST"])
@login_required
def create_month():
    d = request.json
    key = d["key"]
    db = get_db()
    if db.execute("SELECT 1 FROM months WHERE key=?", (key,)).fetchone():
        return jsonify({"error": "month exists"}), 409
    db.execute(
        "INSERT INTO months(key,year,month,label,plan,partial) VALUES(?,?,?,?,?,?)",
        (key, d["year"], d["month"], d["label"], float(d.get("plan",150000)), 1 if d.get("partial") else 0)
    )
    db.commit()
    row = db.execute("SELECT * FROM months WHERE key=?", (key,)).fetchone()
    res = dict(row); res["partial"] = bool(res["partial"])
    return jsonify(res), 201

@app.route("/api/months/<key>", methods=["PUT"])
@login_required
def update_month(key):
    d = request.json
    db = get_db()
    db.execute(
        "UPDATE months SET label=?,plan=?,partial=? WHERE key=?",
        (d.get("label"), float(d.get("plan",150000)), 1 if d.get("partial") else 0, key)
    )
    db.commit()
    row = db.execute("SELECT * FROM months WHERE key=?", (key,)).fetchone()
    res = dict(row); res["partial"] = bool(res["partial"])
    return jsonify(res)

@app.route("/api/months/<key>", methods=["DELETE"])
@login_required
def delete_month(key):
    db = get_db()
    db.execute("DELETE FROM months WHERE key=?", (key,))
    db.commit()
    return jsonify({"ok": True})

# ─── EXPENSES API ─────────────────────────────────────────────────────────────

@app.route("/api/expenses", methods=["GET"])
@login_required
def get_expenses():
    db = get_db()
    rows = db.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()
    return jsonify(rows2list(rows))

@app.route("/api/expenses", methods=["POST"])
@login_required
def create_expense():
    d = request.json
    if not d.get("name") or not d.get("amt"):
        return jsonify({"error": "name and amt required"}), 400
    eid = d.get("id") or str(uuid.uuid4())[:8]
    parts = d["date"].split("-")
    db = get_db()
    db.execute(
        "INSERT INTO expenses(id,date,year,month,name,type,who,amt,comment) VALUES(?,?,?,?,?,?,?,?,?)",
        (eid, d["date"], parts[0], parts[1], d["name"],
         d.get("type","lead_fb"), d.get("who","me"),
         float(d.get("amt",0)), d.get("comment",""))
    )
    db.commit()
    row = db.execute("SELECT * FROM expenses WHERE id=?", (eid,)).fetchone()
    return jsonify(row2dict(row)), 201

@app.route("/api/expenses/<eid>", methods=["PUT"])
@login_required
def update_expense(eid):
    d = request.json
    parts = d["date"].split("-")
    db = get_db()
    db.execute(
        "UPDATE expenses SET date=?,year=?,month=?,name=?,type=?,who=?,amt=?,comment=? WHERE id=?",
        (d["date"], parts[0], parts[1], d["name"],
         d.get("type","lead_fb"), d.get("who","me"),
         float(d.get("amt",0)), d.get("comment",""), eid)
    )
    db.commit()
    row = db.execute("SELECT * FROM expenses WHERE id=?", (eid,)).fetchone()
    return jsonify(row2dict(row))

@app.route("/api/expenses/<eid>", methods=["DELETE"])
@login_required
def delete_expense(eid):
    db = get_db()
    db.execute("DELETE FROM expenses WHERE id=?", (eid,))
    db.commit()
    return jsonify({"ok": True})

# ─── PIPELINE API ─────────────────────────────────────────────────────────────

@app.route("/api/pipeline", methods=["GET"])
@login_required
def get_pipeline():
    db = get_db()
    rows = db.execute("SELECT * FROM pipeline ORDER BY updated_at DESC").fetchall()
    return jsonify(rows2list(rows))

@app.route("/api/pipeline", methods=["POST"])
@login_required
def create_pipeline():
    d = request.json
    if not d.get("name"):
        return jsonify({"error": "name required"}), 400
    did = d.get("id") or str(uuid.uuid4())[:8]
    now = int(datetime.now().timestamp() * 1000)
    db = get_db()
    db.execute(
        "INSERT INTO pipeline(id,name,value,svc,stage,src,mgr,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (did, d["name"], float(d.get("value",0)), d.get("svc","meta"),
         d.get("stage","new"), d.get("src","baza"), d.get("mgr","Макс"), now, now)
    )
    db.commit()
    row = db.execute("SELECT * FROM pipeline WHERE id=?", (did,)).fetchone()
    return jsonify(row2dict(row)), 201

@app.route("/api/pipeline/<did>", methods=["PUT"])
@login_required
def update_pipeline(did):
    d = request.json
    now = int(datetime.now().timestamp() * 1000)
    db = get_db()
    db.execute(
        "UPDATE pipeline SET name=?,value=?,svc=?,stage=?,src=?,mgr=?,updated_at=? WHERE id=?",
        (d["name"], float(d.get("value",0)), d.get("svc","meta"),
         d.get("stage","new"), d.get("src","baza"), d.get("mgr","Макс"), now, did)
    )
    db.commit()
    row = db.execute("SELECT * FROM pipeline WHERE id=?", (did,)).fetchone()
    return jsonify(row2dict(row))

@app.route("/api/pipeline/<did>", methods=["DELETE"])
@login_required
def delete_pipeline(did):
    db = get_db()
    db.execute("DELETE FROM pipeline WHERE id=?", (did,))
    db.commit()
    return jsonify({"ok": True})

# ─── RESET API ────────────────────────────────────────────────────────────────

@app.route("/api/reset", methods=["POST"])
@login_required
def reset_data():
    db = get_db()
    db.executescript("DELETE FROM payments; DELETE FROM months; DELETE FROM expenses; DELETE FROM pipeline;")
    _seed_defaults(db)
    return jsonify({"ok": True})

# ─── RUN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
