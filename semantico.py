"""
Analizador Semántico para Pascal — versión extendida
Dos pasadas sobre los tokens:
  1. Recolectar declaraciones (variables, funciones, procedimientos, tipos, constantes)
  2. Verificar uso correcto (variables no declaradas, tipos incompatibles,
     argumentos incorrectos, variables no usadas, etc.)

Verificaciones añadidas respecto a la versión base:
  - Incompatibilidad de tipos en asignaciones  (integer := string, etc.)
  - Incompatibilidad de tipos en operaciones   (string + integer, etc.)
  - Variables declaradas pero nunca usadas     → advertencia
  - Funciones/procedimientos declarados pero nunca llamados → advertencia
  - Uso de variable antes de ser inicializada  → advertencia (best-effort)
  - Retorno de función no asignado             → advertencia
"""

import sys
import lexer as pascal_lexer
import parser as pascal_parser


# ==============================================================
#   COMPATIBILIDAD DE TIPOS
# ==============================================================

# Tipos escalares reconocidos (en minúsculas)
TIPOS_ESCALARES = {'integer', 'real', 'boolean', 'char', 'string'}

# Tabla de compatibilidad para asignación:
#   asignable[destino][origen] = True  →  OK
#   Si el par no aparece              →  incompatible
ASIGNABLE = {
    'integer': {'integer'},
    'real':    {'real', 'integer'},   # integer cabe en real (promoción implícita)
    'boolean': {'boolean'},
    'char':    {'char'},
    'string':  {'string', 'char'},    # char cabe en string
}

# Tabla de resultado de operaciones aritméticas/lógicas:
#   resultado_op[izq][der] = tipo_resultado
RESULTADO_OP = {
    ('integer', 'integer'): 'integer',
    ('integer', 'real'):    'real',
    ('real',    'integer'): 'real',
    ('real',    'real'):    'real',
    ('boolean', 'boolean'): 'boolean',
    ('char',    'char'):    'char',
    ('string',  'string'):  'string',
    ('string',  'char'):    'string',
    ('char',    'string'):  'string',
}

def son_compatibles_asignacion(tipo_destino, tipo_origen):
    """Devuelve True si tipo_origen puede asignarse a tipo_destino."""
    td = tipo_destino.lower() if tipo_destino else 'unknown'
    to = tipo_origen.lower()  if tipo_origen  else 'unknown'
    if 'unknown' in (td, to) or 'error' in (td, to):
        return True   # no reportar si alguno es desconocido
    if td not in TIPOS_ESCALARES or to not in TIPOS_ESCALARES:
        return True   # tipos de usuario / arrays: no verificar
    return to in ASIGNABLE.get(td, set())

def _merge_tipos(t1, t2):
    """Combina dos tipos parciales en la inferencia del RHS."""
    if t1 == 'unknown':
        return t2
    if t2 == 'unknown':
        return t1
    if t1 == t2:
        return t1
    resultado = tipo_resultado_op(t1, t2)
    return resultado if resultado != 'error' else t1   # conservador ante conflicto


def tipo_resultado_op(tipo_izq, tipo_der):
    """Devuelve el tipo resultado de una operación binaria, o 'error'."""
    ti = (tipo_izq or 'unknown').lower()
    td = (tipo_der or 'unknown').lower()
    if 'unknown' in (ti, td) or 'error' in (ti, td):
        return 'unknown'
    return RESULTADO_OP.get((ti, td), 'error')


# ==============================================================
#   TABLA DE SÍMBOLOS
# ==============================================================

