import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

TOKEN = re.compile(r'//[^\n]*|/\*.*?\*/|#[^\n]*|\$?@?"(?:\\.|""|[^"\\])*"'
                   r"|'(?:\\.|[^'\\])*'|@?\w+|=>|[=!<>]=|.", re.S)
KW = r"\b(?:if|else|for|foreach|while|do|switch|case|default)\b"


def tokenize(src):
    toks, lines, line = [], [], 1
    for m in TOKEN.finditer(src):
        t = m.group()
        if not t.isspace() and t[:2] not in ("//", "/*") and t[0] != "#":
            toks.append(t); lines.append(line)
        line += t.count("\n")
    return toks, lines


class Gilb:

    def __init__(self, loops_nest=True):
        self.nest, self.cl, self.cli, self.n, self.i = loops_nest, 0, 0, 0, 0

    def run(self, src):
        self.t, self.ln = tokenize(src)
        while self.peek():
            if self.peek() == "}": self.fail("лишняя «}»")
            self.stmt(0, False)
        return self.cl, (self.cl / self.n if self.n else 0.0), self.cli, self.n

    def peek(self, k=0):
        return self.t[self.i + k] if self.i + k < len(self.t) else ""

    def fail(self, msg):
        line = self.ln[min(self.i, len(self.ln) - 1)] if self.ln else 1
        raise SyntaxError(f"строка {line}: {msg}")

    def skip(self, o, c):
        if self.peek() != o: self.fail(f"ожидалась «{o}»")
        d = 0
        while True:
            t = self.peek()
            if not t: self.fail(f"не закрыта «{o}»")
            d += (t == o) - (t == c)
            self.i += 1
            if d == 0: return

    def block(self, d, code):
        while self.peek() != "}":
            if not self.peek(): self.fail("не закрыта «{»")
            self.stmt(d, code)
        self.i += 1

    def loop(self, d):
        self.cl += 1
        if self.nest: self.cli = max(self.cli, d); d += 1
        self.stmt(d, True)

    def stmt(self, d, code):
        t = self.peek()
        if t == "{": self.i += 1; self.block(d, code)
        elif t == ";": self.i += 1
        elif t in ("catch", "finally"):
            self.i += 1
            if self.peek() == "(": self.skip("(", ")")
            if self.peek() == "when": self.i += 1; self.skip("(", ")")
            self.stmt(d, code)
        elif t == "if":
            self.n += 1; self.cl += 1; self.cli = max(self.cli, d)
            self.i += 1; self.skip("(", ")")
            self.stmt(d + 1, True)
            if self.peek() == "else":          # else if = if внутри else
                self.i += 1; self.stmt(d + 1, True)
        elif t in ("for", "foreach", "while"):
            self.n += 1; self.i += 1; self.skip("(", ")"); self.loop(d)
        elif t == "do":
            self.n += 1; self.i += 1; self.loop(d)
            if self.peek() != "while": self.fail("после тела do ожидалось while")
            self.i += 1; self.skip("(", ")")
        elif t == "switch" and self.peek(1) == "(":
            self.n += 1; self.i += 1; self.skip("(", ")"); self.switch(d)
        else: self.simple(d, code)

    def simple(self, d, code):
        head, p, eq = [], 0, False
        while True:
            t = self.peek()
            if not t or (t == "}" and code): self.fail("ожидалась «;»")
            if t == "}": return                # конец enum и т.п.
            p += (t == "(") - (t == ")")
            if p == 0 and t == ";":
                self.i += 1; self.n += code; return
            if t == "{":
                if p or eq or "new" in head:   # инициализатор или лямбда
                    self.skip("{", "}"); continue
                break
            eq = eq or (p == 0 and t in ("=", "=>"))
            head.append(t); self.i += 1
        self.i += 1
        self.n += code and head[0] in ("try", "using", "lock", "checked",
                                        "unchecked", "unsafe", "fixed")
        self.block(d, code or "(" in head
                   or head[-1] in ("get", "set", "init", "add", "remove"))

    def switch(self, d):
        if self.peek() != "{": self.fail("ожидалась «{» после switch")
        kinds, depth, prev, j = [], 0, "", self.i
        while True:
            if j >= len(self.t): self.fail("не закрыта «{» у switch")
            t = self.t[j]
            depth += (t == "{") - (t == "}")
            if depth == 0: break
            nxt = self.t[j + 1] if j + 1 < len(self.t) else ""
            if depth == 1 and (t == "case" or t == "default" and nxt == ":"):
                if prev == ":": kinds[-1] |= t == "default"
                else: kinds.append(t == "default")
            prev, j = t, j + 1
        real = kinds.count(False)
        total = real + any(kinds)
        br = total >= 2
        if br:
            self.cl += total - 1
            self.cli = max(self.cli, d + total - 2)
        lab = lambda: self.peek() == "case" or (self.peek() == "default"
                                                and self.peek(1) == ":")
        self.i += 1
        k = 0
        while self.peek() != "}":
            if not self.peek(): self.fail("не закрыта «{» у switch")
            dflt = False
            while lab():
                dflt |= self.peek() == "default"
                while self.peek() != ":":
                    if not self.peek(): self.fail("в метке case ожидалось «:»")
                    self.i += 1
                self.i += 1
            dd = d + (real if dflt else k + 1) if br else d
            k += not dflt
            while self.peek() and self.peek() != "}" and not lab():
                self.stmt(dd, True)
        self.i += 1


