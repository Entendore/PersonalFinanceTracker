#!/usr/bin/env python3
"""Personal Finance Tracker Pro — PySide6 + Matplotlib + SQLite + Financial Math + Live Currency"""

import sys, sqlite3, json, math
from datetime import datetime
from collections import defaultdict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QHeaderView, QFrame,
    QStackedWidget, QDoubleSpinBox, QMessageBox, QAbstractItemView,
    QSizePolicy, QGridLayout, QScrollArea, QMenu, QProgressBar,
    QFileDialog, QDialogButtonBox, QSpinBox, QInputDialog
)
from PySide6.QtCore import Qt, QDate, Signal, QUrl, QSize
from PySide6.QtGui import QFont, QColor, QCursor, QIcon, QAction
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# ── Theme & Constants ────────────────────────────────────────────────────────

THEMES = {
    "light": {
        "PRIMARY": "#2563EB", "INCOME": "#10B981", "EXPENSE": "#EF4444",
        "BALANCE": "#8B5CF6", "BG": "#F1F5F9", "CARD": "#FFFFFF",
        "SIDEBAR_BG": "#1E293B", "SIDEBAR_HOV": "#334155", "SIDEBAR_ACT": "#3B82F6",
        "TEXT": "#1E293B", "MUTED": "#64748B", "BORDER": "#E2E8F0",
        "INPUT_BG": "#FFFFFF", "CHART_BG": "#FFFFFF", "PROGRESS_BG": "#E2E8F0",
    },
    "dark": {
        "PRIMARY": "#60A5FA", "INCOME": "#34D399", "EXPENSE": "#F87171",
        "BALANCE": "#C4B5FD", "BG": "#0B0F19", "CARD": "#141A2A",
        "SIDEBAR_BG": "#0B0F19", "SIDEBAR_HOV": "#1A2035", "SIDEBAR_ACT": "#3B82F6",
        "TEXT": "#E2E8F0", "MUTED": "#7B8BA5", "BORDER": "#1E2840",
        "INPUT_BG": "#0F1628", "CHART_BG": "#141A2A", "PROGRESS_BG": "#1E2840",
    }
}

EXPENSE_CATEGORIES = [
    "Food & Dining", "Transportation", "Housing & Rent", "Utilities",
    "Entertainment", "Shopping", "Health & Fitness", "Education",
    "Travel", "Insurance", "Subscriptions", "Other Expense"
]
INCOME_CATEGORIES = [
    "Salary", "Freelance", "Investment", "Business",
    "Rental Income", "Gifts", "Refunds", "Other Income"
]
CHART_COLORS = [
    "#60A5FA", "#34D399", "#FBBF24", "#F87171", "#A78BFA", "#F472B6",
    "#22D3EE", "#FB923C", "#818CF8", "#2DD4BF", "#A3E635", "#C084FC"
]

CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR",
    "BRL", "KRW", "RUB", "MXN", "SGD", "HKD", "NOK", "SEK", "DKK",
    "NZD", "ZAR", "TRY", "HUF", "ILS", "CZK", "RON", "BGN", "ISK",
    "THB", "MYR", "PHP"
]

CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "AUD": "A$",
    "CAD": "C$", "CHF": "CHF", "CNY": "¥", "INR": "₹", "BRL": "R$",
    "KRW": "₩", "RUB": "₽", "MXN": "MX$", "SGD": "S$", "HKD": "HK$",
    "NOK": "kr", "SEK": "kr", "DKK": "kr", "NZD": "NZ$", "ZAR": "R",
    "TRY": "₺", "HUF": "Ft", "ILS": "₪", "CZK": "Kč", "RON": "lei",
    "BGN": "лв", "ISK": "kr", "THB": "฿", "MYR": "RM", "PHP": "₱"
}

NAV_ITEMS = [
    ("🏠", "Dashboard"), ("📋", "Transactions"), ("📊", "Analytics"),
    ("💰", "Budgets"), ("🏦", "Accounts"), ("💳", "Debts"),
    ("🎯", "Goals"), ("📈", "Planning"), ("⚙️", "Settings")
]


# ── Master Stylesheet Builder ────────────────────────────────────────────────

def build_stylesheet(t):
    """Return a comprehensive QSS stylesheet for the given theme dict."""
    return f"""

    /* ── Global ─────────────────────────────────────────────────────── */
    QWidget {{
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 13px;
    }}
    QMainWindow {{
        background: {t['BG']};
    }}

    /* ── Scroll Area ────────────────────────────────────────────────── */
    QScrollArea {{
        background: transparent; border: none;
    }}
    QScrollBar:vertical {{
        background: {t['BG']}; width: 6px; border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['BORDER']}; border-radius: 3px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t['MUTED']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {t['BG']}; height: 6px; border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: {t['BORDER']}; border-radius: 3px; min-width: 30px;
    }}

    /* ── Labels ─────────────────────────────────────────────────────── */
    QLabel {{
        color: {t['TEXT']};
        background: transparent;
        border: none;
    }}

    /* ── Buttons ────────────────────────────────────────────────────── */
    QPushButton {{
        background: {t['CARD']};
        color: {t['TEXT']};
        border: 1px solid {t['BORDER']};
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background: {t['BORDER']};
        border-color: {t['MUTED']};
    }}
    QPushButton:pressed {{
        background: {t['SIDEBAR_HOV']};
    }}
    QPushButton:checked {{
        background: {t['SIDEBAR_ACT']};
        color: #fff;
        border-color: {t['SIDEBAR_ACT']};
    }}

    /* ── Line Edit ──────────────────────────────────────────────────── */
    QLineEdit {{
        background: {t['INPUT_BG']};
        color: {t['TEXT']};
        border: 1px solid {t['BORDER']};
        border-radius: 8px;
        padding: 8px 14px;
        selection-background-color: {t['SIDEBAR_ACT']};
    }}
    QLineEdit:focus {{
        border-color: {t['PRIMARY']};
    }}

    /* ── ComboBox ───────────────────────────────────────────────────── */
    QComboBox {{
        background: {t['INPUT_BG']};
        color: {t['TEXT']};
        border: 1px solid {t['BORDER']};
        border-radius: 8px;
        padding: 8px 14px;
        min-width: 100px;
    }}
    QComboBox:focus, QComboBox:hover {{
        border-color: {t['PRIMARY']};
    }}
    QComboBox::drop-down {{
        border: none; width: 30px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {t['MUTED']};
    }}
    QComboBox QAbstractItemView {{
        background: {t['CARD']};
        color: {t['TEXT']};
        border: 1px solid {t['BORDER']};
        border-radius: 8px;
        selection-background-color: {t['SIDEBAR_ACT']};
        selection-color: #fff;
        padding: 4px;
        outline: none;
    }}

    /* ── SpinBox ────────────────────────────────────────────────────── */
    QDoubleSpinBox, QSpinBox {{
        background: {t['INPUT_BG']};
        color: {t['TEXT']};
        border: 1px solid {t['BORDER']};
        border-radius: 8px;
        padding: 8px 14px;
    }}
    QDoubleSpinBox:focus, QSpinBox:focus {{
        border-color: {t['PRIMARY']};
    }}
    QDoubleSpinBox::up-button, QSpinBox::up-button,
    QDoubleSpinBox::down-button, QSpinBox::down-button {{
        background: transparent; border: none; width: 20px;
    }}

    /* ── DateEdit ───────────────────────────────────────────────────── */
    QDateEdit {{
        background: {t['INPUT_BG']};
        color: {t['TEXT']};
        border: 1px solid {t['BORDER']};
        border-radius: 8px;
        padding: 8px 14px;
    }}
    QDateEdit:focus {{
        border-color: {t['PRIMARY']};
    }}
    QDateEdit::drop-down {{
        border: none; width: 30px;
    }}

    /* ── Table ──────────────────────────────────────────────────────── */
    QTableWidget {{
        background: {t['CARD']};
        color: {t['TEXT']};
        border: 1px solid {t['BORDER']};
        border-radius: 10px;
        gridline-color: {t['BORDER']};
        selection-background-color: {t['SIDEBAR_HOV']};
        selection-color: {t['TEXT']};
        outline: none;
    }}
    QTableWidget::item {{
        padding: 6px 10px;
        border-bottom: 1px solid {t['BORDER']};
    }}
    QTableWidget::item:selected {{
        background: {t['SIDEBAR_HOV']};
    }}
    QHeaderView::section {{
        background: {t['INPUT_BG']};
        color: {t['MUTED']};
        border: none;
        border-bottom: 1px solid {t['BORDER']};
        padding: 10px 12px;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    QTableWidget QTableCornerButton::section {{
        background: {t['INPUT_BG']};
        border: none;
    }}

    /* ── Progress Bar ───────────────────────────────────────────────── */
    QProgressBar {{
        background: {t['PROGRESS_BG']};
        border: none;
        border-radius: 6px;
        height: 8px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        border-radius: 6px;
    }}

    /* ── Frame / Cards ──────────────────────────────────────────────── */
    QFrame {{
        background: transparent;
        border: none;
    }}

    /* ── Dialog ─────────────────────────────────────────────────────── */
    QDialog {{
        background: {t['CARD']};
        color: {t['TEXT']};
    }}
    QDialogButtonBox QPushButton {{
        min-width: 90px;
    }}

    /* ── Menu ───────────────────────────────────────────────────────── */
    QMenu {{
        background: {t['CARD']};
        color: {t['TEXT']};
        border: 1px solid {t['BORDER']};
        border-radius: 10px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 8px 28px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background: {t['SIDEBAR_HOV']};
    }}

    /* ── MessageBox ─────────────────────────────────────────────────── */
    QMessageBox {{
        background: {t['CARD']};
        color: {t['TEXT']};
    }}

    /* ── Tooltip ────────────────────────────────────────────────────── */
    QToolTip {{
        background: {t['CARD']};
        color: {t['TEXT']};
        border: 1px solid {t['BORDER']};
        border-radius: 6px;
        padding: 6px 10px;
    }}

    """


