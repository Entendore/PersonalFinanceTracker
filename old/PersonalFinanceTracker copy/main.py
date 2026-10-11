import sqlite3
import csv
import os
from datetime import datetime, timedelta
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, ListProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy_garden.graph import Graph, MeshLinePlot, PieChart

# --- Database Logic ---
DB_NAME = 'finances.db'

def init_db():
    """Initializes the database and creates all necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL UNIQUE,
        amount REAL NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
        name TEXT PRIMARY KEY UNIQUE
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recurring_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        frequency TEXT NOT NULL,
        next_due_date TEXT NOT NULL
    )''')
    
    # Add default categories if the table is empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = ['Groceries', 'Transport', 'Utilities', 'Entertainment', 'Dining Out', 'Healthcare', 'Salary', 'Other']
        for cat in default_categories:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
            
    conn.commit()
    conn.close()

# --- Category Database Functions ---
def add_category(name):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        return True, "Category added successfully."
    except sqlite3.IntegrityError:
        return False, "Category already exists."
    finally:
        conn.close()

def get_all_categories():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories ORDER BY name")
    rows = cursor.fetchall(); conn.close()
    return [row[0] for row in rows]

def delete_category(name):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE category = ?", (name,))
    if cursor.fetchone()[0] > 0: conn.close(); return False, "Cannot delete category: it is used in transactions."
    cursor.execute("SELECT COUNT(*) FROM budgets WHERE category = ?", (name,))
    if cursor.fetchone()[0] > 0: conn.close(); return False, "Cannot delete category: it is used in a budget."
    cursor.execute("DELETE FROM categories WHERE name = ?", (name,))
    conn.commit(); conn.close()
    return True, "Category deleted successfully."

# --- Budget Database Functions ---
def add_budget(category, amount):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO budgets (category, amount) VALUES (?, ?)', (category, amount))
    conn.commit(); conn.close()

def get_all_budgets():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute('SELECT category, amount FROM budgets')
    rows = cursor.fetchall(); conn.close()
    return {row[0]: row[1] for row in rows}

def delete_budget(category):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute('DELETE FROM budgets WHERE category = ?', (category,))
    conn.commit(); conn.close()

# --- Recurring Transaction Functions ---
def add_recurring_template(t_type, amount, category, description, frequency, next_due_date):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute('''INSERT INTO recurring_templates (type, amount, category, description, frequency, next_due_date)
        VALUES (?, ?, ?, ?, ?, ?)''', (t_type, amount, category, description, frequency, next_due_date))
    conn.commit(); conn.close()

def get_all_recurring_templates():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute('SELECT id, type, amount, category, description, frequency, next_due_date FROM recurring_templates ORDER BY next_due_date')
    rows = cursor.fetchall(); conn.close()
    return rows

def delete_recurring_template(template_id):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute('DELETE FROM recurring_templates WHERE id = ?', (template_id,))
    conn.commit(); conn.close()

def process_due_recurring_transactions():
    """Checks for and creates any transactions that are due."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute('SELECT id, type, amount, category, description, frequency, next_due_date FROM recurring_templates WHERE next_due_date <= ?', (today_str,))
    due_templates = cursor.fetchall()
    
    for template in due_templates:
        t_id, t_type, t_amount, t_category, t_description, t_frequency, t_next_due_str = template
        add_transaction(t_type, t_amount, t_category, t_description, t_next_due_str)
        
        next_due_date_obj = datetime.strptime(t_next_due_str, '%Y-%m-%d')
        if t_frequency == 'Weekly': next_due_date_obj += timedelta(weeks=1)
        elif t_frequency == 'Monthly':
            if next_due_date_obj.month == 12:
                next_due_date_obj = next_due_date_obj.replace(year=next_due_date_obj.year + 1, month=1)
            else:
                next_due_date_obj = next_due_date_obj.replace(month=next_due_date_obj.month + 1)
        elif t_frequency == 'Yearly':
            next_due_date_obj = next_due_date_obj.replace(year=next_due_date_obj.year + 1)
            
        cursor.execute('UPDATE recurring_templates SET next_due_date = ? WHERE id = ?', (next_due_date_obj.strftime('%Y-%m-%d'), t_id))
        
    conn.commit(); conn.close()
    return len(due_templates)

