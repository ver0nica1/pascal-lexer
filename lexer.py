import ply.lex as lex
import sys

# Analizador léxico para un subconjunto de Pascal

tokens = (

    # 35 palabras reservadas de la documentación básica de pascal basic syntax

    'AND', 'ARRAY', 'BEGIN', 'CASE', 'CONST',
    'DIV', 'DO', 'DOWNTO', 'ELSE', 'END',
    'FILE', 'FOR', 'FUNCTION', 'GOTO', 'IF',
    'IN', 'LABEL', 'MOD', 'NIL', 'NOT',
    'OF', 'OR', 'PACKED', 'PROCEDURE', 'PROGRAM',
    'RECORD', 'REPEAT', 'SET', 'THEN', 'TO',
    'TYPE', 'UNTIL', 'VAR', 'WHILE', 'WITH',

    # Tipos de dato

    'INTEGER', 'REAL', 'BOOLEAN', 'CHAR', 'STRING',

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
)

# Palabras reservadas: una función por cada keyword, con el mismo nombre que el token

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

# Palabras reservadas

def t_PROCEDURE(t):
    r'[pP][rR][oO][cC][eE][dD][uU][rR][eE]'
    return t

def t_FUNCTION(t):
    r'[fF][uU][nN][cC][tT][iI][oO][nN]'
    return t

def t_BOOLEAN(t):
    r'[bB][oO][oO][lL][eE][aA][nN]'
    return t

def t_INTEGER(t):
    r'[iI][nN][tT][eE][gG][eE][rR]'
    return t

def t_PROGRAM(t):
    r'[pP][rR][oO][gG][rR][aA][mM]'
    return t

def t_DOWNTO(t):
    r'[dD][oO][wW][nN][tT][oO]'
    return t

def t_PACKED(t):
    r'[pP][aA][cC][kK][eE][dD]'
    return t

def t_RECORD(t):
    r'[rR][eE][cC][oO][rR][dD]'
    return t

def t_REPEAT(t):
    r'[rR][eE][pP][eE][aA][tT]'
    return t

def t_STRING(t):
    r'[sS][tT][rR][iI][nN][gG]'
    return t

def t_ARRAY(t):
    r'[aA][rR][rR][aA][yY]'
    return t

def t_BEGIN(t):
    r'[bB][eE][gG][iI][nN]'
    return t

def t_CONST(t):
    r'[cC][oO][nN][sS][tT]'
    return t

def t_LABEL(t):
    r'[lL][aA][bB][eE][lL]'
    return t

def t_UNTIL(t):
    r'[uU][nN][tT][iI][lL]'
    return t

def t_WHILE(t):
    r'[wW][hH][iI][lL][eE]'
    return t

def t_CASE(t):
    r'[cC][aA][sS][eE]'
    return t

def t_CHAR(t):
    r'[cC][hH][aA][rR]'
    return t

def t_ELSE(t):
    r'[eE][lL][sS][eE]'
    return t

def t_FILE(t):
    r'[fF][iI][lL][eE]'
    return t

def t_GOTO(t):
    r'[gG][oO][tT][oO]'
    return t

def t_REAL(t):
    r'[rR][eE][aA][lL]'
    return t

def t_THEN(t):
    r'[tT][hH][eE][nN]'
    return t

def t_TYPE(t):
    r'[tT][yY][pP][eE]'
    return t

def t_WITH(t):
    r'[wW][iI][tT][hH]'
    return t

def t_AND(t):
    r'[aA][nN][dD]'
    return t

def t_DIV(t):
    r'[dD][iI][vV]'
    return t

def t_END(t):
    r'[eE][nN][dD]'
    return t

def t_FOR(t):
    r'[fF][oO][rR]'
    return t

def t_MOD(t):
    r'[mM][oO][dD]'
    return t

def t_NIL(t):
    r'[nN][iI][lL]'
    return t

def t_NOT(t):
    r'[nN][oO][tT]'
    return t

def t_SET(t):
    r'[sS][eE][tT]'
    return t

def t_VAR(t):
    r'[vV][aA][rR]'
    return t

def t_DO(t):
    r'[dD][oO]'
    return t

def t_IF(t):
    r'[iI][fF]'
    return t

def t_IN(t):
    r'[iI][nN]'
    return t

def t_OF(t):
    r'[oO][fF]'
    return t

def t_OR(t):
    r'[oO][rR]'
    return t

def t_TO(t):
    r'[tT][oO]'
    return t

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