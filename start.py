"""
Запуск локально: python start.py
Откроется на http://localhost:5000
Пароль по умолчанию: tolk2026
"""
from app import app, init_db

if __name__ == "__main__":
    init_db()
    print("=" * 50)
    print("  Tolk Dashboard запущено!")
    print("  Открой: http://localhost:5000")
    print("  Пароль: tolk2026")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5000, debug=True)
