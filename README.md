# 🔬 Compilador Pascal

Compilador de subconjunto Pascal desarrollado en Python con PLY (Python Lex-Yacc). Implementa las tres fases clásicas de análisis de un compilador: **léxico**, **sintáctico** y **semántico**, con reporte detallado de errores y tabla de símbolos.

---

## 📁 Estructura del proyecto

```
.
├── lexer.py          # Analizador léxico
├── parser.py         # Analizador sintáctico (LALR(1)) — sin acciones semánticas
├── parser_sem.py     # Parser con acciones semánticas integradas
├── semantico.py      # Clases semánticas: Symbol, SymbolTable, SemanticAnalyzer
├── test.py           # Punto de entrada principal (3 fases)
└── input.pas         # Archivo Pascal de prueba
```

### Archivos principales

| Archivo | Descripción |
|---|---|
| `lexer.py` | Tokenizador con PLY-Lex. Reconoce palabras reservadas, literales, operadores y símbolos de Pascal. |
| `parser.py` | Parser LALR(1) puro con `pass` en cada regla. Solo verifica estructura gramatical. |
| `parser_sem.py` | Parser LALR(1) con acciones semánticas. Importa las clases de `semantico.py` y construye la tabla de símbolos durante el parseo. |
| `semantico.py` | Clases puras sin dependencias del parser: `Symbol`, `SymbolTable`, `SemanticAnalyzer`. Contiene toda la lógica de validación semántica. |
| `test.py` | Orquestador que ejecuta las 3 fases en orden y muestra el reporte unificado. |

---

## ⚙️ Requisitos

- Python 3.8 o superior
- PLY (Python Lex-Yacc)

```bash
pip install ply
```

---

## 🚀 Uso

### Ejecutar las 3 fases (recomendado)

```bash
python test.py <archivo.pas>
```

### Ejecutar solo el análisis semántico

```bash
python semantico.py <archivo.pas>
```

Si no se pasa un archivo, el compilador busca `input.pas` en el directorio actual por defecto.

---

## 🧩 Fases del compilador

### [ 1 ] Análisis léxico — `lexer.py`

Tokeniza el código fuente y detecta caracteres ilegales. Reconoce:

- **35 palabras reservadas** de Pascal: `program`, `begin`, `end`, `if`, `then`, `else`, `while`, `for`, `repeat`, `until`, `case`, `function`, `procedure`, `var`, `const`, `type`, `array`, `record`, `set`, `file`, `packed`, `goto`, `label`, `with`, `and`, `or`, `not`, `div`, `mod`, `in`, `nil`, `do`, `to`, `downto`, `of`
- **Tipos de dato**: `integer`, `real`, `boolean`, `char`, `string`
- **Literales**: números enteros y reales (`42`, `3.14`, `1e5`), constantes de carácter (`'a'`, `'hola'`)
- **Operadores**: aritméticos, relacionales, lógicos, asignación (`:=`), rango (`..`)
- **Símbolos**: paréntesis, corchetes, punto, coma, dos puntos, punto y coma
- **Comentarios**: estilo `{ ... }` y `(* ... *)` — ignorados silenciosamente

---

### [ 2 ] Análisis sintáctico — `parser.py`

Parser LALR(1) construido con PLY que verifica la estructura gramatical del programa. Soporta:

- Estructura general: `program nombre; bloque.`
- Secciones de declaración: `label`, `const`, `type`, `var`
- Tipos: escalares, `array`, `record`, `set`, `file`, `packed`
- Sentencias: asignación, `if/else`, `while`, `for`, `repeat/until`, `case`, `goto`, `with`
- Subprogramas: `function` y `procedure` con parámetros tipados
- Expresiones: aritméticas, relacionales, lógicas, con precedencia correcta
- Constructores de conjuntos: `[a, b..c, d]`

**Recuperación de errores:** ante un error sintáctico el parser busca el siguiente `;`, `begin` o `end` para continuar el análisis y reportar todos los errores posibles en una sola pasada.

---

### [ 3 ] Análisis semántico — `parser_sem.py` + `semantico.py`

El análisis semántico se divide en dos archivos para mantener el código limpio:

- **`semantico.py`** contiene las clases puras:
  - `Symbol` — representa un símbolo (variable, constante, función, etc.)
  - `SymbolTable` — gestiona ámbitos (scopes) y la tabla de símbolos
  - `SemanticAnalyzer` — métodos `visit_*` con toda la lógica de validación

