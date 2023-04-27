import sqlite3
import sys
import time
import cv2
import pyzbar
import os
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog



DATABASE = "inventory.db"

def create_tables():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        barcode TEXT UNIQUE,
        name TEXT,
        checked_out INTEGER DEFAULT 0,
        checked_out_by TEXT,
        quantity INTEGER DEFAULT 0,
        FOREIGN KEY (checked_out_by) REFERENCES users (id_number)
    );
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        id_number TEXT UNIQUE
    );
    """)


    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        barcode TEXT,
        user_id_number TEXT,
        checkout_date TIMESTAMP,
        checkin_date TIMESTAMP,
        FOREIGN KEY (barcode) REFERENCES items (barcode),
        FOREIGN KEY (user_id_number) REFERENCES users (id_number)
    );
    """)

    conn.commit()
    conn.close()


# Call create_tables() before adding users
create_tables()

def add_item(barcode, name):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    try:
        c.execute("INSERT INTO items (barcode, name) VALUES (?, ?)", (barcode, name))
        conn.commit()
        messagebox.showinfo("Add Item", "Item added successfully!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Add Item", "Item with barcode already exists.")

    conn.close()



def remove_item(barcode):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("DELETE FROM items WHERE barcode=?", (barcode,))
    conn.commit()
    print("Item removed successfully!")

    conn.close()

def check_out_batch(id_number):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id_number=?", (id_number,))
    user = c.fetchone()

    if user:
        while True:
            print("To stop checking out items, type 'done' as the barcode.")
            barcode = input("Scan or enter the barcode: ")

            if barcode.lower() == 'done':
                break

            c.execute("SELECT * FROM items WHERE barcode=?", (barcode,))
            item = c.fetchone()

            if item:
                current_quantity = item[5]
                checkout_quantity = 1  # Assume a single item is checked out

                if current_quantity >= checkout_quantity:
                    new_quantity = current_quantity - checkout_quantity
                    c.execute("UPDATE items SET quantity=? WHERE barcode=?", (new_quantity, barcode))

                    for _ in range(checkout_quantity):
                        c.execute("INSERT INTO transactions (barcode, user_id_number, checkout_date) VALUES (?, ?, datetime('now'))", (barcode, id_number))

                    conn.commit()
                    print(f"{checkout_quantity} item checked out successfully!")
                else:
                    print("Not enough quantity available.")
            else:
                print("Item not found.")
    else:
        print("User not found.")

    conn.close()
def check_out_batch_gui(id_number):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id_number=?", (id_number,))
    user = c.fetchone()

    if user:
        while True:
            barcode = simpledialog.askstring("Check Out Item", "Scan or enter the barcode (type 'done' to stop):")

            if barcode is None or barcode.lower() == 'done':
                break

            c.execute("SELECT * FROM items WHERE barcode=?", (barcode,))
            item = c.fetchone()

            if item:
                current_quantity = item[5]
                checkout_quantity = 1  # Assume a single item is checked out

                if current_quantity >= checkout_quantity:
                    new_quantity = current_quantity - checkout_quantity
                    c.execute("UPDATE items SET quantity=? WHERE barcode=?", (new_quantity, barcode))

                    for _ in range(checkout_quantity):
                        c.execute("INSERT INTO transactions (barcode, user_id_number, checkout_date) VALUES (?, ?, datetime('now'))", (barcode, id_number))

                    conn.commit()
                    messagebox.showinfo("Check Out Item", f"{checkout_quantity} item checked out successfully!")
                else:
                    messagebox.showerror("Check Out Item", "Not enough quantity available.")
            else:
                messagebox.showerror("Check Out Item", "Item not found.")
    else:
        messagebox.showerror("Check Out Item", "User not found.")

    conn.close()
def show_user_transactions():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
    SELECT users.id_number, users.first_name, users.last_name, items.barcode, items.name, transactions.checkout_date
    FROM transactions
    JOIN items ON transactions.barcode = items.barcode
    JOIN users ON transactions.user_id_number = users.id_number
    WHERE transactions.checkin_date IS NULL
    """)
    transactions = c.fetchall()

    conn.close()

    if transactions:
        # Create a new window to display the transactions
        window = tk.Toplevel()
        window.title("User Transactions")

        # Create a text box to display the transactions
        text_box = tk.Text(window, height=10, width=50)
        text_box.pack()

        # Add the transactions to the text box
        text_box.insert(tk.END, "User Transactions:\n\n")
        for transaction in transactions:
            id_number, first_name, last_name, barcode, name, checkout_date = transaction
            text_box.insert(tk.END, f"User ID: {id_number}\nName: {first_name} {last_name}\nBarcode: {barcode}\nItem: {name}\nCheckout Date: {checkout_date}\n\n")

    else:
        messagebox.showinfo("User Transactions", "No transactions found.")



def search_items_by_user_gui(id_number):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
    SELECT items.barcode, items.name
    FROM transactions
    JOIN items ON transactions.barcode = items.barcode
    WHERE transactions.user_id_number = ? AND transactions.checkin_date IS NULL
    """, (id_number,))
    items = c.fetchall()

    if items:
        # Create a new window to display the search results
        window = tk.Toplevel()
        window.title("Search Results")

        # Create a text box to display the search results
        text_box = tk.Text(window, height=10, width=50)
        text_box.pack()

        # Add the search results to the text box
        text_box.insert(tk.END, f"Items checked out by user with ID number {id_number}:\n\n")
        for item in items:
            barcode, name = item
            text_box.insert(tk.END, f"Barcode: {barcode}, Name: {name}\n")

    else:
        messagebox.showinfo("Search Items by User", f"No items checked out by user with ID number {id_number}.")

    conn.close()


