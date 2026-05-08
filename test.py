"""
Compilador Pascal - Punto de entrada principal
Ejecuta los tres análisis en orden:
  1. Léxico   → errores de caracteres ilegales
  2. Sintáctico → errores de estructura gramatical
  3. Semántico → errores de uso, tipos y declaraciones
"""

import sys
import lexer as pascal_lexer
import parser as pascal_parser
import semantico as pascal_semantico


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
    """Tokeniza el archivo y devuelve (tokens, errores, num_lineas)."""
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
    """Parsea el archivo y devuelve lista de errores sintácticos."""
    pascal_lexer.lexer_errors = []
    pascal_lexer.lexer.lineno = 1
    pascal_parser.errors_list.clear()
    pascal_parser.parser.parse(data, lexer=pascal_lexer.lexer, tracking=True)
    return list(pascal_lexer.lexer_errors) + list(pascal_parser.errors_list)


def analisis_semantico(tokens):
    """Ejecuta el analizador semántico completo y devuelve el objeto analizador.
    analizar() internamente hace: recolectar → reset flags → verificar → advertencias.
    """
    pascal_lexer.lexer.lineno = 1
    analizador = pascal_semantico.AnalizadorSemantico(tokens)
    analizador.analizar()
    return analizador


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


def imprimir_seccion_semantica(analizador):
    errores      = analizador.tabla.errores
    advertencias = analizador.tabla.advertencias

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


def imprimir_tabla_simbolos(analizador):
    tabla = analizador.tabla

    print(f"\n{'[ 4 ] TABLA DE SÍMBOLOS':^60}")
    print(SEP2)

    # Variables globales
    vars_globales = tabla.scopes[0]
    print(f"\n  Variables globales: {len(vars_globales)}")
    for nombre, info in vars_globales.items():
        estado = "✓ usada" if info.get('usada') else "✗ no usada"
        print(f"    - {nombre} : {info['tipo']} [{estado}] (línea {info['linea']})")

    # Constantes
    print(f"\n  Constantes: {len(tabla.constantes)}")
    for nombre, info in tabla.constantes.items():
        print(f"    - {nombre} : {info['tipo']} (línea {info['linea']})")

    # Tipos
    print(f"\n  Tipos definidos: {len(tabla.tipos)}")
    for nombre, info in tabla.tipos.items():
        print(f"    - {nombre} = {info['definicion']} (línea {info['linea']})")

    # Funciones
    print(f"\n  Funciones: {len(tabla.funciones)}")
    for nombre, info in tabla.funciones.items():
        estado     = "✓ usada" if info['usada'] else "✗ no usada"
        params_str = ', '.join(f"{p['nombre']}: {p['tipo']}" for p in info['params'])
        print(f"    - {nombre}({params_str}) : {info['tipo']} [{estado}] (línea {info['linea']})")
        vars_loc = tabla.vars_locales.get(nombre.lower(), {})
        for vnom, vinfo in vars_loc.items():
            info_g   = tabla.scopes[0].get(vnom)
            usada    = info_g['usada'] if info_g else vinfo.get('usada', False)
            estado_v = "✓ usada" if usada else "✗ no usada"
            print(f"        var {vnom} : {vinfo['tipo']} [{estado_v}] (línea {vinfo['linea']})")

    # Procedimientos
    print(f"\n  Procedimientos: {len(tabla.procedimientos)}")
    for nombre, info in tabla.procedimientos.items():
        estado     = "✓ usado" if info['usado'] else "✗ no usado"
        params_str = ', '.join(f"{p['nombre']}: {p['tipo']}" for p in info['params'])
        print(f"    - {nombre}({params_str}) [{estado}] (línea {info['linea']})")
        vars_loc = tabla.vars_locales.get(nombre.lower(), {})
        for vnom, vinfo in vars_loc.items():
            info_g   = tabla.scopes[0].get(vnom)
            usada    = info_g['usada'] if info_g else vinfo.get('usada', False)
            estado_v = "✓ usada" if usada else "✗ no usada"
            print(f"        var {vnom} : {vinfo['tipo']} [{estado_v}] (línea {vinfo['linea']})")


def imprimir_resumen(err_lex, err_sin, analizador):
    err_sem = analizador.tabla.errores
    adv_sem = analizador.tabla.advertencias
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


# ==============================================================
#   MAIN
# ==============================================================

if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) > 1 else 'input.pas'
    data     = leer_archivo(filename)

    tokens, err_lex, num_lineas = analisis_lexico(data)
    err_sin                     = analisis_sintactico(data)
    analizador                  = analisis_semantico(tokens)

    imprimir_encabezado(filename, len(tokens), num_lineas)
    imprimir_seccion_lexica(err_lex)
    imprimir_seccion_sintactica(err_sin)
    imprimir_seccion_semantica(analizador)
    imprimir_tabla_simbolos(analizador)
    imprimir_resumen(err_lex, err_sin, analizador)