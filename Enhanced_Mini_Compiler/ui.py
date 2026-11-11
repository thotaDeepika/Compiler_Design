import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lexer import tokenize
from parser import Parser
from semantic import SemanticAnalyzer
from tac import TACGenerator, format_tac
from optimizer import optimize
from interpreter import execute


SAMPLE_PROGRAMS = {
    "1. Basic Arithmetic": """// Example 1: Basic arithmetic & constant folding
int a = 5;
int b = 10;
int c = a + b;
print(c);
""",
    "2. Optimization Showcase": """// Example 2: Demonstrates CF, CSE, Strength Reduction & DCE
int x = 4;
int y = 8;
int a = x * 8;
int b = x * 8;
int c = 10 + 20;
int unused = 99;
print(a + b + c);
""",
    "3. String Operations": """// Example 3: String types and concatenation
string greeting = "Hello";
string name = "Compiler";
print(greeting + " " + name);
""",
    "4. Runtime Input & Strength Reduction": """// Example 4: Runtime read, CSE and strength reduction (x*8 -> x<<3)
int x;
read(x);
int a = x * 8;
int b = x * 8;
int c = a + b;
print(c);
"""
}


def ast_to_tree_str(node, indent=""):
    """Format AST nodes into an indented visual hierarchy."""
    if node is None:
        return f"{indent}(None)\n"
    name = type(node).__name__
    
    if name == "Program":
        res = "Program\n"
        for i, stmt in enumerate(node.statements):
            is_last = (i == len(node.statements) - 1)
            branch = "└── " if is_last else "├── "
            next_indent = indent + ("    " if is_last else "│   ")
            res += f"{indent}{branch}{ast_to_tree_str(stmt, next_indent).lstrip()}"
        return res
    elif name == "Declaration":
        init_str = f" = ...\n" if node.initializer else "\n"
        res = f"Declaration: {node.type_name} {node.name}{init_str}"
        if node.initializer:
            res += f"{indent}└── Init: {ast_to_tree_str(node.initializer, indent + '    ').lstrip()}"
        return res
    elif name == "Assignment":
        res = f"Assignment: {node.name} =\n"
        res += f"{indent}└── Expr: {ast_to_tree_str(node.expression, indent + '    ').lstrip()}"
        return res
    elif name == "Print":
        res = f"Print\n"
        res += f"{indent}└── Expr: {ast_to_tree_str(node.expression, indent + '    ').lstrip()}"
        return res
    elif name == "Read":
        return f"Read: {node.name}\n"
    elif name == "Binary":
        res = f"Binary: '{node.operator}'\n"
        res += f"{indent}├── Left:  {ast_to_tree_str(node.left, indent + '│   ').lstrip()}"
        res += f"{indent}└── Right: {ast_to_tree_str(node.right, indent + '    ').lstrip()}"
        return res
    elif name == "Unary":
        res = f"Unary: '{node.operator}'\n"
        res += f"{indent}└── Operand: {ast_to_tree_str(node.operand, indent + '    ').lstrip()}"
        return res
    elif name == "Number":
        return f"Number({node.value})\n"
    elif name == "String":
        return f"String({repr(node.value)})\n"
    elif name == "Variable":
        return f"Variable({node.name})\n"
    return f"{indent}{repr(node)}\n"


class CompilerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Mini Compiler - Visual Studio")
        self.root.geometry("1180x760")
        self.root.minsize(960, 640)

        # Apply a clean theme
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except:
            pass

        self.setup_ui()

    def setup_ui(self):
        # Top toolbar
        toolbar = ttk.Frame(self.root, padding=6)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(toolbar, text="Sample Programs:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(4, 6))

        self.sample_var = tk.StringVar(value="1. Basic Arithmetic")
        sample_cb = ttk.Combobox(
            toolbar, textvariable=self.sample_var, values=list(SAMPLE_PROGRAMS.keys()),
            state="readonly", width=34
        )
        sample_cb.pack(side=tk.LEFT, padx=4)
        sample_cb.bind("<<ComboboxSelected>>", self.load_sample)

        btn_load = ttk.Button(toolbar, text="Load", command=self.load_sample)
        btn_load.pack(side=tk.LEFT, padx=4)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        btn_run = tk.Button(
            toolbar, text="▶ Compile & Run", bg="#2563EB", fg="white",
            font=("Segoe UI", 10, "bold"), activebackground="#1D4ED8",
            activeforeground="white", relief=tk.FLAT, padx=14, pady=3,
            command=self.compile_and_run
        )
        btn_run.pack(side=tk.LEFT, padx=6)

        btn_clear = ttk.Button(toolbar, text="Clear", command=self.clear_all)
        btn_clear.pack(side=tk.LEFT, padx=4)

        # Simulation input entry
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text="Runtime read() input:").pack(side=tk.LEFT, padx=(4, 2))
        self.input_entry = ttk.Entry(toolbar, width=8)
        self.input_entry.insert(0, "3")
        self.input_entry.pack(side=tk.LEFT, padx=4)

        # Main Split Panes (Left: Editor, Right: Compiler Pipeline Notebook)
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        # Left: Source Editor Frame
        left_frame = ttk.LabelFrame(paned, text=" Source Code (.mc) ", padding=6)
        paned.add(left_frame, weight=1)

        self.editor = tk.Text(
            left_frame, wrap=tk.NONE, font=("Consolas", 11),
            bg="#1E1E2E", fg="#CDD6F4", insertbackground="white",
            padx=8, pady=8, relief=tk.FLAT
        )
        ed_scroll_y = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.editor.yview)
        ed_scroll_x = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.editor.xview)
        self.editor.configure(xscrollcommand=ed_scroll_x.set, yscrollcommand=ed_scroll_y.set)

        ed_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        ed_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.editor.pack(fill=tk.BOTH, expand=True)

        # Right: Pipeline Stages Notebook
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 1. Output & Summary Tab
        self.tab_output = self.create_tab("1. Execution Output")
        # 2. Tokens Tab
        self.tab_tokens = self.create_tab("2. Lexer (Tokens)")
        # 3. AST Tab
        self.tab_ast = self.create_tab("3. Parser (AST)")
        # 4. Symbol Table Tab
        self.tab_symbols = self.create_tab("4. Semantic Analysis")
        # 5. TAC Comparison Tab
        self.tab_tac = self.create_tab("5. Optimization & TAC")

        # Status Bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W, padding=(6, 3))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Load first sample initially
        self.load_sample()

    def create_tab(self, title):
        frame = ttk.Frame(self.notebook, padding=4)
        self.notebook.add(frame, text=title)
        txt = tk.Text(
            frame, wrap=tk.NONE, font=("Consolas", 10),
            bg="#FAFAFA", fg="#1F2937", padx=8, pady=8, relief=tk.FLAT
        )
        scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=txt.yview)
        scroll_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=txt.xview)
        txt.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        txt.pack(fill=tk.BOTH, expand=True)
        return txt

    def load_sample(self, event=None):
        name = self.sample_var.get()
        code = SAMPLE_PROGRAMS.get(name, "")
        self.editor.delete("1.0", tk.END)
        self.editor.insert(tk.END, code)
        self.status_bar.config(text=f"Loaded: {name}")

    def clear_all(self):
        self.editor.delete("1.0", tk.END)
        for tab in [self.tab_output, self.tab_tokens, self.tab_ast, self.tab_symbols, self.tab_tac]:
            tab.delete("1.0", tk.END)
        self.status_bar.config(text="Cleared")

    def set_tab_text(self, text_widget, content):
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, content)

    def compile_and_run(self):
        source = self.editor.get("1.0", tk.END).strip()
        if not source:
            messagebox.showwarning("Empty Program", "Please write or load some source code first.")
            return

        mock_input = self.input_entry.get().strip() or "0"

        try:
            # 1. Lexer
            tokens = tokenize(source)
            tokens_str = f"{'KIND':<12} {'VALUE':<20} {'LINE':<6} {'COLUMN':<6}\n"
            tokens_str += "=" * 50 + "\n"
            for t in tokens:
                tokens_str += f"{t.kind:<12} {repr(t.value):<20} {t.line:<6} {t.column:<6}\n"
            self.set_tab_text(self.tab_tokens, tokens_str)

            # 2. Parser (AST)
            ast = Parser(tokens).parse()
            ast_str = "ABSTRACT SYNTAX TREE:\n" + "=" * 50 + "\n"
            ast_str += ast_to_tree_str(ast)
            self.set_tab_text(self.tab_ast, ast_str)

            # 3. Semantic Analysis
            analyzer = SemanticAnalyzer()
            symbols = analyzer.analyze(ast)
            sym_str = f"{'VARIABLE':<15} {'TYPE':<10} {'INITIALIZED'}\n"
            sym_str += "=" * 45 + "\n"
            for name, info in symbols.items():
                sym_str += f"{name:<15} {info['type']:<10} {str(info['initialized'])}\n"
            self.set_tab_text(self.tab_symbols, sym_str)

            # 4. TAC Generation
            gen = TACGenerator()
            orig_tac = gen.generate(ast)
            before_lines = format_tac(orig_tac)

            # 5. Optimizer
            opt_tac = optimize(orig_tac)
            after_lines = format_tac(opt_tac)

            # Metrics
            removed = len(orig_tac) - len(opt_tac)
            pct = (removed / len(orig_tac) * 100) if orig_tac else 0.0

            tac_str = f"=== TAC BEFORE OPTIMIZATION ({len(before_lines)} instructions) ===\n"
            tac_str += "\n".join(before_lines) if before_lines else "(empty)"
            tac_str += f"\n\n=== TAC AFTER OPTIMIZATION ({len(after_lines)} instructions) ===\n"
            tac_str += "\n".join(after_lines) if after_lines else "(empty)"
            tac_str += f"\n\n{'='*50}\n"
            tac_str += f"OPTIMIZATION METRICS:\n"
            tac_str += f" - Original Instructions: {len(before_lines)}\n"
            tac_str += f" - Optimized Instructions: {len(after_lines)}\n"
            tac_str += f" - Instructions Eliminated: {removed}\n"
            tac_str += f" - Reduction Percentage:   {pct:.1f}%\n"
            tac_str += f" - Techniques Triggered:   Constant Folding, Constant Propagation, CSE, Strength Reduction, Dead Code Elimination\n"
            self.set_tab_text(self.tab_tac, tac_str)

            # 6. Interpreter Execution
            import builtins
            orig_input = builtins.input
            builtins.input = lambda prompt="": mock_input

            try:
                output, memory = execute(opt_tac)
            finally:
                builtins.input = orig_input

            out_str = "╔══════════════════════════════════════════════════╗\n"
            out_str += "║              PROGRAM EXECUTION OUTPUT            ║\n"
            out_str += "╚══════════════════════════════════════════════════╝\n\n"
            if output:
                for line in output:
                    out_str += f"  > {line}\n"
            else:
                out_str += "  (Program executed with no print output)\n"

            out_str += "\n" + "=" * 52 + "\n"
            out_str += "FINAL RUNTIME MEMORY STATE:\n"
            for k, v in memory.items():
                out_str += f"  {k} = {repr(v)}\n"

            out_str += f"\nINSTRUCTION REDUCTION: {len(before_lines)} -> {len(after_lines)} ({pct:.1f}% saved)\n"

            self.set_tab_text(self.tab_output, out_str)
            self.notebook.select(0)  # Switch to output tab

            self.status_bar.config(
                text=f"✔ Compilation & Execution Succeeded! ({len(before_lines)} -> {len(after_lines)} TAC instructions, {pct:.1f}% reduction)"
            )

        except Exception as e:
            err_msg = f"Error during compilation/execution:\n\n{type(e).__name__}: {e}"
            self.set_tab_text(self.tab_output, f"❌ COMPILER ERROR:\n\n{type(e).__name__}: {e}\n")
            self.notebook.select(0)
            self.status_bar.config(text=f"❌ Error: {e}")
            messagebox.showerror("Compiler Error", err_msg)


def main():
    root = tk.Tk()
    app = CompilerUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

