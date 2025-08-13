import tkinter as tk
from tkinter import messagebox, ttk
import random, json, time, os, sys
from dataclasses import dataclass
from pathlib import Path
import tkinter.font as tkfont   # 新增导入

# ====== Windows 11 like palette ======
WIN_BG            = "#F3F3F3"
WIN_PANEL         = "#FFFFFF"
WIN_PANEL_ALT     = "#F7F7F7"
WIN_BORDER        = "#D9D9D9"
WIN_ACCENT        = "#2563EB"
WIN_ACCENT_HOVER  = "#1E55C7"
WIN_ACCENT_PRESSED= "#174394"
WIN_TEXT          = "#1F1F1F"
WIN_TEXT_SECOND   = "#5A5A5A"
WIN_HIGHLIGHT_BG  = "#E0EEFF"
WIN_SCROLL_BG     = "#E6E6E6"
WIN_SCROLL_THUMB  = "#C9C9C9"
WIN_SCROLL_THUMB_H= "#B5B5B5"

BASE = Path(os.path.abspath(os.path.dirname(__file__)))
_HISTORY_FILE = BASE / "history.json"
_FAV_FILE     = BASE / "favorites.json"
_LATEST_FILE  = BASE / "latest_draw.json"

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
        return f"{red_str} | {self.blue:02d}"

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

def _remove_ticket_from_json(path, ticket_fmt):
    """从指定 json 文件中删除首个格式匹配的号码(按 Ticket.format)。"""
    data = _load_json(path, [])
    removed = False
    new_list = []
    for item in data:
        if not removed:
            fmt = Ticket(tuple(item["reds"]), item["blue"], item.get("ts", 0)).format()
            if fmt == ticket_fmt:
                removed = True
                continue
        new_list.append(item)
    if removed:
        _save_json(path, new_list)
    return removed

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
        if odd_count is not None and sum(r % 2 for r in reds) != odd_count:
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

# ===== DPI =====
def enable_dpi_awareness():
    if sys.platform.startswith("win"):
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            try:
                windll.user32.SetProcessDPIAware()
            except:
                pass

# ===== Win11 Style (TTK) =====
def apply_win11_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except:
        pass
    style.configure(".", font=("Segoe UI", 10))
    style.configure("TButton",
                    background=WIN_PANEL_ALT,
                    foreground=WIN_TEXT,
                    padding=(14,6),
                    borderwidth=0,
                    focusthickness=0)
    style.map("TButton",
              background=[("active", "#EDEDED"), ("pressed", "#E0E0E0")])
    style.configure("Accent.TButton",
                    background=WIN_ACCENT,
                    foreground="#FFFFFF")
    style.map("Accent.TButton",
              background=[("active", WIN_ACCENT_HOVER),
                          ("pressed", WIN_ACCENT_PRESSED)])
    style.configure("TEntry",
                    fieldbackground=WIN_PANEL_ALT,
                    bordercolor=WIN_BORDER,
                    lightcolor=WIN_ACCENT,
                    darkcolor=WIN_BORDER,
                    padding=4)
    # 滚动条
    style.element_create("Plain.Horizontal.Scrollbar.trough", "from", "clam")
    style.element_create("Plain.Vertical.Scrollbar.trough", "from", "clam")
    style.configure("Vertical.TScrollbar",
                    background=WIN_SCROLL_BG,
                    troughcolor=WIN_SCROLL_BG,
                    bordercolor=WIN_SCROLL_BG,
                    lightcolor=WIN_SCROLL_BG,
                    darkcolor=WIN_SCROLL_BG,
                    arrowsize=14)
    style.map("Vertical.TScrollbar",
              background=[("active", WIN_SCROLL_THUMB_H)],
              troughcolor=[("active", WIN_SCROLL_BG)])
    # 去掉 focus 虚线
    root.option_add("*TButton.highlightThickness", 0)
    root.option_add("*TButton.takeFocus", 0)

