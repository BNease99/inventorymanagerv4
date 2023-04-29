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
import tkinter as tk
from tkinter import messagebox
import time



DATABASE = "inventory.db"

class CustomDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, prompt=None, input_type='string'):
        self.prompt = prompt
        self.result = None
        self.input_type = input_type
        super().__init__(parent, title=title)

    def body(self, master):
        tk.Label(master, text=self.prompt).grid(row=0)
        self.entry = tk.Entry(master)
        self.entry.grid(row=1)

        # Set focus after a delay of 100ms
        self.entry.focus_set()
        self.entry.after(100, self.entry.focus_set)

    def apply(self):
        if self.input_type == 'integer':
            try:
                self.result = int(self.entry.get())
            except ValueError:
                self.result = None
        else:
            self.result = self.entry.get()

    def show(self):
        self.attributes('-topmost', True)
        return self.result

class IntegerDialog(CustomDialog):
    def __init__(self, parent, title, prompt):
        super().__init__(parent, title, prompt)

    def create_widgets(self):
        self.label = tk.Label(self.top, text=self.prompt, font=self.font)
        self.label.pack(side=tk.TOP, pady=10)

        self.entry = tk.Entry(self.top, font=self.font, validate="key")
        self.entry.configure(validatecommand=(self.entry.register(self.validate_integer), "%P"))
        self.entry.pack(side=tk.TOP)

        self.ok_button = tk.Button(self.top, text="OK", font=self.font, command=self.on_ok)
        self.ok_button.pack(side=tk.LEFT, padx=10)

        self.cancel_button = tk.Button(self.top, text="Cancel", font=self.font, command=self.on_cancel)
        self.cancel_button.pack(side=tk.RIGHT)

    def validate_integer(self, new_value):
        if new_value == "":
            return True
        try:
            int(new_value)
            return True
        except ValueError:
            return False
class DropdownDialog(CustomDialog):
    def __init__(self, parent, title, prompt, items):
        self.items = items
        super().__init__(parent, title, prompt)

    def body(self, master):
        tk.Label(master, text=self.prompt).grid(row=0)
        self.selected_item = tk.StringVar()
        self.selected_item.set(self.items[0])  # Set the default selected item
        self.dropdown = tk.OptionMenu(master, self.selected_item, *self.items)
        self.dropdown.grid(row=1)

    def apply(self):
        self.result = self.selected_item.get()

