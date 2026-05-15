"""
Analizador Semántico para Pascal
Recorre los tokens directamente (sin PLY-YACC) en dos pasadas:
  1. Recolectar declaraciones (variables, funciones, procedimientos, tipos, constantes)
  2. Verificar uso correcto (variables no declaradas, tipos incompatibles, argumentos, etc.)
"""

import sys
import lexer as pascal_lexer
import parser as pascal_parser


# ==============================================================
#   TABLA DE SÍMBOLOS
# ==============================================================

class TablaSimbolos:

    def __init__(self):
        self.scopes       = [{}]   # pila de scopes, [0] es global
        self.funciones    = {}     # {nombre: {params, tipo_retorno, linea, usada}}
        self.procedimientos = {}   # {nombre: {params, linea, usado}}
        self.tipos        = {}     # tipos definidos con TYPE
        self.constantes   = {}     # constantes definidas con CONST
        self.vars_locales = {}  # {nombre_funcion: {nombre_var: info}}
        self.errores      = []
        self.advertencias = []

    # ----------------------------------------------------------
    #   Variables
    # ----------------------------------------------------------

    def declarar_variable(self, nombre, tipo, linea):
        scope = self.scopes[-1]
        clave = nombre.lower()
        if clave in scope:
            self.errores.append(
                f"Error en línea {linea}: "
                f"'{nombre}' ya fue declarado en línea {scope[clave]['linea']}"
            )
        else:
            scope[clave] = {'clase': 'var', 'tipo': tipo, 'linea': linea, 'usada': False}

    def usar_variable(self, nombre, linea):
        clave = nombre.lower()
        for scope in reversed(self.scopes):
            if clave in scope:
                scope[clave]['usada'] = True
                return scope[clave]['tipo']
        # Puede ser parámetro de función/procedimiento
        for info in list(self.funciones.values()) + list(self.procedimientos.values()):
            if clave in [p['nombre'].lower() for p in info.get('params', [])]:
                return 'unknown'
        self.errores.append(
            f"Error en línea {linea}: Variable '{nombre}' usada sin declarar"
        )
        return 'error'

    def buscar_variable(self, nombre):
        clave = nombre.lower()
        for scope in reversed(self.scopes):
            if clave in scope:
                return scope[clave]
        return None

    # ----------------------------------------------------------
    #   Funciones y procedimientos
    # ----------------------------------------------------------

    def declarar_funcion(self, nombre, params, tipo_retorno, linea):
        clave = nombre.lower()
        if clave in self.funciones:
            self.errores.append(
                f"Error en línea {linea}: "
                f"Función '{nombre}' ya declarada en línea {self.funciones[clave]['linea']}"
            )
        else:
            self.funciones[clave] = {
                'params': params, 'tipo': tipo_retorno,
                'linea': linea, 'usada': False
            }

    def declarar_procedimiento(self, nombre, params, linea):
        clave = nombre.lower()
        if clave in self.procedimientos:
            self.errores.append(
                f"Error en línea {linea}: "
                f"Procedimiento '{nombre}' ya declarado en línea {self.procedimientos[clave]['linea']}"
            )
        else:
            self.procedimientos[clave] = {
                'params': params, 'linea': linea, 'usado': False
            }

    def llamar_subprograma(self, nombre, num_args, linea):
        clave = nombre.lower()
        if clave in BUILTINS:
            return
        if clave in self.funciones:
            self.funciones[clave]['usada'] = True
            esperados = len(self.funciones[clave]['params'])
            if num_args != esperados:
                self.errores.append(
                    f"Error en línea {linea}: '{nombre}' espera {esperados} "
                    f"argumento(s), se llamó con {num_args}"
                )
        elif clave in self.procedimientos:
            self.procedimientos[clave]['usado'] = True
            esperados = len(self.procedimientos[clave]['params'])
            if num_args != esperados:
                self.errores.append(
                    f"Error en línea {linea}: '{nombre}' espera {esperados} "
                    f"argumento(s), se llamó con {num_args}"
                )
        else:
            self.errores.append(
                f"Error en línea {linea}: '{nombre}' no está declarado"
            )

    # ----------------------------------------------------------
    #   Tipos y constantes
    # ----------------------------------------------------------

    def declarar_tipo(self, nombre, definicion, linea):
        clave = nombre.lower()
        if clave in self.tipos:
            self.errores.append(
                f"Error en línea {linea}: Tipo '{nombre}' ya declarado"
            )
        else:
            self.tipos[clave] = {'definicion': definicion, 'linea': linea}

    def declarar_constante(self, nombre, tipo, linea):
        clave = nombre.lower()
        if clave in self.constantes:
            self.errores.append(
                f"Error en línea {linea}: Constante '{nombre}' ya declarada"
            )
        else:
            self.constantes[clave] = {'tipo': tipo, 'linea': linea}



