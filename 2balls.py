import tkinter as tk
from tkinter import messagebox
import random, json, time, os
from dataclasses import dataclass
from pathlib import Path

# 数据文件路径
_BASE = Path(os.path.abspath(os.path.dirname(__file__)))
_HISTORY_FILE = _BASE / "history.json"
_FAV_FILE = _BASE / "favorites.json"
_LATEST_FILE = _BASE / "latest_draw.json"

def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@dataclass
class Ticket:
    reds: tuple
    blue: int
    ts: float = 0.0
    def format(self):
        red_str = " ".join(f"{r:02d}" for r in self.reds)
        return f"{red_str}|{self.blue:02d}"

def _dict_from_ticket(t: Ticket):
    return {"reds": list(t.reds), "blue": t.blue, "ts": t.ts}

def _ticket_from_dict(d):
    return Ticket(tuple(d["reds"]), d["blue"], d.get("ts", 0.0))

def list_history(limit=50):
    data = _load_json(_HISTORY_FILE, [])
    tickets = [_ticket_from_dict(x) for x in data]
    return tickets[-limit:][::-1]

def _append_history(tickets):
    data = _load_json(_HISTORY_FILE, [])
    data.extend(_dict_from_ticket(t) for t in tickets)
    _save_json(_HISTORY_FILE, data)

def generate_random_tickets(count=1):
    res = []
    for _ in range(count):
        reds = sorted(random.sample(range(1,34), 6))
        blue = random.randint(1,16)
        res.append(Ticket(tuple(reds), blue, time.time()))
    _append_history(res)
    return res

def generate_with_conditions(count=1, red_ranges=None, odd_count=None, sum_range=None,
                             exclude_reds=None, exclude_blues=None):
    exclude_reds = exclude_reds or set()
    exclude_blues = exclude_blues or set()
    results = []
    attempts = 0
    while len(results) < count and attempts < 10000:
        attempts += 1
        # 处理区间分配
        if red_ranges:
            reds = []
            for a,b,k in red_ranges:
                pool = [x for x in range(a,b+1) if x not in reds and x not in exclude_reds]
                if len(pool) < k:
                    reds = None
                    break
                reds.extend(random.sample(pool, k))
            if reds is None or len(reds)!=6:
                continue
            reds = sorted(reds)
        else:
            pool = [x for x in range(1,34) if x not in exclude_reds]
            if len(pool) < 6:
                break
            reds = sorted(random.sample(pool,6))
        if odd_count is not None:
            if sum(r % 2 for r in reds) != odd_count:
                continue
        if sum_range is not None:
            s = sum(reds)
            if not (sum_range[0] <= s <= sum_range[1]):
                continue
        blue_pool = [x for x in range(1,17) if x not in exclude_blues]
        if not blue_pool:
            break
        blue = random.choice(blue_pool)
        t = Ticket(tuple(reds), blue, time.time())
        # 去重
        if any(existing.reds == t.reds and existing.blue == t.blue for existing in results):
            continue
        results.append(t)
    if results:
        _append_history(results)
    return results

def save_favorite(ticket: Ticket):
    data = _load_json(_FAV_FILE, [])
    key = ticket.format()
    if key not in [Ticket(tuple(x["reds"]), x["blue"]).format() for x in data]:
        data.append(_dict_from_ticket(ticket))
        _save_json(_FAV_FILE, data)

def list_favorites():
    data = _load_json(_FAV_FILE, [])
    return [_ticket_from_dict(x) for x in data]

def update_latest_draw(pair):
    reds, blue = pair
    reds = sorted(reds)
    if len(reds) != 6:
        return None
    t = Ticket(tuple(reds), blue, time.time())
    _save_json(_LATEST_FILE, _dict_from_ticket(t))
    return t

def load_latest_draw():
    data = _load_json(_LATEST_FILE, None)
    if not data:
        return None
    return _ticket_from_dict(data)

def compare_ticket(win: Ticket, other: Ticket):
    red_hits = len(set(win.reds) & set(other.reds))
    blue_hit = 1 if win.blue == other.blue else 0
    return {"red_hits": red_hits, "blue_hit": blue_hit}