# --- Transaction Database Functions ---
def add_transaction(t_type, amount, category, description, date):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute('INSERT INTO transactions (type, amount, category, description, date) VALUES (?, ?, ?, ?, ?)', (t_type, amount, category, description, date))
    conn.commit(); conn.close()

def get_filtered_transactions(search_text='', category_filter='', start_date='', end_date=''):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    query, params = 'SELECT id, type, amount, category, description, date FROM transactions WHERE 1=1', []
    if search_text: query += ' AND (description LIKE ? OR category LIKE ?)'; params.extend([f'%{search_text}%', f'%{search_text}%'])
    if category_filter: query += ' AND category = ?'; params.append(category_filter)
    if start_date: query += ' AND date >= ?'; params.append(start_date)
    if end_date: query += ' AND date <= ?'; params.append(end_date)
    query += ' ORDER BY date DESC'
    cursor.execute(query, params); rows = cursor.fetchall(); conn.close()
    return rows

def get_spending_by_category():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute("SELECT category, SUM(amount) FROM transactions WHERE type='Expense' GROUP BY category")
    data = cursor.fetchall(); conn.close()
    return data

def get_monthly_totals():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute("""SELECT strftime('%Y-%m', date) as month, type, SUM(amount) FROM transactions GROUP BY month, type ORDER BY month ASC""")
    data = cursor.fetchall(); conn.close()
    return data

def get_current_month_spending():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    current_month = datetime.now().strftime('%Y-%m')
    cursor.execute("""SELECT category, SUM(amount) FROM transactions WHERE type='Expense' AND strftime('%Y-%m', date) = ? GROUP BY category""", (current_month,))
    data = cursor.fetchall(); conn.close()
    return {row[0]: row[1] for row in data}

def delete_transaction_by_id(trans_id):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = ?', (trans_id,))
    conn.commit(); conn.close()

def update_transaction_by_id(trans_id, t_type, amount, category, description, date):
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute('UPDATE transactions SET type = ?, amount = ?, category = ?, description = ?, date = ? WHERE id = ?', (t_type, amount, category, description, date, trans_id))
    conn.commit(); conn.close()

def get_summary():
    conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
    cursor.execute('SELECT type, SUM(amount) FROM transactions GROUP BY type')
    results = cursor.fetchall(); conn.close()
    income, expense = 0.0, 0.0
    for t_type, amount in results:
        if t_type == 'Income': income += amount
        elif t_type == 'Expense': expense += amount
    return income, expense, income - expense

def export_all_transactions_to_csv(file_path):
    try:
        transactions = get_filtered_transactions()
        if not transactions: return False, "No data to export."
        with open(file_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['ID', 'Type', 'Amount', 'Category', 'Description', 'Date'])
            csv_writer.writerows(transactions)
        return True, f"Successfully exported {len(transactions)} transactions."
    except Exception as e: return False, f"Error during export: {e}"

# --- Kivy UI Logic ---
def refresh_all_category_spinners(app_instance):
    categories = get_all_categories()
    app_instance.root.get_screen('tracker').ids.category_spinner.values = categories
    app_instance.root.get_screen('tracker').ids.filter_category_spinner.values = ['All Categories'] + categories
    app_instance.root.get_screen('budgets').ids.budget_category_spinner.values = categories
    app_instance.root.get_screen('recurring').ids.recurring_category_spinner.values = categories
    app_instance.root.get_screen('categories').update_category_list()

