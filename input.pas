PROGRAM Factorial;                    { MAYUSCULAS }

Var                                   { Mixta }
  n        : INTEGER;                 { MAYUSCULAS }
  resultado: integer;                 { minusculas }
  i        : Integer;                 { Mixta }
  mensaje  : STRING;                  { MAYUSCULAS }

(* Funcion que calcula el factorial de un numero *)

FUNCTION calcFactorial(num: integer): INTEGER;   
Var
  acum: integer;
  j   : integer;
Begin                                 { Mixta }
  acum := 1;
  j    := 1;
  WHILE j <= num DO                   { MAYUSCULAS }
  begin                               { minusculas }
    acum := acum * j;
    j    := j + 1;
  end;
  calcFactorial := acum; 
EnD;                                  { Mixta }

BEGIN                                 { MAYUSCULAS }
  n := 5;

  IF n < 0 then                       { Mixta: IF MAYUSCULAS, then minusculas }
  begin
    mensaje := 'Numero negativo';     { comillas simples }
  end
  ELSE IF n = 0 then
  Begin                               { Mixta }
    mensaje := "Factorial es 1";      { comillas dobles }
  End
  else                                { minusculas }
  begin
    resultado := calcFactorial(n);
    IF resultado > 100 then
      mensaje := 'Numero grande'
    else
      mensaje := 'Numero chico';
  end;

eNd.                                  { Mixta con punto final }