# ==============================================================
#   BUILT-INS de Pascal
# ==============================================================

BUILTINS = {'writeln', 'write', 'readln', 'read', 'new', 'dispose',
            'length', 'copy', 'concat', 'pos', 'chr', 'ord',
            'abs', 'sqr', 'sqrt', 'trunc', 'round', 'succ', 'pred'}

PALABRAS_ESTRUCTURA = {
    'program', 'begin', 'end', 'if', 'then', 'else',
    'while', 'do', 'for', 'to', 'downto', 'repeat',
    'until', 'case', 'of', 'var', 'const', 'type',
    'function', 'procedure', 'array', 'record', 'set',
    'file', 'packed', 'goto', 'label', 'with', 'nil',
    'true', 'false', 'not', 'and', 'or', 'div', 'mod', 'in'
}


# ==============================================================
#   ANALIZADOR SEMÁNTICO
# ==============================================================

class AnalizadorSemantico:

    def __init__(self, tokens_lista):
        self.tokens  = tokens_lista
        self.pos     = 0
        self.tabla   = TablaSimbolos()
        self.linea   = 1

    def token_actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def ver_siguiente(self, offset=1):
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return None

    def avanzar(self):
        if self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            if hasattr(tok, 'lineno'):
                self.linea = tok.lineno
            self.pos += 1
            return tok
        return None

    # ----------------------------------------------------------
    #   Leer tipo: INTEGER, REAL, BOOLEAN, CHAR, STRING, ARRAY, o ID
    # ----------------------------------------------------------

    def leer_tipo(self):
        tok = self.token_actual()
        if tok is None:
            return 'unknown'
        t = tok.type.lower()
        if t in ('integer', 'real', 'boolean', 'char', 'string'):
            self.avanzar()
            return t
        if t == 'array':
            self.avanzar()  # array
            # [ num .. num ]
            while self.token_actual() and self.token_actual().type != 'OF':
                self.avanzar()
            self.avanzar()  # OF
            tipo_base = self.leer_tipo()
            return f'array of {tipo_base}'
        if t == 'id':
            nombre = tok.value
            self.avanzar()
            return nombre.lower()
        return 'unknown'

    # ----------------------------------------------------------
    #   Leer lista de identificadores: a, b, c
    # ----------------------------------------------------------

    def leer_id_list(self):
        nombres = []
        tok = self.token_actual()
        if tok and tok.type == 'ID':
            nombres.append(tok.value)
            self.avanzar()
        while self.token_actual() and self.token_actual().type == 'COMMA':
            self.avanzar()  # ,
            tok = self.token_actual()
            if tok and tok.type == 'ID':
                nombres.append(tok.value)
                self.avanzar()
        return nombres

    # ----------------------------------------------------------
    #   Leer parámetros: (a, b: integer; c: real)
    # ----------------------------------------------------------

    def leer_params(self):
        params = []
        if self.token_actual() and self.token_actual().type == 'LPAR':
            self.avanzar()  # (
            while self.token_actual() and self.token_actual().type != 'RPAR':
                nombres = self.leer_id_list()
                if self.token_actual() and self.token_actual().type == 'COLON':
                    self.avanzar()  # :
                tipo = self.leer_tipo()
                for n in nombres:
                    params.append({'nombre': n, 'tipo': tipo})
                if self.token_actual() and self.token_actual().type == 'SEMICOLON':
                    self.avanzar()
            if self.token_actual() and self.token_actual().type == 'RPAR':
                self.avanzar()  # )
        return params

    # ----------------------------------------------------------
    #   Contar argumentos y verificar variables dentro de la llamada
    # ----------------------------------------------------------

    def contar_args_y_verificar(self, linea_llamada):
        if not self.token_actual() or self.token_actual().type != 'LPAR':
            return 0
        self.avanzar()  # (
        if self.token_actual() and self.token_actual().type == 'RPAR':
            self.avanzar()
            return 0
        count = 1
        profundidad = 0
        while self.token_actual():
            tok = self.token_actual()
            t = tok.type
            if t == 'LPAR':
                profundidad += 1
                self.avanzar()
            elif t == 'RPAR':
                if profundidad == 0:
                    self.avanzar()
                    break
                profundidad -= 1
                self.avanzar()
            elif t == 'COMMA' and profundidad == 0:
                count += 1
                self.avanzar()
            elif t == 'ID':
                nombre_arg = tok.value
                linea_arg  = tok.lineno
                sig = self.ver_siguiente()
                if sig and sig.type == 'LPAR':
                    # llamada anidada: registrar y consumir recursivamente
                    self.avanzar()
                    num_inner = self.contar_args_y_verificar(linea_arg)
                    if nombre_arg.lower() not in BUILTINS:
                        self.tabla.llamar_subprograma(nombre_arg, num_inner, linea_arg)
                else:
                    # uso de variable
                    self.tabla.usar_variable(nombre_arg, linea_arg)
                    self.avanzar()
            else:
                self.avanzar()
        return count

    # ==============================================================
    #   PRIMERA PASADA: recolectar declaraciones
    # ==============================================================

    def recolectar_declaraciones(self):
        while self.pos < len(self.tokens):
            tok = self.token_actual()
            if tok is None:
                break

            # CONST
            if tok.type == 'CONST':
                self.avanzar()
                while self.token_actual() and self.token_actual().type == 'ID':
                    nombre = self.token_actual().value
                    linea  = self.token_actual().lineno
                    self.avanzar()
                    if self.token_actual() and self.token_actual().type == 'EQ':
                        self.avanzar()
                        # leer valor: número o charconst
                        val_tok = self.token_actual()
                        tipo = 'integer'
                        if val_tok:
                            if val_tok.type == 'NUMBER':
                                tipo = 'real' if isinstance(val_tok.value, float) else 'integer'
                            elif val_tok.type == 'CHARCONST':
                                tipo = 'char' if len(str(val_tok.value)) == 3 else 'string'
                            self.avanzar()
                        if self.token_actual() and self.token_actual().type == 'SEMICOLON':
                            self.avanzar()
                        self.tabla.declarar_constante(nombre, tipo, linea)

            # TYPE
            elif tok.type == 'TYPE':
                self.avanzar()
                while self.token_actual() and self.token_actual().type == 'ID':
                    nombre = self.token_actual().value
                    linea  = self.token_actual().lineno
                    self.avanzar()
                    if self.token_actual() and self.token_actual().type == 'EQ':
                        self.avanzar()
                        definicion = self.leer_tipo()
                        if self.token_actual() and self.token_actual().type == 'SEMICOLON':
                            self.avanzar()
                        self.tabla.declarar_tipo(nombre, definicion, linea)

            # VAR
            elif tok.type == 'VAR':
                self.avanzar()
                # Una declaración VAR válida siempre tiene la forma: ID {, ID} : TIPO ;
                # Si después del ID no viene COMMA ni COLON, ya salimos de la sección VAR
                while self.token_actual() and self.token_actual().type == 'ID':
                    # Verificar que la declaración tenga COLON antes de registrar
                    # Buscar si hay un COLON en los próximos tokens (antes de SEMICOLON/BEGIN)
                    tiene_colon = False
                    offset = 1
                    while self.ver_siguiente(offset) is not None:
                        t = self.ver_siguiente(offset).type
                        if t == 'COLON':
                            tiene_colon = True
                            break
                        if t in ('SEMICOLON', 'BEGIN', 'FUNCTION', 'PROCEDURE',
                                 'VAR', 'CONST', 'TYPE', 'END', 'ASSIGN'):
                            break
                        offset += 1
                    if not tiene_colon:
                        break  # no es una declaración VAR válida, salir
                    nombres = self.leer_id_list()
                    linea   = self.linea
                    if self.token_actual() and self.token_actual().type == 'COLON':
                        self.avanzar()
                    tipo = self.leer_tipo()
                    if self.token_actual() and self.token_actual().type == 'SEMICOLON':
                        self.avanzar()
                    for n in nombres:
                        self.tabla.declarar_variable(n, tipo, linea)

            # FUNCTION
            elif tok.type == 'FUNCTION':
                linea = tok.lineno
                self.avanzar()
                nombre_tok = self.token_actual()
                if nombre_tok and nombre_tok.type == 'ID':
                    nombre = nombre_tok.value
                    self.avanzar()
                    params = self.leer_params()
                    tipo_ret = 'unknown'
                    if self.token_actual() and self.token_actual().type == 'COLON':
                        self.avanzar()
                        tipo_ret = self.leer_tipo()
                    self.tabla.declarar_funcion(nombre, params, tipo_ret, linea)
                    # Leer el VAR interno de la función y guardarlo en vars_locales
                    self._leer_vars_locales(nombre)

            # PROCEDURE
            elif tok.type == 'PROCEDURE':
                linea = tok.lineno
                self.avanzar()
                nombre_tok = self.token_actual()
                if nombre_tok and nombre_tok.type == 'ID':
                    nombre = nombre_tok.value
                    self.avanzar()
                    params = self.leer_params()
                    self.tabla.declarar_procedimiento(nombre, params, linea)
                    # Leer el VAR interno del procedimiento y guardarlo en vars_locales
                    self._leer_vars_locales(nombre)

            else:
                self.avanzar()

    # ==============================================================
    #   SEGUNDA PASADA: verificar uso
    # ==============================================================

    def verificar_uso(self):
        while self.pos < len(self.tokens):
            tok = self.token_actual()
            if tok is None:
                break

            # Saltar el nombre del programa (PROGRAM NombrePrograma ;)
            if tok.type == 'PROGRAM':
                self.avanzar()  # PROGRAM
                self.avanzar()  # nombre
                continue

            # Variable usada (lado derecho o condición)
            if tok.type == 'ID':
                nombre   = tok.value
                linea    = tok.lineno
                sig      = self.ver_siguiente()

                # Llamada a función o procedimiento
                if sig and sig.type == 'LPAR':
                    self.avanzar()  # nombre de la función
                    num_args = self.contar_args_y_verificar(linea)
                    if nombre.lower() not in BUILTINS:
                        self.tabla.llamar_subprograma(nombre, num_args, linea)
                    continue

                # Asignación: validar LHS y avanzar; el RHS lo procesa la siguiente iteración
                if sig and sig.type == 'ASSIGN':
                    self.avanzar()  # nombre
                    self.avanzar()  # :=
                    info = self.tabla.buscar_variable(nombre)
                    if info is None and nombre.lower() not in self.tabla.funciones:
                        self.tabla.errores.append(
                            f"Error en línea {linea}: Variable '{nombre}' usada sin declarar"
                        )
                    continue

                # Uso normal de variable
                info = self.tabla.buscar_variable(nombre)
                if info is not None:
                    self.tabla.usar_variable(nombre, linea)
                elif nombre.lower() not in self.tabla.funciones \
                     and nombre.lower() not in self.tabla.procedimientos \
                     and nombre.lower() not in self.tabla.constantes \
                     and nombre.lower() not in self.tabla.tipos \
                     and nombre.lower() not in BUILTINS \
                     and nombre.lower() not in PALABRAS_ESTRUCTURA:
                    self.tabla.usar_variable(nombre, linea)

            # FOR: verificar variable de control
            elif tok.type == 'FOR':
                self.avanzar()
                var_tok = self.token_actual()
                if var_tok and var_tok.type == 'ID':
                    info = self.tabla.buscar_variable(var_tok.value)
                    if info is None:
                        self.tabla.errores.append(
                            f"Error en línea {var_tok.lineno}: "
                            f"Variable de control '{var_tok.value}' no declarada"
                        )
                    elif info['tipo'] not in ('integer', 'char', 'error', 'unknown'):
                        self.tabla.errores.append(
                            f"Error en línea {var_tok.lineno}: "
                            f"La variable de control '{var_tok.value}' debe ser integer o char"
                        )
                continue

            self.avanzar()

    # ==============================================================
    #   VARIABLES LOCALES DE SUBPROGRAMAS
    # ==============================================================

    def _leer_vars_locales(self, nombre_subprog):
        """Lee el bloque VAR que sigue a un FUNCTION o PROCEDURE y lo guarda."""
        # Avanzar hasta el SEMICOLON que cierra la cabecera
        while self.token_actual() and self.token_actual().type != 'SEMICOLON':
            self.avanzar()
        if self.token_actual():
            self.avanzar()  # saltar ;
        # Ahora puede venir VAR
        if self.token_actual() and self.token_actual().type == 'VAR':
            self.avanzar()  # VAR
            locales = {}
            while self.token_actual() and self.token_actual().type == 'ID':
                # Verificar que hay COLON (declaración válida)
                tiene_colon = False
                offset = 1
                while self.ver_siguiente(offset) is not None:
                    t = self.ver_siguiente(offset).type
                    if t == 'COLON':
                        tiene_colon = True
                        break
                    if t in ('SEMICOLON', 'BEGIN', 'FUNCTION', 'PROCEDURE',
                             'VAR', 'CONST', 'TYPE', 'END', 'ASSIGN'):
                        break
                    offset += 1
                if not tiene_colon:
                    break
                nombres = self.leer_id_list()
                linea_v = self.linea
                if self.token_actual() and self.token_actual().type == 'COLON':
                    self.avanzar()
                tipo = self.leer_tipo()
                if self.token_actual() and self.token_actual().type == 'SEMICOLON':
                    self.avanzar()
                for n in nombres:
                    locales[n.lower()] = {'tipo': tipo, 'linea': linea_v, 'usada': False}
                    self.tabla.declarar_variable(n, tipo, linea_v)
            self.tabla.vars_locales[nombre_subprog.lower()] = locales

    # ==============================================================
    #   ANÁLISIS COMPLETO
    # ==============================================================

    def analizar(self):
        print("Iniciando análisis semántico...")
        print("=" * 60)

        self.recolectar_declaraciones()

        self.pos   = 0
        self.linea = 1
        self.verificar_uso()

        self.generar_reporte()

    # ==============================================================
    #   REPORTE FINAL
    # ==============================================================

    def generar_reporte(self):
        errores     = self.tabla.errores
        advertencias = self.tabla.advertencias

        print("\nRESUMEN DEL ANÁLISIS SEMÁNTICO")
        print("=" * 60)
        print(f"Errores semánticos encontrados:  {len(errores)}")
        print(f"Advertencias encontradas:        {len(advertencias)}")

        if not errores and not advertencias:
            print("\n[OK] ANÁLISIS SEMÁNTICO EXITOSO")
            print("El código es semánticamente correcto.")
        else:
            if errores:
                print(f"\n[ERROR] SE ENCONTRARON {len(errores)} ERROR(ES) SEMÁNTICO(S)\n")
                for i, e in enumerate(errores, 1):
                    print(f"  {i}. {e}")
            if advertencias:
                print(f"\n[WARNING] SE ENCONTRARON {len(advertencias)} ADVERTENCIA(S)\n")
                for i, a in enumerate(advertencias, 1):
                    print(f"  {i}. {a}")

        print("\n" + "=" * 60)
        print("INFORMACIÓN DE LA TABLA DE SÍMBOLOS")
        print("=" * 60)

        # Variables globales
        vars_globales = self.tabla.scopes[0]
        print(f"\nVariables globales declaradas: {len(vars_globales)}")
        for nombre, info in vars_globales.items():
            estado = "✓ usada" if info.get('usada') else "✗ no usada"
            print(f"  - {nombre} : {info['tipo']} [{estado}] (línea {info['linea']})")

        # Constantes
        print(f"\nConstantes declaradas: {len(self.tabla.constantes)}")
        for nombre, info in self.tabla.constantes.items():
            print(f"  - {nombre} : {info['tipo']} (línea {info['linea']})")

        # Tipos
        print(f"\nTipos declarados: {len(self.tabla.tipos)}")
        for nombre, info in self.tabla.tipos.items():
            print(f"  - {nombre} = {info['definicion']} (línea {info['linea']})")

        # Funciones
        print(f"\nFunciones declaradas: {len(self.tabla.funciones)}")
        for nombre, info in self.tabla.funciones.items():
            estado = "✓ usada" if info['usada'] else "✗ no usada"
            params_str = ', '.join(f"{p['nombre']}: {p['tipo']}" for p in info['params'])
            print(f"  - {nombre}({params_str}) : {info['tipo']} [{estado}] (línea {info['linea']})")
            # Variables locales de la función (declaradas en su VAR interno)
            vars_locales = self.tabla.vars_locales.get(nombre.lower(), {})
            if vars_locales:
                for vnom, vinfo in vars_locales.items():
                    # Leer el estado real desde el scope global (ahí las marca usar_variable)
                    info_global = self.tabla.scopes[0].get(vnom)
                    usada_real = info_global['usada'] if info_global else vinfo.get('usada', False)
                    estado_v = "✓ usada" if usada_real else "✗ no usada"
                    print(f"      var {vnom} : {vinfo['tipo']} [{estado_v}] (línea {vinfo['linea']})")

        # Procedimientos
        print(f"\nProcedimientos declarados: {len(self.tabla.procedimientos)}")
        for nombre, info in self.tabla.procedimientos.items():
            estado = "✓ usado" if info['usado'] else "✗ no usado"
            params_str = ', '.join(f"{p['nombre']}: {p['tipo']}" for p in info['params'])
            print(f"  - {nombre}({params_str}) [{estado}] (línea {info['linea']})")
            vars_locales = self.tabla.vars_locales.get(nombre.lower(), {})
            if vars_locales:
                for vnom, vinfo in vars_locales.items():
                    info_global = self.tabla.scopes[0].get(vnom)
                    usada_real = info_global['usada'] if info_global else vinfo.get('usada', False)
                    estado_v = "✓ usada" if usada_real else "✗ no usada"
                    print(f"      var {vnom} : {vinfo['tipo']} [{estado_v}] (línea {vinfo['linea']})")

        print("=" * 60)