class FinancialTrackerScreen(Screen):
    transaction_list = ListProperty()
    total_income = NumericProperty(0.0)
    total_expense = NumericProperty(0.0)
    total_balance = NumericProperty(0.0)

    def on_enter(self, *args):
        self.ids.category_spinner.values = get_all_categories()
        self.ids.filter_category_spinner.values = ['All Categories'] + get_all_categories()
        self.update_data()

    def update_data(self):
        income, expense, balance = get_summary()
        self.total_income, self.total_expense, self.total_balance = income, expense, balance
        search_text = self.ids.search_input.text
        category_filter = self.ids.filter_category_spinner.text if self.ids.filter_category_spinner.text != 'All Categories' else ''
        start_date, end_date = self.ids.start_date_input.text, self.ids.end_date_input.text
        transactions = get_filtered_transactions(search_text, category_filter, start_date, end_date)
        self.transaction_list = [{'id': t[0], 'type': t[1], 'amount': f"${t[2]:.2f}", 'category': t[3], 'description': t[4], 'date': t[5], 'color': (0.2, 0.8, 0.4, 1) if t[1] == 'Income' else (0.9, 0.3, 0.3, 1)} for t in transactions]
        self.ids.rv.data = self.transaction_list

    def add_transaction(self):
        t_type = 'Income' if self.ids.toggle_income.state == 'down' else 'Expense'
        try: amount = float(self.ids.input_amount.text)
        except ValueError: print("Error: Amount must be a number."); return
        category = self.ids.category_spinner.text
        description = self.ids.input_description.text
        date = self.ids.input_date.text or datetime.now().strftime('%Y-%m-%d')
        if not category or category == 'Select Category': print("Error: A valid category must be selected."); return
        add_transaction(t_type, amount, category, description, date)
        self.ids.input_amount.text = ''; self.ids.input_description.text = ''; self.ids.input_date.text = ''
        self.update_data()

    def show_delete_popup(self, trans_data):
        popup_content = ConfirmDeletePopup(transaction_id=trans_data['id'], main_root=self)
        popup = Popup(title="Confirm Delete", content=popup_content, size_hint=(0.8, None), height=150, auto_dismiss=False)
        popup_content.popup = popup; popup.open()

    def delete_transaction(self, popup, trans_id):
        delete_transaction_by_id(trans_id); popup.dismiss(); self.update_data()

    def show_edit_popup(self, trans_data):
        popup_content = EditPopup(transaction_data=trans_data, main_root=self)
        popup = Popup(title="Edit Transaction", content=popup_content, size_hint=(0.9, None), height=400, auto_dismiss=False)
        popup_content.popup = popup; popup.open()

    def save_edited_transaction(self, popup, trans_id):
        t_type = 'Income' if popup_content.ids.toggle_income.state == 'down' else 'Expense'
        try: amount = float(popup_content.ids.input_amount.text)
        except ValueError: print("Error: Amount must be a number."); return
        category = popup_content.ids.edit_category_spinner.text
        description = popup_content.ids.input_description.text
        date = popup_content.ids.input_date.text
        if not category: print("Error: Category cannot be empty."); return
        update_transaction_by_id(trans_id, t_type, amount, category, description, date)
        popup.dismiss(); self.update_data()

    def show_export_popup(self):
        popup_content = ExportPopup(main_root=self)
        popup = Popup(title="Export Data to CSV", content=popup_content, size_hint=(0.9, 0.9), auto_dismiss=False)
        popup_content.popup = popup; popup.open()

    def perform_export(self, popup, path, filename):
        if not filename: print("Error: Filename cannot be empty."); return
        full_path = os.path.join(path, filename)
        if not full_path.endswith('.csv'): full_path += '.csv'
        success, message = export_all_transactions_to_csv(full_path)
        print(message); popup.dismiss()