# ── Utility ──────────────────────────────────────────────────────────────────

def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            w.setParent(None)
            w.deleteLater()
        sub = item.layout()
        if sub:
            clear_layout(sub)


def style_ax(ax, theme):
    ax.set_facecolor(theme["CARD"])
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(theme["BORDER"])
    ax.tick_params(colors=theme["MUTED"], labelsize=9)


# ── Financial Math Helpers ───────────────────────────────────────────────────

def calc_debt_payoff_months(balance, apr, payment):
    if payment <= 0:
        return float("inf"), 0
    if apr == 0:
        return balance / payment, 0
    r = apr / 100.0 / 12.0
    if payment <= balance * r:
        return float("inf"), float("inf")
    n = -math.log(1 - r * balance / payment) / math.log(1 + r)
    total_paid = payment * n
    return n, total_paid - balance


def calc_required_monthly_payment(balance, apr, months):
    if months <= 0:
        return float("inf")
    if apr == 0:
        return balance / months
    r = apr / 100.0 / 12.0
    return balance * (r * (1 + r) ** months) / ((1 + r) ** months - 1)


def calc_compound_interest(principal, monthly, apr, years):
    r = apr / 100.0 / 12.0
    n = years * 12
    if r == 0:
        total = principal + monthly * n
        return total, principal, monthly * n, 0
    fv_principal = principal * (1 + r) ** n
    fv_series = monthly * (((1 + r) ** n - 1) / r)
    total = fv_principal + fv_series
    contributions = principal + monthly * n
    interest = total - contributions
    return total, principal, contributions, interest


# ── Database ─────────────────────────────────────────────────────────────────

