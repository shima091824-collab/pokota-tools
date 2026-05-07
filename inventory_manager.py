#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InventoryManager - ~/inventory.json を直接編集するGUIツール
ダークモード対応版（ttk.Button使用）
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date

INVENTORY_PATH = os.path.expanduser("~/inventory.json")


def load_inventory():
    # スプレッドシートから読み込む
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(
            os.path.expanduser('~/credentials.json'), scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key('1XnGiqlGvIDfTyCOUXecclDJaBm_J6Gyg12mvZuKZFPg')
        ws = sh.worksheet('在庫管理')
        rows = ws.get_all_values()
        if len(rows) <= 1:
            return {}
        data = {}
        for row in rows[1:]:  # 1行目はヘッダーなのでスキップ
            if len(row) < 4 or not row[0]:
                continue
            name = row[0]
            lot = {
                'cost': int(row[1]) if row[1].isdigit() else 0,
                'date': row[2],
                'stock': int(row[3]) if row[3].isdigit() else 0
            }
            if name not in data:
                data[name] = []
            data[name].append(lot)
        # バックアップとしてjsonにも保存
        with open(INVENTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data
    except Exception as e:
        print(f"スプレッドシート読み込みエラー: {e}")
        # 失敗時はjsonから読む（フォールバック）
        if not os.path.exists(INVENTORY_PATH):
            return {}
        with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)


def save_inventory(data):
    with open(INVENTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # スプレッドシートにも同期
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(
            os.path.expanduser('~/credentials.json'), scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key('1XnGiqlGvIDfTyCOUXecclDJaBm_J6Gyg12mvZuKZFPg')
        ws = sh.worksheet('在庫管理')
        ws.clear()
        ws.update(values=[['商品名','仕入れ値','仕入れ日','在庫数']], range_name='A1')
        rows = []
        for name, lots in data.items():
            for lot in lots:
                rows.append([name, lot['cost'], lot['date'], lot.get('stock', '')])
        if rows:
            ws.update(values=rows, range_name='A2')
    except Exception as e:
        print(f"スプレッドシート同期エラー: {e}")

class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("在庫管理ツール - InventoryManager")
        self.geometry("820x580")
        self.resizable(True, True)
        self.configure(bg="#f5f5f5")

        self.inventory = load_inventory()
        self.selected_product = None
        self.selected_lot_index = None

        self._build_ui()
        self._refresh_product_list()

    # ── UI構築 ──────────────────────────────────────────────

    def _build_ui(self):
        # ── 上部タイトル
        title_bar = tk.Frame(self, bg="#2c3e50", height=48)
        title_bar.pack(fill="x")
        tk.Label(title_bar, text="📦 在庫管理ツール", font=("Helvetica", 16, "bold"),
                 bg="#2c3e50", fg="white").pack(side="left", padx=16, pady=8)

        # ── メインエリア（左：商品リスト ／ 右：ロット詳細）
        main = tk.Frame(self, bg="#f5f5f5")
        main.pack(fill="both", expand=True, padx=12, pady=8)

        # 左パネル
        left = tk.LabelFrame(main, text="商品一覧", bg="#f5f5f5",
                             font=("Helvetica", 11, "bold"), padx=6, pady=6)
        left.pack(side="left", fill="y", padx=(0, 8))

        self.product_listbox = tk.Listbox(left, width=22, font=("Helvetica", 12),
                                          selectbackground="#3498db", activestyle="none")
        self.product_listbox.pack(fill="y", expand=True, side="left")
        self.product_listbox.bind("<<ListboxSelect>>", self._on_product_select)

        sb_prod = ttk.Scrollbar(left, orient="vertical",
                                command=self.product_listbox.yview)
        sb_prod.pack(side="right", fill="y")
        self.product_listbox.config(yscrollcommand=sb_prod.set)

        prod_btn = tk.Frame(main, bg="#f5f5f5")
        prod_btn.pack(side="left", fill="y", padx=(0, 8))
        ttk.Button(prod_btn, text="＋ 商品追加",
                   command=self._add_product).pack(pady=(0, 4), fill="x")
        ttk.Button(prod_btn, text="✎ 商品名変更",
                   command=self._rename_product).pack(pady=(0, 4), fill="x")
        ttk.Button(prod_btn, text="✕ 商品削除",
                   command=self._delete_product).pack(fill="x")

        # 右パネル
        right = tk.LabelFrame(main, text="ロット一覧（選択中の商品）", bg="#f5f5f5",
                              font=("Helvetica", 11, "bold"), padx=6, pady=6)
        right.pack(side="left", fill="both", expand=True)

        cols = ("lot", "date", "cost", "stock")
        self.lot_tree = ttk.Treeview(right, columns=cols, show="headings", height=14)
        self.lot_tree.heading("lot",   text="ロット")
        self.lot_tree.heading("date",  text="仕入れ日")
        self.lot_tree.heading("cost",  text="仕入れ単価 (¥)")
        self.lot_tree.heading("stock", text="在庫数")
        self.lot_tree.column("lot",   width=55,  anchor="center")
        self.lot_tree.column("date",  width=110, anchor="center")
        self.lot_tree.column("cost",  width=140, anchor="e")
        self.lot_tree.column("stock", width=100, anchor="e")
        self.lot_tree.pack(fill="both", expand=True, side="left")
        self.lot_tree.bind("<<TreeviewSelect>>", self._on_lot_select)

        sb_lot = ttk.Scrollbar(right, orient="vertical", command=self.lot_tree.yview)
        sb_lot.pack(side="right", fill="y")
        self.lot_tree.config(yscrollcommand=sb_lot.set)

        lot_btn_frame = tk.Frame(self, bg="#f5f5f5")
        lot_btn_frame.pack(fill="x", padx=12, pady=(0, 4))
        ttk.Button(lot_btn_frame, text="＋ ロット追加",
                   command=self._add_lot).pack(side="left", padx=(0, 4))
        ttk.Button(lot_btn_frame, text="✎ ロット編集",
                   command=self._edit_lot).pack(side="left", padx=(0, 4))
        ttk.Button(lot_btn_frame, text="✕ ロット削除",
                   command=self._delete_lot).pack(side="left")

        # ── 保存ボタン
        save_frame = tk.Frame(self, bg="#f5f5f5")
        save_frame.pack(fill="x", padx=12, pady=(4, 10))
        self.status_label = tk.Label(save_frame, text="", bg="#f5f5f5",
                                     font=("Helvetica", 10), fg="#27ae60")
        self.status_label.pack(side="left")
        ttk.Button(save_frame, text="💾  保存する（~/inventory.json を上書き）",
                   command=self._save).pack(side="right")

    # ── 商品リスト操作 ──────────────────────────────────────

    def _refresh_product_list(self):
        self.product_listbox.delete(0, tk.END)
        for name in self.inventory:
            self.product_listbox.insert(tk.END, name)

    def _on_product_select(self, _event=None):
        sel = self.product_listbox.curselection()
        if not sel:
            return
        self.selected_product = self.product_listbox.get(sel[0])
        self.selected_lot_index = None
        self._refresh_lot_tree()

    def _add_product(self):
        name = simpledialog.askstring("商品追加", "新しい商品名を入力してください：",
                                      parent=self)
        if not name:
            return
        name = name.strip()
        if name in self.inventory:
            messagebox.showwarning("重複", f"「{name}」はすでに存在します。")
            return
        self.inventory[name] = []
        self._refresh_product_list()
        self.status_label.config(text=f"「{name}」を追加しました（未保存）")

    def _rename_product(self):
        if not self.selected_product:
            messagebox.showinfo("選択してください", "商品一覧から商品を選択してください。")
            return
        new_name = simpledialog.askstring("商品名変更",
                                          f"「{self.selected_product}」の新しい名前：",
                                          initialvalue=self.selected_product, parent=self)
        if not new_name or new_name.strip() == self.selected_product:
            return
        new_name = new_name.strip()
        if new_name in self.inventory:
            messagebox.showwarning("重複", f"「{new_name}」はすでに存在します。")
            return
        new_inv = {}
        for k, v in self.inventory.items():
            new_inv[new_name if k == self.selected_product else k] = v
        self.inventory = new_inv
        self.selected_product = new_name
        self._refresh_product_list()
        self.status_label.config(text=f"名前を「{new_name}」に変更しました（未保存）")

    def _delete_product(self):
        if not self.selected_product:
            messagebox.showinfo("選択してください", "商品一覧から商品を選択してください。")
            return
        if not messagebox.askyesno("確認", f"「{self.selected_product}」を削除しますか？\n（ロットもすべて削除されます）"):
            return
        del self.inventory[self.selected_product]
        self.selected_product = None
        self._refresh_product_list()
        self._refresh_lot_tree()
        self.status_label.config(text="商品を削除しました（未保存）")

    # ── ロット操作 ──────────────────────────────────────────

    def _refresh_lot_tree(self):
        for row in self.lot_tree.get_children():
            self.lot_tree.delete(row)
        if not self.selected_product:
            return
        lots = self.inventory.get(self.selected_product, [])
        for i, lot in enumerate(lots):
            self.lot_tree.insert("", tk.END, iid=str(i), values=(
                f"ロット{i+1}",
                lot.get("date", ""),
                f"¥{lot.get('cost', 0):,}",
                lot.get("stock", 0),
            ))

    def _on_lot_select(self, _event=None):
        sel = self.lot_tree.selection()
        self.selected_lot_index = int(sel[0]) if sel else None

    def _add_lot(self):
        if not self.selected_product:
            messagebox.showinfo("選択してください", "まず商品を選択してください。")
            return
        dialog = LotDialog(self, title="ロット追加")
        if dialog.result:
            self.inventory[self.selected_product].append(dialog.result)
            self._refresh_lot_tree()
            self.status_label.config(text="ロットを追加しました（未保存）")

    def _edit_lot(self):
        if self.selected_product is None or self.selected_lot_index is None:
            messagebox.showinfo("選択してください", "編集するロットを選択してください。")
            return
        current = self.inventory[self.selected_product][self.selected_lot_index]
        dialog = LotDialog(self, title="ロット編集", initial=current)
        if dialog.result:
            self.inventory[self.selected_product][self.selected_lot_index] = dialog.result
            self._refresh_lot_tree()
            self.status_label.config(text="ロットを編集しました（未保存）")

    def _delete_lot(self):
        if self.selected_product is None or self.selected_lot_index is None:
            messagebox.showinfo("選択してください", "削除するロットを選択してください。")
            return
        if not messagebox.askyesno("確認", f"ロット{self.selected_lot_index+1}を削除しますか？"):
            return
        self.inventory[self.selected_product].pop(self.selected_lot_index)
        self.selected_lot_index = None
        self._refresh_lot_tree()
        self.status_label.config(text="ロットを削除しました（未保存）")

    # ── 保存 ────────────────────────────────────────────────

    def _save(self):
        try:
            save_inventory(self.inventory)
            self.status_label.config(
                text=f"✅ 保存しました → {INVENTORY_PATH}", fg="#27ae60")
        except Exception as e:
            messagebox.showerror("保存エラー", str(e))


# ── ロット入力ダイアログ ────────────────────────────────────────

class LotDialog(tk.Toplevel):
    def __init__(self, parent, title="ロット", initial=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.result = None

        default_date = (initial or {}).get("date", str(date.today()))
        default_cost  = str((initial or {}).get("cost", ""))
        default_stock = str((initial or {}).get("stock", ""))

        pad = {"padx": 10, "pady": 5}

        tk.Label(self, text="仕入れ日（例: 2026-04-13）").grid(row=0, column=0, sticky="w", **pad)
        self.date_var = tk.StringVar(value=default_date)
        tk.Entry(self, textvariable=self.date_var, width=18).grid(row=0, column=1, **pad)

        tk.Label(self, text="仕入れ単価（¥）").grid(row=1, column=0, sticky="w", **pad)
        self.cost_var = tk.StringVar(value=default_cost)
        tk.Entry(self, textvariable=self.cost_var, width=18).grid(row=1, column=1, **pad)

        tk.Label(self, text="在庫数").grid(row=2, column=0, sticky="w", **pad)
        self.stock_var = tk.StringVar(value=default_stock)
        tk.Entry(self, textvariable=self.stock_var, width=18).grid(row=2, column=1, **pad)

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="OK",
                   command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="キャンセル",
                   command=self.destroy).pack(side="left", padx=4)

        self.wait_window()

    def _ok(self):
        try:
            cost  = int(self.cost_var.get().replace("¥", "").replace(",", "").strip())
            stock = int(self.stock_var.get().strip())
            d     = self.date_var.get().strip()
            if len(d) != 10 or d[4] != "-" or d[7] != "-":
                raise ValueError("日付形式が正しくありません")
            self.result = {"date": d, "cost": cost, "stock": stock}
            self.destroy()
        except ValueError as e:
            messagebox.showerror("入力エラー", f"入力内容を確認してください。\n{e}", parent=self)


if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
