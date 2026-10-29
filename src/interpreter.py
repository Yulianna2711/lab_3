import operator
import sys

from parser import parse, MiniCError

ARITHMETIC = {'+': operator.add, '-': operator.sub, '*': operator.mul}
COMPARISON = {'<': operator.lt, '>': operator.gt, '<=': operator.le,
              '>=': operator.ge, '==': operator.eq, '!=': operator.ne}


def divide_like_c(a, b):
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


class MiniCRuntimeError(Exception):
    def __init__(self, line, msg):
        super().__init__(msg)
        self.line, self.msg = line, msg


class Interpreter:
    MAX_LOOP_STEPS = 1_000_000

    def __init__(self):
        self.scopes = []
        self.loop_steps = 0

    def run(self, tree):
        self.visit(tree)

    def visit(self, node):
        method = getattr(self, 'visit_' + type(node).__name__)
        return method(node)

    def fail(self, node, msg):
        raise MiniCRuntimeError(node.lineno, msg)

    def find_scope(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope
        return None

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
        scope = self.scopes[-1]
        if node.name in scope:
            self.fail(node, f"variable '{node.name}' is already declared")
        value = None
        if node.initializer is not None:
            value = self.visit(node.initializer)
        scope[node.name] = value

    def visit_Assignment(self, node):
        value = self.visit(node.value)
        scope = self.find_scope(node.name)
        if scope is None:
            self.fail(node, f"variable '{node.name}' is not declared")
        scope[node.name] = value

    def visit_PrintStmt(self, node):
        print(self.visit(node.argument))

    def visit_IfStmt(self, node):
        if self.visit(node.condition) != 0:
            self.visit(node.then_body)
        elif node.else_body is not None:
            self.visit(node.else_body)

    def visit_WhileStmt(self, node):
        while self.visit(node.condition) != 0:
            self.loop_steps += 1
            if self.loop_steps > self.MAX_LOOP_STEPS:
                self.fail(node, "loop step limit exceeded (possible infinite loop)")
            self.visit(node.body)

    def visit_NumberLit(self, node):
        return node.value

    def visit_Identifier(self, node):
        scope = self.find_scope(node.name)
        if scope is None:
            self.fail(node, f"variable '{node.name}' is not declared")
        value = scope[node.name]
        if value is None:
            self.fail(node, f"variable '{node.name}' is used before it is assigned")
        return value

    def visit_UnaryExpr(self, node):
        value = self.visit(node.operand)
        if node.op == '-':
            return -value
        return 1 if value == 0 else 0

    def visit_BinaryExpr(self, node):
        op = node.op
        if op == '&&':
            return 1 if self.visit(node.left) != 0 and self.visit(node.right) != 0 else 0
        if op == '||':
            return 1 if self.visit(node.left) != 0 or self.visit(node.right) != 0 else 0

        left = self.visit(node.left)
        right = self.visit(node.right)

        if op in ARITHMETIC:
            return ARITHMETIC[op](left, right)
        if op in COMPARISON:
            return 1 if COMPARISON[op](left, right) else 0
        if op in ('/', '%'):
            if right == 0:
                self.fail(node, "division by zero")
            quotient = divide_like_c(left, right)
            return quotient if op == '/' else left - right * quotient
        self.fail(node, f"unknown operator {op!r}")


def main(argv):
    args = argv[1:]
    if not args:
        print("Usage: python src/interpreter.py <file.c>", file=sys.stderr)
        return 2

    with open(args[0], encoding='utf-8') as f:
        source = f.read()

    interpreter = Interpreter()
    try:
        tree = parse(source)
        interpreter.run(tree)
    except MiniCError as e:
        print(f"{e.kind} (line {e.line}, column {e.column}): {e.msg}", file=sys.stderr)
        return 1
    except MiniCRuntimeError as e:
        print(f"Runtime error (line {e.line}): {e.msg}", file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))