import ply.yacc as yacc
from lexer import tokens, lexer, lexer_errors
from semantico import Symbol, SemanticAnalyzer

sem = SemanticAnalyzer()
syntax_errors = []


def p_program(p):
    'program : PROGRAM ID SEMICOLON block DOT'
    pass


def p_block(p):
    'block : label_part const_part type_part var_part subprogram_declarations compound_stmt'
    pass


def p_label_part_1(p): 'label_part : LABEL label_list SEMICOLON'
def p_label_part_2(p): 'label_part : empty'
def p_label_list_1(p): 'label_list : label_list COMMA NUMBER'
def p_label_list_2(p): 'label_list : NUMBER'


def p_const_part_1(p): 'const_part : CONST const_list'
def p_const_part_2(p): 'const_part : empty'
def p_const_list_1(p): 'const_list : const_list const_def'
def p_const_list_2(p): 'const_list : const_def'


def p_const_def(p):
    'const_def : ID EQ literal SEMICOLON'
    typ = p[3] if p[3] else 'unknown'
    sem.visit_const_def(p[1], typ, p.lineno(1))


def p_type_part_1(p): 'type_part : TYPE type_list'
def p_type_part_2(p): 'type_part : empty'
def p_type_list_1(p): 'type_list : type_list type_def'
def p_type_list_2(p): 'type_list : type_def'


def p_type_def(p):
    'type_def : ID EQ type_specifier SEMICOLON'
    sym = Symbol(p[1], 'type', p[3] or 'unknown', sem.table.current_scope, p.lineno(1), initialized=True)
    if not sem.table.insert(sym):
        sem.error(p.lineno(1), f"'{p[1]}' ya fue declarado en este ámbito")


def p_var_part_1(p): 'var_part : VAR var_declaration_list'
def p_var_part_2(p): 'var_part : empty'
def p_var_declaration_list_1(p): 'var_declaration_list : var_declaration_list var_declaration'
def p_var_declaration_list_2(p): 'var_declaration_list : var_declaration'


def p_var_declaration(p):
    'var_declaration : id_list COLON type_specifier SEMICOLON'
    names = p[1] if p[1] else []
    typ   = p[3] or 'unknown'
    sem.visit_var_declaration(names, typ, p.lineno(2))


def p_id_list_1(p):
    'id_list : id_list COMMA ID'
    p[0] = p[1] + [p[3]]


def p_id_list_2(p):
    'id_list : ID'
    p[0] = [p[1]]


def p_type_specifier_integer(p):
    'type_specifier : INTEGER'
    p[0] = 'integer'


def p_type_specifier_real(p):
    'type_specifier : REAL'
    p[0] = 'real'


def p_type_specifier_boolean(p):
    'type_specifier : BOOLEAN'
    p[0] = 'boolean'


def p_type_specifier_char(p):
    'type_specifier : CHAR'
    p[0] = 'char'


def p_type_specifier_string(p):
    'type_specifier : STRING'
    p[0] = 'string'


def p_type_specifier_array(p):
    'type_specifier : ARRAY LBR NUMBER RANGE NUMBER RBR OF type_specifier'
    p[0] = f'array[{p[3]}..{p[5]}] of {p[8]}'


def p_type_specifier_record(p):
    'type_specifier : RECORD field_list END'
    p[0] = 'record'


def p_type_specifier_set(p):
    'type_specifier : SET OF type_specifier'
    p[0] = f'set of {p[3]}'


def p_type_specifier_file(p):
    'type_specifier : FILE OF type_specifier'
    p[0] = f'file of {p[3]}'


def p_type_specifier_file_plain(p):
    'type_specifier : FILE'
    p[0] = 'file'


def p_type_specifier_packed(p):
    'type_specifier : PACKED type_specifier'
    p[0] = f'packed {p[2]}'


def p_type_specifier_id(p):
    'type_specifier : ID'
    sym = sem.table.lookup(p[1])
    if sym is None:
        sem.error(p.lineno(1), f"Tipo '{p[1]}' no declarado")
        p[0] = 'unknown'
    else:
        p[0] = sym.type


def p_field_list_1(p): 'field_list : field_list SEMICOLON field_declaration'
def p_field_list_2(p): 'field_list : field_declaration'
def p_field_list_3(p): 'field_list : empty'
def p_field_declaration(p): 'field_declaration : id_list COLON type_specifier'


def p_subprogram_declarations_1(p): 'subprogram_declarations : subprogram_declarations subprogram_declaration'
def p_subprogram_declarations_2(p): 'subprogram_declarations : empty'
def p_subprogram_declaration_function(p):  'subprogram_declaration : function_declaration'
def p_subprogram_declaration_procedure(p): 'subprogram_declaration : procedure_declaration'


def p_function_head(p):
    'function_head : FUNCTION ID LPAR params RPAR COLON type_specifier SEMICOLON'
    params = p[4] or []
    sem.visit_function_decl_begin(p[2], params, p[7], p.lineno(1))
    p[0] = (p[2], p[7])


def p_function_declaration(p):
    'function_declaration : function_head subblock SEMICOLON'
    sem.visit_function_decl_end()