def check_out_item(barcode, id_number):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id_number=?", (id_number,))
    user = c.fetchone()

    if user:
        c.execute("SELECT * FROM items WHERE barcode=?", (barcode,))
        item = c.fetchone()

        if item:
            if item[3] == 0:  # Check if item is not checked out
                c.execute("UPDATE items SET checked_out=1, checked_out_by=? WHERE barcode=?", (id_number, barcode))
                conn.commit()
                messagebox.showinfo("Check Out Item", "Item checked out successfully!")
            else:
                messagebox.showwarning("Check Out Item", "Item is already checked out.")
        else:
            messagebox.showerror("Check Out Item", "Item not found.")
    else:
        messagebox.showerror("Check Out Item", "User not found.")

    conn.close()

def check_in_item(barcode):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
    SELECT transactions.id
    FROM transactions
    JOIN items ON transactions.barcode = items.barcode
    WHERE transactions.barcode=? AND transactions.checkin_date IS NULL
    """, (barcode,))
    transaction = c.fetchone()

    if transaction:
        c.execute("UPDATE transactions SET checkin_date=datetime('now') WHERE id=?", (transaction[0],))
        c.execute("UPDATE items SET quantity=quantity+1 WHERE barcode=?", (barcode,))
        conn.commit()
        print("Item checked in successfully!")
    else:
        print("Item not found or already checked in.")

    conn.close()


def add_user(first_name, last_name, id_number):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (first_name, last_name, id_number) VALUES (?, ?, ?)",
                  (first_name, last_name, id_number))
        conn.commit()
        print("User added successfully!")
    except sqlite3.IntegrityError:
        print("User with the provided ID number already exists.")

    conn.close()


def check_quantity(barcode):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE barcode=?", (barcode,))
    item = c.fetchone()

    if item:
        name = item[2]
        quantity = item[5]
        messagebox.showinfo("Check Quantity", f"Item: {name} (Barcode: {barcode})\nQuantity: {quantity}")
    else:
        messagebox.showerror("Check Quantity", "Item not found.")

    conn.close()


def add_quantity(barcode, quantity):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE barcode=?", (barcode,))
    item = c.fetchone()
    if item:
        current_quantity = item[5]  # Get the current quantity
        new_quantity = current_quantity + quantity
        c.execute("UPDATE items SET quantity=? WHERE barcode=?", (new_quantity, barcode))
        conn.commit()
        print(f"Quantity added successfully! New quantity for {item[2]} (Barcode: {barcode}): {new_quantity}")
    else:
        print("Item not found.")

    conn.close()

def remove_quantity(barcode, quantity):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE barcode=?", (barcode,))
    item = c.fetchone()

    if item:
        current_quantity = item[5]  # Get the current quantity

        if current_quantity >= quantity:
            new_quantity = current_quantity - quantity
            c.execute("UPDATE items SET quantity=? WHERE barcode=?", (new_quantity, barcode))
            conn.commit()
            print(f"Quantity removed successfully! New quantity for {item[2]} (Barcode: {barcode}): {new_quantity}")
        else:
            print(f"Not enough quantity available for {item[2]} (Barcode: {barcode}). Current quantity: {current_quantity}")
    else:
        print("Item not found.")

    conn.close()


def main_menu():
    print("Welcome to the Inventory System!")
    print("Select an option:")
    print("1. Add Item")
    print("2. Remove Item")
    print("3. Check Out Item")
    print("4. Check In Item")
    print("5. Search Items by User")
    print("6. Add User")
    print("7. Add Quantity")
    print("8. Remove Quantity")
    print("9. Check Quantity")
    print("10. Exit")

def handle_menu_choice(choice):
    if choice == "1":
        barcode = input("Enter the barcode: ")
        name = input("Enter the item name: ")
        add_item(barcode, name)
    elif choice == "2":
        barcode = input("Enter the barcode of the item to remove: ")
        remove_item(barcode)
    elif choice == "3":
        id_number = input("Scan back of CAC: ")
        check_out_batch(id_number)
    elif choice == "4":
        barcode = input("Scan or enter the barcode: ")
        check_in_item(barcode)
    elif choice == "5":
        id_number = input("Scan CAC to search for: ")
        search_items_by_user(id_number)
    elif choice == "6":
        first_name = input("Enter the user's first name: ")
        last_name = input("Enter the user's last name: ")
        id_number = input("Scan the back of the user's CAC: ")
        add_user(first_name, last_name, id_number)
    elif choice == "7":
        barcode = input("Enter the barcode: ")
        quantity = int(input("Enter the quantity to add: "))
        add_quantity(barcode, quantity)
    elif choice == "8":
        barcode = input("Enter the barcode: ")
        quantity = int(input("Enter the quantity to remove: "))
        remove_quantity(barcode, quantity)
    elif choice == "9":
        barcode = input("Enter the barcode: ")
        check_quantity(barcode)
    elif choice == "10":
        sys.exit()
    else:
        print("Invalid choice. Please try again.")
def export_report():
    folder_path = r"C:\Users\Readi\Documents"
    filename = "inventory_report.xlsx"

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT barcode, name, quantity FROM items")
    items = c.fetchall()

    if items:
        df = pd.DataFrame(items, columns=["Barcode", "Name", "Quantity"])
        file_path = os.path.join(folder_path, filename)
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Export Report", f"Inventory report exported to '{file_path}'!")

        # Open the exported file
        os.startfile(file_path)
    else:
        messagebox.showinfo("Export Report", "No items found in the inventory.")

    conn.close()
def run_inventory_system():
    create_tables()
    while True:
        main_menu()
        choice = input("Enter your choice: ")
        handle_menu_choice(choice)
        time.sleep(1)  # Add a short delay to make the output more readable
def create_gui():
    window = tk.Tk()
    window.title("Inventory System")
    # Maximize the window to fullscreen
    window.attributes("-fullscreen", True)

    options = [
        ("Add Item", 1),
        ("Remove Item", 2),
        ("Check Out Item", 3),
        ("See Previous Issues", 4),
        ("Search Items by User", 5),
        ("Add User", 6),
        ("Add Current Quantity", 7),
        ("Remove From Quantity", 8),
        ("Check Quantity Of Item", 9),
        ("Export Current Inventory to Excel", 10),
        ("Exit", 11),
    ]

    for text, option in options:
        button = tk.Button(window, text=text, command=lambda option=option: on_button_click(option), height=3, width=20)
        button.pack(fill=tk.X)


    window.mainloop()

def on_button_click(option):
    if option == 1:
        barcode = simpledialog.askstring("Add Item", "Enter the barcode:")
        if barcode is None:
            return
        name = simpledialog.askstring("Add Item", "Enter the item name:")
        if name is None:
            return
        add_item(barcode, name)
    elif option == 2:
        barcode = simpledialog.askstring("Remove Item", "Enter the barcode of the item to remove:")
        if barcode is None:
            return
        remove_item(barcode)
    elif option == 3:
        id_number = simpledialog.askstring("Check Out Item", "Enter the user's ID number:")
        if id_number is None:
            return
        check_out_batch_gui(id_number)
    elif option == 4:
        show_user_transactions()
    elif option == 5:
        id_number = simpledialog.askstring("Search Items by User", "Enter the user's ID number to search for:")
        if id_number is None:
            return
        search_items_by_user_gui(id_number)

    elif option == 6:
        first_name = simpledialog.askstring("Add User", "Enter the user's first name:")
        if first_name is None:
            return
        last_name = simpledialog.askstring("Add User", "Enter the user's last name:")
        if last_name is None:
            return
        id_number = simpledialog.askstring("Add User", "Enter the user's ID number:")
        if id_number is None:
            return
        add_user(first_name, last_name, id_number)
    elif option == 7:
        barcode = simpledialog.askstring("Add Quantity", "Enter the barcode:")
        if barcode is None:
            return
        quantity = simpledialog.askinteger("Add Quantity", "Enter the quantity to add:")
        if quantity is None:
            return
        add_quantity(barcode, quantity)
    elif option == 8:
        barcode = simpledialog.askstring("Remove Quantity", "Enter the barcode:")
        if barcode is None:
            return
        quantity = simpledialog.askinteger("Remove Quantity", "Enter the quantity to remove:")
        if quantity is None:
            return
        remove_quantity(barcode, quantity)
    elif option == 9:
        barcode = simpledialog.askstring("Check Quantity", "Enter the barcode:")
        if barcode is None:
            return
        check_quantity(barcode)
    elif option == 10:
        export_report()
    elif option == 11:
        sys.exit()
if __name__ == "__main__":
    create_gui()
run_inventory_system()