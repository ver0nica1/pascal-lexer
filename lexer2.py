import ply.lex as lex
import sys

# Analizador léxico para un subconjunto de Pascal (case-insensitive)

# Diccionario de palabras reservadas (case-insensitive)
# La clave es la palabra en minúscula, el valor es el nombre del token

reserved = {
    'and': 'AND', 'array': 'ARRAY', 'begin': 'BEGIN', 'case': 'CASE',
    'const': 'CONST', 'div': 'DIV', 'do': 'DO', 'downto': 'DOWNTO',
    'else': 'ELSE', 'end': 'END', 'file': 'FILE', 'for': 'FOR',
    'function': 'FUNCTION', 'goto': 'GOTO', 'if': 'IF', 'in': 'IN',
    'label': 'LABEL', 'mod': 'MOD', 'nil': 'NIL', 'not': 'NOT',
    'of': 'OF', 'or': 'OR', 'packed': 'PACKED', 'procedure': 'PROCEDURE',
    'program': 'PROGRAM', 'record': 'RECORD', 'repeat': 'REPEAT',
    'set': 'SET', 'then': 'THEN', 'to': 'TO', 'type': 'TYPE',
    'until': 'UNTIL', 'var': 'VAR', 'while': 'WHILE', 'with': 'WITH',
    'integer': 'INTEGER', 'real': 'REAL', 'boolean': 'BOOLEAN',
    'char': 'CHAR', 'string': 'STRING',
}

tokens = [

    # Literales

    'NUMBER',       # Enteros y reales: 123, 3.14, 2e10
    'CHARCONST',    # String entre comillas simples o dobles: 'a'  "hello"

    # Identificador

    'ID',

    # Operadores y símbolos

    'PLUS',         # +
    'MINUS',        # -
    'TIMES',        # *
    'DIVISION',     # /
    'EQ',           # =
    'NE',           # <>
    'LT',           # <
    'GT',           # >
    'LE',           # <=
    'GE',           # >=
    'ASSIGN',       # :=
    'RANGE',        # ..
    'DOT',          # .
    'COMMA',        # ,
    'SEMICOLON',    # ;
    'COLON',        # :
    'LPAR',         # (
    'RPAR',         # )
    'LBR',          # [
    'RBR',          # ]
] + list(reserved.values())

t_PLUS      = r'\+'
t_MINUS     = r'\-'
t_TIMES     = r'\*'
t_DIVISION  = r'/'
t_EQ        = r'='
t_LT        = r'<'
t_GT        = r'>'
t_DOT       = r'\.'
t_COMMA     = r','
t_SEMICOLON = r';'
t_COLON     = r':'
t_LPAR      = r'\('
t_RPAR      = r'\)'
t_LBR       = r'\['
t_RBR       = r'\]'

# Literales

def t_CHARCONST(t):
    r'\'[^\']*\'|"[^"]*"'
    return t

def t_NUMBER(t):
    r'\d+(\.\d+)?([eE][+-]?\d+)?'
    if '.' in t.value or 'e' in t.value.lower():
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value.lower(), 'ID')  # Case-insensitive keyword lookup
    return t

# Operadores compuestos (como funciones, después de ID)

def t_ASSIGN(t):
    r':='
    return t

def t_NE(t):
    r'<>'
    return t

def t_LE(t):
    r'<='
    return t

def t_GE(t):
    r'>='
    return t

def t_RANGE(t):
    r'\.\.'
    return t

# Nueva línea

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t\r'

# Comentarios

def t_COMMENT(t):
    r'\(\*(.|\n)*?\*\)|{[^}]*}'
    t.lexer.lineno += t.value.count('\n')

# Error léxico

def t_error(t):
    print(f"[ERROR LÉXICO] Línea {t.lexer.lineno}: carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

# Función de prueba

def test(data, lexer):
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)

# Construye el lexer

lexer = lex.lex()

# main

if __name__ == '__main__':
    if len(sys.argv) > 1:
        fin = sys.argv[1]
    else:
        fin = 'input.pas'
    f = open(fin, 'r')
    data = f.read()
    print(data)
    lexer.input(data)
    test(data, lexer)
