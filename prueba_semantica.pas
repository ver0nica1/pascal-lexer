{ ============================================================
  prueba_semantica.pas
  Programa Pascal diseñado para disparar TODOS los tipos de
  errores y advertencias que detecta el analizador semántico.

  ERRORES ESPERADOS:
    1. Variable 'x' declarada dos veces
    2. Función 'duplicada' declarada dos veces
    3. Asignación de string a integer  (incompatibilidad de tipos)
    4. Asignación de real a boolean    (incompatibilidad de tipos)
    5. Variable 'noExiste' usada sin declarar
    6. 'sumar' llamada con 3 args, espera 2
    7. 'funcionFantasma' no está declarada
    8. Variable de control 'k' del FOR no declarada

  ADVERTENCIAS ESPERADAS:
    9.  Variable 'x' declarada dos veces (segunda declaracion)
   10.  Variable 'sinUsar' nunca usada
   11.  Procedimiento 'procSinLlamar' nunca llamado
============================================================ }

PROGRAM PruebaSemantica;

{ ── Sección VAR global ─────────────────────────────────── }
Var
  x        : INTEGER;
  x        : REAL;          { ERROR 1: 'x' ya fue declarado }
  sinUsar  : STRING;        { → advertencia: declarada pero nunca usada }
  contador : INTEGER;
  bandera  : BOOLEAN;
  nombre   : STRING;
  precio   : REAL;

{ ── Funciones ──────────────────────────────────────────── }

{ Función válida: suma dos enteros y devuelve un entero }
FUNCTION sumar(a: integer; b: integer): INTEGER;
Begin
  sumar := a + b;
End;

{ ERROR 2: función 'duplicada' declarada por segunda vez }
FUNCTION duplicada(n: integer): INTEGER;
Begin
  duplicada := n * 2;
End;

FUNCTION duplicada(n: integer): INTEGER;    { ERROR 2 }
Begin
  duplicada := n + 1;
End;

{ ── Procedimientos ─────────────────────────────────────── }

{ Procedimiento válido pero que NUNCA se llama → advertencia }
PROCEDURE procSinLlamar(msg: string);
Begin
  WriteLn(msg);
End;

{ ── Cuerpo principal ────────────────────────────────────── }
BEGIN

  { OK: asignaciones de tipos compatibles }
  contador := 10;
  precio   := 3.14;
  nombre   := 'Pascal';

  { ERROR 3: asignar string a integer }
  contador := 'esto es un string';

  { ERROR 4: asignar real a boolean }
  bandera := 9.99;

  { ERROR 5: variable 'noExiste' nunca fue declarada }
  contador := noExiste + 1;

  { OK: llamada correcta a sumar con 2 argumentos }
  contador := sumar(contador, 5);

  { ERROR 6: sumar espera 2 argumentos, se llama con 3 }
  contador := sumar(1, 2, 3);

  { ERROR 7: 'funcionFantasma' no está declarada en ningún lado }
  contador := funcionFantasma(contador);

  { ERROR 8: variable de control 'k' no fue declarada }
  FOR k := 1 TO 5 DO
    contador := contador + 1;

  { OK: uso de WriteLn (built-in, no se verifica) }
  WriteLn('Contador: ', contador);
  WriteLn('Precio:   ', precio);
  WriteLn('Nombre:   ', nombre);

END.