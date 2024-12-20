from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, messagebox
import sqlite3
import tkinter as tk
from tkinter import ttk, simpledialog


# Пути к ресурсам
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"C:\Users\solov\Downloads\proekt\proekt\frame0")

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


# Функция для центрирования окна
def center_window(window, width, height):
    """
    Функция для центрирования окна на экране.
    """
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)

    window.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

class TrafficViolationsApp:
    def __init__(self, root, user_role):
        self.root = root
        self.user_role = user_role  # 'admin' или 'user'
        self.root.title("Управление нарушениями ПДД")
        center_window(self.root, 1250, 600)  # Центрируем окно

        self.connection = sqlite3.connect("traffic_violations.db")
        self.cursor = self.connection.cursor()

        self.create_widgets()

    def create_widgets(self):
        # закладки для таблиц
        if self.user_role == 'admin':
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill=tk.BOTH, expand=True)

            # Tabs
            self.tabs = {}
            for table_name in ["Violators", "Violations", "Events", "Fines"]:
                frame = ttk.Frame(self.notebook)
                self.notebook.add(frame, text=table_name)
                self.tabs[table_name] = frame
                self.create_table_view(table_name, frame)
        elif self.user_role == 'user':
            self.create_user_search_interface()

    def create_table_view(self, table_name, frame):
        # Treeview for table records
        tree = ttk.Treeview(frame, columns=("#1"), show="headings")
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Get column names
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in self.cursor.fetchall()]
        tree["columns"] = columns

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons (based on user role)
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)

        if self.user_role == 'admin':  # Admin has full access
            ttk.Button(button_frame, text="Добавить", command=lambda: self.add_record(table_name, tree)).pack(
                side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Править", command=lambda: self.edit_record(table_name, tree)).pack(
                side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Удалить", command=lambda: self.delete_record(table_name, tree)).pack(
                side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Поиск", command=lambda: self.search_record(table_name, tree)).pack(side=tk.LEFT,
                                                                                                           padx=5)

        # Кнопка "Выйти"
        ttk.Button(button_frame, text="Выйти", command=self.logout).pack(side=tk.RIGHT, padx=5)

        # Load data
        self.load_data(tree, table_name)

    def create_user_search_interface(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Поиск нарушителя", font=("Arial", 14)).pack(pady=10)
        search_button = ttk.Button(frame, text="Найти по имени", command=self.search_record_user)
        search_button.pack(pady=10)

        # Кнопка "Выйти"
        ttk.Button(frame, text="Выйти", command=self.logout).pack(side=tk.RIGHT, padx=5)

    def load_data(self, tree, table_name):
        for row in tree.get_children():
            tree.delete(row)

        self.cursor.execute(f"SELECT * FROM {table_name}")
        for record in self.cursor.fetchall():
            tree.insert("", "end", values=record)

    def add_record(self, table_name, tree):
        """
        Функция администратора для добавления записи
        """
        if self.user_role == 'admin':
            popup = tk.Toplevel(self.root)
            popup.title("Add Record")
            center_window(popup, 400, 300)  # Центрируем окно
            form_entries = {}

            # Get column names
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in self.cursor.fetchall()]

            for idx, col in enumerate(columns):
                ttk.Label(popup, text=col).grid(row=idx, column=0, padx=5, pady=5)
                entry = ttk.Entry(popup)
                entry.grid(row=idx, column=1, padx=5, pady=5)
                form_entries[col] = entry

            def save():
                values = [form_entries[col].get() for col in columns]
                placeholders = ", ".join(["?"] * len(columns))
                self.cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", values)
                self.connection.commit()
                self.load_data(tree, table_name)
                popup.destroy()

            ttk.Button(popup, text="Сохранить", command=save).grid(row=len(columns), columnspan=2, pady=10)

    def edit_record(self, table_name, tree):
        # Admin function to edit records
        if self.user_role == 'admin':
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Запись не выбрана!")
                return

            popup = tk.Toplevel(self.root)
            popup.title("Edit Record")
            center_window(popup, 400, 300)  # Центрируем окно
            form_entries = {}

            # получаем column names
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in self.cursor.fetchall()]

            selected_values = tree.item(selected_item[0], "values")

            for idx, (col, value) in enumerate(zip(columns, selected_values)):
                ttk.Label(popup, text=col).grid(row=idx, column=0, padx=5, pady=5)
                entry = ttk.Entry(popup)
                entry.insert(0, value)
                entry.grid(row=idx, column=1, padx=5, pady=5)
                form_entries[col] = entry

            def save():
                values = [form_entries[col].get() for col in columns]
                set_clause = ", ".join([f"{col} = ?" for col in columns])
                self.cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE rowid = ?",
                                    values + [selected_values[0]])
                self.connection.commit()
                self.load_data(tree, table_name)
                popup.destroy()

            ttk.Button(popup, text="Сохранить", command=save).grid(row=len(columns), columnspan=2, pady=10)

    def delete_record(self, table_name, tree):
        # Admin function to delete records
        if self.user_role == 'admin':
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Запись не выбрана!")
                return

            selected_values = tree.item(selected_item[0], "values")
            confirm = messagebox.askyesno("Подтверждаю", "Вы уверены, что хотите удалить эту запись?")

            if confirm:
                self.cursor.execute(f"DELETE FROM {table_name} WHERE rowid = ?", (selected_values[0],))
                self.connection.commit()
                self.load_data(tree, table_name)

    def search_record(self, table_name, tree):
        """
        Функция администратора для поиска записи по имени
        """
        name = simpledialog.askstring("Поиск", "Введите имя для поиска:")
        if name:
            try:
                # Поиск по фамилии, имени и отчеству
                self.cursor.execute(f"""
                    SELECT * FROM {table_name}
                    WHERE last_name || ' ' || first_name || ' ' || COALESCE(middle_name, '') LIKE ?
                """, ('%' + name + '%',))
                rows = self.cursor.fetchall()
                for row in tree.get_children():
                    tree.delete(row)
                for record in rows:
                    tree.insert("", "end", values=record)
            except sqlite3.OperationalError as e:
                messagebox.showerror("Ошибка", f"Ошибка выполнения запроса: {e}")
        else:
            messagebox.showwarning("Поиск", "Имя не введено!")

    def search_record_user(self):
        """
        Функция юзера для поиска записи по имени
        """
        full_name = simpledialog.askstring("Поиск", "Введите полное имя нарушителя:")
        if full_name:
            try:
                # Поиск по атрибутам last_name, first_name, middle_name
                self.cursor.execute("""
                    SELECT 
                        v.last_name || ' ' || v.first_name || ' ' || COALESCE(v.middle_name, '') AS full_name,
                        viol.violation_type,
                        f.payment_status
                    FROM Violators AS v
                    JOIN Events AS e ON v.violator_id = e.violator_id
                    JOIN Violations AS viol ON e.violation_id = viol.violation_id
                    JOIN Fines AS f ON f.violation_id = viol.violation_id
                    WHERE v.last_name || ' ' || v.first_name || ' ' || COALESCE(v.middle_name, '') LIKE ?
                """, ('%' + full_name + '%',))
                result = self.cursor.fetchall()

                if result:
                    details = "\n".join(
                        [f"Нарушитель: {row[0]}, Нарушение: {row[1]}, Статус оплаты: {row[2]}" for row in result]
                    )
                    messagebox.showinfo("Результаты поиска", details)
                else:
                    messagebox.showinfo("Результаты поиска", "Нарушитель не найден.")
            except sqlite3.OperationalError as e:
                messagebox.showerror("Ошибка", f"Ошибка выполнения запроса: {e}")
        else:
            messagebox.showwarning("Поиск", "Имя не введено!")

    def logout(self):
        """
        Функция для выхода из приложения
        """
        confirm = messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?")
        if confirm:
            self.root.destroy()
            root = Tk()
            login = LoginWindow(root)
            root.mainloop()


