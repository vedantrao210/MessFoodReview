"""
Combined backend + UI with a Main Control UI (User / Admin / Quit).
This version runs a Python-level control loop: the main menu Tk() is created,
destroyed, and based on the user's choice a standalone User/Admin Tk() is launched.
Only when Quit is chosen does the program exit.
"""

import traceback
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import tkinter.simpledialog as simpledialog
from tkinter import messagebox


# -------------------------
# Backend (unchanged logic, minor adapts)
# -------------------------
# Try MySQL clients first
db = None
db_type = None  # 'pymysql' | 'mysqlconnector' | 'sqlite'
conn = None
cur = None

def adapt_query(q, using_sqlite):
    if using_sqlite:
        return q.replace("%s", "?")
    return q

# Attempt DB clients
try:
    import pymysql
    conn = pymysql.connect(host="localhost", user="root", password="", database="menu_review", autocommit=False)
    cur = conn.cursor()
    db_type = "pymysql"
    db = pymysql
except Exception:
    try:
        import mysql.connector
        conn = mysql.connector.connect(host="localhost", user="root", passwd="", database="menu_review")
        cur = conn.cursor()
        db_type = "mysqlconnector"
        db = mysql.connector
    except Exception:
        import sqlite3
        conn = sqlite3.connect("menu_review.db", check_same_thread=False)
        cur = conn.cursor()
        db_type = "sqlite"
        db = sqlite3

def tab():
    try:
        using_sqlite = (db_type == "sqlite")
        q1 = """
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY,
            day VARCHAR(20) NOT NULL,
            meal VARCHAR(50) NOT NULL,
            item TEXT DEFAULT '#'
        )
        """
        q2 = """
        CREATE TABLE IF NOT EXISTS reviews(
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_id INTEGER,
            review_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (menu_id) REFERENCES menu(id)
        )
        """
        cur.execute(adapt_query(q1, using_sqlite))
        cur.execute(adapt_query(q2, using_sqlite))
        conn.commit()
        return {"status": "success", "message": "Tables created (or already exist).", "db_type": db_type}
    except Exception as e:
        return {"status": "error", "message": str(e), "trace": traceback.format_exc()}