- **`parser_sem.py`** contiene las reglas gramaticales con acciones semánticas que llaman a los métodos del `SemanticAnalyzer` durante el parseo.

#### Errores detectados

| Error | Descripción |
|---|---|
| Redeclaración | Variable, función o procedimiento declarado más de una vez en el mismo ámbito |
| Variable sin declarar | Uso de un identificador que no aparece en ninguna sección `var` |
| Incompatibilidad de tipos en asignación | `contador := 'texto'` cuando `contador` es `integer` |
| Operación con tipos inválidos | Operación aritmética con operandos no numéricos |
| Condición no booleana | `if`, `while`, `repeat` con expresión que no es `boolean` |
| Argumentos incorrectos | Llamada con distinto número o tipo de argumentos del esperado |
| Subprograma no declarado | Llamada a función o procedimiento inexistente |
| Tipo no declarado | Uso de un identificador como tipo que no fue definido |

#### Advertencias generadas

| Advertencia | Descripción |
|---|---|
| Variable sin inicializar | Se usa una variable `var` antes de recibir una asignación |

#### Compatibilidad de tipos soportada

| Destino | Orígenes compatibles |
|---|---|
| `integer` | `integer` |
| `real` | `real`, `integer` (promoción implícita) |
| `boolean` | `boolean` |
| `char` | `char` |
| `string` | `string` |

#### Built-ins reconocidos

El analizador conoce los procedimientos estándar de Pascal y no los reporta como no declarados:

`writeln`, `write`, `readln`, `read`

---

## 📋 Ejemplo de salida

```
============================================================
  COMPILADOR PASCAL
  Archivo : input.pas
  Tokens  : 146    Líneas: 46
============================================================

                   [ 1 ] ANÁLISIS LÉXICO
------------------------------------------------------------
  [OK] Sin errores léxicos.

                 [ 2 ] ANÁLISIS SINTÁCTICO
------------------------------------------------------------
  [OK] Sin errores sintácticos.

                  [ 3 ] ANÁLISIS SEMÁNTICO
------------------------------------------------------------
  [ERROR] 11 error(es) semántico(s) encontrado(s):

    1.   ERROR SEMÁNTICO (línea 15): Operación aritmética '+' requiere operandos numéricos, pero se tienen 'integer' y 'string'
    2.   ERROR SEMÁNTICO (línea 26): 'n' no fue declarado
    ...

  [WARNING] 1 advertencia(s):

    1.   ADVERTENCIA (línea 20): 'h' se usa sin haber sido inicializada

                  [ 4 ] TABLA DE SÍMBOLOS
------------------------------------------------------------
  NOMBRE             TIPO               CATEGORÍA    ÁMBITO           LÍNEA   INIC
  --------------------------------------------------------------------------------

  Ámbito: global (variables)
  nx                 integer            var          global               4     no
  resultado          integer            var          global               5     sí
  mensaje            string             var          global               6     sí

  Ámbito: global (funciones)
  calcFactorial      integer->integer   function     global               9     sí

  Ámbito: global (procedimientos)
  writeln            void(variadic)     procedure    global               0     sí

                     [ RESUMEN FINAL ]
------------------------------------------------------------
  Errores léxicos    : 0
  Errores sintácticos: 0
  Errores semánticos : 11
  Advertencias       : 1
------------------------------------------------------------
  [FALLO] Se encontraron 11 error(es) en total.
============================================================
```

---

## 📐 Subconjunto de Pascal soportado

Este compilador implementa un subconjunto representativo de Pascal estándar. Lo que **sí** soporta:

- Programas completos con secciones `const`, `type`, `var`
- Funciones y procedimientos con parámetros y variables locales
- Todos los tipos escalares y estructurados básicos (`array`, `record`, `set`, `file`, `packed`)
- Todas las sentencias de control (`if`, `while`, `for`, `repeat`, `case`, `goto`, `with`)
- Expresiones con precedencia correcta, operador `in`, constructores de conjuntos
- Etiquetas numéricas (`label`) y sentencia `goto`

Lo que **no** soporta (fuera del alcance del proyecto):

- Punteros y tipos de acceso (`^`)
- Parámetros por referencia (`var` en parámetros)
- Unidades (`unit`) y módulos
- Generación de código intermedio o ejecutable

---

## 🛠️ Tecnologías

- **Python 3** — lenguaje de implementación
- **PLY 3.x** — librería de construcción de lexers y parsers LALR(1) para Python

---

## 👥 Autores

Proyecto desarrollado como entrega académica para el curso de **Compiladores** — Universidad Tecnológica de Pereira.
