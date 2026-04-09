import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import psycopg2
import random

conn = psycopg2.connect(
    dbname="custom_orders_db",
    user="postgres",
    password="BabaYaga1q2w3e4r",
    host="localhost",
    port="5432"
)

class PuzzleCaptcha:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self.frame.pack()

        self.correct_order = ["1.png", "2.png", "3.png", "4.png"]
        self.current_order = self.correct_order.copy()
        random.shuffle(self.current_order)

        self.first_click = None
        self.render()

    def render(self):
        for w in self.frame.winfo_children():
            w.destroy()

        self.photos = []

        for i, path in enumerate(self.current_order):
            img = Image.open(path).resize((100,100))
            photo = ImageTk.PhotoImage(img)
            self.photos.append(photo)

            lbl = tk.Label(self.frame, image=photo, borderwidth=2, relief="solid")
            lbl.grid(row=i//2, column=i%2)
            lbl.bind("<Button-1>", lambda e, idx=i: self.swap(idx))

    def swap(self, idx):
        if self.first_click is None:
            self.first_click = idx
        else:
            self.current_order[self.first_click], self.current_order[idx] = \
                self.current_order[idx], self.current_order[self.first_click]
            self.first_click = None
            self.render()

    def is_correct(self):
        return self.current_order == self.correct_order


def authenticate(login, password):
    cur = conn.cursor()
    cur.execute("SELECT password, role, is_blocked, failed_attempts FROM users WHERE login=%s", (login,))
    user = cur.fetchone()

    if not user:
        return False, None, "Вы ввели неверный логин или пароль"

    db_password, role, is_blocked, attempts = user

    if is_blocked:
        return False, None, "Вы заблокированы. Обратитесь к администратору"

    if password == db_password:
        cur.execute("UPDATE users SET failed_attempts=0 WHERE login=%s", (login,))
        conn.commit()
        return True, role, "Вы успешно авторизовались"
    else:
        attempts += 1
        if attempts >= 3:
            cur.execute("UPDATE users SET is_blocked=TRUE WHERE login=%s", (login,))
        else:
            cur.execute("UPDATE users SET failed_attempts=%s WHERE login=%s", (attempts, login))
        conn.commit()
        return False, None, "Вы ввели неверный логин или пароль"


class AdminWindow:
    def __init__(self, root):
        self.root = root
        self.win = tk.Toplevel()
        self.win.title("Администратор")

        tk.Label(self.win, text="Логин").pack()
        self.login = tk.Entry(self.win)
        self.login.pack()

        tk.Label(self.win, text="Пароль").pack()
        self.password = tk.Entry(self.win)
        self.password.pack()

        tk.Label(self.win, text="Роль (admin/user)").pack()
        self.role = tk.Entry(self.win)
        self.role.pack()

        tk.Button(self.win, text="Добавить пользователя", command=self.add_user).pack()
        tk.Button(self.win, text="Обновить пользователя", command=self.update_user).pack()
        tk.Button(self.win, text="Разблокировать", command=self.unlock_user).pack()

        tk.Button(self.win, text="Удалить пользователя", command=self.delete_user).pack(pady=5)
        tk.Button(self.win, text="Показать пользователей", command=self.load_users).pack(pady=5)

        # КНОПКА ВЫХОДА
        tk.Button(self.win, text="Выйти", command=self.logout).pack(pady=10)

        self.tree = ttk.Treeview(self.win, columns=("login", "password", "role"), show="headings")
        self.tree.heading("login", text="Логин")
        self.tree.heading("password", text="Пароль")
        self.tree.heading("role", text="Роль")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def logout(self):
        self.win.destroy()
        self.root.deiconify()

    def load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        cur = conn.cursor()
        cur.execute("SELECT login, password, role FROM users")
        users = cur.fetchall()

        for user in users:
            self.tree.insert("", "end", values=user)

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            self.login.delete(0, tk.END)
            self.password.delete(0, tk.END)
            self.role.delete(0, tk.END)

            self.login.insert(0, values[0])
            self.password.insert(0, values[1])
            self.role.insert(0, values[2])

    def delete_user(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showerror("Ошибка", "Выберите пользователя из таблицы")
            return

        values = self.tree.item(selected[0], "values")
        login, password, role = values

        if login == "admin" and password == "admin" and role == "admin":
            messagebox.showerror("Ошибка", "Главного героя удалить нельзя")
            return

        if login == "johnwick" and password == "johnwick" and role == "admin":
            messagebox.showerror("Ай яй-яй-яй", "Экскомьюникадо уже выехал за тобой")
            return

        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE login=%s", (login,))
        conn.commit()

        messagebox.showinfo("Успех", "Пользователь удалён")
        self.load_users()

    def add_user(self):
        login = self.login.get()
        password = self.password.get()
        role = self.role.get()

        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE login=%s", (login,))

        if cur.fetchone():
            messagebox.showerror("Ошибка", "Пользователь уже существует")
            return

        cur.execute("INSERT INTO users (login, password, role) VALUES (%s,%s,%s)",
                    (login, password, role))
        conn.commit()
        messagebox.showinfo("Успех", "Пользователь добавлен")
        self.load_users()

    def update_user(self):
        login = self.login.get()
        password = self.password.get()
        role = self.role.get()

        cur = conn.cursor()
        cur.execute("UPDATE users SET password=%s, role=%s WHERE login=%s",
                    (password, role, login))
        conn.commit()
        messagebox.showinfo("Успех", "Данные обновлены")
        self.load_users()

    def unlock_user(self):
        login = self.login.get()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_blocked=FALSE, failed_attempts=0 WHERE login=%s", (login,))
        conn.commit()
        messagebox.showinfo("Успех", "Пользователь разблокирован")
        self.load_users()


class UserWindow:
    def __init__(self, root):
        self.root = root
        self.win = tk.Toplevel()
        self.win.title("Пользователь")

        tk.Label(self.win, text="Добро пожаловать!").pack()
        tk.Button(self.win, text="Выйти", command=self.logout).pack(pady=10)

    def logout(self):
        self.win.destroy()
        self.root.deiconify()


class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Авторизация")

        tk.Label(root, text="Логин").pack()
        self.login_entry = tk.Entry(root)
        self.login_entry.pack()

        tk.Label(root, text="Пароль").pack()
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.pack()

        tk.Label(root, text="Соберите пазл").pack()
        self.puzzle = PuzzleCaptcha(root)

        tk.Button(root, text="Войти", command=self.login).pack()

    def login(self):
        login = self.login_entry.get()
        password = self.password_entry.get()

        if not login or not password:
            messagebox.showerror("Ошибка", "Все поля обязательны")
            return

        if not self.puzzle.is_correct():
            messagebox.showerror("Ошибка", "Капча собрана неверно")
            return

        success, role, msg = authenticate(login, password)

        if success:
            messagebox.showinfo("Успех", msg)
            self.root.withdraw()

            if role == 'admin':
                AdminWindow(self.root)
            else:
                UserWindow(self.root)
        else:
            messagebox.showerror("Ошибка", msg)


root = tk.Tk()
app = LoginApp(root)
root.mainloop()

