import sqlite3
import os
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import pandas as pd
from reportlab.pdfgen import canvas


def create_database():
    conn = sqlite3.connect("mini_erp.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        stock REAL DEFAULT 0,
        unit_price REAL DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        stock REAL DEFAULT 0,
        sale_price REAL DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        material_id INTEGER,
        percentage REAL,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (material_id) REFERENCES materials(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER,
        amount REAL,
        total_cost REAL,
        date TEXT,
        FOREIGN KEY (material_id) REFERENCES materials(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        amount REAL,
        total_income REAL,
        date TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Veritabanı başarıyla oluşturuldu.")

# Veritabanı dosyası
DB_PATH = os.path.join(os.path.expanduser("~/Desktop/mini_erp"), "mini_erp.db")

# Giriş ekranı
def login_screen(on_success_callback):
    def check_credentials():
        username = entry_user.get()
        password = entry_pass.get()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            login_win.destroy()
            on_success_callback()
        else:
            messagebox.showerror("Hatalı Giriş", "Kullanıcı adı veya şifre hatalı.")

    login_win = tk.Tk()
    login_win.title("Kullanıcı Girişi")
    login_win.geometry("300x180")

    tk.Label(login_win, text="Kullanıcı Adı").pack(pady=5)
    entry_user = tk.Entry(login_win)
    entry_user.pack()

    tk.Label(login_win, text="Şifre").pack(pady=5)
    entry_pass = tk.Entry(login_win, show="*")
    entry_pass.pack()

    tk.Button(login_win, text="Giriş Yap", command=check_credentials).pack(pady=10)
    login_win.mainloop()

# Kullanıcı tablosunu oluştur (ilk çalıştırmada bir kere çağrılır)
def create_user_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    # Örnek kullanıcı ekle (varsa eklemez)
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))
    conn.commit()
    conn.close()

BASE_DIR = os.path.expanduser("~/Desktop/mini_erp")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def get_db_connection():
    return sqlite3.connect("mini_erp.db")

# 0. Malzeme Ekleme

def add_material():
    def save_material():
        name = entry_name.get()
        stock = entry_stock.get()
        price = entry_price.get()

        if not name or not stock or not price:
            messagebox.showwarning("Uyarı", "Tüm alanları doldurun.")
            return

        try:
            stock = float(stock)
            price = float(price)
        except ValueError:
            messagebox.showerror("Hata", "Stok ve fiyat sayısal olmalı.")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO materials (name, stock, unit_price) VALUES (?, ?, ?)", (name, stock, price))
        conn.commit()
        conn.close()

        messagebox.showinfo("Başarılı", "Malzeme eklendi.")
        win.destroy()

    win = tk.Toplevel()
    win.title("Malzeme Ekle")

    tk.Label(win, text="Malzeme Adı").pack()
    entry_name = tk.Entry(win)
    entry_name.pack()

    tk.Label(win, text="Stok Miktarı").pack()
    entry_stock = tk.Entry(win)
    entry_stock.pack()

    tk.Label(win, text="Birim Fiyatı").pack()
    entry_price = tk.Entry(win)
    entry_price.pack()

    tk.Button(win, text="Kaydet", command=save_material).pack(pady=10)

# 1. Malzeme Listesi

def show_materials():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM materials")
    records = cursor.fetchall()
    conn.close()

    win = tk.Toplevel()
    win.title("Malzeme Listesi")
    tree = ttk.Treeview(win, columns=("ID", "Ad", "Stok", "Fiyat"), show='headings')
    tree.heading("ID", text="ID")
    tree.heading("Ad", text="Ad")
    tree.heading("Stok", text="Stok")
    tree.heading("Fiyat", text="Birim Fiyat")
    tree.pack(fill="both", expand=True)

    for row in records:
        tree.insert("", "end", values=row)

# 2. Ürün ve Reçete

def add_product_with_recipe():
    def save_product():
        name = entry_name.get()
        price = float(entry_price.get())

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, sale_price) VALUES (?, ?)", (name, price))
        product_id = cursor.lastrowid

        for i in tree.get_children():
            item = tree.item(i)['values']
            material_id, perc = item[0], float(item[1])
            cursor.execute("INSERT INTO recipes (product_id, material_id, percentage) VALUES (?, ?, ?)",
                           (product_id, material_id, perc))

        conn.commit()
        conn.close()
        messagebox.showinfo("Başarılı", "Ürün ve reçete kaydedildi.")
        win.destroy()

    def add_recipe_row():
        mat_id = combo_material.get().split(" - ")[0]
        perc = entry_perc.get()
        tree.insert("", "end", values=(mat_id, perc))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM materials")
    materials = cursor.fetchall()
    conn.close()

    win = tk.Toplevel()
    win.title("Ürün ve Reçete Tanımı")

    tk.Label(win, text="Ürün Adı").pack()
    entry_name = tk.Entry(win)
    entry_name.pack()

    tk.Label(win, text="Satış Fiyatı").pack()
    entry_price = tk.Entry(win)
    entry_price.pack()

    tk.Label(win, text="Malzeme Seç").pack()
    combo_material = ttk.Combobox(win, values=[f"{m[0]} - {m[1]}" for m in materials])
    combo_material.pack()

    tk.Label(win, text="Yüzde (%)").pack()
    entry_perc = tk.Entry(win)
    entry_perc.pack()

    tk.Button(win, text="Reçeteye Ekle", command=add_recipe_row).pack()

    tree = ttk.Treeview(win, columns=("Malzeme ID", "Yüzde"), show='headings')
    tree.heading("Malzeme ID", text="Malzeme ID")
    tree.heading("Yüzde", text="Yüzde")
    tree.pack()

    tk.Button(win, text="Kaydet", command=save_product).pack(pady=10)