class App:
    def __init__(self, root):
        root.title("双色球工具")
        self.root = root

        frm_top = tk.Frame(root)
        frm_top.pack(fill="x", padx=8, pady=4)

        tk.Button(frm_top, text="随机生成", command=self.gen_random).pack(side="left", padx=4)
        tk.Button(frm_top, text="条件生成", command=self.open_cond_win).pack(side="left", padx=4)
        tk.Button(frm_top, text="收藏选中", command=self.collect_selected).pack(side="left", padx=4)
        tk.Button(frm_top, text="查看收藏", command=self.show_favorites).pack(side="left", padx=4)
        tk.Button(frm_top, text="更新开奖号码", command=self.update_draw).pack(side="left", padx=4)
        tk.Button(frm_top, text="对照收藏", command=self.compare_favs).pack(side="left", padx=4)

        self.listbox = tk.Listbox(root, height=18, font=("Consolas", 12))
        self.listbox.pack(fill="both", expand=True, padx=8, pady=4)

        self.status = tk.StringVar()
        tk.Label(root, textvariable=self.status, anchor="w").pack(fill="x", padx=8, pady=2)

        self.refresh_history()

    def set_status(self, msg):
        self.status.set(msg)

    def refresh_history(self):
        self.listbox.delete(0, tk.END)
        for t in list_history(50):
            self.listbox.insert(tk.END, t.format())
        self.set_status("显示最近 50 条历史")

    def gen_random(self):
        tickets = generate_random_tickets(5)
        self.listbox.delete(0, tk.END)
        for t in tickets:
            self.listbox.insert(tk.END, t.format())
        self.set_status("生成 5 组随机号码")

    def open_cond_win(self):
        win = tk.Toplevel(self.root)
        win.title("条件生成")
        entries = {}

        def add_row(label, key):
            row = tk.Frame(win)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, width=14, anchor="w").pack(side="left")
            e = tk.Entry(row)
            e.pack(side="left", fill="x", expand=True)
            entries[key] = e

        add_row("组数", "count")
        add_row("奇数个数", "odd")
        add_row("和值范围 80-120", "sum_range")
        add_row("排除红球 1 2", "ex_reds")
        add_row("排除蓝球 3 6", "ex_blues")
        add_row("区间 1-20:3,21-33:3", "ranges")

        def do_gen():
            try:
                count = int(entries["count"].get() or 1)
            except:
                count = 1
            odd_txt = entries["odd"].get().strip()
            odd = int(odd_txt) if odd_txt.isdigit() else None
            sum_rng = None
            sr = entries["sum_range"].get().strip()
            if "-" in sr:
                try:
                    a, b = map(int, sr.split("-"))
                    sum_rng = (min(a,b), max(a,b))
                except:
                    pass
            ex_reds = {int(x) for x in entries["ex_reds"].get().split() if x.isdigit()}
            ex_blues = {int(x) for x in entries["ex_blues"].get().split() if x.isdigit()}
            rr_txt = entries["ranges"].get().strip()
            red_ranges = None
            if rr_txt:
                try:
                    red_ranges=[]
                    for seg in rr_txt.split(","):
                        rg,k = seg.split(":")
                        a,b = rg.split("-")
                        red_ranges.append((int(a), int(b), int(k)))
                    if sum(x[2] for x in red_ranges)!=6:
                        red_ranges=None
                except:
                    red_ranges=None
            tickets = generate_with_conditions(
                count=count,
                red_ranges=red_ranges,
                odd_count=odd,
                sum_range=sum_rng,
                exclude_reds=ex_reds,
                exclude_blues=ex_blues
            )
            self.listbox.delete(0, tk.END)
            for t in tickets:
                self.listbox.insert(tk.END, t.format())
            self.set_status(f"条件生成 {len(tickets)} 组")
            win.destroy()

        tk.Button(win, text="生成", command=do_gen).pack(pady=6)

    def collect_selected(self):
        idxs = self.listbox.curselection()
        if not idxs:
            messagebox.showinfo("提示","先选择一行")
            return
        line = self.listbox.get(idxs[0])
        if "|" not in line:
            messagebox.showerror("错误","格式不正确")
            return
        parts = line.split("|")
        reds = [int(x) for x in parts[0].split()]
        blue = int(parts[1])
        t = Ticket(tuple(reds), blue, time.time())
        save_favorite(t)
        self.set_status("已收藏")
        messagebox.showinfo("提示","收藏成功")

    def show_favorites(self):
        favs = list_favorites()
        self.listbox.delete(0, tk.END)
        for f in favs:
            self.listbox.insert(tk.END, f.format())
        self.set_status(f"收藏 {len(favs)} 条")

    def update_draw(self):
        win = tk.Toplevel(self.root)
        win.title("更新开奖号码")
        tk.Label(win, text="红球(6个空格分隔)").pack()
        red_entry = tk.Entry(win, width=40)
        red_entry.pack()
        tk.Label(win, text="蓝球").pack()
        blue_entry = tk.Entry(win, width=10)
        blue_entry.pack()

        def do_update():
            reds = red_entry.get().split()
            blue = blue_entry.get().strip()
            if len(reds)!=6 or not all(r.isdigit() for r in reds) or not blue.isdigit():
                messagebox.showerror("错误","格式不正确")
                return
            t = update_latest_draw((list(map(int, reds)), int(blue)))
            if t:
                self.set_status("已更新开奖号码")
                messagebox.showinfo("成功", t.format())
                win.destroy()
        tk.Button(win, text="保存", command=do_update).pack(pady=6)

    def compare_favs(self):
        win_ticket = load_latest_draw()
        if not win_ticket:
            messagebox.showinfo("提示","暂无最新开奖号码")
            return
        favs = list_favorites()
        self.listbox.delete(0, tk.END)
        self.listbox.insert(tk.END, "最新: " + win_ticket.format())
        for f in favs:
            st = compare_ticket(win_ticket, f)
            self.listbox.insert(tk.END, f"{f.format()} -> 红:{st['red_hits']} 蓝:{st['blue_hit']}")
        self.set_status("对照完成")

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