class LoginWindow:
    """
    Функция авторизации
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Авторизация")
        center_window(self.root, 720, 480)  # Центрируем окно
        self.root.configure(bg="#FFFFFF")

        self.canvas = Canvas(
            self.root,
            bg="#FFFFFF",
            height=480,
            width=720,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        # Фон
        self.image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
        self.image_1 = self.canvas.create_image(360.0, 240.0, image=self.image_image_1)

        # Поле для ввода логина
        self.entry_image_1 = PhotoImage(file=relative_to_assets("entry_1.png"))
        self.entry_bg_1 = self.canvas.create_image(375.0, 170.5, image=self.entry_image_1)
        self.entry_1 = Entry(
            bd=0,
            bg="#FFFFFF",
            fg="#000716",
            highlightthickness=0
        )
        self.entry_1.place(
            x=280.0,
            y=143.0,
            width=190.0,
            height=53.0
        )
        self.entry_1.focus()

        # Поле для ввода пароля (скрытые символы)
        self.entry_image_2 = PhotoImage(file=relative_to_assets("entry_2.png"))
        self.entry_bg_2 = self.canvas.create_image(375.0, 289.5, image=self.entry_image_2)
        self.entry_2 = Entry(
            bd=0,
            bg="#FFFFFF",
            fg="#000716",
            highlightthickness=0,
            show="*"  # Скрываем вводимые символы
        )
        self.entry_2.place(
            x=280.0,
            y=262.0,
            width=190.0,
            height=53.0
        )

        # Надписи
        self.canvas.create_text(
            290.0,
            218.0,
            anchor="nw",
            text="Пароль",
            fill="#000000",
            font=("Inter Bold", 32 * -1)
        )
        self.canvas.create_text(
            290.0,
            100.0,
            anchor="nw",
            text="Логин",
            fill="#000000",
            font=("Inter Bold", 32 * -1)
        )

        # Кнопка входа
        self.button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=self.login,
            relief="flat"
        )
        self.button_1.place(
            x=320.0,
            y=352.0,
            width=110.0,
            height=35.0
        )

        self.root.bind("<Return>", self.login_with_enter)

    def login(self):
        username = self.entry_1.get()
        password = self.entry_2.get()

        # Hardcoded for example purposes
        if username == "admin" and password == "admin":
            self.root.destroy()
            root = Tk()
            app = TrafficViolationsApp(root, user_role="admin")
            root.mainloop()
        elif username == "user" and password == "user":
            self.root.destroy()
            root = Tk()
            app = TrafficViolationsApp(root, user_role="user")
            root.mainloop()
        else:
            messagebox.showerror("Ошибка входа", "Неверные учетные данные")

    def login_with_enter(self, event=None):
        """
        Метод для обработки нажатия клавиши Enter.
        """
        self.login()

if __name__ == "__main__":
    root = Tk()
    login = LoginWindow(root)
    root.resizable(False, False)
    root.mainloop()