# ==============================================================
#   TOKENIZAR EL ARCHIVO
# ==============================================================

def tokenizar(filename):
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
        pascal_lexer.lexer.input(data)
        pascal_lexer.lexer.lineno = 1
        tokens = []
        while True:
            tok = pascal_lexer.lexer.token()
            if not tok:
                break
            tokens.append(tok)
        return tokens, len(data.splitlines())
    except FileNotFoundError:
        print(f"ERROR: Archivo '{filename}' no encontrado")
        return None, 0


# ==============================================================
#   MAIN
# ==============================================================

if __name__ == '__main__':

    if len(sys.argv) > 1:
        fin = sys.argv[1]
    else:
        fin = 'input.pas'

    print(f"Analizando archivo: {fin}")
    print("=" * 60)

    tokens, total_lineas = tokenizar(fin)
    if tokens is None:
        sys.exit(1)

    print(f"Total de tokens:  {len(tokens)}")
    print(f"Total de líneas:  {total_lineas}")
    print("=" * 60)

    # --- Paso 1: verificar sintaxis ---
    # Si hay errores sintácticos no tiene sentido analizar semántica
    with open(fin, 'r', encoding='utf-8', errors='ignore') as f:
        data = f.read()

    pascal_lexer.lexer_errors = []
    pascal_lexer.lexer.lineno = 1
    pascal_parser.errors_list.clear()
    pascal_parser.parser.parse(data, lexer=pascal_lexer.lexer, tracking=True)

    errores_sintacticos = pascal_lexer.lexer_errors + pascal_parser.errors_list
    if errores_sintacticos:
        print(f"\n[!] Se encontraron {len(errores_sintacticos)} error(es) sintáctico(s):")
        for i, e in enumerate(errores_sintacticos, 1):
            print(f"  {i}. {e}")
        print()

    # --- Paso 2: análisis semántico ---
    pascal_lexer.lexer.lineno = 1
    analizador = AnalizadorSemantico(tokens)
    analizador.analizar()