def p_procedure_head(p):
    'procedure_head : PROCEDURE ID LPAR params RPAR SEMICOLON'
    params = p[4] or []
    sem.visit_procedure_decl_begin(p[2], params, p.lineno(1))
    p[0] = p[2]


def p_procedure_declaration(p):
    'procedure_declaration : procedure_head subblock SEMICOLON'
    sem.visit_procedure_decl_end()


def p_subblock(p):
    'subblock : label_part var_part compound_stmt'


def p_params_1(p):
    'params : param_list'
    p[0] = p[1]


def p_params_2(p):
    'params : empty'
    p[0] = []


def p_param_list_1(p):
    'param_list : param_list SEMICOLON param'
    p[0] = p[1] + p[3]


def p_param_list_2(p):
    'param_list : param'
    p[0] = p[1]


def p_param(p):
    'param : id_list COLON type_specifier'
    p[0] = [(name, p[3]) for name in (p[1] or [])]


def p_compound_stmt(p):
    'compound_stmt : BEGIN statement_list END'


def p_statement_list_1(p):
    'statement_list : statement_list SEMICOLON statement'


def p_statement_list_2(p):
    'statement_list : statement'


def p_statement(p):
    '''statement : assignment_stmt
                 | compound_stmt
                 | if_stmt
                 | while_stmt
                 | for_stmt
                 | repeat_stmt
                 | case_stmt
                 | goto_stmt
                 | with_stmt
                 | labeled_stmt
                 | procedure_call_stmt
                 | empty
    '''


def p_assignment_stmt(p):
    'assignment_stmt : lvalue ASSIGN expression'
    lhs_name, lhs_type = p[1]
    rhs_type = p[3]
    if lhs_name:
        sem.visit_assignment(lhs_name, lhs_type, rhs_type, p.lineno(2))


def p_lvalue_simple(p):
    'lvalue : ID'
    typ = sem.visit_lvalue(p[1], p.lineno(1))
    p[0] = (p[1], typ)


def p_lvalue_array(p):
    'lvalue : ID LBR expression RBR'
    sym = sem.table.lookup(p[1])
    if sym is None:
        sem.error(p.lineno(1), f"'{p[1]}' no fue declarado")
        p[0] = (p[1], None)
    else:
        base = sym.type
        if 'of' in str(base):
            base = base.split('of')[-1].strip()
        p[0] = (p[1], base)


def p_lvalue_field(p):
    'lvalue : lvalue DOT ID'
    p[0] = (p[3], None)


def p_if_stmt_1(p):
    'if_stmt : IF expression THEN statement ELSE statement'
    if p[2] and p[2] != 'boolean':
        sem.error(p.lineno(1), f"La condición del IF debe ser booleana, se tiene '{p[2]}'")


def p_if_stmt_2(p):
    'if_stmt : IF expression THEN statement'
    if p[2] and p[2] != 'boolean':
        sem.error(p.lineno(1), f"La condición del IF debe ser booleana, se tiene '{p[2]}'")


def p_while_stmt(p):
    'while_stmt : WHILE expression DO statement'
    if p[2] and p[2] != 'boolean':
        sem.error(p.lineno(1), f"La condición del WHILE debe ser booleana, se tiene '{p[2]}'")


def p_for_stmt_1(p):
    'for_stmt : FOR ID ASSIGN expression TO expression DO statement'
    sym = sem.table.lookup(p[2])
    if sym is None:
        sem.error(p.lineno(2), f"'{p[2]}' no fue declarado")
    sem.table.mark_initialized(p[2])


def p_for_stmt_2(p):
    'for_stmt : FOR ID ASSIGN expression DOWNTO expression DO statement'
    sym = sem.table.lookup(p[2])
    if sym is None:
        sem.error(p.lineno(2), f"'{p[2]}' no fue declarado")
    sem.table.mark_initialized(p[2])


def p_repeat_stmt(p):
    'repeat_stmt : REPEAT statement_list UNTIL expression'
    if p[4] and p[4] != 'boolean':
        sem.error(p.lineno(1), f"La condición del REPEAT-UNTIL debe ser booleana, se tiene '{p[4]}'")


def p_case_stmt_1(p):
    'case_stmt : CASE expression OF case_list END'


def p_case_stmt_2(p):
    'case_stmt : CASE expression OF case_list ELSE statement END'


def p_case_list_1(p): 'case_list : case_list case_element'
def p_case_list_2(p): 'case_list : case_element'


def p_case_element(p):
    'case_element : case_label_list COLON statement SEMICOLON'


def p_case_label_list_1(p): 'case_label_list : case_label_list COMMA literal'
def p_case_label_list_2(p): 'case_label_list : literal'


def p_goto_stmt(p):
    'goto_stmt : GOTO NUMBER'


def p_labeled_stmt(p):
    'labeled_stmt : NUMBER COLON statement'


def p_with_stmt(p):
    'with_stmt : WITH variable_list DO statement'


def p_variable_list_1(p): 'variable_list : variable_list COMMA variable'
def p_variable_list_2(p): 'variable_list : variable'


