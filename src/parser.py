import sys

import ply.yacc as yacc

from lexer import tokens, minic_lexer, get_column
from ast_nodes import (Root, Compound, Declaration, Assignment, PrintStmt, IfStmt,
                       WhileStmt, BinaryExpr, UnaryExpr, NumberLit, Identifier, print_tree)

precedence = (
    ('nonassoc', 'IFX'),
    ('nonassoc', 'ELSE'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NE'),
    ('left', 'LT', 'GT', 'LE', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'NOT', 'UMINUS'),
)

start = 'program'

def p_start_program(p):
    'program : stmt_list'
    p[0] = Root(p[1], lineno=1)


def p_statement_sequence(p):
    '''stmt_list : stmt_list stmt
                 | empty'''
    if len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    else:
        p[0] = []


def p_nothing(p):
    'empty :'
    pass

def p_compound_statement(p):
    'block : LBRACE stmt_list RBRACE'
    p[0] = Compound(p[2], lineno=p.lineno(1))

def p_statement_with_semicolon(p):
    '''stmt : var_decl SEMI
            | assign SEMI
            | print_stmt SEMI'''
    p[0] = p[1]


def p_statement_without_semicolon(p):
    '''stmt : if_stmt
            | while_stmt
            | block'''
    p[0] = p[1]


def p_declaration(p):
    '''var_decl : INT ID
                | INT ID ASSIGN expr'''
    initializer = p[4] if len(p) == 5 else None
    p[0] = Declaration(p[2], initializer, lineno=p.lineno(2))


def p_assignment(p):
    'assign : ID ASSIGN expr'
    p[0] = Assignment(p[1], p[3], lineno=p.lineno(1))


def p_print_call(p):
    'print_stmt : PRINT LPAREN expr RPAREN'
    p[0] = PrintStmt(p[3], lineno=p.lineno(1))


def p_if_statement(p):
    '''if_stmt : IF LPAREN expr RPAREN stmt %prec IFX
               | IF LPAREN expr RPAREN stmt ELSE stmt'''
    else_body = p[7] if len(p) == 8 else None
    p[0] = IfStmt(p[3], p[5], else_body, lineno=p.lineno(1))


def p_while_statement(p):
    'while_stmt : WHILE LPAREN expr RPAREN stmt'
    p[0] = WhileStmt(p[3], p[5], lineno=p.lineno(1))

def p_binary_expression(p):
    '''expr : expr PLUS expr
            | expr MINUS expr
            | expr TIMES expr
            | expr DIVIDE expr
            | expr MOD expr
            | expr LT expr
            | expr GT expr
            | expr LE expr
            | expr GE expr
            | expr EQ expr
            | expr NE expr
            | expr AND expr
            | expr OR expr'''
    p[0] = BinaryExpr(p[2], p[1], p[3], lineno=p.lineno(2))


def p_unary_minus(p):
    'expr : MINUS expr %prec UMINUS'
    p[0] = UnaryExpr('-', p[2], lineno=p.lineno(1))


def p_logical_not(p):
    'expr : NOT expr'
    p[0] = UnaryExpr('!', p[2], lineno=p.lineno(1))


def p_parenthesized(p):
    'expr : LPAREN expr RPAREN'
    p[0] = p[2]


def p_number_literal(p):
    'expr : NUMBER'
    p[0] = NumberLit(p[1], lineno=p.lineno(1))


def p_identifier_expr(p):
    'expr : ID'
    p[0] = Identifier(p[1], lineno=p.lineno(1))

class MiniCError(Exception):
    def __init__(self, kind, line, column, msg):
        super().__init__(msg)
        self.kind, self.line, self.column, self.msg = kind, line, column, msg


def p_error(p):
    data = minic_lexer.lexdata
    if p is None:
        raise MiniCError('Syntax error', minic_lexer.lineno,
                         get_column(data, len(data)), "unexpected end of input")
    raise MiniCError('Syntax error', p.lineno, get_column(data, p.lexpos),
                     f"unexpected token {p.value!r} ({p.type})")

minic_parser = yacc.yacc(debug=True, write_tables=False)


def parse(source):
    minic_lexer.lineno = 1
    minic_lexer.lex_errors = []
    try:
        tree = minic_parser.parse(source, lexer=minic_lexer)
    except MiniCError:
        if not minic_lexer.lex_errors:
            raise
        tree = None
    if minic_lexer.lex_errors:
        line, col, msg = minic_lexer.lex_errors[0]
        raise MiniCError('Lexical error', line, col, msg)
    return tree


def main(argv):
    if len(argv) < 2:
        print("Usage: python src/parser.py <file.c>", file=sys.stderr)
        return 2

    with open(argv[1], encoding='utf-8') as f:
        source = f.read()

    try:
        tree = parse(source)
    except MiniCError as e:
        print(f"{e.kind} (line {e.line}, column {e.column}): {e.msg}", file=sys.stderr)
        return 1

    print_tree(tree)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))