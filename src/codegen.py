import keyword
import sys

from parser import parse, MiniCError

INDENT = '    '

PY_OPERATORS = {'&&': 'and', '||': 'or'}

HELPERS = '''\
def c_div(a, b):
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q

def c_mod(a, b):
    return a - b * c_div(a, b)

'''

RESERVED = set(keyword.kwlist) | {'abs', 'int', 'print', 'c_div', 'c_mod'}


class CodeGenerator:
    def __init__(self):
        self.lines = []
        self.level = 0
        self.scopes = []
        self.taken = set()

    def generate(self, tree):
        self.visit(tree)
        return HELPERS + '\n'.join(self.lines) + '\n'

    def visit(self, node):
        return getattr(self, 'visit_' + type(node).__name__)(node)

    def emit(self, text):
        self.lines.append(INDENT * self.level + text)

    def emit_body(self, node):
        self.level += 1
        start = len(self.lines)
        self.visit(node)
        if len(self.lines) == start:
            self.emit('pass')
        self.level -= 1

    def declare(self, name):
        scope = self.scopes[-1]
        if name in scope:
            return scope[name]
        py_name = name
        n = 0
        while py_name in RESERVED or py_name in self.taken:
            n += 1
            py_name = f"{name}__{n}"
        self.taken.add(py_name)
        scope[name] = py_name
        return py_name

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return name + '_' if name in RESERVED else name

    def visit_Root(self, node):
        self.scopes.append({})
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Compound(self, node):
        self.scopes.append({})
        for stmt in node.statements:
            self.visit(stmt)
        self.scopes.pop()

    def visit_Declaration(self, node):
        init = None
        if node.initializer is not None:
            init = self.visit(node.initializer)
        py_name = self.declare(node.name)
        if init is not None:
            self.emit(f"{py_name} = {init}")

    def visit_Assignment(self, node):
        value = self.visit(node.value)
        self.emit(f"{self.lookup(node.name)} = {value}")

    def visit_PrintStmt(self, node):
        self.emit(f"print({self.visit(node.argument)})")

    def visit_IfStmt(self, node):
        self.emit(f"if {self.visit(node.condition)}:")
        self.emit_body(node.then_body)
        if node.else_body is not None:
            self.emit('else:')
            self.emit_body(node.else_body)

    def visit_WhileStmt(self, node):
        self.emit(f"while {self.visit(node.condition)}:")
        self.emit_body(node.body)

    def visit_NumberLit(self, node):
        return str(node.value)

    def visit_Identifier(self, node):
        return self.lookup(node.name)

    def visit_UnaryExpr(self, node):
        operand = self.visit(node.operand)
        if node.op == '-':
            return f"(-{operand})"
        return f"(1 if {operand} == 0 else 0)"

    def visit_BinaryExpr(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        if op == '/':
            return f"c_div({left}, {right})"
        if op == '%':
            return f"c_mod({left}, {right})"
        if op in PY_OPERATORS:
            result = f"({left} != 0 {PY_OPERATORS[op]} {right} != 0)"
            return f"(1 if {result} else 0)"
        if op in ('<', '>', '<=', '>=', '==', '!='):
            return f"int({left} {op} {right})"
        return f"({left} {op} {right})"


def generate(tree):
    return CodeGenerator().generate(tree)


def main(argv):
    args = argv[1:]
    if not args:
        print("Usage: python src/codegen.py <file.c> [-o out.py]", file=sys.stderr)
        return 2

    with open(args[0], encoding='utf-8') as f:
        source = f.read()

    try:
        code = generate(parse(source))
    except MiniCError as e:
        print(f"{e.kind} (line {e.line}, column {e.column}): {e.msg}", file=sys.stderr)
        return 1

    if '-o' in args:
        out_path = args[args.index('-o') + 1]
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"Generated {out_path}")
    else:
        print(code, end='')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))