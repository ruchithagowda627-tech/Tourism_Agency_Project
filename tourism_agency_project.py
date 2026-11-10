"""
TOURISM AGENCY MANAGEMENT SYSTEM
Single-file Python desktop application using SQLite and Tkinter.

Features:
- Manage tour operators
- Manage tour packages
- Manage package cost items
- Search and view records
- Foreign keys with cascading delete
- Light theme interface

Run:
    python tourism_agency_project.py
"""

import sqlite3
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime


# =========================================================
# DATABASE CLASS
# =========================================================

class Database:
    def __init__(self, db_name):
        self.con = sqlite3.connect(db_name)
        self.con.execute("PRAGMA foreign_keys = ON")
        self.cur = self.con.cursor()

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS operators (
                operator_id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator_name TEXT NOT NULL UNIQUE,
                contact_email TEXT NOT NULL
            )
        """)

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS tour_packages (
                package_id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator_id INTEGER NOT NULL,
                destination TEXT NOT NULL,
                departure_date TEXT NOT NULL,
                FOREIGN KEY (operator_id)
                    REFERENCES operators(operator_id)
                    ON DELETE CASCADE
            )
        """)

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS cost_items (
                cost_id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                FOREIGN KEY (package_id)
                    REFERENCES tour_packages(package_id)
                    ON DELETE CASCADE
            )
        """)

        self.con.commit()

    def add_operator(self, name, email):
        self.cur.execute(
            "INSERT INTO operators (operator_name, contact_email) VALUES (?, ?)",
            (name, email)
        )
        self.con.commit()
        return self.cur.lastrowid

    def get_or_add_operator(self, name, email):
        self.cur.execute(
            "SELECT operator_id FROM operators WHERE operator_name = ?",
            (name,)
        )
        row = self.cur.fetchone()
        if row:
            self.cur.execute(
                "UPDATE operators SET contact_email=? WHERE operator_id=?",
                (email, row[0])
            )
            self.con.commit()
            return row[0]
        return self.add_operator(name, email)

    def add_package(self, operator_id, destination, departure_date):
        self.cur.execute("""
            INSERT INTO tour_packages (operator_id, destination, departure_date)
            VALUES (?, ?, ?)
        """, (operator_id, destination, departure_date))
        self.con.commit()
        return self.cur.lastrowid

    def add_cost(self, package_id, description, amount):
        self.cur.execute("""
            INSERT INTO cost_items (package_id, description, amount)
            VALUES (?, ?, ?)
        """, (package_id, description, amount))
        self.con.commit()

    def operators(self):
        self.cur.execute("""
            SELECT operator_id, operator_name, contact_email
            FROM operators ORDER BY operator_id
        """)
        return self.cur.fetchall()

    def packages(self):
        self.cur.execute("""
            SELECT p.package_id, o.operator_name, p.destination, p.departure_date
            FROM tour_packages p
            JOIN operators o ON p.operator_id = o.operator_id
            ORDER BY p.package_id
        """)
        return self.cur.fetchall()

    def costs(self):
        self.cur.execute("""
            SELECT c.cost_id, p.destination, c.description, c.amount
            FROM cost_items c
            JOIN tour_packages p ON c.package_id = p.package_id
            ORDER BY c.cost_id
        """)
        return self.cur.fetchall()

    def bookings(self):
        self.cur.execute("""
            SELECT p.package_id, o.operator_name, o.contact_email,
                   p.destination, p.departure_date,
                   COALESCE(SUM(c.amount), 0) AS total_cost
            FROM tour_packages p
            JOIN operators o ON p.operator_id = o.operator_id
            LEFT JOIN cost_items c ON p.package_id = c.package_id
            GROUP BY p.package_id, o.operator_name, o.contact_email,
                     p.destination, p.departure_date
            ORDER BY p.package_id
        """)
        return self.cur.fetchall()

    def delete_operator(self, operator_id):
        self.cur.execute("DELETE FROM operators WHERE operator_id=?", (operator_id,))
        self.con.commit()

    def delete_package(self, package_id):
        self.cur.execute("DELETE FROM tour_packages WHERE package_id=?", (package_id,))
        self.con.commit()

    def delete_cost(self, cost_id):
        self.cur.execute("DELETE FROM cost_items WHERE cost_id=?", (cost_id,))
        self.con.commit()

    def counts(self):
        result = []
        for table in ("operators", "tour_packages", "cost_items"):
            self.cur.execute(f"SELECT COUNT(*) FROM {table}")
            result.append(self.cur.fetchone()[0])
        return result

    def close(self):
        self.con.close()


# =========================================================
# GUI APPLICATION SETUP
# =========================================================

db = Database("tourism_agency.db")

root = Tk()
root.title("TOURISM AGENCY MANAGEMENT SYSTEM")
root.geometry("1250x780")
root.minsize(1050, 680)
root.configure(bg="#f3f7fb")

try:
    root.state("zoomed")
except Exception:
    pass

# Light theme colours
BG = "#f3f7fb"
WHITE = "#ffffff"
NAVY = "#17324d"
TEAL = "#159a9c"
BLUE = "#3b82c4"
PALE = "#e5f2f8"
TEXT = "#263746"
MUTED = "#647789"
BORDER = "#d9e4ec"

# Form variables
operator_name = StringVar()
email = StringVar()
destination = StringVar()
departure_date = StringVar()
cost_description = StringVar()
amount = StringVar()
search_text = StringVar()
selected_package_id = None


# ---------------- Header ----------------

header = Frame(root, bg=NAVY, height=82)
header.pack(side=TOP, fill=X)
header.pack_propagate(False)

Label(
    header,
    text="✈  TOURISM AGENCY",
    font=("Segoe UI", 22, "bold"),
    bg=NAVY,
    fg=WHITE
).pack(side=LEFT, padx=25, pady=18)

Label(
    header,
    text="Tour Operators  •  Tour Packages  •  Billing Dashboard",
    font=("Segoe UI", 11),
    bg=NAVY,
    fg="#d7e8f3"
).pack(side=RIGHT, padx=25)


# ---------------- Summary cards ----------------

summary_frame = Frame(root, bg=BG)
summary_frame.pack(fill=X, padx=20, pady=(16, 8))

summary_values = []
summary_titles = ["TOTAL OPERATORS", "TOTAL PACKAGES", "TOTAL COST ITEMS"]

for i, title_text in enumerate(summary_titles):
    card = Frame(summary_frame, bg=WHITE, highlightbackground=BORDER,
                 highlightthickness=1, padx=18, pady=10)
    card.pack(side=LEFT, fill=X, expand=True, padx=(0 if i == 0 else 10, 0))
    Label(card, text=title_text, font=("Segoe UI", 9, "bold"),
          bg=WHITE, fg=MUTED).pack(anchor="w")
    value_label = Label(card, text="0", font=("Segoe UI", 22, "bold"),
                        bg=WHITE, fg=TEAL)
    value_label.pack(anchor="w", pady=(3, 0))
    summary_values.append(value_label)


# ---------------- Main content ----------------

main = Frame(root, bg=BG)
main.pack(fill=BOTH, expand=True, padx=20, pady=10)

form_frame = Frame(main, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
form_frame.pack(side=LEFT, fill=Y, padx=(0, 14), pady=2)

Label(form_frame, text="ADD NEW TOUR PACKAGE", font=("Segoe UI", 14, "bold"),
      bg=WHITE, fg=NAVY).pack(anchor="w", padx=18, pady=(18, 5))
Label(form_frame, text="Enter operator, destination and cost details",
      font=("Segoe UI", 9), bg=WHITE, fg=MUTED).pack(anchor="w", padx=18, pady=(0, 12))


def add_field(parent, label_text, variable):
    Label(parent, text=label_text, font=("Segoe UI", 10, "bold"),
          bg=WHITE, fg=TEXT).pack(anchor="w", padx=18, pady=(8, 4))
    entry = Entry(parent, textvariable=variable, font=("Segoe UI", 10),
                  relief=SOLID, bd=1, width=30)
    entry.pack(anchor="w", padx=18, ipady=7)
    return entry


txt_operator = add_field(form_frame, "Operator Name", operator_name)
txt_email = add_field(form_frame, "Contact Email", email)
txt_destination = add_field(form_frame, "Destination", destination)
txt_date = add_field(form_frame, "Departure Date (YYYY-MM-DD)", departure_date)
txt_description = add_field(form_frame, "Cost Description", cost_description)
txt_amount = add_field(form_frame, "Cost Amount (₹)", amount)


# ---------------- Table area and tabs ----------------

right_frame = Frame(main, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
right_frame.pack(side=LEFT, fill=BOTH, expand=True, pady=2)

top_bar = Frame(right_frame, bg=WHITE)
top_bar.pack(fill=X, padx=15, pady=12)

Label(top_bar, text="PROJECT RECORDS", font=("Segoe UI", 14, "bold"),
      bg=WHITE, fg=NAVY).pack(side=LEFT)

search_entry = Entry(top_bar, textvariable=search_text, font=("Segoe UI", 10),
                     width=24, relief=SOLID, bd=1)
search_entry.pack(side=RIGHT, ipady=5, padx=(8, 0))


def make_tree(parent, columns, headings, widths):
    frame = Frame(parent, bg=WHITE)
    frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    tree = ttk.Treeview(frame, columns=columns, show="headings", height=16)
    for col, heading, width in zip(columns, headings, widths):
        tree.heading(col, text=heading)
        tree.column(col, width=width, anchor="center")

    y_scroll = ttk.Scrollbar(frame, orient=VERTICAL, command=tree.yview)
    x_scroll = ttk.Scrollbar(frame, orient=HORIZONTAL, command=tree.xview)
    tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
    tree.pack(side=TOP, fill=BOTH, expand=True)
    y_scroll.pack(side=RIGHT, fill=Y)
    x_scroll.pack(side=BOTTOM, fill=X)
    return tree


style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background=WHITE, foreground=TEXT,
                rowheight=30, fieldbackground=WHITE, font=("Segoe UI", 9))
style.configure("Treeview.Heading", background=PALE, foreground=NAVY,
                font=("Segoe UI", 9, "bold"), relief="flat")
style.map("Treeview", background=[("selected", "#cce9ef")],
          foreground=[("selected", NAVY)])

notebook = ttk.Notebook(right_frame)
notebook.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))

bookings_tab = Frame(notebook, bg=WHITE)
operators_tab = Frame(notebook, bg=WHITE)
packages_tab = Frame(notebook, bg=WHITE)
costs_tab = Frame(notebook, bg=WHITE)

notebook.add(bookings_tab, text="Bookings")
notebook.add(operators_tab, text="Operators")
notebook.add(packages_tab, text="Tour Packages")
notebook.add(costs_tab, text="Cost Items")

booking_tree = make_tree(
    bookings_tab,
    ("id", "operator", "email", "destination", "date", "total"),
    ("Package ID", "Operator", "Email", "Destination", "Departure Date", "Total Cost (₹)"),
    (75, 130, 170, 130, 115, 110)
)
operator_tree = make_tree(
    operators_tab,
    ("id", "name", "email"),
    ("Operator ID", "Operator Name", "Contact Email"),
    (100, 220, 260)
)
package_tree = make_tree(
    packages_tab,
    ("id", "operator", "destination", "date"),
    ("Package ID", "Operator", "Destination", "Departure Date"),
    (100, 180, 180, 140)
)
cost_tree = make_tree(
    costs_tab,
    ("id", "destination", "description", "amount"),
    ("Cost ID", "Destination", "Description", "Amount (₹)"),
    (90, 180, 220, 120)
)


# ---------------- Refresh functions ----------------

def refresh_all():
    for tree in (booking_tree, operator_tree, package_tree, cost_tree):
        tree.delete(*tree.get_children())

    for row in db.bookings():
        booking_tree.insert("", END, values=row)
    for row in db.operators():
        operator_tree.insert("", END, values=row)
    for row in db.packages():
        package_tree.insert("", END, values=row)
    for row in db.costs():
        cost_tree.insert("", END, values=row)

    counts = db.counts()
    for label, count in zip(summary_values, counts):
        label.config(text=str(count))


# ---------------- Event functions ----------------

def clear_form():
    operator_name.set("")
    email.set("")
    destination.set("")
    departure_date.set("")
    cost_description.set("")
    amount.set("")


def add_package_record():
    name = operator_name.get().strip()
    mail = email.get().strip()
    place = destination.get().strip()
    date_text = departure_date.get().strip()
    description = cost_description.get().strip()
    amount_text = amount.get().strip()

    if not all((name, mail, place, date_text, description, amount_text)):
        messagebox.showerror("Missing Details", "Please fill in all fields.")
        return

    if "@" not in mail or "." not in mail.split("@")[-1]:
        messagebox.showerror("Invalid Email", "Please enter a valid email address.")
        return

    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Invalid Date", "Enter the date as YYYY-MM-DD.")
        return

    try:
        cost_value = float(amount_text)
        if cost_value < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Amount", "Enter a valid non-negative amount.")
        return

    try:
        operator_id = db.get_or_add_operator(name, mail)
        package_id = db.add_package(operator_id, place, date_text)
        db.add_cost(package_id, description, cost_value)
        messagebox.showinfo("Success", "Tour package and cost item added successfully.")
        clear_form()
        refresh_all()
    except sqlite3.Error as error:
        messagebox.showerror("Database Error", str(error))


def selected_id(tree):
    item = tree.focus()
    if not item:
        return None
    values = tree.item(item, "values")
    return values[0] if values else None


def delete_selected():
    tab_index = notebook.index(notebook.select())

    if tab_index == 1:
        record_id = selected_id(operator_tree)
        if not record_id:
            messagebox.showwarning("Select Record", "Select an operator to delete.")
            return
        confirm_text = "Delete this operator and all their packages and cost items?"
        action = lambda: db.delete_operator(record_id)

    elif tab_index == 2:
        record_id = selected_id(package_tree)
        if not record_id:
            messagebox.showwarning("Select Record", "Select a package to delete.")
            return
        confirm_text = "Delete this package and its cost items?"
        action = lambda: db.delete_package(record_id)

    elif tab_index == 3:
        record_id = selected_id(cost_tree)
        if not record_id:
            messagebox.showwarning("Select Record", "Select a cost item to delete.")
            return
        confirm_text = "Delete this cost item?"
        action = lambda: db.delete_cost(record_id)

    else:
        messagebox.showinfo("Choose a Tab", "Open Operators, Tour Packages or Cost Items to delete a record.")
        return

    if messagebox.askyesno("Confirm Delete", confirm_text):
        action()
        refresh_all()
        messagebox.showinfo("Deleted", "Selected record deleted successfully.")


def search_records():
    query = search_text.get().strip().lower()
    if not query:
        refresh_all()
        return

    # Search and filter the visible Bookings table.
    booking_tree.delete(*booking_tree.get_children())
    for row in db.bookings():
        if any(query in str(value).lower() for value in row):
            booking_tree.insert("", END, values=row)
    notebook.select(bookings_tab)


def show_all():
    search_text.set("")
    refresh_all()


# ---------------- Buttons ----------------

button_frame = Frame(form_frame, bg=WHITE)
button_frame.pack(fill=X, padx=18, pady=18)


def make_button(parent, text, command, colour):
    return Button(
        parent, text=text, command=command,
        font=("Segoe UI", 10, "bold"),
        bg=colour, fg=WHITE, activebackground=colour,
        activeforeground=WHITE, relief=FLAT, bd=0,
        cursor="hand2", padx=12, pady=9
    )


make_button(button_frame, "Add Package", add_package_record, TEAL).pack(fill=X, pady=4)
make_button(button_frame, "Clear Form", clear_form, BLUE).pack(fill=X, pady=4)
make_button(button_frame, "Delete Selected", delete_selected, "#d45b5b").pack(fill=X, pady=4)
make_button(button_frame, "Refresh Records", show_all, NAVY).pack(fill=X, pady=4)

search_button = Button(top_bar, text="Search", command=search_records,
                       font=("Segoe UI", 9, "bold"), bg=TEAL, fg=WHITE,
                       relief=FLAT, cursor="hand2", padx=12, pady=5)
search_button.pack(side=RIGHT)


# ---------------- Initial load and close ----------------

refresh_all()


def close_app():
    db.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