def add_menu(menuid, day, meal, item):
    try:
        using_sqlite = (db_type == "sqlite")
        q = "INSERT INTO menu (id, day, meal, item) VALUES (%s, %s, %s, %s)"
        cur.execute(adapt_query(q, using_sqlite), (menuid, day, meal, item))
        conn.commit()
        return {"status": "success", "message": f"Menu id {menuid} added."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def mod_menu(menuid, DAY, MEAL, ITEM, password=""):
    if password != "":
        return {"status": "denied", "message": "Invalid access"}
    return add_menu(menuid, DAY, MEAL, ITEM)

def del_menu(menuid, password=""):
    if password != "":
        return {"status": "denied", "message": "Viewers cannot delete menu"}
    try:
        q = "DELETE FROM menu WHERE id = %s"
        cur.execute(adapt_query(q, db_type == "sqlite"), (menuid,))
        conn.commit()
        return {"status": "success", "message": f"Menu id {menuid} deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_full_menu():
    try:
        q = "SELECT id, day, meal, item FROM menu"
        cur.execute(adapt_query(q, db_type == "sqlite"))
        rows = cur.fetchall()
        menu_list = []
        for r in rows:
            menu_list.append({"id": r[0], "day": r[1], "meal": r[2], "item": r[3]})
        return {"status": "success", "menu": menu_list}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def ad(menu_id, review_text):
    if menu_id is None or review_text is None:
        return {"status": "error", "message": "Invalid parameters"}
    try:
        q = "INSERT INTO reviews (menu_id, review_text) VALUES (%s, %s)"
        cur.execute(adapt_query(q, db_type == "sqlite"), (menu_id, review_text))
        conn.commit()
        return {"status": "success", "menu_id": menu_id, "review_text": review_text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def del_review(menuid):
    try:
        q = "DELETE FROM reviews WHERE menu_id = %s"
        cur.execute(adapt_query(q, db_type == "sqlite"), (menuid,))
        conn.commit()
        return {"status": "success", "message": f"Reviews for menu id {menuid} deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def upd_menu(column, newval, menuid, password=""):
    if password != "":
        return {"status": "denied", "message": "Unauthorized"}
    if column not in ("day", "meal", "item"):
        return {"status": "error", "message": "Invalid column"}
    try:
        q = f"UPDATE menu SET {column} = %s WHERE id = %s"
        cur.execute(adapt_query(q, db_type == "sqlite"), (newval, menuid))
        conn.commit()
        return {"status": "success", "message": f"Menu id {menuid} column {column} updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def upd_review_by_id(review_id, new_text):
    """
    Update a single review identified by review_id with new_text.
    Returns a dict with status/message like other backend functions.
    """
    try:
        q = "UPDATE reviews SET review_text = %s WHERE review_id = %s"
        cur.execute(adapt_query(q, db_type == "sqlite"), (new_text, review_id))
        conn.commit()
        return {"status": "success", "message": f"Review id {review_id} updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}    

def upd_rev(newre, menuid):
    try:
        q = "UPDATE reviews SET review_text = %s WHERE menu_id = %s"
        cur.execute(adapt_query(q, db_type == "sqlite"), (newre, menuid))
        conn.commit()
        return {"status": "success", "message": f"Reviews for menu id {menuid} updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_reviews(menuid):
    try:
        q = "SELECT review_id, menu_id, review_text, created_at FROM reviews WHERE menu_id = %s"
        cur.execute(adapt_query(q, db_type == "sqlite"), (menuid,))
        rows = cur.fetchall()
        result = []
        for r in rows:
            result.append({"review_id": r[0], "menu_id": r[1], "text": r[2], "created_at": str(r[3])})
        return {"status": "success", "reviews": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Ensure tables exist on import
_init_resp = tab()
if _init_resp.get("status") != "success":
    print("Warning: backend tab() init:", _init_resp)

# Provide module-like access (some UI parts expected 'b' module)
this_module = sys.modules[__name__]


# -------------------------
# Utility used by UIs to call backend functions
# -------------------------
def call_backend(fn_name, *args, **kwargs):
    # attempt to call functions defined in this file (module)
    if not hasattr(this_module, fn_name):
        return False, f"Backend has no function '{fn_name}'"
    fn = getattr(this_module, fn_name)
    try:
        return True, fn(*args, **kwargs)
    except TypeError as te:
        # some older UI code may try to call with cur as first arg - try falling back
        if hasattr(this_module, "cur"):
            try:
                return True, fn(this_module.cur, *args, **kwargs)
            except Exception as e:
                return False, str(e)
        return False, str(te)
    except Exception as e:
        return False, str(e)


# -------------------------
# UI builder: User window
# Works in two modes:
# - as Toplevel if parent (control UI) passed
# - as standalone Tk when parent is None (used in looped control flow)
# -------------------------
def open_user_window(parent=None):
    is_toplevel = parent is not None
    if is_toplevel:
        win = tk.Toplevel(parent)
    else:
        win = tk.Tk()
    win.title("Mess Menu & Reviews — User View")
    win.geometry("1000x640")
    win.minsize(900, 600)
    current_edit_review = {"id": None}

    top_frame = ttk.Frame(win, padding=8)
    top_frame.pack(fill="x")

    ttk.Label(top_frame, text="Select Day:").pack(side="left", padx=(0,6))
    day_var = tk.StringVar(value="Monday")
    day_combo = ttk.Combobox(top_frame, textvariable=day_var, state="readonly",
                            values=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], width=12)
    day_combo.pack(side="left", padx=(0,14))

    ttk.Label(top_frame, text="Select Meal:").pack(side="left", padx=(0,6))
    meal_var = tk.StringVar(value="Breakfast")
    meal_combo = ttk.Combobox(top_frame, textvariable=meal_var, state="readonly",
                            values=["Breakfast","Lunch","Snacks","Dinner"], width=12)
    meal_combo.pack(side="left", padx=(0,14))

    def refresh_menu_for_selection():
        ok, res = call_backend("get_full_menu")
        if not ok:
            messagebox.showerror("Error", f"Could not load menu: {res}", parent=(win if is_toplevel else None))
            return
        if isinstance(res, dict) and res.get("status") == "success":
            all_menu = res.get("menu", [])
        else:
            messagebox.showerror("Error", f"Unexpected get_full_menu response: {res}", parent=(win if is_toplevel else None))
            return

        sel_day = day_var.get()
        sel_meal = meal_var.get()

        filtered = [m for m in all_menu if m.get("day") == sel_day and m.get("meal") == sel_meal]
        menu_listbox.delete(0, "end")

        menu_listbox.menu_items = filtered
        for idx, m in enumerate(filtered):
            item_short = (m.get("item") or "#").replace("\n", " ")
            if len(item_short) > 60:
                item_short = item_short[:57] + "..."
            menu_listbox.insert("end", f"{m.get('id')}  •  {item_short}")

    ttk.Button(top_frame, text="Show Menu", command=refresh_menu_for_selection).pack(side="left", padx=6)

    main_pane = ttk.Frame(win, padding=8)
    main_pane.pack(fill="both", expand=True)

    left_frame = ttk.Frame(main_pane)
    left_frame.pack(side="left", fill="y", padx=(0,8), pady=4)

    ttk.Label(left_frame, text="Menu entries for selected Day & Meal").pack(anchor="w")
    menu_listbox = tk.Listbox(left_frame, width=40, height=25, activestyle="dotbox")
    menu_listbox.pack(fill="y", expand=False)

    mid_frame = ttk.Frame(main_pane)
    mid_frame.pack(side="left", fill="both", expand=True, padx=(8,8))

    ttk.Label(mid_frame, text="Selected Menu Item (full text)").pack(anchor="w")
    menu_text = scrolledtext.ScrolledText(mid_frame, width=60, height=8, wrap="word")
    menu_text.pack(fill="x", pady=(0,8))
    menu_text.configure(state="disabled")

    ttk.Label(mid_frame, text="Reviews for selected item").pack(anchor="w", pady=(8,0))
    reviews_box = tk.Listbox(mid_frame, width=80, height=10)
    reviews_box.pack(fill="both", expand=False, pady=(0,8))

    ttk.Label(mid_frame, text="Write your review:").pack(anchor="w")
    review_entry = scrolledtext.ScrolledText(mid_frame, width=60, height=4, wrap="word")
    review_entry.pack(fill="x", pady=(0,8))

    button_frame_mid = ttk.Frame(mid_frame)
    button_frame_mid.pack(fill="x", pady=(0,6))

    def load_reviews_for_menuid(menuid):
        reviews_box.delete(0, "end")
        ok, res = call_backend("get_reviews", menuid)
        if not ok:
            # fallback: try direct cur access
            if hasattr(this_module, "cur"):
                try:
                    this_module.cur.execute("SELECT review_id, menu_id, review_text, created_at FROM reviews WHERE menu_id = %s", (menuid,))
                    rows = this_module.cur.fetchall()
                    for r in rows:
                        display = f"[{r[0]}] {r[2]}  ({r[3]})"
                        reviews_box.insert("end", display)
                except Exception as e:
                    reviews_box.insert("end", f"Error loading reviews: {e}")
            else:
                reviews_box.insert("end", f"Error: {res}")
            return
        if isinstance(res, dict) and res.get("status") == "success":
            for rv in res.get("reviews", []):
                reviews_box.insert("end", f"[{rv.get('review_id')}] {rv.get('text')}  ({rv.get('created_at')})")
        elif isinstance(res, list):
            for r in res:
                reviews_box.insert("end", f"[{r[0]}] {r[2]}  ({r[3]})")
        else:
            reviews_box.insert("end", str(res))

    def add_review_for_selected():
        sel_index = menu_listbox.curselection()
        if not sel_index:
            messagebox.showwarning("No item", "Please select a menu entry first.", parent=(win if is_toplevel else None))
            return
        menudict = menu_listbox.menu_items[sel_index[0]]
        menuid = menudict.get("id")
        text = review_entry.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty", "Please write a review before adding.", parent=(win if is_toplevel else None))
            return
        ok, res = call_backend("ad", menuid, text)
        if not ok:
            messagebox.showerror("Error", f"Could not add review: {res}", parent=(win if is_toplevel else None))
            return
        messagebox.showinfo("Added", "Review added successfully.", parent=(win if is_toplevel else None))
        review_entry.delete("1.0", "end")
        load_reviews_for_menuid(menuid)
    # keep track of which review the user is editing
        current_edit_review = {"id": None}
    current_edit_review = {"id": None}    

    def start_edit_selected_review():
      """
      Load the selected review's text into the review_entry for editing.
      Stores the review_id in current_edit_review['id'].
      """
      sel = reviews_box.curselection()
      if not sel:
        messagebox.showwarning("No selection", "Please select a review to edit.", parent=(win if is_toplevel else None))
        return
      text = reviews_box.get(sel[0])
      import re
    # Pattern: [123] Review text  (2025-10-26 12:05:00)
      m = re.match(r"\s*\[(\d+)\]\s*(.?)\s\(", text)
      if not m:
        # fallback: try more lenient parse (id then rest)
        m2 = re.match(r"\s*\[(\d+)\]\s*(.*)", text)
        if not m2:
            messagebox.showerror("Parse error", "Could not parse review id/text from selected item.", parent=(win if is_toplevel else None))
            return
        rid = int(m2.group(1))
        body = m2.group(2).strip()
      else:
        rid = int(m.group(1))
        body = m.group(2).strip()
      # put text in the entry box for user to edit
      review_entry.delete("1.0", "end")
      review_entry.insert("1.0", body)
      current_edit_review["id"] = rid
      messagebox.showinfo("Edit mode", f"Editing review id {rid}. Make changes and click 'Update Review'.", parent=(win if is_toplevel else None))

    def update_review_from_user():
      """
      Update the review currently loaded for editing (current_edit_review['id']).
      Calls backend upd_review_by_id.
      """
      rid = current_edit_review.get("id")
      if not rid:
        messagebox.showwarning("No review loaded", "Click 'Edit Selected Review' first.", parent=(win if is_toplevel else None))
        return
      new_text = review_entry.get("1.0", "end").strip()
      if not new_text:
        messagebox.showwarning("Empty", "Please enter review text before updating.", parent=(win if is_toplevel else None))
        return
      ok, res = call_backend("upd_review_by_id", rid, new_text)
      if not ok:
        messagebox.showerror("Error", f"Could not update review: {res}", parent=(win if is_toplevel else None))
        return
      if isinstance(res, dict) and res.get("status") == "success":
        messagebox.showinfo("Updated", res.get("message"), parent=(win if is_toplevel else None))
      else:
        messagebox.showinfo("Updated", f"Review id {rid} updated.", parent=(win if is_toplevel else None))
      # clear edit state and refresh reviews for current menu
      current_edit_review["id"] = None
      review_entry.delete("1.0", "end")
      sel_menu = menu_listbox.curselection()
      if sel_menu:
        menudict = menu_listbox.menu_items[sel_menu[0]]
        load_reviews_for_menuid(menudict.get("id"))
      else:
        reviews_box.delete(0, "end")    
        

    def delete_reviews_for_selected():
        sel_index = menu_listbox.curselection()
        if not sel_index:
            messagebox.showwarning("No item", "Select a menu entry first", parent=(win if is_toplevel else None))
            return
        menudict = menu_listbox.menu_items[sel_index[0]]
        menuid = menudict.get("id")
        if not messagebox.askyesno("Confirm", f"Delete ALL reviews for menu id {menuid}?", parent=(win if is_toplevel else None)):
            return
        ok, res = call_backend("del_review", menuid)
        if not ok:
            messagebox.showerror("Error", f"Could not delete: {res}", parent=(win if is_toplevel else None))
            return
        messagebox.showinfo("Deleted", "All reviews deleted for this menu entry.", parent=(win if is_toplevel else None))
        load_reviews_for_menuid(menuid)

    ttk.Button(button_frame_mid, text="Add Review", command=add_review_for_selected).pack(side="left", padx=6)
    ttk.Button(button_frame_mid, text="Edit Selected Review", command=start_edit_selected_review).pack(side="left", padx=6)
    ttk.Button(button_frame_mid, text="Update Review", command=update_review_from_user).pack(side="left", padx=6)

    def on_menu_select(evt):
        sel = menu_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        m = menu_listbox.menu_items[idx]
        menu_text.configure(state="normal")
        menu_text.delete("1.0", "end")
        menu_text.insert("1.0", m.get("item") or "#")
        menu_text.configure(state="disabled")
        load_reviews_for_menuid(m.get("id"))

    menu_listbox.bind("<<ListboxSelect>>", on_menu_select)

    # initial populate
    refresh_menu_for_selection()

    # Close area
    def do_close():
        try:
            win.destroy()
        except Exception:
            pass

    close_frame = ttk.Frame(win, padding=6)
    close_frame.pack(fill="x", side="bottom")
    ttk.Button(close_frame, text="Close (Return to Main)", command=do_close).pack(side="right", padx=6, pady=6)

    win.protocol("WM_DELETE_WINDOW", do_close)

    # If running as Toplevel, do transient/grab; if standalone Tk, just return and caller will run .mainloop()
    if is_toplevel:
        win.transient(parent)
        win.grab_set()
        win.focus_force()
        return win
    else:
        # standalone mode: run until closed
        try:
            win.mainloop()
        except Exception:
            pass
        return None


# -------------------------
# UI builder: Admin window
# also supports Toplevel or standalone Tk modes
# -------------------------
def open_admin_window(parent=None):
    is_toplevel = parent is not None
    if is_toplevel:
        win = tk.Toplevel(parent)
    else:
        win = tk.Tk()

    win.title("Admin — Simple")
    win.geometry("1000x600")

    # tiny helpers
    def ph():
        return "?" if getattr(this_module, "db_type", None) == "sqlite" else "%s"

    def call(fn_name, *args):
        if not hasattr(this_module, fn_name):
            return False, f"Backend missing {fn_name}"
        try:
            fn = getattr(this_module, fn_name)
            return True, fn(*args)
        except TypeError:
            if hasattr(this_module, "cur"):
                try:
                    return True, getattr(this_module, fn_name)(this_module.cur, *args)
                except Exception as e:
                    return False, str(e)
            return False, "TypeError calling " + fn_name
        except Exception as e:
            return False, str(e)

    def exec_sql(sql, params=()):
        if not hasattr(this_module, "cur") or not hasattr(this_module, "conn"):
            return False, "Backend has no cur/conn"
        try:
            this_module.cur.execute(sql, params)
            if sql.strip().lower().startswith("select"):
                return True, this_module.cur.fetchall()
            this_module.conn.commit()
            return True, {"ok": True}
        except Exception as e:
            return False, str(e)

    # Left: menu tree
    left = ttk.Frame(win, padding=6)
    left.pack(side="left", fill="both", expand=True)

    cols = ("id","day","meal","item")
    menu_tree = ttk.Treeview(left, columns=cols, show="headings", height=20)
    for c in cols:
        menu_tree.heading(c, text=c.capitalize())
        menu_tree.column(c, width=100 if c!="item" else 400, anchor="w")
    menu_tree.pack(fill="both", expand=True)

    # Right: form + reviews
    right = ttk.Frame(win, padding=6)
    right.pack(side="left", fill="y")

    ttk.Label(right, text="Menu ID:").pack(anchor="w")
    e_id = ttk.Entry(right); e_id.pack(fill="x", pady=2)

    ttk.Label(right, text="Day:").pack(anchor="w")
    e_day = ttk.Entry(right); e_day.pack(fill="x", pady=2)

    ttk.Label(right, text="Meal:").pack(anchor="w")
    e_meal = ttk.Entry(right); e_meal.pack(fill="x", pady=2)

    ttk.Label(right, text="Item text:").pack(anchor="w")
    e_item = scrolledtext.ScrolledText(right, width=40, height=6); e_item.pack(pady=4)

    btn_frame = ttk.Frame(right); btn_frame.pack(fill="x", pady=4)

    def load_menu():
        menu_tree.delete(*menu_tree.get_children())
        if hasattr(this_module, "get_full_menu"):
            ok,res = call("get_full_menu")
            if not ok:
                messagebox.showerror("Error", res, parent=(win if is_toplevel else None)); return
            rows = res.get("menu", []) if isinstance(res, dict) else []
        else:
            ok,res = exec_sql("SELECT id, day, meal, item FROM menu")
            if not ok:
                messagebox.showerror("Error", res, parent=(win if is_toplevel else None)); return
            rows = res
        for r in rows:
            if isinstance(r, dict):
                menu_tree.insert("", "end", values=(r["id"], r["day"], r["meal"], r["item"]))
            else:
                menu_tree.insert("", "end", values=(r[0], r[1], r[2], r[3]))

    def add_menu_cmd():
        try:
            mid = int(e_id.get().strip())
        except:
            messagebox.showerror("Input", "Menu id must be int", parent=(win if is_toplevel else None)); return
        day = e_day.get().strip(); meal = e_meal.get().strip(); item = e_item.get("1.0","end").strip()
        ok,res = call("add_menu", mid, day, meal, item)
        if not ok:
            ok2,res2 = call("mod_menu", mid, day, meal, item, "")
            if not ok2:
                messagebox.showerror("Error", f"{res}\n{res2}", parent=(win if is_toplevel else None)); return
            messagebox.showinfo("OK", res2.get("message",res2), parent=(win if is_toplevel else None))
        else:
            messagebox.showinfo("OK", res.get("message", res), parent=(win if is_toplevel else None))
        load_menu()

    def update_menu_cmd():
        try:
            mid = int(e_id.get().strip())
        except:
            messagebox.showerror("Input", "Menu id must be int", parent=(win if is_toplevel else None)); return
        for col, val in (("day", e_day.get().strip()), ("meal", e_meal.get().strip()), ("item", e_item.get("1.0","end").strip())):
            ok,res = call("upd_menu", col, val, mid, "")
            if not ok:
                messagebox.showerror("Error updating: "+str(res), parent=(win if is_toplevel else None)); return
        messagebox.showinfo("OK","Updated", parent=(win if is_toplevel else None))
        load_menu()

    def delete_menu_cmd():
        try:
            mid = int(e_id.get().strip())
        except:
            messagebox.showerror("Input", "Menu id must be int", parent=(win if is_toplevel else None)); return
        if not messagebox.askyesno("Confirm","Delete menu id "+str(mid)+"?", parent=(win if is_toplevel else None)): return
        ok,res = call("del_menu", mid, "")
        if not ok:
            messagebox.showerror("Error", res, parent=(win if is_toplevel else None)); return
        messagebox.showinfo("OK", res.get("message", res), parent=(win if is_toplevel else None))
        load_menu()

    ttk.Button(btn_frame, text="Add", command=add_menu_cmd).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Update", command=update_menu_cmd).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Delete", command=delete_menu_cmd).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="Refresh", command=load_menu).pack(side="left", padx=4)

    # Reviews area
    ttk.Separator(right, orient="horizontal").pack(fill="x", pady=6)
    ttk.Label(right, text="Reviews for selected menu id").pack(anchor="w")
    rev_tree = ttk.Treeview(right, columns=("review_id","menu_id","text","created_at"), show="headings", height=10)
    for c,w in (("review_id",60),("menu_id",60),("text",300),("created_at",120)):
        rev_tree.heading(c, text=c)
        rev_tree.column(c, width=w, anchor="w")
    rev_tree.pack(fill="both", expand=False)

    rev_edit = scrolledtext.ScrolledText(right, width=40, height=6); rev_edit.pack(pady=4)
    rev_id_entry = ttk.Entry(right); rev_id_entry.pack(fill="x", pady=2)

    def load_reviews_for_selected():
        sel = menu_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a menu row first", parent=(win if is_toplevel else None)); return
        mid = int(menu_tree.item(sel[0],"values")[0])
        rev_tree.delete(*rev_tree.get_children())
        if hasattr(this_module, "get_reviews"):
            ok,res = call("get_reviews", int(mid))
            if not ok:
                messagebox.showerror("Err", res, parent=(win if is_toplevel else None)); return
            rows = res.get("reviews", []) if isinstance(res, dict) else []
        else:
            ok,res = exec_sql(f"SELECT review_id, menu_id, review_text, created_at FROM reviews WHERE menu_id = {ph()}", (int(mid),))
            if not ok:
                messagebox.showerror("Err", res, parent=(win if is_toplevel else None)); return
            rows = res
        for r in rows:
            if isinstance(r, dict):
                rev_tree.insert("", "end", values=(r["review_id"], r["menu_id"], r["text"], r["created_at"]))
            else:
                rev_tree.insert("", "end", values=(r[0], r[1], r[2], r[3]))

    def on_menu_select(evt):
        sel = menu_tree.selection()
        if not sel: return
        v = menu_tree.item(sel[0],"values")
        e_id.delete(0,"end"); e_id.insert(0, v[0])
        e_day.delete(0,"end"); e_day.insert(0, v[1])
        e_meal.delete(0,"end"); e_meal.insert(0, v[2])
        e_item.delete("1.0","end"); e_item.insert("1.0", v[3])
        load_reviews_for_selected()

    menu_tree.bind("<<TreeviewSelect>>", on_menu_select)

    def on_rev_select(evt):
        sel = rev_tree.selection()
        if not sel: return
        v = rev_tree.item(sel[0],"values")
        rev_id_entry.delete(0,"end"); rev_id_entry.insert(0, v[0])
        rev_edit.delete("1.0","end"); rev_edit.insert("1.0", v[2])

    rev_tree.bind("<<TreeviewSelect>>", on_rev_select)

    def update_review():
        rid = rev_id_entry.get().strip()
        if not rid:
            messagebox.showwarning("Select", "Select a review", parent=(win if is_toplevel else None)); return
        new = rev_edit.get("1.0","end").strip()
        ok,res = exec_sql(f"UPDATE reviews SET review_text = {ph()} WHERE review_id = {ph()}", (new, int(rid)))
        if not ok:
            messagebox.showerror("Err", res, parent=(win if is_toplevel else None)); return
        messagebox.showinfo("OK","Review updated", parent=(win if is_toplevel else None))
        load_reviews_for_selected()

    def delete_review():
        rid = rev_id_entry.get().strip()
        if not rid:
            messagebox.showwarning("Select", "Select a review", parent=(win if is_toplevel else None)); return
        if not messagebox.askyesno("Confirm","Delete review id "+rid+"?", parent=(win if is_toplevel else None)): return
        ok,res = exec_sql(f"DELETE FROM reviews WHERE review_id = {ph()}", (int(rid),))
        if not ok:
            messagebox.showerror("Err", res, parent=(win if is_toplevel else None)); return
        messagebox.showinfo("OK","Deleted", parent=(win if is_toplevel else None))
        load_reviews_for_selected()
    def delete_all_reviews_for_menu():
    # Ensure a menu row is selected
      sel = menu_tree.selection()
      if not sel:
        messagebox.showwarning("Select", "Select a menu row first", parent=(win if is_toplevel else None))
        return
      mid = int(menu_tree.item(sel[0], "values")[0])
      if not messagebox.askyesno("Confirm", f"Delete ALL reviews for menu id {mid}?", parent=(win if is_toplevel else None)):
        return
      # Call backend del_review which deletes reviews for the menu_id
      # If you implemented admin password protection, prompt and pass the password here
      # Example without password:
      ok, res = call("del_review", mid)
      if not ok:
        messagebox.showerror("Error", f"Could not delete reviews: {res}", parent=(win if is_toplevel else None))
        return
      # res may be dict or other; handle gracefully
      if isinstance(res, dict) and res.get("status") == "success":
        messagebox.showinfo("Deleted", res.get("message"), parent=(win if is_toplevel else None))
      else:
        messagebox.showinfo("Deleted", f"All reviews for menu id {mid} deleted.", parent=(win if is_toplevel else None))
      # Refresh review list for the current menu
      load_reviews_for_selected()    

    rbtns = ttk.Frame(right); rbtns.pack(fill="x", pady=4)
    ttk.Button(rbtns, text="Delete ALL Reviews", command=delete_all_reviews_for_menu).pack(side="left", padx=4)
    ttk.Button(rbtns, text="Update Review", command=update_review).pack(side="left", padx=4)
    ttk.Button(rbtns, text="Delete Review", command=delete_review).pack(side="left", padx=4)
    ttk.Button(rbtns, text="Reload Reviews", command=load_reviews_for_selected).pack(side="left", padx=4)

    # initial load
    load_menu()

    # Close area
    def do_close():
        try:
            win.destroy()
        except Exception:
            pass

    close_frame = ttk.Frame(win, padding=6)
    close_frame.pack(fill="x", side="bottom")
    ttk.Button(close_frame, text="Close (Return to Main)", command=do_close).pack(side="right", padx=6, pady=6)

    win.protocol("WM_DELETE_WINDOW", do_close)

    if is_toplevel:
        win.transient(parent)
        win.grab_set()
        win.focus_force()
        return win
    else:
        try:
            win.mainloop()
        except Exception:
            pass
        return None


# -------------------------
# Control loop implementation
# The main control UI is created in a loop; when the user chooses 'User' or 'Admin'
# the control root is destroyed and the corresponding UI is launched as its own Tk()
# Only when 'Quit' is selected does the program break the loop and exit.
# -------------------------
def control_loop():
    choice = None
    while True:
        # create control Tk instance
        root = tk.Tk()
        root.title("Main Control Panel")
        root.geometry("360x200")
        root.resizable(False, False)

        frame = ttk.Frame(root, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Choose Mode:", font=("TkDefaultFont", 12, "bold")).pack(pady=(0,8))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(6,8))

        # store selected option in mutable so button callbacks can set it
        sel = {"option": None}

        def select_user():
            sel["option"] = "user"
            root.destroy()  # stop this mainloop and return control
            
        ADMIN_PASSWORD = "vit123"
        def select_admin():
        # Ask for admin password before opening Admin mode
           pw = simpledialog.askstring("Admin Login", "Enter admin password:", show="*", parent=root)
           if pw == ADMIN_PASSWORD:
              sel["option"] = "admin"
              root.destroy()
           elif pw is None:
            # user pressed Cancel
             return
           else:
              messagebox.showerror("Access Denied", "Incorrect password! Access to Admin mode denied.",parent=root)
        def select_quit():
            if messagebox.askyesno("Quit", "Do you want to quit the application?", parent=root):
                sel["option"] = "quit"
                root.destroy()

        ttk.Button(btn_frame, text="User", width=14, command=select_user).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="Admin", width=14, command=select_admin).pack(side="left", padx=8)
        ttk.Button(frame, text="Quit", width=36, command=select_quit).pack(pady=(6,0))

        # run control UI loop until one of the buttons calls root.destroy()
        try:
            root.mainloop()
        except Exception:
            # if mainloop errors out, try to continue or break cleanly
            try:
                root.destroy()
            except Exception:
                pass

        choice = sel["option"]

        if choice == "user":
            # Launch User UI as standalone Tk() — this call returns when the user window is closed
            try:
                open_user_window(parent=None)
            except Exception as e:
                print("Error opening user UI:", e)
        elif choice == "admin":
            try:
                open_admin_window(parent=None)
            except Exception as e:
                print("Error opening admin UI:", e)
        elif choice == "quit" or choice is None:
            # Cleanup DB connection if present, then exit loop
            try:
                if hasattr(this_module, "conn") and this_module.conn:
                    try:
                        this_module.conn.close()
                    except Exception:
                        pass
            except Exception:
                pass
            break
        # after user/admin window closed, loop restarts and control UI will be recreated

# Run the control loop when executed directly
if __name__ == "__main__":
    control_loop()