class AnalyticsScreen(Screen):
    def on_enter(self, *args): self.update_pie_chart(); self.update_line_chart()
    def update_pie_chart(self):
        self.ids.pie_chart.chart_data = []; data = get_spending_by_category()
        if not data: self.ids.pie_chart_label.text = "No expense data available."; return
        self.ids.pie_chart_label.text = "Spending by Category"
        total_spending = sum(d[1] for d in data); chart_items = []
        for category, amount in data:
            percentage = (amount / total_spending) * 100
            chart_items.append({'value': amount, 'label': f'{category}\n${amount:.0f} ({percentage:.1f}%)', 'color': (0.3, 0.6, 1, 1)})
        self.ids.pie_chart.chart_data = chart_items
    def update_line_chart(self):
        self.ids.line_chart.clear_plots(); data = get_monthly_totals()
        if not data: self.ids.line_chart_label.text = "No data available for trends."; return
        self.ids.line_chart_label.text = "Income vs. Expenses Trend"
        income_data, expense_data = [], []; months = sorted(list(set(d[0] for d in data)))
        income_map = {d[0]: d[2] for d in data if d[1] == 'Income'}
        expense_map = {d[0]: d[2] for d in data if d[1] == 'Expense'}
        for i, month in enumerate(months):
            income_data.append((i, income_map.get(month, 0))); expense_data.append((i, expense_map.get(month, 0)))
        income_plot = MeshLinePlot(color=[0.2, 0.8, 0.4, 1]); expense_plot = MeshLinePlot(color=[0.9, 0.3, 0.3, 1])
        income_plot.points = income_data; expense_plot.points = expense_data
        self.ids.line_chart.add_plot(income_plot); self.ids.line_chart.add_plot(expense_plot)
        self.ids.line_chart.x_ticks_major = 1; self.ids.line_chart.x_ticks_minor = 0; self.ids.line_chart.x_grid = True; self.ids.line_chart.y_grid = True
        self.ids.line_chart.x_labels = months
        self.ids.line_chart.ymax = max(max(income_map.values(), default=0), max(expense_map.values(), default=0)) * 1.1 or 100
        self.ids.line_chart.ymin = 0

class BudgetsScreen(Screen):
    budget_list = ListProperty()
    def on_enter(self, *args):
        self.ids.budget_category_spinner.values = get_all_categories()
        self.update_budget_list()
    def update_budget_list(self):
        budgets = get_all_budgets(); spending = get_current_month_spending(); self.budget_list = []
        for category, budget_amount in budgets.items():
            spent_amount = spending.get(category, 0.0); remaining = budget_amount - spent_amount; percentage = (spent_amount / budget_amount) * 100 if budget_amount > 0 else 0
            bar_color = (0.8, 0.2, 0.2, 1) if percentage >= 100 else (0.9, 0.7, 0.2, 1) if percentage >= 75 else (0.2, 0.8, 0.4, 1)
            self.budget_list.append({'category': category, 'budget': f"${budget_amount:,.2f}", 'spent': f"${spent_amount:,.2f}", 'remaining': f"${remaining:,.2f}", 'percentage': min(percentage, 100), 'bar_color': bar_color})
        self.ids.budget_rv.data = self.budget_list
    def add_budget(self):
        category = self.ids.budget_category_spinner.text
        try: amount = float(self.ids.budget_amount_input.text)
        except ValueError: print("Error: Budget amount must be a number."); return
        if not category or amount <= 0: print("Error: Category and amount must be valid."); return
        add_budget(category, amount); self.ids.budget_category_spinner.text = ''; self.ids.budget_amount_input.text = ''; self.update_budget_list()
    def show_delete_budget_popup(self, category):
        popup_content = ConfirmDeleteBudgetPopup(category=category, main_root=self)
        popup = Popup(title="Confirm Delete", content=popup_content, size_hint=(0.8, None), height=150, auto_dismiss=False)
        popup_content.popup = popup; popup.open()
    def delete_budget(self, popup, category):
        delete_budget(category); popup.dismiss(); self.update_budget_list()

class CategoriesScreen(Screen):
    category_list = ListProperty()
    def on_enter(self, *args): self.update_category_list()
    def update_category_list(self):
        self.category_list = [{'name': cat} for cat in get_all_categories()]
        self.ids.categories_rv.data = self.category_list
    def add_category(self):
        name = self.ids.new_category_input.text
        if not name: print("Error: Category name cannot be empty."); return
        success, message = add_category(name); print(message)
        if success: self.ids.new_category_input.text = ''; self.update_category_list(); refresh_all_category_spinners(App.get_running_app())
    def show_delete_category_popup(self, category_name):
        popup_content = ConfirmDeleteCategoryPopup(category=category_name, main_root=self)
        popup = Popup(title="Confirm Delete", content=popup_content, size_hint=(0.8, None), height=150, auto_dismiss=False)
        popup_content.popup = popup; popup.open()
    def delete_category(self, popup, category_name):
        success, message = delete_category(category_name); print(message)
        if success: popup.dismiss(); self.update_category_list(); refresh_all_category_spinners(App.get_running_app())