# 3. Üretim

def produce_product():
    def produce():
        product_id = combo_product.get().split(" - ")[0]
        qty = float(entry_qty.get())

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT material_id, percentage FROM recipes WHERE product_id = ?", (product_id,))
        recipe = cursor.fetchall()

        for mat_id, perc in recipe:
            cursor.execute("UPDATE materials SET stock = stock - ? WHERE id = ?", (qty * perc / 100, mat_id))

        cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (qty, product_id))
        conn.commit()
        conn.close()

        messagebox.showinfo("Tamamlandı", "Üretim başarıyla yapıldı.")
        win.destroy()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()
    conn.close()

    win = tk.Toplevel()
    win.title("Üretim Yap")

    combo_product = ttk.Combobox(win, values=[f"{p[0]} - {p[1]}" for p in products])
    combo_product.pack(pady=5)

    entry_qty = tk.Entry(win)
    entry_qty.pack(pady=5)
    entry_qty.insert(0, "Üretim Miktarı")

    tk.Button(win, text="Üret", command=produce).pack(pady=10)

# 4. Satış

def sell_product():
    def sell():
        product_id = combo_product.get().split(" - ")[0]
        qty = float(entry_qty.get())
        now = datetime.now().strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sale_price FROM products WHERE id = ?", (product_id,))
        price = cursor.fetchone()[0]
        total_income = qty * price

        cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, product_id))
        cursor.execute("INSERT INTO sales (product_id, amount, total_income, date) VALUES (?, ?, ?, ?)",
                       (product_id, qty, total_income, now))
        conn.commit()
        conn.close()

        messagebox.showinfo("Satış", f"Toplam gelir: ₺{total_income:.2f}")
        win.destroy()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()
    conn.close()

    win = tk.Toplevel()
    win.title("Satış Yap")

    combo_product = ttk.Combobox(win, values=[f"{p[0]} - {p[1]}" for p in products])
    combo_product.pack(pady=5)

    entry_qty = tk.Entry(win)
    entry_qty.pack(pady=5)
    entry_qty.insert(0, "Satış Miktarı")

    tk.Button(win, text="Sat", command=sell).pack(pady=10)

# 5. Rapor

def generate_reports():
    conn = get_db_connection()
    sales = pd.read_sql_query("SELECT * FROM sales", conn)
    materials = pd.read_sql_query("SELECT * FROM materials", conn)
    conn.close()

    sales.to_excel(os.path.join(REPORTS_DIR, "sales_report.xlsx"), index=False)
    materials.to_excel(os.path.join(REPORTS_DIR, "materials_report.xlsx"), index=False)

    pdf_path = os.path.join(REPORTS_DIR, "fatura.pdf")
    c = canvas.Canvas(pdf_path)
    c.drawString(100, 800, "FATURA")
    for i, row in sales.iterrows():
        c.drawString(50, 770 - 20 * i, f"Ürün ID: {row['product_id']} - Adet: {row['amount']} - Gelir: ₺{row['total_income']}")
    c.save()

    messagebox.showinfo("Rapor", f"Excel ve PDF raporları oluşturuldu: \n{REPORTS_DIR}")


# Ana Menü

def main_menu():
    root = tk.Tk()
    root.title("Mini ERP Sistemi")

    tk.Button(root, text="0. Malzeme Ekle", command=add_material).pack(pady=5)
    tk.Button(root, text="1. Malzeme Listesi", command=show_materials).pack(pady=5)
    tk.Button(root, text="2. Ürün Tanımla + Reçete", command=add_product_with_recipe).pack(pady=5)
    tk.Button(root, text="3. Üretim Yap", command=produce_product).pack(pady=5)
    tk.Button(root, text="4. Satış Yap", command=sell_product).pack(pady=5)
    tk.Button(root, text="5. Rapor ve Fatura", command=generate_reports).pack(pady=5)

    root.mainloop()


# Giriş sonrası menü başlatılsın
if __name__ == "__main__":
    create_user_table()
    login_screen(main_menu)