class DatabaseManager:
    def __init__(self, path="finance_tracker.db"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._migrate()

    def _migrate(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
            category TEXT NOT NULL, amount REAL NOT NULL, date TEXT NOT NULL,
            description TEXT DEFAULT '', account TEXT DEFAULT 'General'
        )""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS budgets (
            category TEXT PRIMARY KEY, amount REAL NOT NULL
        )""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS accounts (
            name TEXT PRIMARY KEY, icon TEXT DEFAULT '💳'
        )""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        )""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            balance REAL NOT NULL, apr REAL NOT NULL, min_payment REAL NOT NULL
        )""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            target REAL NOT NULL, saved REAL NOT NULL DEFAULT 0,
            target_date TEXT
        )""")
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(transactions)").fetchall()]
        if "account" not in cols:
            self.conn.execute("ALTER TABLE transactions ADD COLUMN account TEXT DEFAULT 'General'")
        if not self.conn.execute("SELECT * FROM accounts").fetchall():
            self.conn.executemany(
                "INSERT INTO accounts (name, icon) VALUES (?, ?)",
                [("General", "💰"), ("Checking", "🏦"), ("Cash", "💵"), ("Credit Card", "💳")]
            )
        if not self.conn.execute("SELECT * FROM settings WHERE key='currency'").fetchone():
            self.conn.execute("INSERT INTO settings (key, value) VALUES ('currency', 'USD')")
        self.conn.commit()

    def get_setting(self, key, default=""):
        r = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r["value"] if r else default

    def set_setting(self, key, value):
        self.conn.execute("REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
        self.conn.commit()

    def add_txn(self, type_, category, amount, date, description, account):
        self.conn.execute(
            "INSERT INTO transactions (type,category,amount,date,description,account) VALUES (?,?,?,?,?,?)",
            (type_, category, amount, date, description, account),
        )
        self.conn.commit()

    def update_txn(self, id_, type_, category, amount, date, description, account):
        self.conn.execute(
            "UPDATE transactions SET type=?,category=?,amount=?,date=?,description=?,account=? WHERE id=?",
            (type_, category, amount, date, description, account, id_),
        )
        self.conn.commit()

    def delete_txn(self, id_):
        self.conn.execute("DELETE FROM transactions WHERE id=?", (id_,))
        self.conn.commit()

    def get_all_txns(self):
        return self.conn.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC").fetchall()

    def get_filtered_txns(self, type_f=None, cat=None, start=None, end=None, search=None, acc=None):
        q, p = "SELECT * FROM transactions WHERE 1=1", []
        if type_f and type_f != "All":
            q += " AND type=?"
            p.append(type_f.lower())
        if cat and cat != "All":
            q += " AND category=?"
            p.append(cat)
        if start:
            q += " AND date>=?"
            p.append(start.toString("yyyy-MM-dd") if hasattr(start, "toString") else start)
        if end:
            q += " AND date<=?"
            p.append(end.toString("yyyy-MM-dd") if hasattr(end, "toString") else end)
        if search:
            q += " AND (description LIKE ? OR category LIKE ?)"
            p += [f"%{search}%", f"%{search}%"]
        if acc and acc != "All":
            q += " AND account=?"
            p.append(acc)
        q += " ORDER BY date DESC, id DESC"
        return self.conn.execute(q, p).fetchall()

    def get_summary(self, year=None, month=None):
        q, p = "SELECT type, SUM(amount) AS total FROM transactions WHERE 1=1", []
        if year:
            q += " AND strftime('%Y',date)=?"
            p.append(str(year))
        if month:
            q += " AND strftime('%m',date)=?"
            p.append(f"{month:02d}")
        q += " GROUP BY type"
        inc = exp = 0
        for r in self.conn.execute(q, p).fetchall():
            if r["type"] == "income":
                inc = r["total"] or 0
            else:
                exp = r["total"] or 0
        return inc, exp, inc - exp

    def category_totals(self, type_="expense", year=None, month=None):
        q, p = "SELECT category, SUM(amount) AS total FROM transactions WHERE type=?", [type_]
        if year:
            q += " AND strftime('%Y',date)=?"
            p.append(str(year))
        if month:
            q += " AND strftime('%m',date)=?"
            p.append(f"{month:02d}")
        q += " GROUP BY category ORDER BY total DESC"
        return self.conn.execute(q, p).fetchall()

    def monthly_totals(self, limit=6):
        rows = self.conn.execute(
            "SELECT strftime('%Y-%m',date) AS m, type, SUM(amount) AS total "
            "FROM transactions GROUP BY m, type ORDER BY m DESC"
        ).fetchall()
        return rows

    def cumulative_balance(self, limit=12):
        rows = self.conn.execute(
            "SELECT strftime('%Y-%m',date) AS m, "
            "SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS inc, "
            "SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp "
            "FROM transactions GROUP BY m ORDER BY m ASC"
        ).fetchall()[-limit:]
        data, running = [], 0
        for r in rows:
            running += r["inc"] - r["exp"]
            data.append({"m": r["m"], "balance": running})
        return data

    def set_budget(self, category, amount):
        self.conn.execute("REPLACE INTO budgets (category, amount) VALUES (?,?)", (category, amount))
        self.conn.commit()

    def delete_budget(self, category):
        self.conn.execute("DELETE FROM budgets WHERE category=?", (category,))
        self.conn.commit()

    def get_budgets(self):
        return self.conn.execute("SELECT * FROM budgets ORDER BY category").fetchall()

    def get_accounts(self):
        return self.conn.execute("SELECT * FROM accounts ORDER BY name").fetchall()

    def add_account(self, name, icon):
        self.conn.execute("INSERT OR IGNORE INTO accounts (name, icon) VALUES (?,?)", (name, icon))
        self.conn.commit()

    def delete_account(self, name):
        self.conn.execute("DELETE FROM accounts WHERE name=?", (name,))
        self.conn.commit()

    def add_debt(self, name, balance, apr, min_payment):
        self.conn.execute(
            "INSERT INTO debts (name,balance,apr,min_payment) VALUES (?,?,?,?)",
            (name, balance, apr, min_payment),
        )
        self.conn.commit()

    def get_debts(self):
        return self.conn.execute("SELECT * FROM debts ORDER BY balance DESC").fetchall()

    def delete_debt(self, id_):
        self.conn.execute("DELETE FROM debts WHERE id=?", (id_,))
        self.conn.commit()

    def add_goal(self, name, target, saved, target_date):
        self.conn.execute(
            "INSERT INTO goals (name,target,saved,target_date) VALUES (?,?,?,?)",
            (name, target, saved, target_date),
        )
        self.conn.commit()

    def get_goals(self):
        return self.conn.execute("SELECT * FROM goals ORDER BY target_date ASC").fetchall()

    def update_goal_saved(self, id_, saved):
        self.conn.execute("UPDATE goals SET saved=? WHERE id=?", (saved, id_))
        self.conn.commit()

    def delete_goal(self, id_):
        self.conn.execute("DELETE FROM goals WHERE id=?", (id_,))
        self.conn.commit()

    def export_json(self, path):
        data = {
            "transactions": [dict(r) for r in self.get_all_txns()],
            "budgets": [dict(r) for r in self.get_budgets()],
            "accounts": [dict(r) for r in self.get_accounts()],
            "settings": [dict(r) for r in self.conn.execute("SELECT * FROM settings").fetchall()],
            "debts": [dict(r) for r in self.get_debts()],
            "goals": [dict(r) for r in self.get_goals()],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def import_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        required_keys = {"transactions", "budgets", "accounts", "settings", "debts", "goals"}
        if not required_keys.issubset(data.keys()):
            raise ValueError("Invalid backup file: missing required sections")
        self.conn.execute("DELETE FROM transactions")
        self.conn.execute("DELETE FROM budgets")
        self.conn.execute("DELETE FROM accounts")
        self.conn.execute("DELETE FROM settings")
        self.conn.execute("DELETE FROM debts")
        self.conn.execute("DELETE FROM goals")
        for t in data.get("transactions", []):
            self.add_txn(t["type"], t["category"], t["amount"], t["date"],
                         t.get("description", ""), t.get("account", "General"))
        for b in data.get("budgets", []):
            self.set_budget(b["category"], b["amount"])
        for a in data.get("accounts", []):
            self.add_account(a["name"], a["icon"])
        for s in data.get("settings", []):
            self.set_setting(s["key"], s["value"])
        for d in data.get("debts", []):
            self.add_debt(d["name"], d["balance"], d["apr"], d["min_payment"])
        for g in data.get("goals", []):
            self.add_goal(g["name"], g["target"], g["saved"], g.get("target_date", ""))
        self.conn.commit()

    def close(self):
        self.conn.close()


# ── Matplotlib canvas ────────────────────────────────────────────────────────

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, w=5, h=4, dpi=100):
        self.fig = Figure(figsize=(w, h), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


# ── Custom Widgets ───────────────────────────────────────────────────────────

class SummaryCard(QFrame):
    def __init__(self, title, icon, color_key, parent=None):
        super().__init__(parent)
        self.color_key = color_key
        self.setFixedHeight(110)
        self.setObjectName("SummaryCard")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 14)
        v = QVBoxLayout()
        v.setSpacing(4)
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("CardTitle")
        v.addWidget(self.title_lbl)
        self.value_lbl = QLabel("$0.00")
        self.value_lbl.setObjectName("CardValue")
        v.addWidget(self.value_lbl)
        lay.addLayout(v)
        lay.addStretch()
        ic = QLabel(icon)
        ic.setStyleSheet("font-size:28px;border:none;background:transparent;")
        lay.addWidget(ic)

    def set_value(self, val, theme, prefix="", suffix=""):
        color = theme[self.color_key]
        self.value_lbl.setText(f"{prefix}{val:,.2f}{suffix}")
        self.value_lbl.setStyleSheet(
            f"color:{color};font-size:22px;font-weight:700;border:none;background:transparent;"
        )
        self.setStyleSheet(
            f"SummaryCard {{ background:{theme['CARD']}; border-radius:12px; "
            f"border-left:3px solid {color}; }} "
            f"SummaryCard:hover {{ background:{theme['BORDER']}; }} "
            f"#CardTitle {{ color:{theme['MUTED']}; font-size:11px; font-weight:600; "
            f"letter-spacing:0.5px; border:none; background:transparent; }}"
        )


class ChartCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("ChartCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 8)
        lbl = QLabel(title)
        lbl.setObjectName("ChartTitle")
        lbl.setStyleSheet(
            "font-size:13px;font-weight:700;border:none;background:transparent;"
            "letter-spacing:0.3px;"
        )
        lay.addWidget(lbl)
        self.canvas = MplCanvas(self, w=5, h=3.5)
        lay.addWidget(self.canvas)

    def apply_theme(self, theme):
        self.setStyleSheet(
            f"ChartCard {{ background:{theme['CARD']}; border-radius:12px; "
            f"border:1px solid {theme['BORDER']}; }}"
        )
        self.canvas.fig.patch.set_facecolor(theme["CARD"])
        self.findChild(QLabel, "ChartTitle").setStyleSheet(
            f"color:{theme['TEXT']};font-size:13px;font-weight:700;"
            f"border:none;background:transparent;letter-spacing:0.3px;"
        )


# ── Dialogs ──────────────────────────────────────────────────────────────────

class TransactionDialog(QDialog):
    def __init__(self, db, theme, currency_sym, parent=None, txn=None):
        super().__init__(parent)
        self.db = db
        self.theme = theme
        self.currency_sym = currency_sym
        self.txn = txn
        self.setWindowTitle("Edit Transaction" if txn else "Add Transaction")
        self.setMinimumWidth(440)
        self._build()
        if txn:
            self._populate(txn)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(16)
        lay.setContentsMargins(24, 24, 24, 24)

        # type toggle
        type_lay = QHBoxLayout()
        self.btn_inc = QPushButton("💰  Income")
        self.btn_exp = QPushButton("💸  Expense")
        for b in (self.btn_inc, self.btn_exp):
            b.setCheckable(True)
            b.setFixedHeight(42)
            b.setCursor(Qt.PointingHandCursor)
        self.btn_inc.clicked.connect(lambda: self._set_type("income"))
        self.btn_exp.clicked.connect(lambda: self._set_type("expense"))
        type_lay.addWidget(self.btn_inc)
        type_lay.addWidget(self.btn_exp)
        lay.addLayout(type_lay)
        self._set_type("expense")

        form = QFormLayout()
        form.setSpacing(12)
        self.cat_combo = QComboBox()
        form.addRow("Category:", self.cat_combo)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 99_999_999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix(f"{self.currency_sym} ")
        form.addRow("Amount:", self.amount_spin)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Date:", self.date_edit)
        self.acc_combo = QComboBox()
        for a in self.db.get_accounts():
            self.acc_combo.addItem(a["name"])
        form.addRow("Account:", self.acc_combo)
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Optional description…")
        form.addRow("Description:", self.desc_edit)
        lay.addLayout(form)

        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        btn_lay.addWidget(cancel)
        save = QPushButton("  💾  Save  ")
        save.setCursor(Qt.PointingHandCursor)
        save.setStyleSheet(
            f"background:{self.theme['PRIMARY']};color:#fff;font-weight:600;"
            f"border:none;border-radius:8px;padding:10px 24px;"
        )
        save.clicked.connect(self._save)
        btn_lay.addWidget(save)
        lay.addLayout(btn_lay)

    def _set_type(self, t):
        self._type = t
        self.btn_inc.setChecked(t == "income")
        self.btn_exp.setChecked(t == "expense")
        th = self.theme
        if t == "income":
            self.btn_inc.setStyleSheet(
                f"background:{th['INCOME']};color:#0B0F19;font-weight:600;"
                f"border:none;border-radius:8px;padding:10px 20px;"
            )
            self.btn_exp.setStyleSheet(
                f"background:{th['BORDER']};color:{th['MUTED']};"
                f"border:none;border-radius:8px;padding:10px 20px;"
            )
        else:
            self.btn_exp.setStyleSheet(
                f"background:{th['EXPENSE']};color:#0B0F19;font-weight:600;"
                f"border:none;border-radius:8px;padding:10px 20px;"
            )
            self.btn_inc.setStyleSheet(
                f"background:{th['BORDER']};color:{th['MUTED']};"
                f"border:none;border-radius:8px;padding:10px 20px;"
            )
        self.cat_combo.clear()
        self.cat_combo.addItems(INCOME_CATEGORIES if t == "income" else EXPENSE_CATEGORIES)

    def _populate(self, t):
        self._set_type(t["type"])
        idx = self.cat_combo.findText(t["category"])
        if idx >= 0:
            self.cat_combo.setCurrentIndex(idx)
        self.amount_spin.setValue(t["amount"])
        self.date_edit.setDate(QDate.fromString(t["date"], "yyyy-MM-dd"))
        self.desc_edit.setText(t["description"] or "")
        idx2 = self.acc_combo.findText(t.get("account", "General"))
        if idx2 >= 0:
            self.acc_combo.setCurrentIndex(idx2)

    def _save(self):
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Invalid", "Amount must be > 0")
            return
        if not self.cat_combo.currentText():
            QMessageBox.warning(self, "Invalid", "Please select a category")
            return
        data = dict(
            type_=self._type,
            category=self.cat_combo.currentText(),
            amount=self.amount_spin.value(),
            date=self.date_edit.date().toString("yyyy-MM-dd"),
            description=self.desc_edit.text().strip(),
            account=self.acc_combo.currentText(),
        )
        if self.txn:
            self.db.update_txn(self.txn["id"], **data)
        else:
            self.db.add_txn(**data)
        self.accept()


class DebtDialog(QDialog):
    def __init__(self, theme, currency_sym, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Debt")
        self.currency_sym = currency_sym
        self.theme = theme
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        form = QFormLayout()
        form.setSpacing(12)
        self.name_edit = QLineEdit()
        form.addRow("Debt Name:", self.name_edit)
        self.bal_spin = QDoubleSpinBox()
        self.bal_spin.setRange(0, 9999999)
        self.bal_spin.setPrefix(f"{currency_sym} ")
        self.bal_spin.setDecimals(2)
        form.addRow("Current Balance:", self.bal_spin)
        self.apr_spin = QDoubleSpinBox()
        self.apr_spin.setRange(0, 100)
        self.apr_spin.setSuffix(" %")
        self.apr_spin.setDecimals(2)
        form.addRow("APR (Interest Rate):", self.apr_spin)
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(0, 9999999)
        self.min_spin.setPrefix(f"{currency_sym} ")
        self.min_spin.setDecimals(2)
        form.addRow("Minimum Payment:", self.min_spin)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _validate(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Invalid", "Name cannot be empty")
            return
        if self.bal_spin.value() <= 0:
            QMessageBox.warning(self, "Invalid", "Balance must be > 0")
            return
        self.accept()


class GoalDialog(QDialog):
    def __init__(self, theme, currency_sym, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Goal")
        self.theme = theme
        self.currency_sym = currency_sym
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        form = QFormLayout()
        form.setSpacing(12)
        self.name_edit = QLineEdit()
        form.addRow("Goal Name:", self.name_edit)
        self.target_spin = QDoubleSpinBox()
        self.target_spin.setRange(1, 9999999)
        self.target_spin.setPrefix(f"{currency_sym} ")
        self.target_spin.setDecimals(2)
        form.addRow("Target Amount:", self.target_spin)
        self.saved_spin = QDoubleSpinBox()
        self.saved_spin.setRange(0, 9999999)
        self.saved_spin.setPrefix(f"{currency_sym} ")
        self.saved_spin.setDecimals(2)
        form.addRow("Already Saved:", self.saved_spin)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addMonths(6))
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Target Date:", self.date_edit)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _validate(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Invalid", "Name cannot be empty")
            return
        if self.target_spin.value() <= 0:
            QMessageBox.warning(self, "Invalid", "Target must be > 0")
            return
        self.accept()


class AccountDialog(QDialog):
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Account")
        self.theme = theme
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        form = QFormLayout()
        form.setSpacing(12)
        self.name_edit = QLineEdit()
        form.addRow("Account Name:", self.name_edit)
        self.icon_combo = QComboBox()
        self.icon_combo.addItems(["💰", "🏦", "💵", "💳", "📈", "🏠", "🏧"])
        self.icon_combo.setEditable(True)
        form.addRow("Icon:", self.icon_combo)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _validate(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Invalid", "Account name cannot be empty")
            return
        self.accept()


class SettingsDialog(QDialog):
    def __init__(self, db, theme, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme = theme
        self.setWindowTitle("Settings")
        self.setMinimumWidth(440)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(18)
        form = QFormLayout()
        form.setSpacing(12)

        self.currency_combo = QComboBox()
        self.currency_combo.addItems(CURRENCIES)
        cur_code = db.get_setting("currency", "USD")
        idx = self.currency_combo.findText(cur_code)
        if idx >= 0:
            self.currency_combo.setCurrentIndex(idx)
        form.addRow("Currency:", self.currency_combo)
        lay.addLayout(form)

        theme_lay = QHBoxLayout()
        theme_lay.addWidget(QLabel("Theme:"))
        self.theme_light_btn = QPushButton("☀️ Light")
        self.theme_dark_btn = QPushButton("🌙 Dark")
        self.theme_light_btn.setCheckable(True)
        self.theme_dark_btn.setCheckable(True)
        current_theme = db.get_setting("theme", "dark")
        self.theme_light_btn.setChecked(current_theme == "light")
        self.theme_dark_btn.setChecked(current_theme == "dark")
        theme_lay.addWidget(self.theme_light_btn)
        theme_lay.addWidget(self.theme_dark_btn)
        theme_lay.addStretch()
        lay.addLayout(theme_lay)

        btn_lay = QHBoxLayout()
        export_btn = QPushButton("📤 Export Backup (JSON)")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        btn_lay.addWidget(export_btn)
        import_btn = QPushButton("📥 Import Backup (JSON)")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.clicked.connect(self._import)
        btn_lay.addWidget(import_btn)
        lay.addLayout(btn_lay)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _save(self):
        self.db.set_setting("currency", self.currency_combo.currentText())
        theme = "dark" if self.theme_dark_btn.isChecked() else "light"
        self.db.set_setting("theme", theme)
        self.accept()

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Backup", "fintrack_backup.json", "JSON (*.json)")
        if path:
            try:
                self.db.export_json(path)
                QMessageBox.information(self, "Done", "Backup exported!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {e}")

    def _import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Backup", "", "JSON (*.json)")
        if not path:
            return
        if QMessageBox.question(self, "Warning", "This will overwrite ALL current data. Continue?") == QMessageBox.Yes:
            try:
                self.db.import_json(path)
                QMessageBox.information(self, "Done", "Imported successfully! Please restart the app.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Import failed: {e}")


# ── Pages ────────────────────────────────────────────────────────────────────

class DashboardPage(QWidget):
    data_changed = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme = THEMES["dark"]
        self.currency_sym = "$"
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        self.lay = QVBoxLayout(inner)
        self.lay.setSpacing(20)
        self.lay.setContentsMargins(4, 4, 4, 4)

        month_row = QHBoxLayout()
        self.month_lbl = QLabel("Viewing:")
        self.month_lbl.setStyleSheet(
            f"color:{self.theme['MUTED']};font-weight:600;border:none;background:transparent;"
        )
        month_row.addWidget(self.month_lbl)
        self.month_combo = QComboBox()
        self.month_combo.setFixedWidth(180)
        self._refresh_month_combo()
        self.month_combo.currentIndexChanged.connect(self.refresh)
        month_row.addWidget(self.month_combo)
        month_row.addStretch()
        self.lay.addLayout(month_row)

        cards = QHBoxLayout()
        cards.setSpacing(16)
        self.card_income = SummaryCard("Total Income", "💰", "INCOME")
        self.card_expense = SummaryCard("Total Expenses", "💸", "EXPENSE")
        self.card_balance = SummaryCard("Net Balance", "📊", "BALANCE")
        self.card_savings = SummaryCard("Savings Rate", "🤑", "PRIMARY")
        for c in [self.card_income, self.card_expense, self.card_balance, self.card_savings]:
            cards.addWidget(c)
        self.lay.addLayout(cards)

        grid = QGridLayout()
        grid.setSpacing(16)
        self.chart_trend = ChartCard("Income vs Expenses Trend")
        grid.addWidget(self.chart_trend, 0, 0)
        self.chart_pie = ChartCard("Spending Breakdown")
        grid.addWidget(self.chart_pie, 0, 1)
        self.chart_balance = ChartCard("Cumulative Net Balance")
        grid.addWidget(self.chart_balance, 1, 0)
        self.chart_top = ChartCard("Top Spending Categories")
        grid.addWidget(self.chart_top, 1, 1)
        self.lay.addLayout(grid)
        self.lay.addStretch()
        scroll.setWidget(inner)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)

    def apply_theme(self, theme):
        self.theme = theme
        self.month_lbl.setStyleSheet(
            f"color:{theme['MUTED']};font-weight:600;border:none;background:transparent;"
        )
        for c in [self.chart_trend, self.chart_pie, self.chart_balance, self.chart_top]:
            c.apply_theme(theme)

    def _refresh_month_combo(self):
        self.month_combo.blockSignals(True)
        self.month_combo.clear()
        self.month_combo.addItem("All Time")
        now = QDate.currentDate()
        for i in range(12):
            d = now.addMonths(-i)
            self.month_combo.addItem(d.toString("MMM yyyy"))
            self.month_combo.setItemData(self.month_combo.count() - 1, (d.year(), d.month()))
        self.month_combo.blockSignals(False)

    def _selected_period(self):
        idx = self.month_combo.currentIndex()
        return (None, None) if idx == 0 else self.month_combo.itemData(idx)

    def refresh(self):
        year, month = self._selected_period()
        inc, exp, bal = self.db.get_summary(year, month)
        rate = (inc - exp) / inc * 100 if inc > 0 else 0
        self.card_income.set_value(inc, self.theme, prefix=self.currency_sym)
        self.card_expense.set_value(exp, self.theme, prefix=self.currency_sym)
        self.card_balance.set_value(bal, self.theme, prefix=self.currency_sym)
        self.card_savings.set_value(
            rate, self.theme, suffix="%", prefix="+" if rate > 0 else ""
        )
        self._draw_trend()
        self._draw_pie(year, month)
        self._draw_balance()
        self._draw_top(year, month)

    def _draw_trend(self):
        fig = self.chart_trend.canvas.fig
        fig.clear()
        ax = fig.add_subplot(111)
        style_ax(ax, self.theme)
        rows = self.db.monthly_totals()
        if not rows:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center", color=self.theme["MUTED"])
            self.chart_trend.canvas.draw()
            return
        monthly = defaultdict(lambda: {"income": 0, "expense": 0})
        for r in rows:
            monthly[r["m"]][r["type"]] = r["total"]
        months = sorted(monthly.keys())[-6:]
        inc_vals = [monthly[m]["income"] for m in months]
        exp_vals = [monthly[m]["expense"] for m in months]
        labels = [datetime.strptime(m, "%Y-%m").strftime("%b %y") for m in months]
        ax.fill_between(range(len(months)), inc_vals, alpha=0.15, color=self.theme["INCOME"])
        ax.fill_between(range(len(months)), exp_vals, alpha=0.15, color=self.theme["EXPENSE"])
        ax.plot(range(len(months)), inc_vals, marker="o", color=self.theme["INCOME"], linewidth=2, label="Income")
        ax.plot(range(len(months)), exp_vals, marker="o", color=self.theme["EXPENSE"], linewidth=2, label="Expenses")
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(labels)
        ax.yaxis.set_major_formatter(lambda v, _: f"{self.currency_sym}{v:,.0f}")
        ax.legend(frameon=False, fontsize=9)
        fig.tight_layout()
        self.chart_trend.canvas.draw()

    def _draw_pie(self, year, month):
        fig = self.chart_pie.canvas.fig
        fig.clear()
        ax = fig.add_subplot(111)
        data = self.db.category_totals("expense", year, month)
        if not data:
            ax.text(0.5, 0.5, "No expenses", transform=ax.transAxes, ha="center", color=self.theme["MUTED"])
            ax.set_axis_off()
            self.chart_pie.canvas.draw()
            return
        labels = [r["category"] for r in data]
        values = [r["total"] for r in data]
        wedges, texts, autos = ax.pie(
            values, labels=None, autopct="%1.1f%%", startangle=90,
            colors=CHART_COLORS[: len(labels)], pctdistance=0.82,
            wedgeprops=dict(width=0.4, edgecolor=self.theme["CARD"], linewidth=2),
        )
        for t in autos:
            t.set_fontsize(8)
            t.set_color("white")
            t.set_fontweight("bold")
        ax.legend(
            wedges,
            [f"{l} ({self.currency_sym}{v:,.0f})" for l, v in zip(labels, values)],
            loc="center left", bbox_to_anchor=(1, 0.5), fontsize=7, frameon=False,
        )
        ax.set_aspect("equal")
        fig.tight_layout()
        self.chart_pie.canvas.draw()

    def _draw_balance(self):
        fig = self.chart_balance.canvas.fig
        fig.clear()
        ax = fig.add_subplot(111)
        style_ax(ax, self.theme)
        data = self.db.cumulative_balance(limit=12)
        if not data:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center", color=self.theme["MUTED"])
            self.chart_balance.canvas.draw()
            return
        months = [d["m"] for d in data]
        vals = [d["balance"] for d in data]
        labels = [datetime.strptime(m, "%Y-%m").strftime("%b %y") for m in months]
        ax.fill_between(range(len(months)), vals, alpha=0.15, color=self.theme["BALANCE"])
        ax.plot(range(len(months)), vals, marker="o", color=self.theme["BALANCE"], linewidth=2)
        ax.axhline(0, color=self.theme["MUTED"], linestyle="--", linewidth=0.8)
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(labels)
        ax.yaxis.set_major_formatter(lambda v, _: f"{self.currency_sym}{v:,.0f}")
        fig.tight_layout()
        self.chart_balance.canvas.draw()

    def _draw_top(self, year, month):
        fig = self.chart_top.canvas.fig
        fig.clear()
        ax = fig.add_subplot(111)
        style_ax(ax, self.theme)
        data = self.db.category_totals("expense", year, month)[:5]
        if not data:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center", color=self.theme["MUTED"])
            self.chart_top.canvas.draw()
            return
        cats = [r["category"] for r in data][::-1]
        vals = [r["total"] for r in data][::-1]
        ax.barh(cats, vals, color=CHART_COLORS[: len(cats)][::-1], edgecolor=self.theme["CARD"], height=0.6)
        ax.xaxis.set_major_formatter(lambda v, _: f"{self.currency_sym}{v:,.0f}")
        fig.tight_layout()
        self.chart_top.canvas.draw()


class TransactionsPage(QWidget):
    data_changed = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme = THEMES["dark"]
        self.currency_sym = "$"
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(4, 4, 4, 4)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["All", "Income", "Expense"])
        filter_row.addWidget(QLabel("Type:"))
        filter_row.addWidget(self.type_combo)
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("All")
        self.cat_combo.addItems(EXPENSE_CATEGORIES + INCOME_CATEGORIES)
        filter_row.addWidget(QLabel("Category:"))
        filter_row.addWidget(self.cat_combo)
        self.acc_combo = QComboBox()
        self.acc_combo.addItem("All")
        for a in self.db.get_accounts():
            self.acc_combo.addItem(a["name"])
        filter_row.addWidget(QLabel("Account:"))
        filter_row.addWidget(self.acc_combo)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search…")
        filter_row.addWidget(self.search_edit)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate().addMonths(-3))
        self.start_date.setSpecialValueText("From start")
        filter_row.addWidget(QLabel("From:"))
        filter_row.addWidget(self.start_date)
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate())
        filter_row.addWidget(QLabel("To:"))
        filter_row.addWidget(self.end_date)
        filter_btn = QPushButton("Filter")
        filter_btn.setCursor(Qt.PointingHandCursor)
        filter_btn.clicked.connect(self.refresh)
        filter_row.addWidget(filter_btn)
        filter_row.addStretch()
        lay.addLayout(filter_row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Date", "Type", "Category", "Amount", "Account", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._ctx_menu)
        lay.addWidget(self.table)

        add_btn = QPushButton("➕ Add Transaction")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"background:{self.theme['PRIMARY']};color:#fff;font-weight:600;"
            f"border:none;border-radius:8px;padding:10px 20px;"
        )
        add_btn.clicked.connect(self._add_txn)
        lay.addWidget(add_btn)

    def apply_theme(self, theme):
        self.theme = theme
        # Add button accent
        add_btn = self.findChild(QPushButton)
        if add_btn and "➕" in add_btn.text():
            add_btn.setStyleSheet(
                f"background:{theme['PRIMARY']};color:#fff;font-weight:600;"
                f"border:none;border-radius:8px;padding:10px 20px;"
            )

    def _add_txn(self):
        dlg = TransactionDialog(self.db, self.theme, self.currency_sym, self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()
            self.data_changed.emit()

    def _ctx_menu(self, pos):
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return
        row = idx.row()
        txns = self.db.get_filtered_txns(
            type_f=self.type_combo.currentText(),
            cat=self.cat_combo.currentText(),
            start=self.start_date.date(),
            end=self.end_date.date(),
            search=self.search_edit.text().strip() or None,
            acc=self.acc_combo.currentText(),
        )
        if row >= len(txns):
            return
        txn = txns[row]
        menu = QMenu(self)
        edit_act = menu.addAction("✏️  Edit")
        del_act = menu.addAction("🗑️  Delete")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == edit_act:
            dlg = TransactionDialog(self.db, self.theme, self.currency_sym, self, txn=txn)
            if dlg.exec() == QDialog.Accepted:
                self.refresh()
                self.data_changed.emit()
        elif action == del_act:
            if QMessageBox.question(self, "Confirm", "Delete this transaction?") == QMessageBox.Yes:
                self.db.delete_txn(txn["id"])
                self.refresh()
                self.data_changed.emit()

    def refresh(self):
        txns = self.db.get_filtered_txns(
            type_f=self.type_combo.currentText(),
            cat=self.cat_combo.currentText(),
            start=self.start_date.date(),
            end=self.end_date.date(),
            search=self.search_edit.text().strip() or None,
            acc=self.acc_combo.currentText(),
        )
        self.table.setRowCount(len(txns))
        for i, t in enumerate(txns):
            self.table.setItem(i, 0, QTableWidgetItem(t["date"]))
            type_item = QTableWidgetItem(t["type"].capitalize())
            type_item.setForeground(
                QColor(self.theme["INCOME"] if t["type"] == "income" else self.theme["EXPENSE"])
            )
            self.table.setItem(i, 1, type_item)
            self.table.setItem(i, 2, QTableWidgetItem(t["category"]))
            amt_item = QTableWidgetItem(f"{self.currency_sym}{t['amount']:,.2f}")
            amt_item.setForeground(
                QColor(self.theme["INCOME"] if t["type"] == "income" else self.theme["EXPENSE"])
            )
            self.table.setItem(i, 3, amt_item)
            self.table.setItem(i, 4, QTableWidgetItem(t.get("account", "General")))
            self.table.setItem(i, 5, QTableWidgetItem(t.get("description", "")))


class AnalyticsPage(QWidget):
    data_changed = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme = THEMES["dark"]
        self.currency_sym = "$"
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setSpacing(20)
        lay.setContentsMargins(4, 4, 4, 4)

        cards = QHBoxLayout()
        cards.setSpacing(16)
        self.card_net = SummaryCard("Total Net Worth", "🏦", "BALANCE")
        self.card_mom = SummaryCard("MoM Expense Change", "📉", "EXPENSE")
        self.card_avg = SummaryCard("Avg Daily Spend", "📅", "PRIMARY")
        cards.addWidget(self.card_net)
        cards.addWidget(self.card_mom)
        cards.addWidget(self.card_avg)
        lay.addLayout(cards)

        self.chart_yearly = ChartCard("12-Month Income vs Expense")
        lay.addWidget(self.chart_yearly)
        lay.addStretch()
        scroll.setWidget(inner)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)

    def apply_theme(self, theme):
        self.theme = theme
        self.chart_yearly.apply_theme(theme)

    def refresh(self):
        inc, exp, _ = self.db.get_summary()
        self.card_net.set_value(inc - exp, self.theme, prefix=self.currency_sym)
        now = QDate.currentDate()
        cur_exp_m = self.db.get_summary(now.year(), now.month())[1]
        prev = now.addMonths(-1)
        prev_exp_m = self.db.get_summary(prev.year(), prev.month())[1]
        pct = ((cur_exp_m - prev_exp_m) / prev_exp_m * 100) if prev_exp_m > 0 else 0
        self.card_mom.set_value(pct, self.theme, suffix="%", prefix="+" if pct > 0 else "")
        day = now.day()
        avg = cur_exp_m / day if day > 0 else 0
        self.card_avg.set_value(avg, self.theme, prefix=self.currency_sym)
        self._draw_yearly()

    def _draw_yearly(self):
        fig = self.chart_yearly.canvas.fig
        fig.clear()
        ax = fig.add_subplot(111)
        style_ax(ax, self.theme)
        rows = self.db.monthly_totals()
        if not rows:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center", color=self.theme["MUTED"])
            self.chart_yearly.canvas.draw()
            return
        monthly = defaultdict(lambda: {"income": 0, "expense": 0})
        for r in rows:
            monthly[r["m"]][r["type"]] = r["total"]
        months = sorted(monthly.keys())[-12:]
        x = range(len(months))
        inc = [monthly[m]["income"] for m in months]
        exp = [monthly[m]["expense"] for m in months]
        labels = [datetime.strptime(m, "%Y-%m").strftime("%b") for m in months]
        ax.bar([i - 0.2 for i in x], inc, 0.4, label="Income", color=self.theme["INCOME"])
        ax.bar([i + 0.2 for i in x], exp, 0.4, label="Expense", color=self.theme["EXPENSE"])
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels)
        ax.yaxis.set_major_formatter(lambda v, _: f"{self.currency_sym}{v:,.0f}")
        ax.legend(frameon=False)
        fig.tight_layout()
        self.chart_yearly.canvas.draw()


class BudgetsPage(QWidget):
    data_changed = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme = THEMES["dark"]
        self.currency_sym = "$"
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(16)
        lay.setContentsMargins(4, 4, 4, 4)

        form = QHBoxLayout()
        form.setSpacing(10)
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(EXPENSE_CATEGORIES)
        form.addWidget(self.cat_combo)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999)
        self.amount_spin.setPrefix(f"{self.currency_sym} ")
        self.amount_spin.setDecimals(2)
        form.addWidget(self.amount_spin)
        add_btn = QPushButton("Set Budget")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"background:{self.theme['PRIMARY']};color:#fff;font-weight:600;"
            f"border:none;border-radius:8px;padding:10px 20px;"
        )
        add_btn.clicked.connect(self._save_budget)
        form.addWidget(add_btn)
        form.addStretch()
        lay.addLayout(form)

        self.budget_layout = QVBoxLayout()
        self.budget_layout.setSpacing(10)
        lay.addLayout(self.budget_layout)
        lay.addStretch()

    def apply_theme(self, theme):
        self.theme = theme
        self.refresh()

    def _save_budget(self):
        self.db.set_budget(self.cat_combo.currentText(), self.amount_spin.value())
        self.refresh()
        self.data_changed.emit()

    def refresh(self):
        clear_layout(self.budget_layout)
        budgets = self.db.get_budgets()
        now = QDate.currentDate()
        _, exp, _ = self.db.get_summary(now.year(), now.month())
        total_budget = sum(b["amount"] for b in budgets)

        # overview card
        overview = QFrame()
        overview.setStyleSheet(
            f"background:{self.theme['CARD']}; border-radius:12px; "
            f"border:1px solid {self.theme['BORDER']};"
        )
        ov_lay = QVBoxLayout(overview)
        ov_lay.setContentsMargins(20, 16, 20, 16)
        ov_lay.addWidget(QLabel(
            f"Monthly Budget: {self.currency_sym}{total_budget:,.2f} Budgeted vs "
            f"{self.currency_sym}{exp:,.2f} Spent"
        ))
        if total_budget > 0:
            pct = min(exp / total_budget * 100, 100)
            bar = QProgressBar()
            bar.setValue(int(pct))
            color = self.theme["INCOME"] if pct < 80 else self.theme["EXPENSE"]
            bar.setStyleSheet(
                f"QProgressBar::chunk {{ background:{color}; border-radius:6px; }}"
            )
            ov_lay.addWidget(bar)
            remaining = total_budget - exp
            rem_lbl = QLabel(
                f"{'Remaining' if remaining >= 0 else 'Overspent'}: "
                f"{self.currency_sym}{abs(remaining):,.2f}"
            )
            rem_lbl.setStyleSheet(
                f"color:{self.theme['INCOME'] if remaining >= 0 else self.theme['EXPENSE']};"
                f"font-weight:600;border:none;background:transparent;"
            )
            ov_lay.addWidget(rem_lbl)
        self.budget_layout.addWidget(overview)

        # per-category cards
        for b in budgets:
            card = QFrame()
            card.setStyleSheet(
                f"background:{self.theme['CARD']}; border-radius:10px; "
                f"border:1px solid {self.theme['BORDER']};"
            )
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(16, 12, 16, 12)
            info = QVBoxLayout()
            cat_lbl = QLabel(b["category"])
            cat_lbl.setStyleSheet(f"font-weight:600;border:none;background:transparent;")
            info.addWidget(cat_lbl)
            amt_lbl = QLabel(f"{self.currency_sym}{b['amount']:,.2f} budgeted")
            amt_lbl.setStyleSheet(
                f"color:{self.theme['MUTED']};font-size:11px;border:none;background:transparent;"
            )
            info.addWidget(amt_lbl)
            c_lay.addLayout(info)
            c_lay.addStretch()
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(30, 30)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet(
                f"background:transparent;color:{self.theme['MUTED']};border:none;font-size:14px;"
            )
            del_btn.clicked.connect(lambda checked, cat=b["category"]: self._del_budget(cat))
            c_lay.addWidget(del_btn)
            self.budget_layout.addWidget(card)

    def _del_budget(self, cat):
        if QMessageBox.question(self, "Confirm", f"Remove budget for {cat}?") == QMessageBox.Yes:
            self.db.delete_budget(cat)
            self.refresh()
            self.data_changed.emit()


class AccountsPage(QWidget):
    data_changed = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme = THEMES["dark"]
        self.currency_sym = "$"
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(16)
        lay.setContentsMargins(4, 4, 4, 4)

        add_btn = QPushButton("➕ Add Account")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"background:{self.theme['PRIMARY']};color:#fff;font-weight:600;"
            f"border:none;border-radius:8px;padding:10px 20px;"
        )
        add_btn.clicked.connect(self._add_account)
        lay.addWidget(add_btn)

        self.grid = QGridLayout()
        self.grid.setSpacing(16)
        lay.addLayout(self.grid)
        lay.addStretch()

    def apply_theme(self, theme):
        self.theme = theme
        self.refresh()

    def _add_account(self):
        dlg = AccountDialog(self.theme, self)
        if dlg.exec() == QDialog.Accepted:
            self.db.add_account(dlg.name_edit.text().strip(), dlg.icon_combo.currentText())
            self.refresh()
            self.data_changed.emit()

    def refresh(self):
        clear_layout(self.grid)
        accounts = self.db.get_accounts()
        for i, a in enumerate(accounts):
            card = QFrame()
            card.setStyleSheet(
                f"background:{self.theme['CARD']}; border-radius:12px; "
                f"border:1px solid {self.theme['BORDER']};"
            )
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(20, 16, 20, 16)
            icon_lbl = QLabel(a["icon"])
            icon_lbl.setStyleSheet("font-size:28px;border:none;background:transparent;")
            c_lay.addWidget(icon_lbl)
            name_lbl = QLabel(a["name"])
            name_lbl.setStyleSheet("font-weight:600;font-size:14px;border:none;background:transparent;")
            c_lay.addWidget(name_lbl)
            c_lay.addStretch()
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(30, 30)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet(
                f"background:transparent;color:{self.theme['MUTED']};border:none;font-size:14px;"
            )
            del_btn.clicked.connect(lambda checked, n=a["name"]: self._del_account(n))
            c_lay.addWidget(del_btn)
            self.grid.addWidget(card, i // 3, i % 3)

    def _del_account(self, name):
        if name == "General":
            QMessageBox.warning(self, "Cannot Delete", "The General account cannot be removed.")
            return
        if QMessageBox.question(self, "Confirm", f"Delete account '{name}'?") == QMessageBox.Yes:
            self.db.delete_account(name)
            self.refresh()
            self.data_changed.emit()


class DebtsPage(QWidget):
    data_changed = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme = THEMES["dark"]
        self.currency_sym = "$"
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(16)
        lay.setContentsMargins(4, 4, 4, 4)

        add_btn = QPushButton("➕ Add Debt")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"background:{self.theme['PRIMARY']};color:#fff;font-weight:600;"
            f"border:none;border-radius:8px;padding:10px 20px;"
        )
        add_btn.clicked.connect(self._add_debt)
        lay.addWidget(add_btn)

        self.debt_layout = QVBoxLayout()
        self.debt_layout.setSpacing(12)
        lay.addLayout(self.debt_layout)
        lay.addStretch()

    def apply_theme(self, theme):
        self.theme = theme
        self.refresh()

    def _add_debt(self):
        dlg = DebtDialog(self.theme, self.currency_sym, self)
        if dlg.exec() == QDialog.Accepted:
            self.db.add_debt(
                dlg.name_edit.text().strip(),
                dlg.bal_spin.value(),
                dlg.apr_spin.value(),
                dlg.min_spin.value(),
            )
            self.refresh()
            self.data_changed.emit()

    def refresh(self):
        clear_layout(self.debt_layout)
        debts = self.db.get_debts()
        total_debt = sum(d["balance"] for d in debts)
        total_min = sum(d["min_payment"] for d in debts)

        # overview
        overview = QFrame()
        overview.setStyleSheet(
            f"background:{self.theme['CARD']}; border-radius:12px; "
            f"border:1px solid {self.theme['BORDER']};"
        )
        ov_lay = QVBoxLayout(overview)
        ov_lay.setContentsMargins(20, 16, 20, 16)
        ov_lay.addWidget(QLabel(f"Total Debt: {self.currency_sym}{total_debt:,.2f}"))
        ov_lay.addWidget(QLabel(f"Total Minimum Payments: {self.currency_sym}{total_min:,.2f}"))
        self.debt_layout.addWidget(overview)

        for d in debts:
            card = QFrame()
            card.setStyleSheet(
                f"background:{self.theme['CARD']}; border-radius:12px; "
                f"border:1px solid {self.theme['BORDER']}; "
                f"border-left:3px solid {self.theme['EXPENSE']};"
            )
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(20, 14, 20, 14)
            h = QHBoxLayout()
            name_lbl = QLabel(d["name"])
            name_lbl.setStyleSheet("font-weight:600;font-size:15px;border:none;background:transparent;")
            h.addWidget(name_lbl)
            h.addStretch()
            bal_lbl = QLabel(f"{self.currency_sym}{d['balance']:,.2f}")
            bal_lbl.setStyleSheet(
                f"color:{self.theme['EXPENSE']};font-weight:700;font-size:16px;"
                f"border:none;background:transparent;"
            )
            h.addWidget(bal_lbl)
            c_lay.addLayout(h)

            details = QHBoxLayout()
            months, interest = calc_debt_payoff_months(d["balance"], d["apr"], d["min_payment"])
            details.addWidget(QLabel(f"APR: {d['apr']:.1f}%"))
            details.addWidget(QLabel(f"Min: {self.currency_sym}{d['min_payment']:,.2f}/mo"))
            payoff_txt = f"{months:.0f} months" if months != float("inf") else "∞"
            details.addWidget(QLabel(f"Payoff: {payoff_txt}"))
            details.addWidget(QLabel(f"Interest: {self.currency_sym}{interest:,.0f}"))
            for lbl in [w for w in details.itemAt(0).widget().parentWidget().children() if isinstance(w, QLabel)]:
                lbl.setStyleSheet(
                    f"color:{self.theme['MUTED']};font-size:11px;border:none;background:transparent;"
                )
            c_lay.addLayout(details)

            del_btn = QPushButton("🗑️ Delete")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet(
                f"background:transparent;color:{self.theme['MUTED']};"
                f"border:1px solid {self.theme['BORDER']};border-radius:6px;padding:6px 14px;"
            )
            del_btn.clicked.connect(lambda checked, id_=d["id"]: self._del_debt(id_))
            c_lay.addWidget(del_btn)
            self.debt_layout.addWidget(card)

    def _del_debt(self, id_):
        if QMessageBox.question(self, "Confirm", "Delete this debt?") == QMessageBox.Yes:
            self.db.delete_debt(id_)
            self.refresh()
            self.data_changed.emit()


class GoalsPage(QWidget):
    data_changed = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme = THEMES["dark"]
        self.currency_sym = "$"
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(16)
        lay.setContentsMargins(4, 4, 4, 4)

        add_btn = QPushButton("➕ Add Goal")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"background:{self.theme['PRIMARY']};color:#fff;font-weight:600;"
            f"border:none;border-radius:8px;padding:10px 20px;"
        )
        add_btn.clicked.connect(self._add_goal)
        lay.addWidget(add_btn)

        self.goal_layout = QVBoxLayout()
        self.goal_layout.setSpacing(12)
        lay.addLayout(self.goal_layout)
        lay.addStretch()

    def apply_theme(self, theme):
        self.theme = theme
        self.refresh()

    def _add_goal(self):
        dlg = GoalDialog(self.theme, self.currency_sym, self)
        if dlg.exec() == QDialog.Accepted:
            self.db.add_goal(
                dlg.name_edit.text().strip(),
                dlg.target_spin.value(),
                dlg.saved_spin.value(),
                dlg.date_edit.date().toString("yyyy-MM-dd"),
            )
            self.refresh()
            self.data_changed.emit()

    def refresh(self):
        clear_layout(self.goal_layout)
        goals = self.db.get_goals()
        for g in goals:
            card = QFrame()
            card.setStyleSheet(
                f"background:{self.theme['CARD']}; border-radius:12px; "
                f"border:1px solid {self.theme['BORDER']}; "
                f"border-left:3px solid {self.theme['BALANCE']};"
            )
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(20, 14, 20, 14)
            h = QHBoxLayout()
            name_lbl = QLabel(g["name"])
            name_lbl.setStyleSheet("font-weight:600;font-size:15px;border:none;background:transparent;")
            h.addWidget(name_lbl)
            h.addStretch()
            pct = (g["saved"] / g["target"] * 100) if g["target"] > 0 else 0
            pct_lbl = QLabel(f"{pct:.0f}%")
            pct_lbl.setStyleSheet(
                f"color:{self.theme['BALANCE']};font-weight:700;font-size:16px;"
                f"border:none;background:transparent;"
            )
            h.addWidget(pct_lbl)
            c_lay.addLayout(h)

            bar = QProgressBar()
            bar.setValue(min(int(pct), 100))
            bar.setStyleSheet(
                f"QProgressBar::chunk {{ background:{self.theme['BALANCE']}; border-radius:6px; }}"
            )
            c_lay.addWidget(bar)

            info = QHBoxLayout()
            info.addWidget(QLabel(
                f"{self.currency_sym}{g['saved']:,.2f} of {self.currency_sym}{g['target']:,.2f}"
            ))
            if g["target_date"]:
                info.addWidget(QLabel(f"Target: {g['target_date']}"))
            for w in info.parentWidget().findChildren(QLabel):
                w.setStyleSheet(
                    f"color:{self.theme['MUTED']};font-size:11px;border:none;background:transparent;"
                )
            c_lay.addLayout(info)

            btn_row = QHBoxLayout()
            update_btn = QPushButton("💰 Update Saved")
            update_btn.setCursor(Qt.PointingHandCursor)
            update_btn.setStyleSheet(
                f"background:transparent;color:{self.theme['PRIMARY']};"
                f"border:1px solid {self.theme['BORDER']};border-radius:6px;padding:6px 14px;"
            )
            update_btn.clicked.connect(lambda checked, id_=g["id"], s=g["saved"]: self._update_saved(id_, s))
            btn_row.addWidget(update_btn)
            del_btn = QPushButton("🗑️ Delete")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet(
                f"background:transparent;color:{self.theme['MUTED']};"
                f"border:1px solid {self.theme['BORDER']};border-radius:6px;padding:6px 14px;"
            )
            del_btn.clicked.connect(lambda checked, id_=g["id"]: self._del_goal(id_))
            btn_row.addWidget(del_btn)
            btn_row.addStretch()
            c_lay.addLayout(btn_row)
            self.goal_layout.addWidget(card)

    def _update_saved(self, id_, current):
        val, ok = QInputDialog.getDouble(self, "Update Saved", "New saved amount:", current, 0, 9999999, 2)
        if ok:
            self.db.update_goal_saved(id_, val)
            self.refresh()
            self.data_changed.emit()

    def _del_goal(self, id_):
        if QMessageBox.question(self, "Confirm", "Delete this goal?") == QMessageBox.Yes:
            self.db.delete_goal(id_)
            self.refresh()
            self.data_changed.emit()


class PlanningPage(QWidget):
    data_changed = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme = THEMES["dark"]
        self.currency_sym = "$"
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setSpacing(20)
        lay.setContentsMargins(4, 4, 4, 4)

        # Compound interest calculator
        ci_card = QFrame()
        ci_card.setStyleSheet(
            f"background:{self.theme['CARD']}; border-radius:12px; "
            f"border:1px solid {self.theme['BORDER']};"
        )
        ci_lay = QVBoxLayout(ci_card)
        ci_lay.setContentsMargins(20, 16, 20, 16)
        ci_title = QLabel("📈 Compound Interest Calculator")
        ci_title.setStyleSheet("font-weight:700;font-size:16px;border:none;background:transparent;")
        ci_lay.addWidget(ci_title)

        form = QFormLayout()
        form.setSpacing(10)
        self.ci_principal = QDoubleSpinBox()
        self.ci_principal.setRange(0, 99999999)
        self.ci_principal.setPrefix(f"{self.currency_sym} ")
        self.ci_principal.setDecimals(2)
        self.ci_principal.setValue(10000)
        form.addRow("Initial Principal:", self.ci_principal)
        self.ci_monthly = QDoubleSpinBox()
        self.ci_monthly.setRange(0, 999999)
        self.ci_monthly.setPrefix(f"{self.currency_sym} ")
        self.ci_monthly.setDecimals(2)
        self.ci_monthly.setValue(500)
        form.addRow("Monthly Contribution:", self.ci_monthly)
        self.ci_apr = QDoubleSpinBox()
        self.ci_apr.setRange(0, 50)
        self.ci_apr.setSuffix(" %")
        self.ci_apr.setDecimals(2)
        self.ci_apr.setValue(7)
        form.addRow("Annual Return Rate:", self.ci_apr)
        self.ci_years = QSpinBox()
        self.ci_years.setRange(1, 50)
        self.ci_years.setValue(10)
        form.addRow("Years:", self.ci_years)
        ci_lay.addLayout(form)

        calc_btn = QPushButton("Calculate")
        calc_btn.setCursor(Qt.PointingHandCursor)
        calc_btn.setStyleSheet(
            f"background:{self.theme['PRIMARY']};color:#fff;font-weight:600;"
            f"border:none;border-radius:8px;padding:10px 20px;"
        )
        calc_btn.clicked.connect(self._calc_ci)
        ci_lay.addWidget(calc_btn)
        self.ci_result = QLabel("")
        self.ci_result.setWordWrap(True)
        ci_lay.addWidget(self.ci_result)
        lay.addWidget(ci_card)

        # Debt payoff calculator
        dp_card = QFrame()
        dp_card.setStyleSheet(
            f"background:{self.theme['CARD']}; border-radius:12px; "
            f"border:1px solid {self.theme['BORDER']};"
        )
        dp_lay = QVBoxLayout(dp_card)
        dp_lay.setContentsMargins(20, 16, 20, 16)
        dp_title = QLabel("💳 Debt Payoff Calculator")
        dp_title.setStyleSheet("font-weight:700;font-size:16px;border:none;background:transparent;")
        dp_lay.addWidget(dp_title)

        form2 = QFormLayout()
        form2.setSpacing(10)
        self.dp_balance = QDoubleSpinBox()
        self.dp_balance.setRange(0, 99999999)
        self.dp_balance.setPrefix(f"{self.currency_sym} ")
        self.dp_balance.setDecimals(2)
        self.dp_balance.setValue(5000)
        form2.addRow("Debt Balance:", self.dp_balance)
        self.dp_apr = QDoubleSpinBox()
        self.dp_apr.setRange(0, 50)
        self.dp_apr.setSuffix(" %")
        self.dp_apr.setDecimals(2)
        self.dp_apr.setValue(18)
        form2.addRow("APR:", self.dp_apr)
        self.dp_payment = QDoubleSpinBox()
        self.dp_payment.setRange(0, 999999)
        self.dp_payment.setPrefix(f"{self.currency_sym} ")
        self.dp_payment.setDecimals(2)
        self.dp_payment.setValue(200)
        form2.addRow("Monthly Payment:", self.dp_payment)
        dp_lay.addLayout(form2)

        dp_btn = QPushButton("Calculate Payoff")
        dp_btn.setCursor(Qt.PointingHandCursor)
        dp_btn.setStyleSheet(
            f"background:{self.theme['PRIMARY']};color:#fff;font-weight:600;"
            f"border:none;border-radius:8px;padding:10px 20px;"
        )
        dp_btn.clicked.connect(self._calc_dp)
        dp_lay.addWidget(dp_btn)
        self.dp_result = QLabel("")
        self.dp_result.setWordWrap(True)
        dp_lay.addWidget(self.dp_result)
        lay.addWidget(dp_card)

        lay.addStretch()
        scroll.setWidget(inner)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)

    def apply_theme(self, theme):
        self.theme = theme
        # Re-style the cards and buttons
        for card in self.findChildren(QFrame):
            card.setStyleSheet(
                f"background:{theme['CARD']}; border-radius:12px; "
                f"border:1px solid {theme['BORDER']};"
            )
        for btn in self.findChildren(QPushButton):
            if "Calculate" in btn.text():
                btn.setStyleSheet(
                    f"background:{theme['PRIMARY']};color:#fff;font-weight:600;"
                    f"border:none;border-radius:8px;padding:10px 20px;"
                )

    def _calc_ci(self):
        total, principal, contributions, interest = calc_compound_interest(
            self.ci_principal.value(), self.ci_monthly.value(),
            self.ci_apr.value(), self.ci_years.value()
        )
        self.ci_result.setText(
            f"<b>Future Value:</b> {self.currency_sym}{total:,.2f}<br>"
            f"<b>Principal:</b> {self.currency_sym}{principal:,.2f}<br>"
            f"<b>Contributions:</b> {self.currency_sym}{contributions:,.2f}<br>"
            f"<b>Interest Earned:</b> {self.currency_sym}{interest:,.2f}"
        )
        self.ci_result.setStyleSheet(
            f"color:{self.theme['TEXT']};font-size:13px;border:none;background:transparent;"
        )

    def _calc_dp(self):
        months, interest = calc_debt_payoff_months(
            self.dp_balance.value(), self.dp_apr.value(), self.dp_payment.value()
        )
        if months == float("inf"):
            self.dp_result.setText(
                f"<span style='color:{self.theme['EXPENSE']}'>⚠️ Payment too low — "
                f"debt will never be paid off.</span>"
            )
        else:
            req = calc_required_monthly_payment(self.dp_balance.value(), self.dp_apr.value(), 12)
            self.dp_result.setText(
                f"<b>Payoff Time:</b> {months:.1f} months ({months / 12:.1f} years)<br>"
                f"<b>Total Interest:</b> {self.currency_sym}{interest:,.2f}<br>"
                f"<b>To pay off in 12 months:</b> {self.currency_sym}{req:,.2f}/month"
            )
        self.dp_result.setStyleSheet(
            f"color:{self.theme['TEXT']};font-size:13px;border:none;background:transparent;"
        )


# ── Main Window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Finance Tracker Pro")
        self.setMinimumSize(1200, 750)
        self.resize(1340, 800)

        self.db = DatabaseManager()

        # ── Determine theme (default dark) ──
        theme_name = self.db.get_setting("theme", "dark")
        self.theme_name = theme_name
        self.theme = THEMES[theme_name]
        self.currency_sym = CURRENCY_SYMBOLS.get(
            self.db.get_setting("currency", "USD"), "$"
        )

        # ── Network manager for live currency ──
        self.net_mgr = QNetworkAccessManager(self)
        self._currency_rates = {}

        # ── Build UI ──
        self._build_sidebar()
        self._build_pages()
        self._apply_theme()

        # ── Initial refresh ──
        self._switch_page(0)
        self._fetch_rates()

    # ── Sidebar ────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        s_lay = QVBoxLayout(sidebar)
        s_lay.setContentsMargins(12, 20, 12, 20)
        s_lay.setSpacing(4)

        # logo
        logo = QLabel("💰 FinTrack Pro")
        logo.setObjectName("LogoLabel")
        logo.setStyleSheet(
            f"color:{self.theme['TEXT']};font-size:18px;font-weight:700;"
            f"border:none;background:transparent;padding:8px 10px;"
        )
        s_lay.addWidget(logo)
        s_lay.addSpacing(12)

        self.nav_btns = []
        for icon, name in NAV_ITEMS:
            btn = QPushButton(f"  {icon}  {name}")
            btn.setObjectName("NavBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            btn.setStyleSheet(
                f"QPushButton {{ background:transparent; color:{self.theme['MUTED']}; "
                f"border:none; border-radius:8px; text-align:left; "
                f"padding-left:14px; font-size:13px; font-weight:500; }} "
                f"QPushButton:hover {{ background:{self.theme['SIDEBAR_HOV']}; "
                f"color:{self.theme['TEXT']}; }} "
                f"QPushButton:checked {{ background:{self.theme['SIDEBAR_ACT']}; "
                f"color:#fff; font-weight:600; }}"
            )
            btn.setCheckable(True)
            idx = len(self.nav_btns)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            s_lay.addWidget(btn)
            self.nav_btns.append(btn)

        s_lay.addStretch()

        # Currency live label
        self.rate_lbl = QLabel("")
        self.rate_lbl.setStyleSheet(
            f"color:{self.theme['MUTED']};font-size:10px;border:none;background:transparent;padding:4px 10px;"
        )
        s_lay.addWidget(self.rate_lbl)
        self.sidebar = sidebar

    # ── Pages ──────────────────────────────────────────────────────────
    def _build_pages(self):
        self.pages = QStackedWidget()
        self.page_widgets = [
            DashboardPage(self.db),
            TransactionsPage(self.db),
            AnalyticsPage(self.db),
            BudgetsPage(self.db),
            AccountsPage(self.db),
            DebtsPage(self.db),
            GoalsPage(self.db),
            PlanningPage(self.db),
            QWidget(),  # settings placeholder
        ]

        for pw in self.page_widgets:
            pw.theme = self.theme
            pw.currency_sym = self.currency_sym
            self.pages.addWidget(pw)

        # Connect data_changed signals
        for pw in self.page_widgets[:-1]:
            if hasattr(pw, "data_changed"):
                pw.data_changed.connect(self._on_data_changed)

        # Layout
        central = QWidget()
        h_lay = QHBoxLayout(central)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(0)
        h_lay.addWidget(self.sidebar)
        h_lay.addWidget(self.pages, 1)
        self.setCentralWidget(central)

    def _switch_page(self, idx):
        self.pages.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == idx)
        # Refresh the page
        pw = self.page_widgets[idx]
        if idx == 8:  # Settings
            self._open_settings()
            return
        if hasattr(pw, "refresh"):
            pw.refresh()

    def _open_settings(self):
        dlg = SettingsDialog(self.db, self.theme, self)
        if dlg.exec() == QDialog.Accepted:
            # Check if theme changed
            new_theme_name = self.db.get_setting("theme", "dark")
            new_cur = self.db.get_setting("currency", "USD")
            self.currency_sym = CURRENCY_SYMBOLS.get(new_cur, "$")
            if new_theme_name != self.theme_name or new_cur != self.currency_sym:
                self.theme_name = new_theme_name
                self.theme = THEMES[new_theme_name]
                self._apply_theme()
                self._on_data_changed()

    def _apply_theme(self):
        self.setStyleSheet(build_stylesheet(self.theme))
        # Sidebar
        self.sidebar.setStyleSheet(
            f"QFrame#Sidebar {{ background:{self.theme['SIDEBAR_BG']}; "
            f"border-right:1px solid {self.theme['BORDER']}; }}"
        )
        self.sidebar.findChild(QLabel, "LogoLabel").setStyleSheet(
            f"color:{self.theme['TEXT']};font-size:18px;font-weight:700;"
            f"border:none;background:transparent;padding:8px 10px;"
        )
        self.rate_lbl.setStyleSheet(
            f"color:{self.theme['MUTED']};font-size:10px;border:none;background:transparent;padding:4px 10px;"
        )
        for btn in self.nav_btns:
            btn.setStyleSheet(
                f"QPushButton {{ background:transparent; color:{self.theme['MUTED']}; "
                f"border:none; border-radius:8px; text-align:left; "
                f"padding-left:14px; font-size:13px; font-weight:500; }} "
                f"QPushButton:hover {{ background:{self.theme['SIDEBAR_HOV']}; "
                f"color:{self.theme['TEXT']}; }} "
                f"QPushButton:checked {{ background:{self.theme['SIDEBAR_ACT']}; "
                f"color:#fff; font-weight:600; }}"
            )
        # All pages
        for pw in self.page_widgets:
            pw.theme = self.theme
            pw.currency_sym = self.currency_sym
            if hasattr(pw, "apply_theme"):
                pw.apply_theme(self.theme)

    def _on_data_changed(self):
        idx = self.pages.currentIndex()
        pw = self.page_widgets[idx]
        if hasattr(pw, "refresh"):
            pw.refresh()

    # ── Live Currency ──────────────────────────────────────────────────
    def _fetch_rates(self):
        cur = self.db.get_setting("currency", "USD")
        if cur == "USD":
            self.rate_lbl.setText("Base currency: USD")
            return
        url = QUrl(f"https://open.er-api.com/v6/latest/USD")
        req = QNetworkRequest(url)
        reply = self.net_mgr.get(req)
        reply.finished.connect(lambda: self._on_rates(reply, cur))

    def _on_rates(self, reply, cur):
        if reply.error() == QNetworkReply.NoError:
            data = json.loads(reply.readAll().data())
            self._currency_rates = data.get("rates", {})
            rate = self._currency_rates.get(cur, 1)
            self.rate_lbl.setText(f"1 USD = {rate:.4f} {cur}")
        else:
            self.rate_lbl.setText("Currency rates unavailable")
        reply.deleteLater()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)


# ── Entry Point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Force dark palette as fallback
    from PySide6.QtGui import QPalette
    palette = QPalette()
    dark_bg = QColor("#0B0F19")
    dark_card = QColor("#141A2A")
    dark_text = QColor("#E2E8F0")
    dark_muted = QColor("#7B8BA5")
    dark_border = QColor("#1E2840")
    dark_input = QColor("#0F1628")
    palette.setColor(QPalette.Window, dark_bg)
    palette.setColor(QPalette.WindowText, dark_text)
    palette.setColor(QPalette.Base, dark_input)
    palette.setColor(QPalette.AlternateBase, dark_card)
    palette.setColor(QPalette.ToolTipBase, dark_card)
    palette.setColor(QPalette.ToolTipText, dark_text)
    palette.setColor(QPalette.Text, dark_text)
    palette.setColor(QPalette.Button, dark_card)
    palette.setColor(QPalette.ButtonText, dark_text)
    palette.setColor(QPalette.BrightText, QColor("#F87171"))
    palette.setColor(QPalette.Link, QColor("#60A5FA"))
    palette.setColor(QPalette.Highlight, QColor("#3B82F6"))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Disabled, QPalette.Text, dark_muted)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, dark_muted)
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()