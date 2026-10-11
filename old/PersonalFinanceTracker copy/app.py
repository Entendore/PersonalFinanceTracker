#!/usr/bin/env python3

import streamlit as st
import sqlite3
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

class AppConfig:
    APP_DIR = Path.home() / ".personal_finance"
    DB_PATH = APP_DIR / "finance.db"
    LOG_DIR = APP_DIR / "logs"
    BACKUPS_DIR = APP_DIR / "backups"
    EXAMPLE_DATA_LOADED = APP_DIR / "example_data_loaded"
    
    DEFAULT_CATEGORIES = {
        "income": {
            "salary": {"emoji": "💼", "color": "#4361ee"},
            "freelance": {"emoji": "🎤", "color": "#3f37c9"},
            "investments": {"emoji": "📈", "color": "#4895ef"},
            "gifts": {"emoji": "🎁", "color": "#4cc9f0"},
            "other": {"emoji": "🔄", "color": "#4895ef"}
        },
        "expense": {
            "housing": {"emoji": "🏠", "color": "#7209b7"},
            "utilities": {"emoji": "💡", "color": "#560bad"},
            "groceries": {"emoji": "🛒", "color": "#9d4edd"},
            "dining": {"emoji": "🍽️", "color": "#9d4edd"},
            "transportation": {"emoji": "🚗", "color": "#5390d9"},
            "health": {"emoji": "🏥", "color": "#4361ee"},
            "entertainment": {"emoji": "🎬", "color": "#4895ef"},
            "shopping": {"emoji": "🛍️", "color": "#4cc9f0"},
            "personal": {"emoji": "💅", "color": "#4895ef"},
            "education": {"emoji": "📚", "color": "#4361ee"},
            "travel": {"emoji": "✈️", "color": "#4cc9f0"},
            "gifts": {"emoji": "🎁", "color": "#4895ef"},
            "debt": {"emoji": "💳", "color": "#f72585"},
            "subscriptions": {"emoji": "📱", "color": "#b5179e"},
            "other": {"emoji": "❓", "color": "#6c757d"}
        }
    }
    
    LIGHT_THEME = {
        "primary": "#1e293b",
        "secondary": "#334155",
        "accent": "#6366f1",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "background": "#f8fafc",
        "card_bg": "#ffffff",
        "text": "#0f172a",
        "muted_text": "#64748b",
        "border": "#e2e8f0",
        "shadow": "rgba(0,0,0,0.05)"
    }
    
    DARK_THEME = {
        "primary": "#e2e8f0",
        "secondary": "#cbd5e1",
        "accent": "#818cf8",
        "success": "#34d399",
        "warning": "#fbbf24",
        "danger": "#f87171",
        "background": "#0f172a",
        "card_bg": "#1e293b",
        "text": "#f8fafc",
        "muted_text": "#94a3b8",
        "border": "#334155",
        "shadow": "rgba(0,0,0,0.2)"
    }
    
    DEFAULT_CURRENCY = "USD"
    CURRENCY_SYMBOLS = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CAD": "C$",
        "AUD": "A$"
    }
    
    @classmethod
    def init_directories(cls):
        dirs = [cls.APP_DIR, cls.LOG_DIR, cls.BACKUPS_DIR]
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
            if os.name != 'nt':
                directory.chmod(0o700)
        
        logging.basicConfig(
            filename=cls.LOG_DIR / f"finance_{datetime.now().strftime('%Y%m%d')}.log",
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

AppConfig.init_directories()
logger = logging.getLogger("FinanceApp")

def load_example_data(db_path: Path):
    if AppConfig.EXAMPLE_DATA_LOADED.exists():
        return False
    
    db_service = DatabaseService(db_path)
    transaction_service = TransactionService(db_service)
    budget_service = BudgetService(db_service, transaction_service)
    goal_service = GoalService(db_service)
    
    with db_service.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM budgets")
        cursor.execute("DELETE FROM financial_goals")
    
    # Example transactions
    transactions = [
        (3200.00, "salary", "income", "2024-01-15", "Monthly salary", "Acme Corp"),
        (1850.00, "housing", "expense", "2024-01-01", "Monthly rent", "Property Management Inc"),
        (120.00, "utilities", "expense", "2024-01-05", "Electricity bill", "City Power"),
        (250.00, "groceries", "expense", "2024-01-08", "Weekly groceries", "Fresh Market"),
        (45.00, "dining", "expense", "2024-01-12", "Lunch meeting", "Cafe Bistro"),
        (65.00, "transportation", "expense", "2024-01-15", "Gas refill", "Shell Station"),
        (12.99, "subscriptions", "expense", "2024-01-20", "Music streaming", "StreamMusic"),
        (2500.00, "salary", "income", "2024-02-15", "Monthly salary", "Acme Corp"),
        (1850.00, "housing", "expense", "2024-02-01", "Monthly rent", "Property Management Inc"),
        (135.00, "utilities", "expense", "2024-02-05", "Electricity bill", "City Power"),
        (275.00, "groceries", "expense", "2024-02-08", "Weekly groceries", "Fresh Market"),
        (68.00, "dining", "expense", "2024-02-12", "Dinner with friends", "Italian Restaurant"),
        (72.00, "transportation", "expense", "2024-02-15", "Gas refill", "Shell Station"),
        (12.99, "subscriptions", "expense", "2024-02-20", "Music streaming", "StreamMusic"),
        (45.00, "entertainment", "expense", "2024-02-25", "Movie tickets", "Cinema"),
        (2700.00, "salary", "income", "2024-03-15", "Monthly salary", "Acme Corp"),
        (1850.00, "housing", "expense", "2024-03-01", "Monthly rent", "Property Management Inc"),
        (142.00, "utilities", "expense", "2024-03-05", "Electricity bill", "City Power"),
        (310.00, "groceries", "expense", "2024-03-08", "Weekly groceries", "Fresh Market"),
        (55.00, "dining", "expense", "2024-03-12", "Coffee meeting", "Starbucks"),
        (63.00, "transportation", "expense", "2024-03-15", "Gas refill", "Shell Station"),
        (12.99, "subscriptions", "expense", "2024-03-20", "Music streaming", "StreamMusic"),
        (78.00, "health", "expense", "2024-03-22", "Pharmacy", "Health Mart"),
        (150.00, "shopping", "expense", "2024-03-28", "Clothing", "Fashion Store")
    ]
    
    for tx in transactions:
        transaction = Transaction(
            amount=tx[0],
            category=tx[1],
            type=TransactionType(tx[2]),
            date=datetime.strptime(tx[3], "%Y-%m-%d"),
            description=tx[4],
            merchant=tx[5]
        )
        transaction_service.add_transaction(transaction)
    
    # Example budgets
    budgets = [
        ("housing", 1900.00, "2024-01-01", "2024-01-31", False),
        ("utilities", 150.00, "2024-01-01", "2024-01-31", False),
        ("groceries", 300.00, "2024-01-01", "2024-01-31", True),
        ("transportation", 100.00, "2024-01-01", "2024-01-31", False),
        ("dining", 150.00, "2024-01-01", "2024-01-31", False),
        ("entertainment", 100.00, "2024-01-01", "2024-01-31", False),
        ("shopping", 200.00, "2024-01-01", "2024-01-31", False),
        ("subscriptions", 50.00, "2024-01-01", "2024-01-31", False)
    ]
    
    for budget in budgets:
        budget_obj = Budget(
            category=budget[0],
            amount=budget[1],
            period_start=datetime.strptime(budget[2], "%Y-%m-%d"),
            period_end=datetime.strptime(budget[3], "%Y-%m-%d"),
            rollover=budget[4]
        )
        budget_service.set_budget(budget_obj)
    
    # Example goals
    goals = [
        ("Emergency Fund", "savings", 10000.00, 3500.00, "2024-12-31", "High", "6 months of living expenses"),
        ("Vacation", "savings", 2500.00, 800.00, "2024-08-15", "Medium", "Summer vacation to Hawaii"),
        ("Credit Card Debt", "debt", 5000.00, 1500.00, "2025-06-30", "Critical", "Pay off high-interest credit card")
    ]
    
    for goal in goals:
        goal_obj = FinancialGoal(
            name=goal[0],
            type=GoalType(goal[1]),
            target_amount=goal[2],
            current_amount=goal[3],
            target_date=datetime.strptime(goal[4], "%Y-%m-%d"),
            priority=PriorityLevel(goal[5]),
            description=goal[6]
        )
        goal_service.create_goal(goal_obj)
    
    AppConfig.EXAMPLE_DATA_LOADED.touch()
    logger.info("Example data loaded successfully")
    return True

class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"

class GoalType(Enum):
    SAVINGS = "savings"
    DEBT_REDUCTION = "debt"
    MILESTONE = "milestone"

class PriorityLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium" 
    HIGH = "High"
    CRITICAL = "Critical"

@dataclass
class Transaction:
    id: Optional[int] = None
    amount: float = 0.0
    category: str = ""
    type: TransactionType = TransactionType.EXPENSE
    date: datetime = field(default_factory=datetime.now)
    description: str = ""
    merchant: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_display_amount(self, currency_symbol: str = "$") -> str:
        if self.type == TransactionType.INCOME:
            return f"+{currency_symbol}{self.amount:,.2f}"
        return f"-{currency_symbol}{self.amount:,.2f}"

@dataclass
class Budget:
    id: Optional[int] = None
    category: str = ""
    amount: float = 0.0
    period_start: datetime = field(default_factory=lambda: datetime.now().replace(day=1))
    period_end: datetime = field(default_factory=lambda: (datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(seconds=1))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    rollover: bool = False

@dataclass
class FinancialGoal:
    id: Optional[int] = None
    name: str = ""
    type: GoalType = GoalType.SAVINGS
    target_amount: float = 0.0
    current_amount: float = 0.0
    target_date: Optional[datetime] = None
    priority: PriorityLevel = PriorityLevel.MEDIUM
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_completed: bool = False
    
    def progress_percentage(self) -> float:
        if self.target_amount == 0:
            return 0.0
        return (self.current_amount / self.target_amount) * 100
    
    def months_remaining(self) -> Optional[int]:
        if not self.target_date:
            return None
        delta = self.target_date - datetime.now()
        return max(0, delta.days // 30)

class DatabaseService:
    def __init__(self, db_path: Path = AppConfig.DB_PATH):
        self.db_path = db_path
        self._initialize_database()
        self._ensure_example_data()
    
    def _initialize_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA busy_timeout = 5000")
            
            cursor.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                date TIMESTAMP NOT NULL,
                description TEXT,
                merchant TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rollover BOOLEAN DEFAULT 0,
                UNIQUE(category, period_start)
            );
            
            CREATE TABLE IF NOT EXISTS financial_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('savings', 'debt', 'milestone')),
                target_amount REAL NOT NULL CHECK(target_amount > 0),
                current_amount REAL DEFAULT 0 CHECK(current_amount >= 0),
                target_date TIMESTAMP,
                priority TEXT DEFAULT 'Medium' CHECK(priority IN ('Low', 'Medium', 'High', 'Critical')),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_completed BOOLEAN DEFAULT 0
            );
            """)
            
            cursor.executescript("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
            CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
            CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets(period_start, period_end);
            CREATE INDEX IF NOT EXISTS idx_goals_completed ON financial_goals(is_completed);
            """)
    
    def _ensure_example_data(self):
        if not self.db_path.exists():
            load_example_data(self.db_path)
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        return conn
    
    def backup_database(self, backup_dir: Path = AppConfig.BACKUPS_DIR) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"finance_backup_{timestamp}.db"
        
        with self.get_connection() as conn:
            backup_conn = sqlite3.connect(str(backup_path))
            conn.backup(backup_conn)
            backup_conn.close()
        
        if os.name != 'nt':
            backup_path.chmod(0o600)
        
        logger.info(f"Database backed up to {backup_path}")
        return backup_path