class TablaSimbolos:

    def __init__(self):
        self.scopes         = [{}]  # pila de scopes; [0] = global
        self.funciones      = {}    # {nombre: {params, tipo_retorno, linea, usada}}
        self.procedimientos = {}    # {nombre: {params, linea, usado}}
        self.tipos          = {}    # tipos definidos con TYPE
        self.constantes     = {}    # constantes definidas con CONST
        self.vars_locales   = {}    # {nombre_func: {nombre_var: info}}
        self.errores        = []
        self.advertencias   = []

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
            scope[clave] = {
                'clase': 'var', 'tipo': tipo,
                'linea': linea, 'usada': False, 'inicializada': False
            }

    def usar_variable(self, nombre, linea):
        clave = nombre.lower()
        for scope in reversed(self.scopes):
            if clave in scope:
                scope[clave]['usada'] = True
                return scope[clave]['tipo']
        # Puede ser parámetro de función/procedimiento (los params se marcan como 'unknown')
        for info in list(self.funciones.values()) + list(self.procedimientos.values()):
            if clave in [p['nombre'].lower() for p in info.get('params', [])]:
                return 'unknown'
        self.errores.append(
            f"Error en línea {linea}: Variable '{nombre}' usada sin declarar"
        )
        return 'error'

    def asignar_variable(self, nombre, tipo_rhs, linea):
        """Marca la variable como inicializada y verifica compatibilidad de tipos."""
        clave = nombre.lower()
        for scope in reversed(self.scopes):
            if clave in scope:
                scope[clave]['usada']       = True
                scope[clave]['inicializada'] = True
                tipo_dest = scope[clave]['tipo']
                if not son_compatibles_asignacion(tipo_dest, tipo_rhs):
                    self.errores.append(
                        f"Error en línea {linea}: Incompatibilidad de tipos — "
                        f"no se puede asignar '{tipo_rhs}' a '{nombre}' (tipo '{tipo_dest}')"
                    )
                return scope[clave]['tipo']
        # Puede ser retorno de función (nombre == nombre_función)
        if clave in self.funciones:
            return self.funciones[clave]['tipo']
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
                'linea': linea, 'usada': False,
                'retorno_asignado': False
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
            return 'unknown'
        if clave in self.funciones:
            self.funciones[clave]['usada'] = True
            esperados = len(self.funciones[clave]['params'])
            if num_args != esperados:
                self.errores.append(
                    f"Error en línea {linea}: '{nombre}' espera {esperados} "
                    f"argumento(s), se llamó con {num_args}"
                )
            return self.funciones[clave]['tipo']
        elif clave in self.procedimientos:
            self.procedimientos[clave]['usado'] = True
            esperados = len(self.procedimientos[clave]['params'])
            if num_args != esperados:
                self.errores.append(
                    f"Error en línea {linea}: '{nombre}' espera {esperados} "
                    f"argumento(s), se llamó con {num_args}"
                )
            return 'void'
        else:
            self.errores.append(
                f"Error en línea {linea}: '{nombre}' no está declarado"
            )
            return 'error'

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

    # ----------------------------------------------------------
    #   Advertencias post-análisis
    # ----------------------------------------------------------

    def generar_advertencias_uso(self):
        """Variables, funciones y procedimientos declarados pero nunca usados."""
        for nombre, info in self.scopes[0].items():
            if not info.get('usada'):
                self.advertencias.append(
                    f"Advertencia en línea {info['linea']}: "
                    f"Variable '{nombre}' declarada pero nunca usada"
                )
        for nombre, info in self.funciones.items():
            if not info['usada']:
                self.advertencias.append(
                    f"Advertencia en línea {info['linea']}: "
                    f"Función '{nombre}' declarada pero nunca llamada"
                )
        for nombre, info in self.procedimientos.items():
            if not info['usado']:
                self.advertencias.append(
                    f"Advertencia en línea {info['linea']}: "
                    f"Procedimiento '{nombre}' declarado pero nunca llamado"
                )


# ==============================================================
#   BUILT-INS de Pascal
# ==============================================================

