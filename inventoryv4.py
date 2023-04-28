import sqlite3
import sys
import time
import cv2
import pyzbar
import subprocess
import os
import pandas as pd
import tkinter as tk
from tkinter import messagebox, Menu, filedialog
from tkinter import simpledialog
from tkinter.font import Font
import random
from tkinter import simpledialog, messagebox, Button, Tk
from collections import defaultdict



DATABASE = "inventory.db"
def update_database_schema():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Check if the transaction_id column already exists
    c.execute("PRAGMA table_info(transactions)")
    columns = c.fetchall()
    column_names = [col[1] for col in columns]

    if 'transaction_id' not in column_names:
        c.execute("ALTER TABLE transactions ADD COLUMN transaction_id INTEGER")

    conn.commit()
    conn.close()

# Call the function to update the schema at the beginning of your script
update_database_schema()

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
    user_id_number INTEGER,
    staff_name TEXT,
    checkout_date TIMESTAMP,
    checkin_date TIMESTAMP,
    quantity INTEGER,  -- Add the quantity column
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
import tkinter as tk
from tkinter import messagebox
import time

import tkinter as tk
from tkinter import messagebox
import time

import tkinter as tk
from tkinter import messagebox
import time

def check_out_batch_gui(id_number, staff_name):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id_number=?", (id_number,))
    user = c.fetchone()

    if user:
        transaction_id = random.randint(1, 1000000)  # Generate a unique transaction_id for this batch

        while True:
            barcode = simpledialog.askstring("Check Out Item", "Scan or enter the barcode (hit cancel to exit):")

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

                    c.execute(
                        "INSERT INTO transactions (barcode, user_id_number, staff_name, checkout_date, checkin_date, quantity) VALUES (?, ?, ?, datetime('now'), NULL, ?)",
                        (barcode, id_number, staff_name, checkout_quantity))

                    # Show the info message with a delayed auto-close
                    show_info_with_delay("Check Out Item", f"{checkout_quantity} item(s) added to the checkout list!", delay=2000)
                else:
                    messagebox.showerror("Check Out Item", "Not enough quantity available.")
            else:
                messagebox.showerror("Check Out Item", "Item not found.")

        conn.commit()
        conn.close()

    else:
        messagebox.showerror("Check Out Item", "User not found.")


def show_info_with_delay(title, message, delay):
    # Create a new top-level window
    window = tk.Toplevel()
    window.title(title)

    # Set the window to stay on top
    window.attributes("-topmost", True)
    window.grab_set()

    # Create a label to display the message
    label = tk.Label(window, text=message)
    label.pack()

    # Schedule the destruction of the window after the delay
    window.after(delay, lambda: destroy_window(window))