class TransactionService:
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def add_transaction(self, transaction: Transaction) -> Transaction:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (
                    amount, category, type, date,
                    description, merchant
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                transaction.amount,
                transaction.category,
                transaction.type.value,
                transaction.date,
                transaction.description,
                transaction.merchant
            ))
            
            transaction.id = cursor.lastrowid
            transaction.created_at = datetime.now()
            transaction.updated_at = datetime.now()
        
        logger.info(f"Transaction added: {transaction.id}")
        return transaction
    
    def parse_natural_language(self, text: str, default_date: Optional[datetime] = None) -> Transaction:
        text = text.lower().strip()
        amount_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
        if not amount_match:
            raise ValueError("Could not find amount in transaction text")
        
        amount_str = amount_match.group(1).replace(',', '')
        amount = float(amount_str)
        
        t_type = TransactionType.EXPENSE
        if any(word in text for word in ['salary', 'pay', 'income', 'bonus', 'refund', 'reimbursement', 'gift']):
            t_type = TransactionType.INCOME
        
        merchant = ""
        description = ""
        
        pre_amount = text[:amount_match.start()].strip()
        if pre_amount:
            for verb in ['bought', 'spent', 'paid', 'transferred', 'received', 'got']:
                pre_amount = pre_amount.replace(verb, '').strip()
            merchant = pre_amount.title()
        
        post_amount = text[amount_match.end():].strip()
        if post_amount:
            for word in ['for', 'on', 'at', 'to', 'from', 'the', 'this', 'that']:
                post_amount = post_amount.replace(word, '').strip()
            description = post_amount.capitalize()
        
        category = "other"
        if t_type == TransactionType.INCOME:
            if any(word in text for word in ['salary', 'pay', 'wage']):
                category = "salary"
            elif any(word in text for word in ['bonus', 'commission']):
                category = "freelance"
            elif any(word in text for word in ['interest', 'dividend', 'investment']):
                category = "investments"
        else:
            if any(word in text for word in ['grocer', 'food', 'market', 'walmart', 'target']):
                category = "groceries"
            elif any(word in text for word in ['starbucks', 'coffee', 'restaurant', 'diner', 'grill', 'pizza']):
                category = "dining"
            elif any(word in text for word in ['gas', 'fuel', 'shell', 'exxon', 'chevron', 'petrol']):
                category = "transportation"
            elif any(word in text for word in ['electric', 'water', 'gas', 'utility', 'bill']):
                category = "utilities"
            elif any(word in text for word in ['rent', 'mortgage', 'housing']):
                category = "housing"
        
        date = default_date or datetime.now()
        
        return Transaction(
            amount=amount,
            category=category,
            type=t_type,
            date=date,
            description=description,
            merchant=merchant
        )
    
    def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        t_type: Optional[TransactionType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        query = """
            SELECT id, amount, category, type, date,
                   description, merchant, created_at, updated_at
            FROM transactions
            WHERE 1=1
        """
        params: List[Any] = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if t_type:
            query += " AND type = ?"
            params.append(t_type.value)
        
        query += " ORDER BY date DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                Transaction(
                    id=row["id"],
                    amount=row["amount"],
                    category=row["category"],
                    type=TransactionType(row["type"]),
                    date=datetime.fromisoformat(row["date"]) if isinstance(row["date"], str) else row["date"],
                    description=row["description"],
                    merchant=row["merchant"],
                    created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
                    updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"]
                )
                for row in rows
            ]