def create_tables():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()


    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            barcode TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            last_checkout INTEGER,
            last_checkin INTEGER,
            quantity INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id_number TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL,
            user_id_number TEXT NOT NULL,
            staff_name TEXT NOT NULL,
            checkout_date TEXT,
            checkin_date TEXT,
            quantity INTEGER,
            transaction_id INTEGER,
            FOREIGN KEY (barcode) REFERENCES items (barcode),
            FOREIGN KEY (user_id_number) REFERENCES users (id_number)
        )
    """)

    conn.commit()
    conn.close()


# Call create_tables() before adding users
create_tables()

def add_item(barcode, name):
    print(f"Adding item with barcode: {barcode} and name: {name}")
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

    c.execute("SELECT * FROM items WHERE barcode=?", (barcode,))
    item = c.fetchone()

    if item:
        c.execute("DELETE FROM items WHERE barcode=?", (barcode,))
        conn.commit()
        messagebox.showinfo("Item Removed", f"Item with barcode {barcode} removed successfully!")
    else:
        messagebox.showerror("Item Not Found", f"Item with barcode {barcode} not found.")

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
def check_out_batch_gui(id_number, staff_name, main_window):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id_number=?", (id_number,))
    user = c.fetchone()

    if user:
        transaction_id = random.randint(1, 1000000)  # Generate a unique transaction_id for this batch

        while True:
            barcode = simpledialog.askstring("Check Out Item", "Scan or enter the barcode (type 'done' to stop):",
                                             parent=main_window)
            print(f"Scanned barcode: {barcode}")  # Debugging print statement

            if barcode is None or barcode.lower() == 'done':
                break

            c.execute("SELECT * FROM items WHERE barcode=?", (barcode.strip(),))
            item = c.fetchone()
            print(f"Fetched item: {item}")  # Debugging print statement

            if item:
                current_quantity = item[4]
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

import datetime
import pytz

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

            # Convert checkout_date from UTC to local time
            utc_datetime = datetime.datetime.strptime(checkout_date, "%Y-%m-%d %H:%M:%S")
            local_timezone = pytz.timezone('HST')  # Replace 'Your_Local_Timezone' with the desired timezone
            local_datetime = utc_datetime.replace(tzinfo=pytz.utc).astimezone(local_timezone)
            formatted_checkout_date = local_datetime.strftime("%Y-%m-%d %H:%M:%S")

            text_box.insert(tk.END,
                            f"Staff Name: {staff_name}\nCheckout Date: {formatted_checkout_date}\nTransaction ID: {transaction_id}\n"
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
        quantity = item[4]
        messagebox.showinfo("Check Quantity", f"Item: {name} (Barcode: {barcode})\nQuantity: {quantity}")
    else:
        messagebox.showerror("Check Quantity", "Item not found.")

    conn.close()
def get_all_items():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT barcode, name FROM items")
    items = c.fetchall()

    conn.close()

    return items


def add_quantity(barcode, quantity):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE barcode=?", (barcode,))
    item = c.fetchone()
    if item:
        current_quantity = item[4]  # Get the current quantity
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
        current_quantity = item[4]  # Get the current quantity

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
        button = tk.Button(button_frame, text=text,
                           command=lambda option=option, parent=window: on_button_click(option, parent), height=5,
                           width=42, bg="dim gray", fg="white", font=bold_font)
        button.grid(row=i // num_columns, column=i % num_columns, padx=10, pady=10)

    # Center the button frame within the window using pack()
    button_frame.pack(expand=True)
    button_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)



    window.mainloop()

def on_button_click(option, parent):
    if option == 1:
        barcode_dialog = CustomDialog(parent, title="Add Item", prompt="Enter the barcode:")
        barcode = barcode_dialog.result
        if barcode is None:
            return
        name_dialog = CustomDialog(parent, title="Add Item", prompt="Enter the item name:")
        name = name_dialog.result
        if name is None:
            return
        add_item(barcode, name)








    elif option == 2:

        item_dialog = DropdownDialog(parent, title="Remove Item from List", prompt="Select the item to remove:",
                                     items=get_all_items())

        selected_item = item_dialog.result

        if selected_item is None:
            return

        barcode = selected_item.split('(')[1].split(',')[0].strip("'")

        remove_item(barcode)




    elif option == 3:
        staff_name_dialog = CustomDialog(parent, title="Readiness Member", prompt="Name of Issuer:")
        staff_name = staff_name_dialog.result
        if staff_name:
            id_number_dialog = CustomDialog(parent, title="Check Out Item", prompt="Scan back of member's CAC:")
            id_number = id_number_dialog.result
            if id_number is None:
                return
            check_out_batch_gui(id_number, staff_name, parent)

    elif option == 4:
        show_user_transactions()

    elif option == 5:
        id_number_dialog = CustomDialog(parent, title="Search Items by Member", prompt="Scan back of member's CAC number to search for:")
        id_number = id_number_dialog.result
        if id_number is None:
            return
        search_items_by_user_gui(id_number)

    elif option == 6:
        first_name_dialog = CustomDialog(parent, title="Add Member", prompt="Enter the member's first name:")
        first_name = first_name_dialog.result
        if first_name is None:
            return
        last_name_dialog = CustomDialog(parent, title="Add User", prompt="Enter the Member's last name:")
        last_name = last_name_dialog.result
        if last_name is None:
            return
        id_number_dialog = CustomDialog(parent, title="Add User", prompt="Scan back of member's CAC:")
        id_number = id_number_dialog.result
        if id_number is None:
            return
        add_user(first_name, last_name, id_number)


    # For option 7 (add quantity)

    elif option == 7:

        barcode_dialog = CustomDialog(parent, title="Add Quantity", prompt="Enter the barcode:")

        if barcode_dialog.result is None:
            return

        barcode = barcode_dialog.result

        quantity_dialog = IntegerDialog(parent, title="Add Quantity", prompt="Enter the amount to add:")

        if quantity_dialog.result is None:
            return

        quantity = int(quantity_dialog.result)

        add_quantity(barcode, quantity)


    # For option 8 (remove quantity)

    elif option == 8:

        barcode_dialog = CustomDialog(parent, title="Remove Quantity", prompt="Enter the barcode:")

        if barcode_dialog.result is None:
            return

        barcode = barcode_dialog.result

        quantity_dialog = IntegerDialog(parent, title="Remove Quantity", prompt="Enter the amount to remove:")

        if quantity_dialog.result is None:
            return

        quantity = int(quantity_dialog.result)

        remove_quantity(barcode, quantity)

    elif option == 9:
        barcode_dialog = CustomDialog(parent, title="Check Quantity", prompt="Enter the barcode:")
        barcode = barcode_dialog.result
        if barcode is None:
            return
        check_quantity(barcode)
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