# ===== 圆角按钮 (Canvas) =====
class Win11Button(tk.Canvas):
    def __init__(self, master, text, command, accent=False):
        super().__init__(master, bd=0, highlightthickness=0,
                         bg=master["bg"])
        self.command = command
        self.accent = accent
        self._radius = 6
        self._w_pad = 8
        self._h_pad = 4
        self._text = text
        if accent:
            self.colors = {
                "normal": WIN_ACCENT,
                "hover": WIN_ACCENT_HOVER,
                "press": WIN_ACCENT_PRESSED,
                "fg": "#FFFFFF"
            }
        else:
            self.colors = {
                "normal": "#FFFFFF",
                "hover": "#F2F2F2",
                "press": "#E5E5E5",
                "fg": WIN_TEXT
            }
        self._state = "normal"
        self._draw()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw_round_rect(self, x1,y1,x2,y2,r, **kw):
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, style="pieslice", **kw)
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, style="pieslice", **kw)
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style="pieslice", **kw)
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style="pieslice", **kw)
        self.create_rectangle(x1+r, y1, x2-r, y2, **kw)
        self.create_rectangle(x1, y1+r, x2, y2-r, **kw)

    def _draw(self):
        self.delete("all")
        txt_font = ("Segoe UI", 10)
        # 使用 tkfont 而不是 tk.font
        tw = tkfont.Font(font=txt_font).measure(self._text)
        w = tw + self._w_pad*2
        h = 28
        self.config(width=w, height=h)
        color = self.colors[self._state if self._state in ("hover","press") else "normal"]
        self._draw_round_rect(0,0,w,h,self._radius, fill=color, outline=color)
        self.create_text(w/2, h/2, text=self._text, fill=self.colors["fg"], font=txt_font)

    def _on_enter(self, _):
        self._state = "hover"
        self._draw()
    def _on_leave(self, _):
        self._state = "normal"
        self._draw()
    def _on_press(self, _):
        self._state = "press"
        self._draw()
    def _on_release(self, _):
        inside = True
        self._state = "hover"
        self._draw()
        if inside and self.command:
            self.command()

def styled_entry(parent, width=None):
    e = tk.Entry(parent,
                 bg=WIN_PANEL_ALT,
                 fg=WIN_TEXT,
                 insertbackground=WIN_TEXT,
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=WIN_BORDER,
                 highlightcolor=WIN_ACCENT,
                 font=("Consolas", 11))
    if width:
        e.config(width=width)
    return e