class BudgetService:
    def __init__(self, db_service: DatabaseService, transaction_service: TransactionService):
        self.db = db_service
        self.transaction_service = transaction_service
    
    def set_budget(self, budget: Budget) -> Budget:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id
                FROM budgets
                WHERE category = ? AND period_start = ?
            """, (budget.category, budget.period_start))
            
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE budgets
                    SET amount = ?, period_end = ?, rollover = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (budget.amount, budget.period_end, budget.rollover, existing["id"]))
                budget.id = existing["id"]
            else:
                cursor.execute("""
                    INSERT INTO budgets (
                        category, amount, period_start, period_end, rollover
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    budget.category,
                    budget.amount,
                    budget.period_start,
                    budget.period_end,
                    budget.rollover
                ))
                budget.id = cursor.lastrowid
            
            budget.created_at = datetime.now()
            budget.updated_at = datetime.now()
        
        logger.info(f"Budget set for category {budget.category}: ${budget.amount}")
        return budget
    
    def get_budget_status(self, category: str, date: Optional[datetime] = None) -> Dict[str, Any]:
        if date is None:
            date = datetime.now()
        
        period_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = (period_start + relativedelta(months=1)) - timedelta(seconds=1)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, amount, rollover
                FROM budgets
                WHERE category = ?
                AND period_start <= ? AND period_end >= ?
                ORDER BY period_start DESC
                LIMIT 1
            """, (category, date, date))
            
            budget_row = cursor.fetchone()
            budget_amount = budget_row["amount"] if budget_row else 0.0
            has_budget = budget_row is not None
            
            spent_amount = self.get_spent_amount(category, period_start, period_end)
            
            remaining = budget_amount - spent_amount if has_budget else 0.0
            percentage_used = (spent_amount / budget_amount * 100) if budget_amount > 0 else 0.0
            is_over_budget = spent_amount > budget_amount if has_budget else False
            
            return {
                "category": category,
                "budget_amount": budget_amount,
                "spent_amount": spent_amount,
                "remaining": remaining,
                "percentage_used": percentage_used,
                "is_over_budget": is_over_budget,
                "has_budget": has_budget,
                "period_start": period_start,
                "period_end": period_end
            }
    
    def get_spent_amount(self, category: str, start_date: datetime, end_date: datetime) -> float:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE category = ? AND type = 'expense'
                AND date BETWEEN ? AND ?
            """, (category, start_date, end_date))
            
            result = cursor.fetchone()
            return result["total"] if result else 0.0
    
    def get_all_budget_statuses(self, date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        if date is None:
            date = datetime.now()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT category
                FROM transactions
                WHERE type = 'expense'
                AND date >= date('now', '-6 months')
            """)
            
            categories = [row["category"] for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT DISTINCT category
                FROM budgets
                WHERE period_end >= ?
            """, (date,))
            
            budget_categories = [row["category"] for row in cursor.fetchall()]
            all_categories = list(set(categories + budget_categories))
        
        statuses = []
        for category in all_categories:
            status = self.get_budget_status(category, date)
            if status["has_budget"] or status["spent_amount"] > 0:
                statuses.append(status)
        
        statuses.sort(key=lambda x: (x["percentage_used"], x["spent_amount"]), reverse=True)
        
        return statuses

