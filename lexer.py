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

    'NUMBER',
    'CHARCONST',

    # Identificador

    'ID',

    # Operadores y símbolos

    'PLUS',
    'MINUS',
    'TIMES',
    'DIVISION',
    'EQ',
    'NE',
    'LT',
    'GT',
    'LE',
    'GE',
    'ASSIGN',
    'RANGE',
    'DOT',
    'COMMA',
    'SEMICOLON',
    'COLON',
    'LPAR',
    'RPAR',
    'LBR',
    'RBR'
)

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
    r'[pP][rR][oO][cC][eE][dD][uU][rR][eE]\b'
    return t

def t_FUNCTION(t):
    r'[fF][uU][nN][cC][tT][iI][oO][nN]\b'
    return t

def t_BOOLEAN(t):
    r'[bB][oO][oO][lL][eE][aA][nN]\b'
    return t

def t_INTEGER(t):
    r'[iI][nN][tT][eE][gG][eE][rR]\b'
    return t

def t_PROGRAM(t):
    r'[pP][rR][oO][gG][rR][aA][mM]\b'
    return t

def t_DOWNTO(t):
    r'[dD][oO][wW][nN][tT][oO]\b'
    return t

def t_PACKED(t):
    r'[pP][aA][cC][kK][eE][dD]\b'
    return t

def t_RECORD(t):
    r'[rR][eE][cC][oO][rR][dD]\b'
    return t

def t_REPEAT(t):
    r'[rR][eE][pP][eE][aA][tT]\b'
    return t

def t_STRING(t):
    r'[sS][tT][rR][iI][nN][gG]\b'
    return t

def t_ARRAY(t):
    r'[aA][rR][rR][aA][yY]\b'
    return t

def t_BEGIN(t):
    r'[bB][eE][gG][iI][nN]\b'
    return t

def t_CONST(t):
    r'[cC][oO][nN][sS][tT]\b'
    return t

def t_LABEL(t):
    r'[lL][aA][bB][eE][lL]\b'
    return t

def t_UNTIL(t):
    r'[uU][nN][tT][iI][lL]\b'
    return t

def t_WHILE(t):
    r'[wW][hH][iI][lL][eE]\b'
    return t

def t_CASE(t):
    r'[cC][aA][sS][eE]\b'
    return t

def t_CHAR(t):
    r'[cC][hH][aA][rR]\b'
    return t

def t_ELSE(t):
    r'[eE][lL][sS][eE]\b'
    return t

def t_FILE(t):
    r'[fF][iI][lL][eE]\b'
    return t

def t_GOTO(t):
    r'[gG][oO][tT][oO]\b'
    return t

def t_REAL(t):
    r'[rR][eE][aA][lL]\b'
    return t

def t_THEN(t):
    r'[tT][hH][eE][nN]\b'
    return t

def t_TYPE(t):
    r'[tT][yY][pP][eE]\b'
    return t

def t_WITH(t):
    r'[wW][iI][tT][hH]\b'
    return t

def t_AND(t):
    r'[aA][nN][dD]\b'
    return t

def t_DIV(t):
    r'[dD][iI][vV]\b'
    return t

def t_END(t):
    r'[eE][nN][dD]\b'
    return t

def t_FOR(t):
    r'[fF][oO][rR]\b'
    return t

def t_MOD(t):
    r'[mM][oO][dD]\b'
    return t

def t_NIL(t):
    r'[nN][iI][lL]\b'
    return t

def t_NOT(t):
    r'[nN][oO][tT]\b'
    return t

def t_SET(t):
    r'[sS][eE][tT]\b'
    return t

def t_VAR(t):
    r'[vV][aA][rR]\b'
    return t

def t_DO(t):
    r'[dD][oO]\b'
    return t

def t_IF(t):
    r'[iI][fF]\b'
    return t

def t_IN(t):
    r'[iI][nN]\b'
    return t

def t_OF(t):
    r'[oO][fF]\b'
    return t

def t_OR(t):
    r'[oO][rR]\b'
    return t

def t_TO(t):
    r'[tT][oO]\b'
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