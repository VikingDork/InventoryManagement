import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import csv

DATA_FILE = "inventory_data.json"


class Inventory:
    def __init__(self):
        self.products = {}
        self.load_data()

    def add_item(self, item_name, stock_count):
        if item_name not in self.products:
            self.products[item_name] = {"stock_count": stock_count}
            self.save_data()
            return f"✅ Item '{item_name}' added."
        else:
            return f"⚠️ Item '{item_name}' already exists."

    def update_stock(self, item_name, quantity_change):
        if item_name in self.products:
            self.products[item_name]["stock_count"] += quantity_change
            self.save_data()
            return f"🔄 Stock updated: {item_name} = {self.products[item_name]['stock_count']}"
        else:
            return f"❌ Item '{item_name}' not found."

    def delete_item(self, item_name):
        if item_name in self.products:
            del self.products[item_name]
            self.save_data()
            return f"🗑️ Item '{item_name}' deleted."
        else:
            return f"❌ Item '{item_name}' not found."

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.products, f, indent=4)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                self.products = json.load(f)
        else:
            self.products = {}

    def search_items(self, query):
        query = query.lower()
        return {
            name: data
            for name, data in self.products.items()
            if query in name.lower()
        }

    # ---------- CSV Features ----------

    def import_csv(self, file_path, merge=True):
        imported_count = 0
        new_data = {}

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                name = row.get("Name") or row.get("name")
                stock = row.get("Stock") or row.get("stock")
                if name and stock:
                    try:
                        stock = int(stock)
                        new_data[name] = {"stock_count": stock}
                    except ValueError:
                        continue

        if merge:
            for name, data in new_data.items():
                if name in self.products:
                    self.products[name]["stock_count"] += data["stock_count"]
                else:
                    self.products[name] = data
            imported_count = len(new_data)
        else:
            self.products = new_data
            imported_count = len(new_data)

        self.save_data()
        return imported_count, merge

    def export_csv(self, file_path):
        with open(file_path, "w", newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Name", "Stock"])
            for name, data in self.products.items():
                writer.writerow([name, data["stock_count"]])
        return len(self.products)


# ---------------- GUI ----------------

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧺 Inventory Manager (CSV Enabled)")
        self.root.geometry("700x550")
        self.root.resizable(False, False)
        self.inventory = Inventory()
        self.sort_reverse = False

        # Theme
        bg = "#f7f9fc"
        accent = "#3b82f6"
        text = "#1e293b"
        self.root.configure(bg=bg)

        # ---------- Search Bar ----------
        search_frame = tk.Frame(root, bg=bg)
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="🔎 Search:", bg=bg, fg=text).pack(side="left", padx=5)
        self.search_entry = tk.Entry(search_frame, width=40)
        self.search_entry.pack(side="left", padx=5)
        tk.Button(search_frame, text="Search", bg=accent, fg="white", command=self.search_items).pack(side="left", padx=5)
        tk.Button(search_frame, text="Clear", bg="#64748b", fg="white", command=self.clear_search).pack(side="left", padx=5)

        # ---------- Form Frame ----------
        form_frame = tk.Frame(root, bg=bg)
        form_frame.pack(pady=10)

        labels = ["Name", "Stock"]
        self.entries = {}
        for i, label in enumerate(labels):
            tk.Label(form_frame, text=label + ":", bg=bg, fg=text).grid(row=i, column=0, padx=5, pady=5, sticky="e")
            entry = tk.Entry(form_frame)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.entries[label.lower()] = entry

        # ---------- Buttons ----------
        button_frame = tk.Frame(root, bg=bg)
        button_frame.pack(pady=10)

        style = {"bg": accent, "fg": "white", "font": ("Segoe UI", 10, "bold"), "width": 15, "relief": "flat"}
        tk.Button(button_frame, text="Add Item", command=self.add_item, **style).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Update Stock", command=self.update_stock, **style).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Delete Item", command=self.delete_item, **style).grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Refresh Table", command=self.refresh_table, **style).grid(row=0, column=3, padx=5)

        # ---------- CSV Buttons ----------
        csv_frame = tk.Frame(root, bg=bg)
        csv_frame.pack(pady=5)

        csv_style = {"bg": "#10b981", "fg": "white", "font": ("Segoe UI", 9, "bold"), "width": 15, "relief": "flat"}
        tk.Button(csv_frame, text="Import CSV", command=self.import_csv, **csv_style).grid(row=0, column=0, padx=5)
        tk.Button(csv_frame, text="Export CSV", command=self.export_csv, **csv_style).grid(row=0, column=1, padx=5)

        # ---------- Table ----------
        table_frame = tk.Frame(root)
        table_frame.pack(pady=10)

        columns = ("name", "stock")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        self.tree.pack()

        for col in columns:
            self.tree.heading(col, text=col.capitalize(), command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=300, anchor="center")

        # ---------- Status Bar ----------
        self.status_label = tk.Label(root, text="Data loaded successfully ✅", bg=accent, fg="white",
                                     font=("Segoe UI", 10, "italic"), anchor="w")
        self.status_label.pack(fill="x", pady=5)

        self.refresh_table()

    # ---------- Actions ----------

    def add_item(self):
        try:
            name = self.entries["name"].get().strip()
            stock = int(self.entries["stock"].get())
            if not name:
                messagebox.showwarning("Warning", "Please enter an item name.")
                return
            msg = self.inventory.add_item(name, stock)
            self.refresh_table()
            self.update_status(msg)
        except ValueError:
            messagebox.showerror("Error", "Stock must be a number.")

    def update_stock(self):
        try:
            name = self.entries["name"].get().strip()
            stock_change = int(self.entries["stock"].get())
            msg = self.inventory.update_stock(name, stock_change)
            self.refresh_table()
            self.update_status(msg)
        except ValueError:
            messagebox.showerror("Error", "Stock change must be a number.")

    def delete_item(self):
        name = self.entries["name"].get().strip()
        msg = self.inventory.delete_item(name)
        self.refresh_table()
        self.update_status(msg)

    def search_items(self):
        query = self.search_entry.get().strip()
        if query:
            filtered = self.inventory.search_items(query)
            self.populate_table(filtered)
            self.update_status(f"🔎 Showing results for '{query}'")
        else:
            self.refresh_table()

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.refresh_table()
        self.update_status("Search cleared.")

    # ---------- CSV Actions ----------

    def import_csv(self):
        file_path = filedialog.askopenfilename(
            title="Import CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        # Ask how to handle the import
        response = messagebox.askyesnocancel(
            "CSV Import Options",
            "Would you like to MERGE with existing data?\n\n"
            "Yes = Merge (add/update existing items)\n"
            "No = Overwrite (replace all data)\n"
            "Cancel = Abort"
        )

        if response is None:  # Cancel
            self.update_status("🚫 Import cancelled.")
            return

        merge = response  # True = Merge, False = Overwrite
        count, merged = self.inventory.import_csv(file_path, merge)
        self.refresh_table()

        if merged:
            self.update_status(f"📥 Imported and merged {count} items from CSV.")
        else:
            self.update_status(f"📂 Imported {count} items (inventory overwritten).")

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Export Inventory as CSV"
        )
        if file_path:
            count = self.inventory.export_csv(file_path)
            self.update_status(f"📤 Exported {count} items to '{os.path.basename(file_path)}'.")

    # ---------- Table Management ----------

    def refresh_table(self):
        self.populate_table(self.inventory.products)

    def populate_table(self, data_dict):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for name, data in data_dict.items():
            self.tree.insert("", "end", values=(name, data["stock_count"]))

    def sort_by_column(self, col):
        self.sort_reverse = not self.sort_reverse
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children("")]

        try:
            data.sort(key=lambda t: int(t[0]), reverse=self.sort_reverse)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=self.sort_reverse)

        for index, (_, child) in enumerate(data):
            self.tree.move(child, "", index)

        self.update_status(f"Sorted by '{col.capitalize()}' {'↓' if self.sort_reverse else '↑'}")

    def update_status(self, message):
        self.status_label.config(text=message)


if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()
