"""
Compilador Pascal - Punto de entrada principal
Ejecuta los tres análisis en orden:
  1. Léxico   → errores de caracteres ilegales
  2. Sintáctico → errores de estructura gramatical
  3. Semántico → errores de uso, tipos y declaraciones
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import lexer as pascal_lexer
import parser as pascal_parser
import semantico as pascal_semantico
import parser_sem


SEP  = "=" * 60
SEP2 = "-" * 60


def leer_archivo(filename):
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Archivo '{filename}' no encontrado.")
        sys.exit(1)


def analisis_lexico(data):
    pascal_lexer.lexer_errors = []
    pascal_lexer.lexer.lineno = 1
    pascal_lexer.lexer.input(data)

    tokens = []
    while True:
        tok = pascal_lexer.lexer.token()
        if not tok:
            break
        tokens.append(tok)

    num_lineas = len(data.splitlines())
    return tokens, list(pascal_lexer.lexer_errors), num_lineas


def analisis_sintactico(data):
    pascal_lexer.lexer_errors = []
    pascal_lexer.lexer.lineno = 1
    pascal_parser.errors_list.clear()
    pascal_parser.parser.parse(data, lexer=pascal_lexer.lexer, tracking=True)
    return list(pascal_lexer.lexer_errors) + list(pascal_parser.errors_list)


def analisis_semantico(data):
    pascal_lexer.lexer_errors = []
    pascal_lexer.lexer.lineno = 1
    parser_sem.syntax_errors.clear()
    parser_sem.sem.errors.clear()
    parser_sem.sem.warnings.clear()
    parser_sem.sem.table = pascal_semantico.SymbolTable()
    parser_sem.sem._current_function = None
    pascal_semantico.register_builtins(parser_sem.sem)
    parser_sem.parser.parse(data, lexer=pascal_lexer.lexer, tracking=True)
    return parser_sem.sem


def imprimir_encabezado(filename, num_tokens, num_lineas):
    print(SEP)
    print(f"  COMPILADOR PASCAL")
    print(f"  Archivo : {filename}")
    print(f"  Tokens  : {num_tokens}    Líneas: {num_lineas}")
    print(SEP)


def imprimir_seccion_lexica(errores):
    print(f"\n{'[ 1 ] ANÁLISIS LÉXICO':^60}")
    print(SEP2)
    if not errores:
        print("  [OK] Sin errores léxicos.")
    else:
        print(f"  [ERROR] {len(errores)} error(es) léxico(s) encontrado(s):\n")
        for i, e in enumerate(errores, 1):
            print(f"    {i}. {e}")


def imprimir_seccion_sintactica(errores):
    print(f"\n{'[ 2 ] ANÁLISIS SINTÁCTICO':^60}")
    print(SEP2)
    if not errores:
        print("  [OK] Sin errores sintácticos.")
    else:
        print(f"  [ERROR] {len(errores)} error(es) sintáctico(s) encontrado(s):\n")
        for i, e in enumerate(errores, 1):
            print(f"    {i}. {e}")


def imprimir_seccion_semantica(sem):
    errores      = sem.errors
    advertencias = sem.warnings

    print(f"\n{'[ 3 ] ANÁLISIS SEMÁNTICO':^60}")
    print(SEP2)

    if not errores and not advertencias:
        print("  [OK] Sin errores semánticos.")
    else:
        if errores:
            print(f"  [ERROR] {len(errores)} error(es) semántico(s) encontrado(s):\n")
            for i, e in enumerate(errores, 1):
                print(f"    {i}. {e}")
        if advertencias:
            print(f"\n  [WARNING] {len(advertencias)} advertencia(s):\n")
            for i, a in enumerate(advertencias, 1):
                print(f"    {i}. {a}")


def imprimir_tabla_simbolos(sem):
    tabla = sem.table

    print(f"\n{'[ 4 ] TABLA DE SÍMBOLOS':^60}")
    print(SEP2)
    print(f"  {'NOMBRE':<18} {'TIPO':<18} {'CATEGORÍA':<12} {'ÁMBITO':<16} {'LÍNEA':>5}  {'INIC':>5}")
    print("  " + "-" * 80)

    vars_globales = {k: v for k, v in tabla._scopes[0].items() if v.kind == 'var'}
    print(f"\n  Ámbito: global (variables)")
    for nombre, info in vars_globales.items():
        init_str = "sí" if info.initialized else "no"
        print(f"  {nombre:<18} {info.type:<18} {info.kind:<12} {info.scope:<16} {info.line:>5}  {init_str:>5}")

    constantes = {k: v for k, v in tabla._scopes[0].items() if v.kind == 'const'}
    if constantes:
        print(f"\n  Ámbito: global (constantes)")
        for nombre, info in constantes.items():
            print(f"  {nombre:<18} {info.type:<18} {info.kind:<12} {info.scope:<16} {info.line:>5}  {'sí':>5}")

    tipos = {k: v for k, v in tabla._scopes[0].items() if v.kind == 'type'}
    if tipos:
        print(f"\n  Ámbito: global (tipos)")
        for nombre, info in tipos.items():
            print(f"  {nombre:<18} {info.type:<18} {info.kind:<12} {info.scope:<16} {info.line:>5}  {'sí':>5}")

    funciones = [s for s in tabla._all_symbols if s.kind == 'function']
    if funciones:
        print(f"\n  Ámbito: global (funciones)")
        for info in funciones:
            extra = ""
            if info.return_type:
                extra = f"->{info.return_type}"
            elif info.params:
                extra = f"({','.join(str(p) for p in info.params)})"
            tipo_str = (info.type + extra)[:17]
            print(f"  {info.name:<18} {tipo_str:<18} {info.kind:<12} {info.scope:<16} {info.line:>5}  {'sí':>5}")

    procedimientos = [s for s in tabla._all_symbols if s.kind == 'procedure']
    if procedimientos:
        print(f"\n  Ámbito: global (procedimientos)")
        for info in procedimientos:
            params_str = ','.join(str(p) for p in info.params)
            tipo_str = (info.type + f"({params_str})")[:17]
            print(f"  {info.name:<18} {tipo_str:<18} {info.kind:<12} {info.scope:<16} {info.line:>5}  {'sí':>5}")


def imprimir_resumen(err_lex, err_sin, sem):
    err_sem = sem.errors
    adv_sem = sem.warnings
    total   = len(err_lex) + len(err_sin) + len(err_sem)

    print(f"\n{'[ RESUMEN FINAL ]':^60}")
    print(SEP2)
    print(f"  Errores léxicos    : {len(err_lex)}")
    print(f"  Errores sintácticos: {len(err_sin)}")
    print(f"  Errores semánticos : {len(err_sem)}")
    print(f"  Advertencias       : {len(adv_sem)}")
    print(SEP2)
    if total == 0:
        print("  [OK] COMPILACIÓN EXITOSA — el código es correcto.")
    else:
        print(f"  [FALLO] Se encontraron {total} error(es) en total.")
    print(SEP)


if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) > 1 else 'input.pas'
    data     = leer_archivo(filename)

    tokens, err_lex, num_lineas = analisis_lexico(data)
    err_sin                     = analisis_sintactico(data)
    sem                         = analisis_semantico(data)

    imprimir_encabezado(filename, len(tokens), num_lineas)
    imprimir_seccion_lexica(err_lex)
    imprimir_seccion_sintactica(err_sin)
    imprimir_seccion_semantica(sem)
    imprimir_tabla_simbolos(sem)
    imprimir_resumen(err_lex, err_sin, sem)