class App:
    def __init__(self, root):
        # 调试：确认实际加载的文件与行号
        print("[DEBUG] App.__init__ in file:", __file__)
        print("[DEBUG] Before setting self.root, has attr root?", hasattr(self, "root"))
        self.root = root  # 确保最早赋值
        root.title("双色球工具 (Win11)")
        # 使用改进后的 _center（即使 self.root 未成功赋值也能 fallback）
        root.geometry(self._center(820, 600))
        root.configure(bg=WIN_BG)
        root.update_idletasks()

        apply_win11_style(root)
        self._build_ui()
        self.refresh_history()
        self.current_mode = "history"  # history | favorites | compare | generated

    def _center(self, w, h):
        """
        计算窗口居中位置。
        若异常（比如 root 尚未挂到实例）则回退使用 tk._default_root。
        """
        r = getattr(self, "root", None)
        if r is None:
            from tkinter import _default_root
            r = _default_root
            print("[DEBUG] _center: self.root 不存在，使用 _default_root =", r)
        if r is None:
            # 仍拿不到，返回基础几何
            return f"{w}x{h}+100+100"
        try:
            sw = r.winfo_screenwidth()
            sh = r.winfo_screenheight()
        except Exception as e:
            print("[DEBUG] _center: 获取屏幕尺寸失败:", e)
            return f"{w}x{h}+120+120"
        x = (sw - w) // 2
        y = (sh - h) // 2 - 20
        return f"{w}x{h}+{x}+{y}"

    def _panel(self, parent, **kw):
        frame = tk.Frame(parent, bg=kw.get("bg", WIN_PANEL), bd=0, highlightthickness=1,
                         highlightbackground=WIN_BORDER)
        return frame

    def _build_ui(self):
        toolbar = self._panel(self.root)
        toolbar.pack(fill="x", padx=18, pady=(16,10))
        toolbar.configure(pady=8)

        def add_btn(text, cmd, accent=False):
            b = Win11Button(toolbar, text, cmd, accent=accent)
            b.pack(side="left", padx=6)

        add_btn("随机生成", self.gen_random, accent=True)
        add_btn("条件生成", self.open_cond_win)
        add_btn("收藏选中", self.collect_selected)
        add_btn("删除选中", self.delete_selected)
        add_btn("查看收藏", self.show_favorites)
        add_btn("更新开奖号码", self.update_draw)
        add_btn("对照收藏", self.compare_favs)

        main = self._panel(self.root)
        main.pack(fill="both", expand=True, padx=18, pady=4)

        list_frame = tk.Frame(main, bg=WIN_PANEL)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.listbox = tk.Listbox(
            list_frame,
            height=18,
            font=("Consolas", 13),
            bg=WIN_PANEL_ALT,
            fg=WIN_TEXT,
            selectbackground=WIN_HIGHLIGHT_BG,
            selectforeground=WIN_TEXT,
            bd=0,
            relief="flat",
            activestyle="none",
            highlightthickness=1,
            highlightbackground=WIN_BORDER
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        # 自定义滚动条包一层使色块更自然
        sb_style = ttk.Style()
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        sb.pack(side="right", fill="y", padx=(4,0))
        self.listbox.config(yscrollcommand=sb.set)

        status_panel = tk.Frame(self.root, bg=WIN_BG)
        status_panel.pack(fill="x", padx=18, pady=(4,14))
        self.status = tk.StringVar()
        status_lbl = tk.Label(status_panel, textvariable=self.status,
                              anchor="w", bg=WIN_PANEL, fg=WIN_TEXT_SECOND,
                              bd=0, padx=12, pady=6,
                              font=("Segoe UI", 9),
                              highlightthickness=1,
                              highlightbackground=WIN_BORDER)
        status_lbl.pack(fill="x")

    def set_status(self, msg):
        self.status.set(msg)

    def refresh_history(self):
        self.listbox.delete(0, tk.END)
        for t in list_history(50):
            self.listbox.insert(tk.END, t.format())
        self.set_status("显示最近 50 条历史")
        self.current_mode = "history"

    def gen_random(self):
        tickets = generate_random_tickets(5)
        self.listbox.delete(0, tk.END)
        for t in tickets:
            self.listbox.insert(tk.END, t.format())
        self.set_status("生成 5 组随机号码")
        self.current_mode = "generated"

    def open_cond_win(self):
        win = tk.Toplevel(self.root)
        win.title("条件生成")
        win.configure(bg=WIN_BG)
        win.geometry("+%d+%d" % (self.root.winfo_rootx()+60, self.root.winfo_rooty()+80))

        entries = {}
        def add_row(label, key, placeholder=""):
            row = tk.Frame(win, bg=WIN_BG)
            row.pack(fill="x", pady=6, padx=16)
            tk.Label(row, text=label, width=14, anchor="w",
                     bg=WIN_BG, fg=WIN_TEXT, font=("Segoe UI",10)).pack(side="left")
            e = styled_entry(row)
            e.pack(side="left", fill="x", expand=True)
            if placeholder:
                e.insert(0, placeholder)
            entries[key] = e

        add_row("组数", "count", "5")
        add_row("奇数个数", "odd", "")
        add_row("和值范围", "sum_range", "80-120")
        add_row("排除红球", "ex_reds", "1 2")
        add_row("排除蓝球", "ex_blues", "3 6")
        add_row("区间分配", "ranges", "1-20:3,21-33:3")

        btn_bar = tk.Frame(win, bg=WIN_BG)
        btn_bar.pack(pady=10)
        Win11Button(btn_bar, "生成", lambda: self._do_cond(entries, win), accent=True).pack(side="left", padx=4)
        Win11Button(btn_bar, "取消", win.destroy).pack(side="left", padx=4)

    def _do_cond(self, entries, win):
        def get_int(v, default=None):
            v = v.strip()
            return int(v) if v.isdigit() else default
        try:
            count = get_int(entries["count"].get(), 1)
        except:
            count = 1
        odd_txt = entries["odd"].get().strip()
        odd = get_int(odd_txt, None)
        sum_rng = None
        sr = entries["sum_range"].get().strip()
        if "-" in sr:
            try:
                a,b = map(int, sr.split("-"))
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
        self.current_mode = "generated"

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
        self.current_mode = "favorites"

    def update_draw(self):
        win = tk.Toplevel(self.root)
        win.title("更新开奖号码")
        win.configure(bg=WIN_BG)
        def lab(txt):
            return tk.Label(win, text=txt, bg=WIN_BG, fg=WIN_TEXT, font=("Segoe UI",10))
        lab("红球(6个空格分隔)").pack(pady=(12,4))
        red_entry = styled_entry(win, width=40)
        red_entry.pack(padx=16)
        lab("蓝球").pack(pady=(12,4))
        blue_entry = styled_entry(win, width=10)
        blue_entry.pack(padx=16)
        btn_bar = tk.Frame(win, bg=WIN_BG)
        btn_bar.pack(pady=14)
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
        Win11Button(btn_bar, "保存", do_update, accent=True).pack(side="left", padx=4)
        Win11Button(btn_bar, "取消", win.destroy).pack(side="left", padx=4)

    def compare_favs(self):
        win_ticket = load_latest_draw()
        if not win_ticket:
            messagebox.showinfo("提示","暂无最新开奖号码")
            return
        favs = list_favorites()
        self.listbox.delete(0, tk.END)
        self.listbox.insert(tk.END, "最新: " + win_ticket.format())
        for f in favs:
            st = self.new_method(win_ticket, f)
            self.listbox.insert(tk.END, f"{f.format()}  ->  红:{st['red_hits']}  蓝:{st['blue_hit']}")
        self.set_status("对照完成")
        self.current_mode = "compare"

    def new_method(self, win_ticket, f):
        st = compare_ticket(win_ticket, f)
        return st

    def delete_selected(self):
        idxs = self.listbox.curselection()
        if not idxs:
            messagebox.showinfo("提示", "先选择一行")
            return
        line = self.listbox.get(idxs[0]).strip()
        if line.startswith("最新:"):
            messagebox.showinfo("提示", "该行不可删除")
            return
        # 提取纯号码部分（去掉比较视图后缀）
        if "->" in line:
            line = line.split("->", 1)[0].strip()
        # 简单校验格式
        if "|" not in line:
            messagebox.showerror("错误", "无法解析号码")
            return
        ticket_fmt = line  # 与 Ticket.format() 输出一致
        removed = False
        if self.current_mode in ("favorites", "compare"):
            removed = _remove_ticket_from_json(_FAV_FILE, ticket_fmt)
            if removed:
                if self.current_mode == "compare":
                    self.compare_favs()
                else:
                    self.show_favorites()
        elif self.current_mode == "history":
            removed = _remove_ticket_from_json(_HISTORY_FILE, ticket_fmt)
            if removed:
                self.refresh_history()
        else:
            # generated 视图只是临时显示，直接从列表移除
            self.listbox.delete(idxs[0])
            self.set_status("已从临时列表移除")
            return

        if removed:
            self.set_status("已删除: " + ticket_fmt)
        else:
            self.set_status("未找到匹配记录 (可能已删除)")

def main():
    enable_dpi_awareness()
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.15)
    except:
        pass
    App(root)
    root.minsize(760, 540)
    root.mainloop()

if __name__ == "__main__":
    main()
