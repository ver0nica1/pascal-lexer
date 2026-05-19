import sys


class Symbol:
    def __init__(self, name, kind, typ, scope, line, initialized=False, params=None, return_type=None):
        self.name        = name
        self.kind        = kind
        self.type        = typ
        self.scope       = scope
        self.line        = line
        self.initialized = initialized
        self.params      = params or []
        self.return_type = return_type

    def __repr__(self):
        return (f"Symbol({self.name!r}, kind={self.kind!r}, type={self.type!r}, "
                f"scope={self.scope!r}, line={self.line})")


class SymbolTable:
    def __init__(self):
        self._scopes = [{}]
        self._scope_names = ['global']
        self._all_symbols = []

    def push_scope(self, name):
        self._scopes.append({})
        self._scope_names.append(name)

    def pop_scope(self):
        self._scopes.pop()
        self._scope_names.pop()

    @property
    def current_scope(self):
        return self._scope_names[-1]

    def insert(self, symbol: Symbol):
        top = self._scopes[-1]
        key = symbol.name.lower()
        if key in top:
            return False
        top[key] = symbol
        self._all_symbols.append(symbol)
        return True

    def lookup(self, name):
        key = name.lower()
        for scope in reversed(self._scopes):
            if key in scope:
                return scope[key]
        return None

    def lookup_current(self, name):
        key = name.lower()
        return self._scopes[-1].get(key)

    def mark_initialized(self, name):
        key = name.lower()
        for scope in reversed(self._scopes):
            if key in scope:
                scope[key].initialized = True
                return

    def print_table(self):
        print()
        print("=" * 84)
        print(f"{'TABLA DE SÍMBOLOS':^84}")
        print("=" * 84)
        print(f"  {'NOMBRE':<18} {'TIPO':<18} {'CATEGORÍA':<12} {'ÁMBITO':<16} {'LÍNEA':>5}  {'INIC':>5}")
        print("  " + "-" * 80)

        scopes_seen = []
        by_scope = {}
        for s in self._all_symbols:
            if s.scope not in by_scope:
                by_scope[s.scope] = []
                scopes_seen.append(s.scope)
            by_scope[s.scope].append(s)

        for scope in scopes_seen:
            syms = by_scope[scope]
            print(f"\n  Ámbito: {scope}")
            print("  " + "-" * 80)
            for s in syms:
                init_str = "sí" if s.initialized else ("-" if s.kind in ('function','procedure','const','type') else "no")
                extra = ""
                if s.kind == 'function':
                    if s.return_type:
                        extra = f"->{s.return_type}"
                    elif s.params:
                        extra = f"({','.join(s.params)})"
                elif s.kind == 'procedure' and s.params:
                    extra = f"({','.join(s.params)})"
                tipo_str = (s.type + extra)[:17]
                print(f"  {s.name:<18} {tipo_str:<18} {s.kind:<12} {s.scope:<16} {s.line:>5}  {init_str:>5}")

        print("=" * 84)