class GoalService:
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def create_goal(self, goal: FinancialGoal) -> FinancialGoal:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO financial_goals (
                    name, type, target_amount, current_amount,
                    target_date, priority, description, is_completed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                goal.name,
                goal.type.value,
                goal.target_amount,
                goal.current_amount,
                goal.target_date,
                goal.priority.value,
                goal.description,
                goal.is_completed
            ))
            
            goal.id = cursor.lastrowid
            goal.created_at = datetime.now()
            goal.updated_at = datetime.now()
        
        logger.info(f"Goal created: {goal.name}")
        return goal
    
    def get_goals(self, include_completed: bool = False) -> List[FinancialGoal]:
        query = """
            SELECT *
            FROM financial_goals
            WHERE 1=1
        """
        params = []
        
        if not include_completed:
            query += " AND is_completed = 0"
        
        query += " ORDER BY priority DESC, target_date ASC"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                FinancialGoal(
                    id=row["id"],
                    name=row["name"],
                    type=GoalType(row["type"]),
                    target_amount=row["target_amount"],
                    current_amount=row["current_amount"],
                    target_date=datetime.fromisoformat(row["target_date"]) if row["target_date"] else None,
                    priority=PriorityLevel(row["priority"]),
                    description=row["description"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    is_completed=bool(row["is_completed"])
                )
                for row in rows
            ]

