import sqlite3
import sys
import time
import cv2
import pyzbar

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
        FOREIGN KEY (checked_out_by) REFERENCES users (username)
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
        print("Item added successfully!")
    except sqlite3.IntegrityError:
        print("Item with barcode already exists.")

    conn.close()

def remove_item(barcode):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("DELETE FROM items WHERE barcode=?", (barcode,))
    conn.commit()
    print("Item removed successfully!")

    conn.close()

def search_items_by_user(id_number):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
    SELECT items.barcode, items.name
    FROM items
    JOIN users ON items.checked_out_by = users.id_number
    WHERE users.id_number = ? AND items.checked_out = 1
    """, (id_number,))
    items = c.fetchall()

    if items:
        print(f"Items checked out by user with ID number {id_number}:")
        for item in items:
            barcode, name = item
            print(f"Barcode: {barcode}, Name: {name}")
    else:
        print(f"No items checked out by user with ID number {id_number}.")

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
                print("Item checked out successfully!")
            else:
                print("Item is already checked out.")
        else:
            print("Item not found.")
    else:
        print("User not found.")

    conn.close()

def check_in_item(barcode):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM items WHERE barcode=? AND checked_out=1", (barcode,))
    item = c.fetchone()

    if item:
        c.execute("UPDATE items SET checked_out=0, checked_out_by=NULL WHERE barcode=?", (barcode,))
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

# Example usage:
add_user("John", "Doe", "123456")


def read_barcode_from_webcam():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        decoded_data = decode(frame)

        if decoded_data:
            barcode = decoded_data[0].data.decode("utf-8")
            break

        cv2.imshow("Barcode Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    return barcode

def main_menu():
    print("Welcome to the Inventory System!")
    print("Select an option:")
    print("1. Add Item")
    print("2. Remove Item")
    print("3. Check Out Item")
    print("4. Check In Item")
    print("5. Search Items by User")
    print("6. Add User")
    print("7. Exit")

def handle_menu_choice(choice):
    if choice == "1":
        barcode = input("Enter the barcode: ")
        name = input("Enter the item name: ")
        add_item(barcode, name)
    elif choice == "2":
        barcode = input("Enter the barcode of the item to remove: ")
        remove_item(barcode)
    elif choice == "3":
        barcode = input("Scan or enter the barcode: ")
        username = input("Enter the username: ")
        check_out_item(barcode, username)
    elif choice == "4":
        barcode = input("Scan or enter the barcode: ")
        check_in_item(barcode)
    elif choice == "5":
        username = input("Enter the username to search for: ")
        search_items_by_user(username)
    elif choice == "6":
        first_name = input("Enter the user's first name: ")
        last_name = input("Enter the user's last name: ")
        id_number = input("Enter the user's ID number: ")
        add_user(first_name, last_name, id_number)
    elif choice == "7":
        sys.exit()
    else:
        print("Invalid choice. Please try again.")

def run_inventory_system():
    create_tables()

    while True:
        main_menu()
        choice = input("Enter your choice: ")
        handle_menu_choice(choice)
        time.sleep(1)  # Add a short delay to make the output more readable

run_inventory_system()