class RecurringScreen(Screen):
    recurring_list = ListProperty()
    def on_enter(self, *args):
        self.ids.recurring_category_spinner.values = get_all_categories()
        self.update_recurring_list()
    def update_recurring_list(self):
        templates = get_all_recurring_templates()
        self.recurring_list = [{'id': t[0], 'type': t[1], 'amount': f"${t[2]:.2f}", 'category': t[3], 'description': t[4], 'frequency': t[5], 'next_due': t[6], 'color': (0.2, 0.8, 0.4, 1) if t[1] == 'Income' else (0.9, 0.3, 0.3, 1)} for t in templates]
        self.ids.recurring_rv.data = self.recurring_list
    def add_recurring_template(self):
        t_type = 'Income' if self.ids.recurring_toggle_income.state == 'down' else 'Expense'
        try: amount = float(self.ids.recurring_amount_input.text)
        except ValueError: print("Error: Amount must be a number."); return
        category = self.ids.recurring_category_spinner.text
        description = self.ids.recurring_description_input.text
        frequency = self.ids.recurring_frequency_spinner.text
        next_due = self.ids.recurring_next_due_input.text
        if not category or category == 'Select Category' or not frequency or not next_due:
            print("Error: Category, Frequency, and Next Due Date cannot be empty."); return
        add_recurring_template(t_type, amount, category, description, frequency, next_due)
        self.ids.recurring_amount_input.text = ''; self.ids.recurring_description_input.text = ''; self.ids.recurring_next_due_input.text = ''
        self.update_recurring_list()
    def show_delete_recurring_popup(self, template_id):
        popup_content = ConfirmDeleteRecurringPopup(template_id=template_id, main_root=self)
        popup = Popup(title="Confirm Delete", content=popup_content, size_hint=(0.8, None), height=150, auto_dismiss=False)
        popup_content.popup = popup; popup.open()
    def delete_recurring(self, popup, template_id):
        delete_recurring_template(template_id); popup.dismiss(); self.update_recurring_list()

# --- Popups and Rows ---
class ConfirmDeletePopup(BoxLayout):
    transaction_id = NumericProperty(None); main_root = ObjectProperty(None)
class EditPopup(BoxLayout):
    transaction_data = ObjectProperty(None); main_root = ObjectProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.input_amount.text = str(self.transaction_data['amount'].replace('$', ''))
        self.ids.edit_category_spinner.values = get_all_categories()
        self.ids.edit_category_spinner.text = self.transaction_data['category']
        self.ids.input_description.text = self.transaction_data['description']
        self.ids.input_date.text = self.transaction_data['date']
        if self.transaction_data['type'] == 'Income': self.ids.toggle_income.state = 'down'
        else: self.ids.toggle_expense.state = 'down'
class TransactionRow(BoxLayout):
    transaction_data = ObjectProperty(None)
class ConfirmDeleteBudgetPopup(BoxLayout):
    category = StringProperty(''); main_root = ObjectProperty(None)
class ExportPopup(BoxLayout):
    main_root = ObjectProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.filename_input.text = f"transactions_{datetime.now().strftime('%Y-%m-%d')}.csv"
class ConfirmDeleteCategoryPopup(BoxLayout):
    category = StringProperty(''); main_root = ObjectProperty(None)
class ConfirmDeleteRecurringPopup(BoxLayout):
    template_id = NumericProperty(None); main_root = ObjectProperty(None)

# --- Main App Class ---
class FinancialTrackerApp(App):
    def build(self):
        init_db()
        num_processed = process_due_recurring_transactions()
        if num_processed > 0:
            print(f"Processed {num_processed} recurring transaction(s).")
        return Builder.load_file('financial_tracker.kv')

if __name__ == '__main__':
    FinancialTrackerApp().run()