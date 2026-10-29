import sys

import ply.lex as lex

reserved = {
    'int': 'INT',
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'print': 'PRINT',
}

tokens = [
    'ID', 'NUMBER',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'LT', 'GT', 'LE', 'GE', 'EQ', 'NE',
    'AND', 'OR', 'NOT',
    'ASSIGN',
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'SEMI',
] + list(reserved.values())

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'

t_LE = r'<='
t_GE = r'>='
t_EQ = r'=='
t_NE = r'!='
t_LT = r'<'
t_GT = r'>'

t_AND = r'&&'
t_OR = r'\|\|'
t_NOT = r'!'

t_ASSIGN = r'='

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_SEMI = r';'

t_ignore = ' \t\r'

t_ignore_LINE_COMMENT = r'//[^\n]*'

def t_MULTI_LINE_COMMENT(t):
    r'/\*[\s\S]*?\*/'
    t.lexer.lineno += t.value.count('\n')


def t_UNCLOSED_COMMENT(t):
    r'/\*'
    add_error(t.lexer, t.lexpos, "There is an unclosed comment /*")
    t.lexer.lexpos = len(t.lexer.lexdata)


def t_ID(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t


def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_lines_counter(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    add_error(t.lexer, t.lexpos, f"The symbol is not available: {t.value[0]!r}")
    t.lexer.skip(1)

def get_column(source, pos):
        line_start = source.rfind('\n', 0, pos)
        return pos - line_start

def add_error(lex_obj, pos, msg):
    column = get_column(lex_obj.lexdata, pos)
    lex_obj.lex_errors.append((lex_obj.lineno, column, msg))

minic_lexer = lex.lex()
minic_lexer.lex_errors = []

def get_tokens(source):
    minic_lexer.lineno = 1
    minic_lexer.lex_errors = []
    minic_lexer.input(source)
    return list(minic_lexer)

def main(argv):
    if len(argv) < 2:
        print("Usage: python src/lexer.py <file.c>", file=sys.stderr)
        return 2

    with open(argv[1], encoding='utf-8') as f:
        source = f.read()

    toks = get_tokens(source)

    print(f"{'LINE':>5} {'COL':>5}  {'TYPE':<8} VALUE")
    for t in toks:
        print(f"{t.lineno:>5} {get_column(source, t.lexpos):>5}  {t.type:<8} {t.value!r}")

    for line, col, msg in minic_lexer.lex_errors:
        print(f"Lexical error (line {line}, column {col}): {msg}", file=sys.stderr)

    return 1 if minic_lexer.lex_errors else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))