# ============================== интерфейс ==============================
BG, PANEL, FG, MUTED = "#15161e", "#1f2130", "#c0caf5", "#7a82a8"
ACCENT, GOLD, GREEN, PINK = "#7aa2f7", "#e0af68", "#9ece6a", "#f7768e"
DEMO = '''class Demo {
    static int Calc(int x, int[] a) {
        int y;
        if (x < 0) y = 0;
        else if (x == 0) y = 1;
        else y = 2;
        for (int i = 0; i < a.Length; i++)
            if (a[i] > 0) y += a[i];
        while (x > 0) x--;
        switch (y) {
            case 1: y = 10; break;
            case 2: y = 20; break;
            default: y = 0; break;
        }
        return y;
    }
}
'''


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gilb Metrics · C#")
        self.geometry("1000x620")
        self.configure(bg=BG)
        side = tk.Frame(self, bg=BG, width=280)
        side.pack(side="right", fill="y", padx=14, pady=14)
        side.pack_propagate(False)
        tk.Label(side, text="МЕТРИКА ДЖИЛБА", bg=BG, fg=FG,
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(0, 10))
        for text, cmd, bg, fg in (("▶  Рассчитать", self.calc, ACCENT, BG),
                                  ("📂  Открыть .cs", self.open, PANEL, FG)):
            tk.Button(side, text=text, command=cmd, bg=bg, fg=fg, bd=0, pady=9,
                      relief="flat", cursor="hand2",
                      font=("Segoe UI", 10, "bold")).pack(fill="x", pady=4)
        self.nest = tk.BooleanVar(value=True)
        tk.Checkbutton(side, text="Циклы увеличивают вложенность (CLI)",
                       variable=self.nest, bg=BG, fg=MUTED, selectcolor=PANEL,
                       activebackground=BG, activeforeground=FG,
                       wraplength=260, justify="left").pack(anchor="w", pady=8)
        self.out = {}
        for key, title, color in (("CL", "CL · абсолютная сложность", GOLD),
                                  ("cl", "cl · относительная сложность", GREEN),
                                  ("CLI", "CLI · макс. вложенность", PINK),
                                  ("N", "всего операторов", ACCENT)):
            card = tk.Frame(side, bg=PANEL)
            card.pack(fill="x", pady=4)
            tk.Frame(card, bg=color, width=4).pack(side="left", fill="y")
            box = tk.Frame(card, bg=PANEL)
            box.pack(side="left", padx=12, pady=6)
            self.out[key] = tk.StringVar(value="—")
            tk.Label(box, text=title, bg=PANEL, fg=MUTED).pack(anchor="w")
            tk.Label(box, textvariable=self.out[key], bg=PANEL, fg=color,
                     font=("Segoe UI", 22, "bold")).pack(anchor="w")
        self.text = scrolledtext.ScrolledText(
            self, bg="#1a1b26", fg=FG, insertbackground=FG, bd=0, padx=10,
            pady=8, font=("Consolas", 12), wrap="none", undo=True)
        self.text.pack(side="left", fill="both", expand=True, padx=14, pady=14)
        self.text.tag_configure("kw", foreground="#bb9af7")
        self.text.bind("<<Modified>>", self.paint)
        self.text.insert("1.0", DEMO)

    def paint(self, _=None):                   # подсветка ключевых слов
        if not self.text.edit_modified(): return
        self.text.edit_modified(False)
        self.text.tag_remove("kw", "1.0", "end")
        for m in re.finditer(KW, self.text.get("1.0", "end-1c")):
            self.text.tag_add("kw", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    def open(self):
        path = filedialog.askopenfilename(filetypes=[("C#", "*.cs"), ("Все", "*.*")])
        if not path: return
        try:
            try: content = open(path, encoding="utf-8-sig").read()
            except UnicodeDecodeError: content = open(path, encoding="cp1251").read()
        except OSError as e:
            return messagebox.showerror("Ошибка чтения файла", str(e))
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.title(f"Gilb Metrics · {path}")

    def calc(self):
        try: cl, rel, cli, n = Gilb(self.nest.get()).run(self.text.get("1.0", "end"))
        except SyntaxError as e:
            return messagebox.showerror("Ошибка разбора", str(e))
        for key, val in zip(("CL", "cl", "CLI", "N"), (cl, f"{rel:.3f}", cli, n)):
            self.out[key].set(val)


if __name__ == "__main__":
    App().mainloop()