def destroy_window(window):
    window.grab_release()  # Release the grab
    window.destroy()  # Destroy the window

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
        user_id_number INTEGER,
        staff_name TEXT,
        checkout_date TIMESTAMP,
        checkin_date TIMESTAMP,
        quantity INTEGER,
        FOREIGN KEY (barcode) REFERENCES items (barcode),
        FOREIGN KEY (user_id_number) REFERENCES users (id_number)
    );
    """)

    conn.commit()
    conn.close()

def show_user_transactions():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
    SELECT transactions.staff_name, transactions.checkout_date, transactions.transaction_id, 
           users.id_number, users.first_name, users.last_name, 
           GROUP_CONCAT(items.name || ' (Qty: ' || transactions.quantity || ')', ', ') as item_details
    FROM transactions
    JOIN users ON transactions.user_id_number = users.id_number
    JOIN items ON transactions.barcode = items.barcode
    WHERE transactions.checkin_date IS NULL
    GROUP BY transactions.staff_name, transactions.transaction_id
    ORDER BY transactions.checkout_date DESC
    """)

    transactions = c.fetchall()
    conn.close()

    if transactions:
        # Create a new window to display the transactions
        window = tk.Toplevel()
        window.title("All Transactions")
        window.attributes('-topmost', True)

        # Create a text box to display the transactions
        text_box = tk.Text(window, height=10, width=90)
        text_box.pack()

        # Add the transactions to the text box
        text_box.insert(tk.END, "User Transactions:\n\n")
        for transaction in transactions:
            staff_name, checkout_date, transaction_id, id_number, first_name, last_name, item_details = transaction
            text_box.insert(tk.END,
                            f"Staff Name: {staff_name}\nCheckout Date: {checkout_date}\nTransaction ID: {transaction_id}\n"
                            f"User ID: {id_number}\nMember: {first_name} {last_name}\nItems: {item_details}\n\n")
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
        window.attributes('-topmost', True)

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
    window.config(bg="steelblue4")
    # Maximize the window to fullscreen
    window.attributes("-fullscreen", True)


    button_frame = tk.Frame(window, bg="steelblue4")
    button_frame.pack()

    options = [
        ("Add Item to inventory", 1),
        ("Remove Item from inventory", 2),
        ("Check Out member", 3),
        ("See Previously Issued", 4),
        ("Search Items by Member", 5),
        ("Add Member", 6),
        ("Add to Current Quantity", 7),
        ("Remove From Current Quantity", 8),
        ("Check Quantity Of Item", 9),
        ("Export Current Inventory to Excel", 10),
        ("Open old sheet (for tracking older issues)", 11),  # New option
        ("Exit", 12),  # Adjust the option number
    ]


    # Define the number of columns for the grid layout
    num_columns = 3

    bold_font = Font(weight="bold")


    for i, (text, option) in enumerate(options):
        button = tk.Button(button_frame, text=text, command=lambda option=option: on_button_click(option), height=5, width=42, bg="dim gray", fg="white", font=bold_font)
        button.grid(row=i // num_columns, column=i % num_columns, padx=10, pady=10)

    # Center the button frame within the window using pack()
    button_frame.pack(expand=True)
    button_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)



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
        pass
    elif option == 2:
        barcode = simpledialog.askstring("Remove Item from List", "Enter the barcode of the item to remove:")
        if barcode is None:
            return
        remove_item(barcode)
        pass
    elif option == 3:
        staff_name = simpledialog.askstring("Readiness Member", "Name of Issuer:")
        if staff_name:
            id_number = simpledialog.askstring("Check Out Item", "Scan back of member's CAC:")
            if id_number is None:
                return
            check_out_batch_gui(id_number, staff_name)
        pass
    elif option == 4:
        show_user_transactions()
        pass
    elif option == 5:
        id_number = simpledialog.askstring("Search Items by Member", "Scan back of member's CAC number to search for:")
        if id_number is None:
            return
        search_items_by_user_gui(id_number)
        pass

    elif option == 6:
        first_name = simpledialog.askstring("Add Member", "Enter the memeber's first name:")
        if first_name is None:
            return
        last_name = simpledialog.askstring("Add User", "Enter the Member's last name:")
        if last_name is None:
            return
        id_number = simpledialog.askstring("Add User", "Scan back of member's CAC:")
        if id_number is None:
            return
        add_user(first_name, last_name, id_number)
        pass
    elif option == 7:
        barcode = simpledialog.askstring("Add Quantity", "Enter the barcode:")
        if barcode is None:
            return
        quantity = simpledialog.askinteger("Add Quantity", "Enter the amount to add:")
        if quantity is None:
            return
        add_quantity(barcode, quantity)
        pass
    elif option == 8:
        barcode = simpledialog.askstring("Remove Quantity", "Enter the barcode:")
        if barcode is None:
            return
        quantity = simpledialog.askinteger("Remove Quantity", "Enter the amount to remove:")
        if quantity is None:
            return
        remove_quantity(barcode, quantity)
        pass
    elif option == 9:
        barcode = simpledialog.askstring("Check Quantity", "Enter the barcode:")
        if barcode is None:
            return
        check_quantity(barcode)
        pass
    elif option == 10:
        export_report()
        pass
    elif option == 11:  # Open Excel File
        file_path = r"C:\Users\Readi\Documents\apr27.xlsm"  # Replace with the actual file path
        if os.path.isfile(file_path) and file_path.endswith(".xlsm"):
            os.startfile(file_path)
        else:
            messagebox.showerror("Error", "Invalid file path or file format.")
        pass
    elif option == 12:
        sys.exit()
        pass
if __name__ == "__main__":
    create_gui()
run_inventory_system()
