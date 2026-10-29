class AstNode:
    attrs = ()

    def __init__(self, *args, lineno=0):
        assert len(args) == len(self.attrs), \
            f"{type(self).__name__} expects {len(self.attrs)} values"
        for attr, arg in zip(self.attrs, args):
            setattr(self, attr, arg)
        self.lineno = lineno


class Root(AstNode):
    attrs = ('statements',)


class Compound(AstNode):
    attrs = ('statements',)


class Declaration(AstNode):
    attrs = ('name', 'initializer')


class Assignment(AstNode):
    attrs = ('name', 'value')


class PrintStmt(AstNode):
    attrs = ('argument',)


class IfStmt(AstNode):
    attrs = ('condition', 'then_body', 'else_body')


class WhileStmt(AstNode):
    attrs = ('condition', 'body')


class BinaryExpr(AstNode):
    attrs = ('op', 'left', 'right')


class UnaryExpr(AstNode):
    attrs = ('op', 'operand')


class NumberLit(AstNode):
    attrs = ('value',)


class Identifier(AstNode):
    attrs = ('name',)


def print_tree(node, level=0):
    indent = '  ' * level
    if isinstance(node, list):
        for item in node:
            print_tree(item, level)
        return

    inline = []
    children = []
    for attr in node.attrs:
        value = getattr(node, attr)
        if isinstance(value, (AstNode, list)):
            children.append((attr, value))
        else:
            inline.append(f"{attr}={value!r}")

    print(f"{indent}{type(node).__name__}({', '.join(inline)})")
    for attr, value in children:
        print(f"{indent}  {attr}:")
        print_tree(value, level + 1 + 1)