BUILTINS = {
    'writeln', 'write', 'readln', 'read', 'new', 'dispose',
    'length', 'copy', 'concat', 'pos', 'chr', 'ord',
    'abs', 'sqr', 'sqrt', 'trunc', 'round', 'succ', 'pred',
    'odd', 'eof', 'eoln', 'reset', 'rewrite', 'close',
    'upcase', 'lowercase', 'str', 'val'
}

PALABRAS_ESTRUCTURA = {
    'program', 'begin', 'end', 'if', 'then', 'else',
    'while', 'do', 'for', 'to', 'downto', 'repeat',
    'until', 'case', 'of', 'var', 'const', 'type',
    'function', 'procedure', 'array', 'record', 'set',
    'file', 'packed', 'goto', 'label', 'with', 'nil',
    'true', 'false', 'not', 'and', 'or', 'div', 'mod', 'in'
}

# Tipos que devuelven los literales
TIPO_LITERAL = {
    'NUMBER':    None,        # se resuelve en tiempo de análisis
    'CHARCONST': None,
    'NIL':       'pointer',
}


# ==============================================================
#   ANALIZADOR SEMÁNTICO
# ==============================================================

class AnalizadorSemantico:

    def __init__(self, tokens_lista):
        self.tokens = tokens_lista
        self.pos    = 0
        self.tabla  = TablaSimbolos()
        self.linea  = 1

    # ----------------------------------------------------------
    #   Navegación básica
    # ----------------------------------------------------------

    def token_actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def ver_siguiente(self, offset=1):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def avanzar(self):
        if self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            if hasattr(tok, 'lineno'):
                self.linea = tok.lineno
            self.pos += 1
            return tok
        return None

    # ----------------------------------------------------------
    #   Tipo de un token literal (NUMBER, CHARCONST)
    # ----------------------------------------------------------

    def tipo_de_literal(self, tok):
        if tok.type == 'NUMBER':
            return 'real' if isinstance(tok.value, float) else 'integer'
        if tok.type == 'CHARCONST':
            # 'x' → char,  'hola' → string
            raw = str(tok.value)
            inner = raw[1:-1].replace("''", "'")
            return 'char' if len(inner) == 1 else 'string'
        return 'unknown'

    # ----------------------------------------------------------
    #   Leer tipo
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
            self.avanzar()
            while self.token_actual() and self.token_actual().type != 'OF':
                self.avanzar()
            self.avanzar()  # OF
            tipo_base = self.leer_tipo()
            return f'array of {tipo_base}'
        if t == 'record':
            self.avanzar()
            depth = 1
            while self.token_actual():
                tt = self.token_actual().type.lower()
                if tt == 'record':
                    depth += 1
                elif tt == 'end':
                    depth -= 1
                    if depth == 0:
                        self.avanzar()
                        break
                self.avanzar()
            return 'record'
        if t == 'set':
            self.avanzar()  # set
            if self.token_actual() and self.token_actual().type == 'OF':
                self.avanzar()
                self.leer_tipo()
            return 'set'
        if t == 'file':
            self.avanzar()
            if self.token_actual() and self.token_actual().type == 'OF':
                self.avanzar()
                self.leer_tipo()
            return 'file'
        if t == 'packed':
            self.avanzar()
            return self.leer_tipo()
        if t == 'id':
            nombre = tok.value
            self.avanzar()
            return nombre.lower()
        return 'unknown'

    # ----------------------------------------------------------
    #   Leer lista de identificadores
    # ----------------------------------------------------------

    def leer_id_list(self):
        nombres = []
        tok = self.token_actual()
        if tok and tok.type == 'ID':
            nombres.append(tok.value)
            self.avanzar()
        while self.token_actual() and self.token_actual().type == 'COMMA':
            self.avanzar()
            tok = self.token_actual()
            if tok and tok.type == 'ID':
                nombres.append(tok.value)
                self.avanzar()
        return nombres

    # ----------------------------------------------------------
    #   Leer parámetros de función/procedimiento
    # ----------------------------------------------------------

    def leer_params(self):
        params = []
        if self.token_actual() and self.token_actual().type == 'LPAR':
            self.avanzar()
            while self.token_actual() and self.token_actual().type != 'RPAR':
                nombres = self.leer_id_list()
                if self.token_actual() and self.token_actual().type == 'COLON':
                    self.avanzar()
                tipo = self.leer_tipo()
                for n in nombres:
                    params.append({'nombre': n, 'tipo': tipo})
                if self.token_actual() and self.token_actual().type == 'SEMICOLON':
                    self.avanzar()
            if self.token_actual() and self.token_actual().type == 'RPAR':
                self.avanzar()
        return params

    # ----------------------------------------------------------
    #   Contar argumentos y verificar usos dentro de una llamada
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
            t   = tok.type
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
                    self.avanzar()
                    num_inner = self.contar_args_y_verificar(linea_arg)
                    if nombre_arg.lower() not in BUILTINS:
                        self.tabla.llamar_subprograma(nombre_arg, num_inner, linea_arg)
                else:
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

            # ---------- CONST ----------
            if tok.type == 'CONST':
                self.avanzar()
                while self.token_actual() and self.token_actual().type == 'ID':
                    nombre = self.token_actual().value
                    linea  = self.token_actual().lineno
                    self.avanzar()
                    if self.token_actual() and self.token_actual().type == 'EQ':
                        self.avanzar()
                    val_tok = self.token_actual()
                    tipo = 'integer'
                    if val_tok:
                        tipo = self.tipo_de_literal(val_tok) if val_tok.type in ('NUMBER','CHARCONST') else 'unknown'
                        self.avanzar()
                    if self.token_actual() and self.token_actual().type == 'SEMICOLON':
                        self.avanzar()
                    self.tabla.declarar_constante(nombre, tipo, linea)

            # ---------- TYPE ----------
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

            # ---------- VAR ----------
            elif tok.type == 'VAR':
                self.avanzar()
                while self.token_actual() and self.token_actual().type == 'ID':
                    # Verificar que hay COLON antes de SEMICOLON/BEGIN/etc.
                    tiene_colon = False
                    offset = 1
                    while self.ver_siguiente(offset) is not None:
                        t2 = self.ver_siguiente(offset).type
                        if t2 == 'COLON':
                            tiene_colon = True
                            break
                        if t2 in ('SEMICOLON', 'BEGIN', 'FUNCTION', 'PROCEDURE',
                                  'VAR', 'CONST', 'TYPE', 'END', 'ASSIGN'):
                            break
                        offset += 1
                    if not tiene_colon:
                        break
                    nombres = self.leer_id_list()
                    linea   = self.linea
                    if self.token_actual() and self.token_actual().type == 'COLON':
                        self.avanzar()
                    tipo = self.leer_tipo()
                    if self.token_actual() and self.token_actual().type == 'SEMICOLON':
                        self.avanzar()
                    for n in nombres:
                        self.tabla.declarar_variable(n, tipo, linea)

            # ---------- FUNCTION ----------
            elif tok.type == 'FUNCTION':
                linea = tok.lineno
                self.avanzar()
                nombre_tok = self.token_actual()
                if nombre_tok and nombre_tok.type == 'ID':
                    nombre = nombre_tok.value
                    self.avanzar()
                    params   = self.leer_params()
                    tipo_ret = 'unknown'
                    if self.token_actual() and self.token_actual().type == 'COLON':
                        self.avanzar()
                        tipo_ret = self.leer_tipo()
                    self.tabla.declarar_funcion(nombre, params, tipo_ret, linea)
                    self._leer_vars_locales(nombre)
                    # Saltar el cuerpo (BEGIN...END) para no confundir
                    # expresiones internas con llamadas en la 1ra pasada
                    self._saltar_cuerpo()

            # ---------- PROCEDURE ----------
            elif tok.type == 'PROCEDURE':
                linea = tok.lineno
                self.avanzar()
                nombre_tok = self.token_actual()
                if nombre_tok and nombre_tok.type == 'ID':
                    nombre = nombre_tok.value
                    self.avanzar()
                    params = self.leer_params()
                    self.tabla.declarar_procedimiento(nombre, params, linea)
                    self._leer_vars_locales(nombre)
                    self._saltar_cuerpo()

            else:
                self.avanzar()

    # ==============================================================
    #   SEGUNDA PASADA: verificar uso y tipos
    # ==============================================================

    def verificar_uso(self):
        while self.pos < len(self.tokens):
            tok = self.token_actual()
            if tok is None:
                break

            # Saltar nombre del programa
            if tok.type == 'PROGRAM':
                self.avanzar()
                self.avanzar()
                continue

            # Saltar declaraciones de FUNCTION/PROCEDURE en la 2da pasada
            # El ID que sigue al keyword es el nombre, no un uso
            if tok.type in ('FUNCTION', 'PROCEDURE'):
                self.avanzar()  # keyword
                if self.token_actual() and self.token_actual().type == 'ID':
                    self.avanzar()  # nombre del subprograma — NO es un uso
                # Saltar hasta el BEGIN del cuerpo y consumirlo completo
                # para que los parámetros y el cuerpo no se procesen como usos globales
                self._saltar_cuerpo_verificacion()
                continue

            # Saltar secciones VAR/CONST/TYPE (declaraciones, no usos)
            if tok.type in ('VAR', 'CONST', 'TYPE'):
                self._saltar_seccion_declaracion(tok.type)
                continue

            if tok.type == 'ID':
                nombre = tok.value
                linea  = tok.lineno
                sig    = self.ver_siguiente()

                # --- Llamada a función/procedimiento ---
                if sig and sig.type == 'LPAR':
                    self.avanzar()
                    num_args = self.contar_args_y_verificar(linea)
                    if nombre.lower() not in BUILTINS:
                        self.tabla.llamar_subprograma(nombre, num_args, linea)
                    continue

                # --- Asignación: variable := expresion ---
                if sig and sig.type == 'ASSIGN':
                    self.avanzar()  # nombre
                    self.avanzar()  # :=
                    tipo_rhs = self._tipo_expresion_simple(linea)

                    # ¿Es retorno de función?
                    if nombre.lower() in self.tabla.funciones:
                        tipo_func = self.tabla.funciones[nombre.lower()]['tipo']
                        self.tabla.funciones[nombre.lower()]['retorno_asignado'] = True
                        if not son_compatibles_asignacion(tipo_func, tipo_rhs):
                            self.tabla.errores.append(
                                f"Error en línea {linea}: Retorno de función '{nombre}' "
                                f"(tipo '{tipo_func}') incompatible con valor '{tipo_rhs}'"
                            )
                    else:
                        self.tabla.asignar_variable(nombre, tipo_rhs, linea)
                    continue

                # --- Uso de variable normal ---
                info = self.tabla.buscar_variable(nombre)
                if info is not None:
                    self.tabla.usar_variable(nombre, linea)
                elif (nombre.lower() not in self.tabla.funciones
                      and nombre.lower() not in self.tabla.procedimientos
                      and nombre.lower() not in self.tabla.constantes
                      and nombre.lower() not in self.tabla.tipos
                      and nombre.lower() not in BUILTINS
                      and nombre.lower() not in PALABRAS_ESTRUCTURA):
                    self.tabla.usar_variable(nombre, linea)

            # --- FOR: verificar variable de control ---
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
                            f"La variable de control '{var_tok.value}' debe ser integer o char, "
                            f"pero es '{info['tipo']}'"
                        )
                    # Avanzar sobre la variable de control para que el handler
                    # general de ID no la reporte de nuevo como "sin declarar"
                    self.avanzar()
                continue

            self.avanzar()

    # ----------------------------------------------------------
    #   Inferir tipo de una expresión simple después de :=
    #   (avanza sobre los tokens del RHS hasta el siguiente ; END ELSE etc.)
    # ----------------------------------------------------------

    def _tipo_expresion_simple(self, linea_asig):
        """
        Avanza consumiendo el RHS de una asignación e intenta inferir su tipo.
        Termina cuando encuentra SEMICOLON, END, ELSE, THEN, DO, UNTIL, o un token
        que no forme parte de una expresión.
        """
        TERMINADORES = {
            'SEMICOLON', 'END', 'ELSE', 'THEN', 'DO', 'UNTIL',
            'BEGIN', 'VAR', 'CONST', 'TYPE', 'FUNCTION', 'PROCEDURE',
        }
        tipo_actual = 'unknown'
        profundidad = 0

        while self.token_actual():
            tok = self.token_actual()
            t   = tok.type

            if t in TERMINADORES and profundidad == 0:
                break

            if t == 'LPAR':
                profundidad += 1
                self.avanzar()
            elif t == 'RPAR':
                if profundidad == 0:
                    break
                profundidad -= 1
                self.avanzar()
            elif t == 'NUMBER':
                nuevo = self.tipo_de_literal(tok)
                tipo_actual = _merge_tipos(tipo_actual, nuevo)
                self.avanzar()
            elif t == 'CHARCONST':
                nuevo = self.tipo_de_literal(tok)
                tipo_actual = _merge_tipos(tipo_actual, nuevo)
                self.avanzar()
            elif t == 'ID':
                nombre = tok.value
                linea  = tok.lineno
                sig    = self.ver_siguiente()
                if sig and sig.type == 'LPAR':
                    # llamada a función dentro de expresión
                    self.avanzar()
                    num_inner = self.contar_args_y_verificar(linea)
                    if nombre.lower() in BUILTINS:
                        nuevo = 'unknown'
                    else:
                        nuevo = self.tabla.llamar_subprograma(nombre, num_inner, linea)
                    tipo_actual = _merge_tipos(tipo_actual, nuevo)
                else:
                    nuevo = self.tabla.usar_variable(nombre, linea)
                    tipo_actual = _merge_tipos(tipo_actual, nuevo)
                    self.avanzar()
            elif t in ('PLUS', 'MINUS', 'TIMES', 'DIVISION', 'DIV', 'MOD',
                       'AND', 'OR', 'NOT', 'EQ', 'NE', 'LT', 'GT', 'LE', 'GE',
                       'IN', 'LBR', 'RBR', 'RANGE', 'COMMA', 'DOT', 'NIL'):
                self.avanzar()
            else:
                # token inesperado → parar
                break

        return tipo_actual

    # ==============================================================
    #   VARIABLES LOCALES DE SUBPROGRAMAS
    # ==============================================================

    def _leer_vars_locales(self, nombre_subprog):
        """Lee el bloque VAR que sigue a FUNCTION/PROCEDURE.
        Deja el cursor justo EN el token BEGIN para que _saltar_cuerpo lo consuma."""
        # Saltar hasta el ; que cierra la cabecera (tipo_retorno ya fue consumido)
        while self.token_actual() and self.token_actual().type != 'SEMICOLON':
            self.avanzar()
        if self.token_actual():
            self.avanzar()  # consumir ;
        # Leer sección VAR local si existe
        locales = {}
        if self.token_actual() and self.token_actual().type == 'VAR':
            self.avanzar()  # consumir VAR
            while self.token_actual() and self.token_actual().type == 'ID':
                # Verificar que hay COLON (declaración válida)
                tiene_colon = False
                offset = 1
                while self.ver_siguiente(offset) is not None:
                    t2 = self.ver_siguiente(offset).type
                    if t2 == 'COLON':
                        tiene_colon = True
                        break
                    if t2 in ('SEMICOLON', 'BEGIN', 'FUNCTION', 'PROCEDURE',
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
        # El cursor ahora apunta a BEGIN (o directo al cuerpo sin VAR)
        # _saltar_cuerpo lo consumirá desde aquí

    # ==============================================================
    #   SALTAR CUERPO DE SUBPROGRAMA (BEGIN...END)
    #   Usado en la 1ra pasada para no confundir el interior
    #   de funciones/procedimientos con llamadas globales.
    # ==============================================================

    def _saltar_cuerpo(self):
        """Consume el BEGIN...END del cuerpo de un subprograma.
        El cursor debe estar apuntando al token BEGIN al entrar."""
        # Avanzar solo si todavía no llegamos al BEGIN
        # (puede haber un LABEL antes en casos raros)
        while self.token_actual() and self.token_actual().type not in ('BEGIN', 'FUNCTION', 'PROCEDURE', 'END'):
            self.avanzar()
        if not self.token_actual() or self.token_actual().type != 'BEGIN':
            return  # no hay cuerpo o ya estamos más allá
        self.avanzar()  # consumir BEGIN
        depth = 1
        while self.token_actual() and depth > 0:
            t = self.token_actual().type
            if t == 'BEGIN':
                depth += 1
            elif t == 'END':
                depth -= 1
            self.avanzar()
        # después del END del subprograma viene ; — consumirlo
        if self.token_actual() and self.token_actual().type == 'SEMICOLON':
            self.avanzar()

    # ==============================================================
    #   HELPERS PARA LA SEGUNDA PASADA
    # ==============================================================

    def _saltar_cuerpo_verificacion(self):
        """Igual que _saltar_cuerpo pero usado en la 2da pasada:
        salta parámetros y cuerpo completo de un subprograma para que
        sus tokens internos no se confundan con usos globales."""
        # Saltar parámetros (dentro de paréntesis)
        if self.token_actual() and self.token_actual().type == 'LPAR':
            depth = 1
            self.avanzar()
            while self.token_actual() and depth > 0:
                if self.token_actual().type == 'LPAR':
                    depth += 1
                elif self.token_actual().type == 'RPAR':
                    depth -= 1
                self.avanzar()
        # Saltar tipo de retorno (FUNCTION) y ; de cabecera
        while self.token_actual() and self.token_actual().type not in ('BEGIN', 'VAR', 'FUNCTION', 'PROCEDURE'):
            self.avanzar()
        # Saltar VAR local si existe
        if self.token_actual() and self.token_actual().type == 'VAR':
            while self.token_actual() and self.token_actual().type != 'BEGIN':
                self.avanzar()
        # Consumir BEGIN...END
        if self.token_actual() and self.token_actual().type == 'BEGIN':
            self.avanzar()
            depth = 1
            while self.token_actual() and depth > 0:
                t = self.token_actual().type
                if t == 'BEGIN':
                    depth += 1
                elif t == 'END':
                    depth -= 1
                self.avanzar()
            if self.token_actual() and self.token_actual().type == 'SEMICOLON':
                self.avanzar()

    def _saltar_seccion_declaracion(self, tipo_seccion):
        """Salta una sección VAR/CONST/TYPE completa en la 2da pasada
        para que los identificadores declarados no se cuenten como usos."""
        self.avanzar()  # consumir VAR/CONST/TYPE
        STOP = {'BEGIN', 'FUNCTION', 'PROCEDURE', 'VAR', 'CONST', 'TYPE'}
        while self.token_actual() and self.token_actual().type not in STOP:
            self.avanzar()

    # ==============================================================
    #   ANÁLISIS COMPLETO
    # ==============================================================

    def analizar(self):
        print("Iniciando análisis semántico...")
        print("=" * 60)
        self.recolectar_declaraciones()
        # Resetear flags 'usada/usado' que pudo marcar la 1ra pasada
        # para que solo cuenten los usos reales del cuerpo del programa
        self._resetear_flags_uso()
        self.pos   = 0
        self.linea = 1
        self.verificar_uso()
        self.tabla.generar_advertencias_uso()
        self.generar_reporte()

    def _resetear_flags_uso(self):
        """Pone 'usada' en False en todas las variables/funciones/procedimientos
        para que la 2da pasada sea la única fuente de verdad sobre el uso real."""
        for scope in self.tabla.scopes:
            for info in scope.values():
                info['usada'] = False
        for info in self.tabla.funciones.values():
            info['usada'] = False
        for info in self.tabla.procedimientos.values():
            info['usado'] = False

    # ==============================================================
    #   REPORTE FINAL
    # ==============================================================

    def generar_reporte(self):
        errores      = self.tabla.errores
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

        vars_globales = self.tabla.scopes[0]
        print(f"\nVariables globales declaradas: {len(vars_globales)}")
        for nombre, info in vars_globales.items():
            estado = "✓ usada" if info.get('usada') else "✗ no usada"
            print(f"  - {nombre} : {info['tipo']} [{estado}] (línea {info['linea']})")

        print(f"\nConstantes declaradas: {len(self.tabla.constantes)}")
        for nombre, info in self.tabla.constantes.items():
            print(f"  - {nombre} : {info['tipo']} (línea {info['linea']})")

        print(f"\nTipos declarados: {len(self.tabla.tipos)}")
        for nombre, info in self.tabla.tipos.items():
            print(f"  - {nombre} = {info['definicion']} (línea {info['linea']})")

        print(f"\nFunciones declaradas: {len(self.tabla.funciones)}")
        for nombre, info in self.tabla.funciones.items():
            estado = "✓ usada" if info['usada'] else "✗ no usada"
            params_str = ', '.join(f"{p['nombre']}: {p['tipo']}" for p in info['params'])
            print(f"  - {nombre}({params_str}) : {info['tipo']} [{estado}] (línea {info['linea']})")
            vars_locales = self.tabla.vars_locales.get(nombre.lower(), {})
            for vnom, vinfo in vars_locales.items():
                info_g   = self.tabla.scopes[0].get(vnom)
                usada_r  = info_g['usada'] if info_g else vinfo.get('usada', False)
                estado_v = "✓ usada" if usada_r else "✗ no usada"
                print(f"      var {vnom} : {vinfo['tipo']} [{estado_v}] (línea {vinfo['linea']})")

        print(f"\nProcedimientos declarados: {len(self.tabla.procedimientos)}")
        for nombre, info in self.tabla.procedimientos.items():
            estado = "✓ usado" if info['usado'] else "✗ no usado"
            params_str = ', '.join(f"{p['nombre']}: {p['tipo']}" for p in info['params'])
            print(f"  - {nombre}({params_str}) [{estado}] (línea {info['linea']})")
            vars_locales = self.tabla.vars_locales.get(nombre.lower(), {})
            for vnom, vinfo in vars_locales.items():
                info_g   = self.tabla.scopes[0].get(vnom)
                usada_r  = info_g['usada'] if info_g else vinfo.get('usada', False)
                estado_v = "✓ usada" if usada_r else "✗ no usada"
                print(f"      var {vnom} : {vinfo['tipo']} [{estado_v}] (línea {vinfo['linea']})")

        print("=" * 60)


# ==============================================================
#   TOKENIZAR
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
    fin = sys.argv[1] if len(sys.argv) > 1 else 'input.pas'

    print(f"Analizando archivo: {fin}")
    print("=" * 60)

    tokens, total_lineas = tokenizar(fin)
    if tokens is None:
        sys.exit(1)

    print(f"Total de tokens:  {len(tokens)}")
    print(f"Total de líneas:  {total_lineas}")
    print("=" * 60)

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

    pascal_lexer.lexer.lineno = 1
    analizador = AnalizadorSemantico(tokens)
    analizador.analizar()