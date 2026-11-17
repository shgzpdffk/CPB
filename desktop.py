import tkinter as tk 
from tkinter import ttk
import json
from pathlib import Path

root = tk.Tk()
root.title("Че по блюдам")
root.geometry("850x450")
form = ttk.Frame(root)
form.pack(side='left', fill='y')

results = ttk.Frame(root)
results.pack(side='left', fill='both', expand=True, padx=20, pady=20)
label = ttk.Label(root, text="Какие есть продукты?")
label.pack(anchor='w', padx=20, pady=(20, 5))

product_input = ttk.Entry(root, width=50)
product_input.pack(anchor="w", padx=20)

def add_product():
    product = product_input.get().strip()
    if product == "":
        return
    
    product_list.insert(tk.END, product)
    product_input.delete(0, tk.END)

def delete_product():
    selected = product_list.curselection()
    if not selected:
        return

    product_list.delete(selected[0])

add_button = ttk.Button(root, text="Добавить", command=add_product)
add_button.pack(anchor="w", padx=20, pady=(10, 0))

delete_button = ttk.Button(root, text="Удалить", command=delete_product)
delete_button.pack(anchor="w", padx=20)

product_list = tk.Listbox(root, width=50, height=10)
product_list.pack(anchor="w", padx=20, pady=(10, 0))

wish_label = ttk.Label(root, text="Пожелания по блюдам")
wish_label.pack(anchor="w", padx=20, pady=(20, 5))

wish_input = ttk.Entry(root, width = 35)
wish_input.pack(anchor="w", padx=20)

def search_recipes():
    products = list(product_list.get(0, tk.END))
    request = {"products": products}
    wish = wish_input.get().strip()
    if wish:
        request["wish"] = wish

    print(request)

    fixture_path = Path(__file__).with_name("search_fixture.json")

    with fixture_path.open(encoding="utf-8") as f:
        response = json.load(f)

    for widget in results.winfo_children():
        widget.destroy()

    for recipe in response["recipes"]:
        card = ttk.LabelFrame(results, text=recipe["title"])
        card.pack(fill='x', pady=(0, 8))

        names = ', '.join(recipe["missing_required"])
        text = f"Докупить: {recipe['missing_count']} - {names}"
        purchases = ttk.Label(card, text=text)
        purchases.pack(anchor="w", padx=10, pady=8)
search_button = ttk.Button(root, text="Найти рецепты", command=search_recipes)
search_button.pack(anchor="w", padx=20, pady=(10, 0))

root.mainloop()