def p_procedure_call_stmt_1(p):
    'procedure_call_stmt : ID LPAR args RPAR'
    arg_types = p[3] or []
    sem.visit_call(p[1], arg_types, p.lineno(1))


def p_procedure_call_stmt_2(p):
    'procedure_call_stmt : ID'
    sym = sem.table.lookup(p[1])
    if sym is None and p[1].lower() not in ('writeln','write','readln','read'):
        sem.error(p.lineno(1), f"'{p[1]}' no fue declarado")


def p_variable_simple(p):
    'variable : ID'
    typ = sem.visit_variable(p[1], p.lineno(1))
    p[0] = (p[1], typ)


def p_variable_array(p):
    'variable : ID LBR expression RBR'
    sym = sem.table.lookup(p[1])
    if sym is None:
        sem.error(p.lineno(1), f"'{p[1]}' no fue declarado")
        p[0] = (p[1], None)
    else:
        base = sym.type
        if 'of' in str(base):
            base = base.split('of')[-1].strip()
        p[0] = (p[1], base)


def p_variable_field(p):
    'variable : variable DOT ID'
    p[0] = (p[3], None)


def p_expression_relop(p):
    'expression : simple_expression relop simple_expression'
    p[0] = sem.visit_binop(p[2], p[1], p[3], p.lineno(2))


def p_expression_simple(p):
    'expression : simple_expression'
    p[0] = p[1]


def p_expression_in(p):
    'expression : simple_expression IN set_constructor'
    p[0] = 'boolean'


def p_relop(p):
    '''relop : EQ
             | NE
             | LT
             | GT
             | LE
             | GE'''
    p[0] = p[1]


def p_simple_expression_addop(p):
    'simple_expression : simple_expression addop term'
    p[0] = sem.visit_binop(p[2], p[1], p[3], p.lineno(2))


def p_simple_expression_term(p):
    'simple_expression : term'
    p[0] = p[1]


def p_addop(p):
    '''addop : PLUS
             | MINUS
             | OR'''
    p[0] = p[1]


def p_term_mulop(p):
    'term : term mulop factor'
    p[0] = sem.visit_binop(p[2], p[1], p[3], p.lineno(2))


def p_term_factor(p):
    'term : factor'
    p[0] = p[1]


def p_mulop(p):
    '''mulop : TIMES
             | DIVISION
             | DIV
             | MOD
             | AND'''
    p[0] = p[1]


def p_factor_number(p):
    'factor : NUMBER'
    p[0] = 'real' if isinstance(p[1], float) else 'integer'


def p_factor_charconst(p):
    'factor : CHARCONST'
    val = p[1]
    inner = val[1:-1].replace("''", "'")
    p[0] = 'char' if len(inner) == 1 else 'string'


def p_factor_nil(p):
    'factor : NIL'
    p[0] = 'nil'


def p_factor_variable(p):
    'factor : variable'
    p[0] = p[1][1] if p[1] else None


def p_factor_call(p):
    'factor : ID LPAR args RPAR'
    arg_types = p[3] or []
    ret = sem.visit_call(p[1], arg_types, p.lineno(1))
    p[0] = ret


def p_factor_paren(p):
    'factor : LPAR expression RPAR'
    p[0] = p[2]


def p_factor_not(p):
    'factor : NOT factor'
    if p[2] and p[2] != 'boolean':
        sem.error(p.lineno(1), f"NOT requiere operando booleano, se tiene '{p[2]}'")
    p[0] = 'boolean'


def p_factor_set(p):
    'factor : set_constructor'
    p[0] = 'set'


def p_set_constructor_1(p):
    'set_constructor : LBR set_element_list RBR'
    p[0] = 'set'


def p_set_constructor_2(p):
    'set_constructor : LBR RBR'
    p[0] = 'set'


def p_set_element_list_1(p): 'set_element_list : set_element_list COMMA set_element'
def p_set_element_list_2(p): 'set_element_list : set_element'


def p_set_element_range(p):
    'set_element : expression RANGE expression'


def p_set_element_single(p):
    'set_element : expression'


def p_args_1(p):
    'args : args_list'
    p[0] = p[1]


def p_args_2(p):
    'args : empty'
    p[0] = []


def p_args_list_1(p):
    'args_list : args_list COMMA expression'
    p[0] = p[1] + [p[3]]


def p_args_list_2(p):
    'args_list : expression'
    p[0] = [p[1]]


def p_literal_number(p):
    'literal : NUMBER'
    p[0] = 'real' if isinstance(p[1], float) else 'integer'


def p_literal_charconst(p):
    'literal : CHARCONST'
    inner = p[1][1:-1].replace("''","'")
    p[0] = 'char' if len(inner) == 1 else 'string'


def p_empty(p):
    'empty :'
    p[0] = None


def p_error(p):
    if p:
        msg = f"ERROR SINTÁCTICO (línea {p.lineno}): token inesperado '{p.value}'"
        if not any(f"línea {p.lineno}" in e for e in syntax_errors):
            syntax_errors.append(msg)
        while True:
            tok = parser.token()
            if not tok or tok.type in ('SEMICOLON','BEGIN','END'):
                break
        parser.errok()


parser = yacc.yacc()