class FinanceApp:
    def __init__(self):
        self._init_theme()
        self.db_service = DatabaseService()
        self.transaction_service = TransactionService(self.db_service)
        self.budget_service = BudgetService(self.db_service, self.transaction_service)
        self.goal_service = GoalService(self.db_service)
        self._init_session_state()
        self._load_custom_css()
    
    def _init_theme(self):
        if 'theme' not in st.session_state:
            st.session_state.theme = 'light'
    
    def _init_session_state(self):
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "dashboard"
        if 'currency' not in st.session_state:
            st.session_state.currency = AppConfig.DEFAULT_CURRENCY
        if 'backup_dir' not in st.session_state:
            st.session_state.backup_dir = str(AppConfig.BACKUPS_DIR)
    
    def _load_custom_css(self):
        theme = AppConfig.LIGHT_THEME if st.session_state.theme == 'light' else AppConfig.DARK_THEME
        
        st.markdown(f"""
        <style>
            :root {{
                --primary-color: {theme["primary"]};
                --secondary-color: {theme["secondary"]};
                --accent-color: {theme["accent"]};
                --success-color: {theme["success"]};
                --warning-color: {theme["warning"]};
                --danger-color: {theme["danger"]};
                --background-color: {theme["background"]};
                --card-background: {theme["card_bg"]};
                --text-color: {theme["text"]};
                --muted-text: {theme["muted_text"]};
                --border-color: {theme["border"]};
                --shadow-color: {theme["shadow"]};
            }}
            
            .stApp {{
                background-color: var(--background-color);
                color: var(--text-color);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
            
            .header-container {{
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 0.75rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 6px var(--shadow-color);
            }}
            
            .header-title {{
                font-size: 1.75rem;
                font-weight: 600;
                margin-bottom: 0.25rem;
            }}
            
            .metric-card {{
                background: var(--card-background);
                border-radius: 0.75rem;
                padding: 1.25rem;
                box-shadow: 0 2px 4px var(--shadow-color);
                border: 1px solid var(--border-color);
                height: 100%;
            }}
            
            .metric-title {{
                font-size: 0.95rem;
                color: var(--muted-text);
                margin-bottom: 0.5rem;
                font-weight: 500;
            }}
            
            .metric-value {{
                font-size: 1.75rem;
                font-weight: 600;
                margin-bottom: 0.25rem;
            }}
            
            .stButton > button {{
                background: var(--accent-color);
                color: white;
                border: none;
                border-radius: 0.5rem;
                padding: 0.6rem 1.2rem;
                font-weight: 500;
                transition: all 0.2s ease;
            }}
            
            [data-testid="stSidebar"] {{
                background: var(--card-background);
                border-right: 1px solid var(--border-color);
            }}
            
            [data-testid="stSidebar"] .sidebar-title {{
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 1rem;
                color: var(--primary-color);
                text-align: center;
                padding: 0.75rem 0;
                border-bottom: 1px solid var(--border-color);
            }}
        </style>
        """, unsafe_allow_html=True)
    
    def _metric_card(self, title, value, delta=None, positive=True, icon="📊"):
        delta_class = "positive" if positive else "negative"
        delta_icon = "↑" if positive else "↓"
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">
                <span style="margin-right: 0.5rem;">{icon}</span>{title}
            </div>
            <div class="metric-value">{value}</div>
            <div class="metric-diff {delta_class}">
                {f'{delta_icon} {delta}' if delta else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _show_sidebar(self):
        with st.sidebar:
            st.markdown('<div class="sidebar-title">💰 Finance</div>', unsafe_allow_html=True)
            
            theme_col1, theme_col2, theme_col3 = st.columns([1, 2, 1])
            with theme_col2:
                dark_mode = st.toggle("🌙", value=(st.session_state.theme == 'dark'))
                if dark_mode:
                    st.session_state.theme = 'dark'
                else:
                    st.session_state.theme = 'light'
                self._load_custom_css()
            
            st.markdown("---")
            
            nav_items = [
                ("📊", "Dashboard", "dashboard"),
                ("➕", "Add Transaction", "add_transaction"),
                ("💰", "Budgets", "budgets"),
                ("🎯", "Goals", "goals"),
                ("📦", "Backup", "backup")
            ]
            
            for icon, label, page in nav_items:
                if st.button(f"{icon} {label}", key=f"nav_{page}", use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()
    
    def _show_dashboard(self):
        st.markdown("""
        <div class="header-container">
            <div class="header-title">Dashboard</div>
        </div>
        """, unsafe_allow_html=True)
        
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + relativedelta(months=1)) - timedelta(seconds=1)
        
        income_transactions = self.transaction_service.get_transactions(
            start_date=month_start,
            end_date=month_end,
            t_type=TransactionType.INCOME
        )
        
        expense_transactions = self.transaction_service.get_transactions(
            start_date=month_start,
            end_date=month_end,
            t_type=TransactionType.EXPENSE
        )
        
        total_income = sum(t.amount for t in income_transactions)
        total_expenses = sum(t.amount for t in expense_transactions)
        net_cashflow = total_income - total_expenses
        
        budget_statuses = self.budget_service.get_all_budget_statuses()
        on_track_budgets = sum(1 for s in budget_statuses if not s["is_over_budget"] and s["percentage_used"] <= 90)
        total_budgets = len(budget_statuses)
        
        goals = self.goal_service.get_goals(include_completed=False)
        
        st.markdown("### Financial Snapshot")
        col1, col2, col3, col4 = st.columns(4)
        
        symbol = AppConfig.CURRENCY_SYMBOLS.get(st.session_state.currency, "$")
        
        with col1:
            self._metric_card(
                title="Total Income",
                value=f"{symbol}{total_income:,.2f}",
                icon="💼"
            )
        
        with col2:
            self._metric_card(
                title="Total Expenses",
                value=f"{symbol}{total_expenses:,.2f}",
                icon="🛒"
            )
        
        with col3:
            self._metric_card(
                title="Net Cashflow",
                value=f"{'+' if net_cashflow >= 0 else '-'}{symbol}{abs(net_cashflow):,.2f}",
                positive=net_cashflow >= 0,
                icon="📈"
            )
        
        with col4:
            budget_percent = (on_track_budgets / total_budgets * 100) if total_budgets > 0 else 100
            self._metric_card(
                title="Budget Health",
                value=f"{budget_percent:.0f}%",
                positive=budget_percent >= 80,
                icon="🎯"
            )
        
        # Charts would go here in a complete implementation
    
    def _show_add_transaction(self):
        st.markdown("""
        <div class="header-container">
            <div class="header-title">Add Transaction</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("transaction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                t_type = st.selectbox("Type", ["Income", "Expense"], index=1)
                amount = st.number_input(f"Amount ({AppConfig.CURRENCY_SYMBOLS[st.session_state.currency]})", min_value=0.01, step=0.01)
            
            with col2:
                category_type = "income" if t_type == "Income" else "expense"
                categories = list(AppConfig.DEFAULT_CATEGORIES[category_type].keys())
                category = st.selectbox("Category", categories, format_func=lambda x: f"{AppConfig.DEFAULT_CATEGORIES[category_type][x]['emoji']} {x.replace('_', ' ').title()}")
                date = st.date_input("Date", value=datetime.now())
            
            merchant = st.text_input("Merchant/Source")
            description = st.text_input("Description")
            
            submitted = st.form_submit_button("Add Transaction", use_container_width=True)
            
            if submitted:
                try:
                    transaction = Transaction(
                        amount=amount,
                        category=category,
                        type=TransactionType.INCOME if t_type == "Income" else TransactionType.EXPENSE,
                        date=datetime.combine(date, datetime.min.time()),
                        merchant=merchant,
                        description=description
                    )
                    self.transaction_service.add_transaction(transaction)
                    st.success("✅ Transaction added successfully!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    def _show_budgets(self):
        st.markdown("""
        <div class="header-container">
            <div class="header-title">Budgets</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("➕ Create Budget", use_container_width=True):
            st.session_state.show_budget_form = True
        
        if st.session_state.get('show_budget_form', False):
            with st.form("budget_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    categories = list(AppConfig.DEFAULT_CATEGORIES["expense"].keys())
                    category = st.selectbox("Category", categories, format_func=lambda x: f"{AppConfig.DEFAULT_CATEGORIES['expense'][x]['emoji']} {x.replace('_', ' ').title()}")
                    amount = st.number_input(f"Budget Amount ({AppConfig.CURRENCY_SYMBOLS[st.session_state.currency]})", min_value=0.01, step=1.00)
                
                with col2:
                    now = datetime.now()
                    period_start = st.date_input("Period Start", value=now.replace(day=1))
                    period_end = st.date_input("Period End", value=(now.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1))
                    rollover = st.checkbox("Allow unused amount to roll over", value=True)
                
                submitted = st.form_submit_button("Create Budget", use_container_width=True)
                
                if submitted:
                    try:
                        budget = Budget(
                            category=category,
                            amount=amount,
                            period_start=datetime.combine(period_start, datetime.min.time()),
                            period_end=datetime.combine(period_end, datetime.max.time()),
                            rollover=rollover
                        )
                        self.budget_service.set_budget(budget)
                        st.success("✅ Budget created successfully!")
                        st.session_state.show_budget_form = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        budget_statuses = self.budget_service.get_all_budget_statuses()
        if budget_statuses:
            for status in budget_statuses:
                category = status["category"].replace('_', ' ').title()
                budgeted = status["budget_amount"]
                spent = status["spent_amount"]
                remaining = status["remaining"]
                used_pct = status["percentage_used"]
                is_over = status["is_over_budget"]
                
                symbol = AppConfig.CURRENCY_SYMBOLS.get(st.session_state.currency, "$")
                color = AppConfig.LIGHT_THEME["success"] if used_pct <= 75 else AppConfig.LIGHT_THEME["warning"] if used_pct <= 90 else AppConfig.LIGHT_THEME["danger"]
                if st.session_state.theme == 'dark':
                    color = AppConfig.DARK_THEME["success"] if used_pct <= 75 else AppConfig.DARK_THEME["warning"] if used_pct <= 90 else AppConfig.DARK_THEME["danger"]
                
                with st.container():
                    st.markdown(f"""
                    <div style="background: var(--card-background); border-radius: 0.75rem; padding: 1.25rem; margin-bottom: 1rem; border: 1px solid var(--border-color);">
                        <div style="font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;">
                            {category}
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem; font-size: 0.95rem;">
                            <span>Budgeted: {symbol}{budgeted:,.2f}</span>
                            <span>Spent: {symbol}{spent:,.2f}</span>
                        </div>
                        <div style="background: var(--border-color); border-radius: 0.25rem; height: 0.4rem; overflow: hidden; margin-bottom: 0.5rem;">
                            <div style="background: {color}; height: 100%; width: {min(used_pct, 100)}%;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; color: var(--muted-text); font-size: 0.85rem;">
                            <span>Remaining: <span style="color: {AppConfig.LIGHT_THEME['success'] if remaining >= 0 else AppConfig.LIGHT_THEME['danger']};">
                                {symbol if remaining >= 0 else '-'}{abs(remaining):,.2f}
                            </span></span>
                            <span>{used_pct:.0f}% used</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    def _show_goals(self):
        st.markdown("""
        <div class="header-container">
            <div class="header-title">Goals</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("➕ Create Goal", use_container_width=True):
            st.session_state.show_goal_form = True
        
        if st.session_state.get('show_goal_form', False):
            with st.form("goal_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    goal_type = st.selectbox("Goal Type", ["Savings", "Debt Reduction", "Milestone"], format_func=lambda x: f"{'💰' if x == 'Savings' else '💳' if x == 'Debt Reduction' else '🎯'} {x}")
                    name = st.text_input("Goal Name")
                    target_amount = st.number_input(f"Target Amount ({AppConfig.CURRENCY_SYMBOLS[st.session_state.currency]})", min_value=1.00, step=100.00)
                
                with col2:
                    current_amount = st.number_input(f"Current Amount ({AppConfig.CURRENCY_SYMBOLS[st.session_state.currency]})", min_value=0.00, max_value=target_amount, step=100.00)
                    target_date = st.date_input("Target Date", min_value=datetime.now().date() + timedelta(days=30))
                    priority = st.select_slider("Priority", options=["Low", "Medium", "High", "Critical"], value="Medium")
                
                description = st.text_area("Description", placeholder="Optional details about your goal")
                
                submitted = st.form_submit_button("Create Goal", use_container_width=True)
                
                if submitted:
                    try:
                        type_map = {
                            "Savings": GoalType.SAVINGS,
                            "Debt Reduction": GoalType.DEBT_REDUCTION,
                            "Milestone": GoalType.MILESTONE
                        }
                        
                        priority_map = {
                            "Low": PriorityLevel.LOW,
                            "Medium": PriorityLevel.MEDIUM,
                            "High": PriorityLevel.HIGH,
                            "Critical": PriorityLevel.CRITICAL
                        }
                        
                        goal = FinancialGoal(
                            name=name,
                            type=type_map[goal_type],
                            target_amount=target_amount,
                            current_amount=current_amount,
                            target_date=datetime.combine(target_date, datetime.min.time()),
                            priority=priority_map[priority],
                            description=description
                        )
                        
                        self.goal_service.create_goal(goal)
                        st.success("✅ Goal created successfully!")
                        st.session_state.show_goal_form = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        goals = self.goal_service.get_goals(include_completed=False)
        if goals:
            for goal in goals:
                progress = goal.progress_percentage()
                color = AppConfig.LIGHT_THEME["success"] if progress >= 100 else AppConfig.LIGHT_THEME["warning"] if progress >= 75 else AppConfig.LIGHT_THEME["danger"]
                if st.session_state.theme == 'dark':
                    color = AppConfig.DARK_THEME["success"] if progress >= 100 else AppConfig.DARK_THEME["warning"] if progress >= 75 else AppConfig.DARK_THEME["danger"]
                
                symbol = AppConfig.CURRENCY_SYMBOLS.get(st.session_state.currency, "$")
                
                with st.container():
                    st.markdown(f"""
                    <div style="background: var(--card-background); border-radius: 0.75rem; padding: 1.25rem; margin-bottom: 1rem; border: 1px solid var(--border-color);">
                        <div style="font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;">
                            {goal.name}
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem; font-size: 0.95rem;">
                            <span>Target: {symbol}{goal.target_amount:,.2f}</span>
                            <span>Current: {symbol}{goal.current_amount:,.2f}</span>
                        </div>
                        <div style="background: var(--border-color); border-radius: 0.25rem; height: 0.4rem; overflow: hidden; margin-bottom: 0.5rem;">
                            <div style="background: {color}; height: 100%; width: {min(progress, 100)}%;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; color: var(--muted-text); font-size: 0.85rem;">
                            <span>Progress: {progress:.0f}%</span>
                            <span>{goal.months_remaining() or 'No deadline'} months left</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    def _show_backup(self):
        st.markdown("""
        <div class="header-container">
            <div class="header-title">Backup & Export</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔐 Database Backup")
            if st.button("Create Backup Now", type="primary", use_container_width=True):
                try:
                    backup_path = Path(st.session_state.backup_dir)
                    backup_path.mkdir(parents=True, exist_ok=True)
                    backup_file = self.db_service.backup_database(backup_path)
                    st.success(f"✅ Backup created: `{backup_file}`")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
            st.markdown(f"#### Current Backup Location")
            st.code(st.session_state.backup_dir)
        
        with col2:
            st.markdown("### 📤 Export Data")
            export_format = st.selectbox("Format", ["CSV", "Excel"])
            if st.button("Export Transactions", use_container_width=True):
                try:
                    transactions = self.transaction_service.get_transactions(limit=1000)
                    df = pd.DataFrame([{
                        'Date': t.date.strftime('%Y-%m-%d'),
                        'Category': t.category,
                        'Type': t.type.value,
                        'Amount': t.amount,
                        'Merchant': t.merchant,
                        'Description': t.description
                    } for t in transactions])
                    
                    csv = df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="finance_export_{datetime.now().strftime("%Y%m%d")}.csv" style="display: inline-block; background: var(--accent-color); color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; text-decoration: none; margin-top: 1rem;">Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    def run(self):
        self._show_sidebar()
        
        if st.session_state.current_page == "dashboard":
            self._show_dashboard()
        elif st.session_state.current_page == "add_transaction":
            self._show_add_transaction()
        elif st.session_state.current_page == "budgets":
            self._show_budgets()
        elif st.session_state.current_page == "goals":
            self._show_goals()
        elif st.session_state.current_page == "backup":
            self._show_backup()

if __name__ == "__main__":
    try:
        app = FinanceApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.error(f"Application crashed: {str(e)}", exc_info=True)