class SemanticAnalyzer:

    SCALAR = {'integer', 'real', 'boolean', 'char', 'string'}
    NUMERIC = {'integer', 'real'}

    def __init__(self):
        self.table   = SymbolTable()
        self.errors  = []
        self.warnings = []
        self._current_function = None

    def error(self, line, msg):
        self.errors.append(f"  ERROR SEMÁNTICO (línea {line}): {msg}")

    def warning(self, line, msg):
        self.warnings.append(f"  ADVERTENCIA (línea {line}): {msg}")

    def compatible(self, t1, t2):
        if t1 is None or t2 is None:
            return True
        t1, t2 = t1.lower(), t2.lower()
        if t1 == t2:
            return True
        if {t1, t2} <= self.NUMERIC:
            return True
        return False

    def numeric_result(self, t1, t2):
        if t1 == 'real' or t2 == 'real':
            return 'real'
        return 'integer'

    def visit_program(self, name, block, line):
        pass

    def visit_var_declaration(self, names, typ, line):
        for name in names:
            sym = Symbol(name, 'var', typ, self.table.current_scope, line)
            if not self.table.insert(sym):
                self.error(line, f"'{name}' ya fue declarado en este ámbito")

    def visit_const_def(self, name, typ, line):
        sym = Symbol(name, 'const', typ, self.table.current_scope, line, initialized=True)
        if not self.table.insert(sym):
            self.error(line, f"'{name}' ya fue declarado en este ámbito")

    def visit_function_decl_begin(self, name, params, return_type, line):
        param_types = [p[1] for p in params]
        sym = Symbol(name, 'function', return_type,
                     self.table.current_scope, line,
                     initialized=True,
                     params=param_types,
                     return_type=return_type)
        if not self.table.insert(sym):
            self.error(line, f"'{name}' ya fue declarado en este ámbito")
        self.table.push_scope(name)
        self._current_function = (name, return_type)
        for pname, ptype in params:
            psym = Symbol(pname, 'param', ptype, self.table.current_scope, line, initialized=True)
            if not self.table.insert(psym):
                self.error(line, f"Parámetro '{pname}' duplicado en '{name}'")

    def visit_function_decl_end(self):
        self.table.pop_scope()
        self._current_function = None

    def visit_procedure_decl_begin(self, name, params, line):
        param_types = [p[1] for p in params]
        sym = Symbol(name, 'procedure', 'void',
                     self.table.current_scope, line,
                     initialized=True,
                     params=param_types)
        if not self.table.insert(sym):
            self.error(line, f"'{name}' ya fue declarado en este ámbito")
        self.table.push_scope(name)
        self._current_function = None
        for pname, ptype in params:
            psym = Symbol(pname, 'param', ptype, self.table.current_scope, line, initialized=True)
            if not self.table.insert(psym):
                self.error(line, f"Parámetro '{pname}' duplicado en '{name}'")

    def visit_procedure_decl_end(self):
        self.table.pop_scope()

    def visit_assignment(self, lhs_name, lhs_type, rhs_type, line):
        sym = self.table.lookup(lhs_name)
        if sym is None:
            self.error(line, f"'{lhs_name}' no fue declarado")
            return
        if sym.kind == 'const':
            self.error(line, f"No se puede asignar a la constante '{lhs_name}'")
            return
        if not self.compatible(sym.type, rhs_type):
            self.error(line, f"Incompatibilidad de tipos en asignación: "
                             f"'{lhs_name}' es '{sym.type}' pero se asigna '{rhs_type}'")
        self.table.mark_initialized(lhs_name)

    def visit_call(self, name, arg_types, line):
        sym = self.table.lookup(name)
        if sym is None:
            self.error(line, f"'{name}' no fue declarado")
            return None
        if sym.kind not in ('function', 'procedure'):
            if name.lower() not in ('writeln', 'write', 'readln', 'read'):
                self.error(line, f"'{name}' no es una función ni un procedimiento")
            return sym.return_type if hasattr(sym, 'return_type') else None
        if len(arg_types) != len(sym.params):
            self.error(line, f"'{name}' espera {len(sym.params)} argumento(s), "
                             f"pero se proporcionaron {len(arg_types)}")
        else:
            for i, (at, pt) in enumerate(zip(arg_types, sym.params)):
                if not self.compatible(pt, at):
                    self.error(line, f"Argumento {i+1} de '{name}': "
                                     f"se esperaba '{pt}' pero se recibió '{at}'")
        return sym.return_type if sym.kind == 'function' else None

    def visit_variable(self, name, line):
        sym = self.table.lookup(name)
        if sym is None:
            self.error(line, f"'{name}' no fue declarado")
            return None
        if sym.kind == 'var' and not sym.initialized:
            self.warning(line, f"'{name}' se usa sin haber sido inicializada")
        return sym.type

    def visit_lvalue(self, name, line):
        sym = self.table.lookup(name)
        if sym is None:
            self.error(line, f"'{name}' no fue declarado")
            return None
        return sym.type

    def visit_binop(self, op, t1, t2, line):
        if t1 is None or t2 is None:
            return None
        arith = {'+', '-', '*', '/', 'div', 'mod'}
        logic = {'and', 'or'}
        rel   = {'=', '<>', '<', '>', '<=', '>=', 'in'}

        if op in arith:
            if t1 not in self.NUMERIC or t2 not in self.NUMERIC:
                self.error(line, f"Operación aritmética '{op}' requiere operandos numéricos, "
                                 f"pero se tienen '{t1}' y '{t2}'")
                return None
            return self.numeric_result(t1, t2)

        if op in logic:
            if t1 != 'boolean' or t2 != 'boolean':
                self.error(line, f"Operación lógica '{op}' requiere booleanos, "
                                 f"pero se tienen '{t1}' y '{t2}'")
                return 'boolean'
            return 'boolean'

        if op in rel:
            if not self.compatible(t1, t2):
                self.error(line, f"Comparación '{op}' entre tipos incompatibles: "
                                 f"'{t1}' y '{t2}'")
            return 'boolean'

        return None

    def report(self, total_lines):
        print()
        print("=" * 62)
        print(f"{'ANÁLISIS SEMÁNTICO':^62}")
        print("=" * 62)

        if self.warnings:
            print(f"\n  {len(self.warnings)} advertencia(s):")
            for w in self.warnings:
                print(w)

        if self.errors:
            print(f"\n  {len(self.errors)} error(es) semántico(s):")
            for e in self.errors:
                print(e)
        else:
            print(f"\n  Sin errores semánticos en {total_lines} líneas.")

        self.table.print_table()


def register_builtins(sem):
    for name in ('writeln','write','readln','read'):
        sym = Symbol(name, 'procedure', 'void', 'global', 0,
                     initialized=True, params=['variadic'])
        sem.table.insert(sym)


if __name__ == '__main__':
    from parser_sem import parser, sem, syntax_errors
    import lexer

    fin = sys.argv[1] if len(sys.argv) > 1 else 'input.pas'

    with open(fin, 'r', encoding='utf-8', errors='ignore') as f:
        data = f.read()

    total_lines = len(data.splitlines())

    register_builtins(sem)
    lexer.lexer.lineno = 1
    lexer.lexer_errors.clear()
    syntax_errors.clear()
    parser.parse(data, lexer=lexer.lexer, tracking=True)

    print()
    print("=" * 62)
    print(f"  Archivo analizado : {fin}")
    print(f"  Líneas totales    : {total_lines}")
    print("=" * 62)

    all_prior = lexer.lexer_errors + syntax_errors
    if all_prior:
        print(f"\n  {len(all_prior)} error(es) léxico/sintáctico(s):")
        for e in all_prior:
            print(f"    {e}")

    sem.report(total_lines)
