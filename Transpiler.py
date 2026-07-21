import re
import colorama
import argparse

BUFFER_SIZE = 256

def arguments():
    parser = argparse.ArgumentParser(description="Argument check")
    parser.add_argument('filename', nargs='?', default=None)
    parser.add_argument('-o', help="output file name")
    parser.add_argument('-b', action='store_true', help="birthday mode!")
    parser.add_argument('--troll', action='store_true', help="trolling mode")
    
    args = parser.parse_args()
    return args

args=arguments()
file = "main" if not args.filename else args.filename

ccode = [
'#include <stdio.h>',
'void printchar(char c) {',
'    char buf = c;',
'    __asm__ volatile (',
'        "mov $1, %%rax\\n"',
'        "mov $1, %%rdi\\n"',
'        "leaq %0, %%rsi\\n"',
'        "mov $1, %%rdx\\n"',
'        "syscall\\n"',
'        :',
'        : "m"(buf)',
'        : "rax", "rdi", "rsi", "rdx", "rcx", "r11"',
'    );',
'}',
'void printstring(const char *str) {',
'    while (*str) { ',
'        printchar(*str);' ,
'        str++; ',
'    }',
'}',
'void printint(long n) {',
"    if (n < 0) { printchar('-'); n = -n; }",
'    if (n >= 10) { printint(n / 10); }',
"    printchar('0' + (char)(n % 10));",
'}',
'void printbool(int b) {',
'    if (b) { printstring("true"); } else { printstring("false"); }',
'}',
'void printfloat(float f) {',
"    if (f < 0) { printchar('-'); f = -f; }",
'    long ip = (long)f;',
'    printint(ip);',
"    printchar('.');",
'    float frac = f - (float)ip;',
'    long frac_part = (long)(frac * 1000000.0f + 0.5f);',
'    long temp = frac_part;',
'    int digits = 0;',
'    while(temp > 0) { digits++; temp /= 10; }',
'    if (frac_part == 0) digits = 1;',
"    for (int _i = 0; _i < (6 - digits); _i++) { printchar('0');}",
'    if (frac_part > 0) printint(frac_part);',
'}',
'void readchar(char *c) {',
'    __asm__ volatile (',
'        "mov $0, %%rax\\n"',
'        "mov $0, %%rdi\\n"',
'        "mov %0, %%rsi\\n"',
'        "mov $1, %%rdx\\n"',
'        "syscall\\n"',
'        :',
'        : "r"(c)',
'        : "rax", "rdi", "rsi", "rdx", "rcx", "r11"',
'    );',
'}',
'void readline(char *buf, unsigned long max_len) {',
'    unsigned long i = 0;',
'    char c;',
'    while (i < max_len - 1) {',
'        readchar(&c);',
"        if (c == '\\n') break;",
'        buf[i] = c;',
'        i++;',
'    }',
"    buf[i] = '\\0';",
'}',
'long str_to_int(const char *s) {',
'    long result = 0;',
'    int neg = 0;',
"    if (*s == '-') { neg = 1; s++; }",
"    while (*s >= '0' && *s <= '9') {",
"        result = result * 10 + (*s - '0');",
'        s++;',
'    }',
'    return neg ? -result : result;',
'}',
'int str_eq(const char *a, const char *b) {',
'    while (*a && *b) {',
'        if (*a != *b) return 0;',
'        a++; b++;',
'    }',
'    return *a == *b;',
'void str_copy(char *dest, const char *src) {',
'    while (*src) { *dest = *src; dest++; src++; }',
"    *dest = '\\0';",
'}',
'}',
'char* main() {',
]


HOIST_INSERT_INDEX = len(ccode)

def hoist_declaration(decl_line):
    global HOIST_INSERT_INDEX
    ccode.insert(HOIST_INSERT_INDEX, decl_line)
    HOIST_INSERT_INDEX += 1

declared_vars_stack = [{}]
anon_var_count = 0

def is_var_declared(name):
    for scope in reversed(declared_vars_stack):
        if name in scope:
            return True
    return False

def get_var_type(name):
    for scope in reversed(declared_vars_stack):
        if name in scope:
            return scope[name]
    return None

def declare_var_in_current_scope(name, var_type):
    declared_vars_stack[-1][name] = var_type

# Keywords
WRITE_RE = re.compile(r'^\s*write\s*\(\s*(?:"((?:[^"\\]|\\.)*)"|([a-zA-Z_][a-zA-Z0-9_]*))\s*\)\s*$')
READ_RE = re.compile(r'^\s*read\s*\(\s*(?:"((?:[^"\\]|\\.)*)"|([a-zA-Z_][a-zA-Z0-9_]*))\s*\)\s*$')
PASS_RE = re.compile(r'^\s*(pass|skip)\s*$')
RETURN_RE = re.compile(r'^\s*return\s+([a-zA-Z0-9_]+)\s*$')
# Types
INT_RE = re.compile(r'^\s*int\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)\s*$')
FLOAT_RE = re.compile(r'^\s*float\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)\s*$')
STR_RE = re.compile(r'^\s*str\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"((?:[^"\\]|\\.)*)"\s*$')
BOOL_RE = re.compile(r'^\s*bool\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(true|false)\s*$')
# Structs
IF_RE = re.compile(r'^\s*if\s*\(\s*(.+?)\s*\)\s*\{(.*)\}\s*$', re.DOTALL)
WHILE_RE = re.compile(r'^\s*while\s*\(\s*(.+?)\s*\)\s*\{(.*)\}\s*$', re.DOTALL)
FUNC_RE = re.compile(r'^\s*while\s*\(\s*(.+?)\s*\)\s*\{(.*)\}\s*$', re.DOTALL)
#Helpers
ASSIGN_STR_RE = re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"((?:[^"\\]|\\.)*)"\s*$')
ASSIGN_RE = re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)\s*$')
IDENT_RE = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
READ_CALL_RE = re.compile(r'read\s*\(\s*(?:"((?:[^"\\]|\\.)*)"|([a-zA-Z_][a-zA-Z0-9_]*))\s*\)')
KNOWN_FUNCS = {"atoi", "str_eq", "str_to_int"}
STR_EQ_RE = re.compile(r'^(.+?)\s*==\s*(.+)$')
STR_NEQ_RE = re.compile(r'^(.+?)\s*!=\s*(.+)$')
#Other
COMM_RE=re.compile(r'^\s*//\s+([a-zA-Z0-9_]+)\s*$')

RESERVED_NAMES = {"true", "false"}

def is_strlike(x):
    x = x.strip()
    if x.startswith('"'):
        return True
    if IDENT_RE.fullmatch(x) and get_var_type(x) == "str":
        return True
    return False

def convert_clause(clause):
    stripped = strip_outer_parens(clause)

    m = STR_NEQ_RE.match(stripped)
    if m:
        left, right = m.group(1).strip(), m.group(2).strip()
        if is_strlike(left) or is_strlike(right):
            return f"!str_eq({left}, {right})"
        return clause

    m = STR_EQ_RE.match(stripped)
    if m:
        left, right = m.group(1).strip(), m.group(2).strip()
        if is_strlike(left) or is_strlike(right):
            return f"str_eq({left}, {right})"
        return clause

    return clause

def convert_condition(condition, indent):
    condition = extract_reads(condition, indent)
    clauses, ops = split_logical(condition)
    converted = [convert_clause(c) for c in clauses]

    result = converted[0]
    for op, c in zip(ops, converted[1:]):
        result += f" {op} {c}"
    return result

def check_expr_vars(expr, line_for_error):
    for name in IDENT_RE.findall(expr):
        if name in ("true", "false") or name in KNOWN_FUNCS:
            continue
        if not is_var_declared(name):
            print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Name Error{colorama.Fore.RESET}: undeclared variable '{colorama.Fore.RED}{name}{colorama.Fore.RESET}' in '{colorama.Fore.RED}{line_for_error}{colorama.Fore.RESET}'")
            return False
    return True

ESCAPE_MAP = {
    'n': '\n',
    't': '\t',
    'r': '\r',
    '0': '\0',
    '\\': '\\',
    '"': '"',
}

def helper_print_string_literal(text, indent_str="    "):
    result_chars = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '\\' and i + 1 < n and text[i + 1] in ESCAPE_MAP:
            result_chars.append(ESCAPE_MAP[text[i + 1]])
            i += 2
            continue
        result_chars.append(ch)
        i += 1

    for ch in result_chars:
        for b in ch.encode('utf-8'):
            ccode.append(f"{indent_str}printchar((char){b});")

def extract_reads(expr, indent):
    global anon_var_count

    def repl(m):
        global anon_var_count
        prompt_text = m.group(1)
        var_name = m.group(2)

        if prompt_text is not None:
            helper_print_string_literal(prompt_text, indent)
        elif var_name is not None:
            if not is_var_declared(var_name):
                print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Name Error{colorama.Fore.RESET}: undeclared variable '{colorama.Fore.RED}{var_name}{colorama.Fore.RESET}'")
                return m.group(0)
            if get_var_type(var_name) != "str":
                print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Type Error{colorama.Fore.RESET}: cannot use '{colorama.Fore.RED}{var_name}{colorama.Fore.RESET}' as read() prompt")
                return m.group(0)
            ccode.append(f"{indent}printstring({var_name});")

        anon_var = f"anon_buf_{anon_var_count}"
        anon_var_count += 1
        ccode.append(f"{indent}char {anon_var}[{BUFFER_SIZE}];")
        ccode.append(f"{indent}readline({anon_var}, {BUFFER_SIZE});")
        declare_var_in_current_scope(anon_var, "str")
        return anon_var

    return READ_CALL_RE.sub(repl, expr)

def split_statements(text):
    statements = []
    buf = []
    depth = 0
    in_string = False
    escape = False
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]
        if in_string:
            buf.append(ch)
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            buf.append(ch)
            i += 1
            continue

        if ch == '{':
            depth += 1
            buf.append(ch)
            i += 1
            continue

        if ch == '}':
            depth -= 1
            buf.append(ch)
            i += 1
            if depth <= 0:
                depth = 0
                stmt = "".join(buf).strip()
                if stmt:
                    statements.append(stmt)
                buf = []
            continue

        if ch == '\n':
            if depth == 0:
                stmt = "".join(buf).strip()
                if stmt:
                    statements.append(stmt)
                buf = []
            else:
                buf.append('\n')
            i += 1
            continue

        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements

def split_logical(text):
    clauses = []
    ops = []
    buf = []
    depth = 0
    in_string = False
    escape = False
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]
        if in_string:
            buf.append(ch)
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            buf.append(ch)
            i += 1
            continue

        if ch == '(':
            depth += 1
            buf.append(ch)
            i += 1
            continue

        if ch == ')':
            depth -= 1
            buf.append(ch)
            i += 1
            continue

        if depth == 0 and text[i:i+2] in ('&&', '||'):
            clauses.append("".join(buf).strip())
            ops.append(text[i:i+2])
            buf = []
            i += 2
            continue

        buf.append(ch)
        i += 1

    clauses.append("".join(buf).strip())
    return clauses, ops

def strip_outer_parens(s):
    s = s.strip()
    while s.startswith('(') and s.endswith(')'):
        depth = 0
        balanced = True
        for idx, ch in enumerate(s):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0 and idx != len(s) - 1:
                    balanced = False
                    break
        if balanced:
            s = s[1:-1].strip()
        else:
            break
    return s

def translate(line, depth=1):
    global anon_var_count
    line = line.strip()
    if not line:
        return 0
    indent = "    " * depth

    m = BOOL_RE.match(line)
    if m:
        namevar = m.group(1)
        value = m.group(2)
        if namevar in declared_vars_stack[-1]:
            print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Redefinition Error{colorama.Fore.RESET}: variable '{colorama.Fore.RED}{namevar}{colorama.Fore.RESET}' already declared in this scope")
            return 1
        if namevar in RESERVED_NAMES:
            print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Syntax Error{colorama.Fore.RESET}: '{colorama.Fore.RED}{namevar}{colorama.Fore.RESET}' is a reserved name")
            return 1
        declare_var_in_current_scope(namevar, "bool")
        c_val = "1" if value == "true" else "0"
        ccode.append(f'{indent}int {namevar} = {c_val};')
        return 0

    m = INT_RE.match(line)
    if m:
        namevar, expr = m.groups()
        if namevar in declared_vars_stack[-1]:
            print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Redefinition Error{colorama.Fore.RESET}: variable '{colorama.Fore.RED}{namevar}{colorama.Fore.RESET}' already declared in this scope")
            return 1
        if READ_CALL_RE.fullmatch(expr.strip()):
            expr = extract_reads(expr, indent)
            expr = f"str_to_int({expr})"
        else:
            expr = extract_reads(expr, indent)
        if not check_expr_vars(expr, line):
            return 1
        declare_var_in_current_scope(namevar, "int")
        ccode.append(f"{indent}int {namevar} = {expr};")
        return 0

    m = FLOAT_RE.match(line)
    if m:
        namevar, expr = m.groups()
        if namevar in declared_vars_stack[-1]:
            print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Redefinition Error{colorama.Fore.RESET}: variable '{colorama.Fore.RED}{namevar}{colorama.Fore.RESET}' already declared in this scope")
            return 1
        if not check_expr_vars(expr, line):
            return 1
        declare_var_in_current_scope(namevar, "str")
        ccode.append(f'{indent}char {namevar}[{BUFFER_SIZE}] = "{value}";')
        return 0

    m = STR_RE.match(line)
    if m:
        namevar = m.group(1)
        value = m.group(2)
        if namevar in declared_vars_stack[-1]:
            print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Redefinition Error{colorama.Fore.RESET}: variable '{colorama.Fore.RED}{namevar}{colorama.Fore.RESET}' already declared in this scope")
            return 1
        declare_var_in_current_scope(namevar, "str")
        ccode.append(f'{indent}char {namevar} = "{value}";')
        return 0

    m = RETURN_RE.match(line)
    if m:
        value = m.group(1)
        ccode.append(f'{indent}return "{value}";')
        return 0

    m = COMM_RE.match(line)
    if m:
        return 0

    m = ASSIGN_STR_RE.match(line)
    if m:
        namevar, value = m.groups()
        if not is_var_declared(namevar):
            print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Name Error{colorama.Fore.RESET}: undeclared variable '{colorama.Fore.RED}{namevar}{colorama.Fore.RESET}'")
            return 1
        if get_var_type(namevar) != "str":
            print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Type Error{colorama.Fore.RESET}: cannot assign string to '{colorama.Fore.RED}{namevar}{colorama.Fore.RESET}' of type '{get_var_type(namevar)}'")
            return 1
        ccode.append(f'{indent}str_copy({namevar}, "{value}");')
        return 0

    m = ASSIGN_RE.match(line)
    if m:
        namevar, expr = m.groups()
        if not is_var_declared(namevar):
            print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Name Error{colorama.Fore.RESET}: undeclared variable '{colorama.Fore.RED}{namevar}{colorama.Fore.RESET}'")
            return 1
        v_type = get_var_type(namevar)
        if v_type not in ("int", "float", "bool"):
            print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Type Error{colorama.Fore.RESET}: cannot assign expression to '{colorama.Fore.RED}{namevar}{colorama.Fore.RESET}' of type '{v_type}'")
            return 1
        if not check_expr_vars(expr, line):
            return 1
        ccode.append(f"{indent}{namevar} = {expr};")
        return 0

    m = WRITE_RE.match(line)
    if m:
        string_literal = m.group(1)
        var_name = m.group(2)

        if string_literal is not None:
            helper_print_string_literal(string_literal, indent)
        elif var_name is not None:
            if not is_var_declared(var_name):
                print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Name Error{colorama.Fore.RESET}: undeclared variable '{colorama.Fore.RED}{var_name}{colorama.Fore.RESET}'")
                return 1

            var_type = get_var_type(var_name)
            if var_type == "str":
                ccode.append(f"{indent}printstring({var_name});")
            elif var_type == "int":
                ccode.append(f"{indent}printint({var_name});")
            elif var_type == "float":
                ccode.append(f"{indent}printfloat({var_name});")
            elif var_type == "bool":
                ccode.append(f"{indent}printbool({var_name});")
        return 0

    m = READ_RE.match(line)
    if m:
        prompt_text = m.group(1)
        var_name = m.group(2)

        if prompt_text is not None:
            helper_print_string_literal(prompt_text, indent)
            anon_var = f"anon_buf_{anon_var_count}"
            anon_var_count += 1
            ccode.append(f"{indent}char {anon_var}[{BUFFER_SIZE}];")
            ccode.append(f"{indent}readline({anon_var}, {BUFFER_SIZE});")
        elif var_name is not None:
            if not is_var_declared(var_name):
                ccode.append(f"{indent}char {var_name}[{BUFFER_SIZE}];")
                declare_var_in_current_scope(var_name, "str")
            elif get_var_type(var_name) != "str":
                print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Type Error{colorama.Fore.RESET}: cannot read() into '{colorama.Fore.RED}{var_name}{colorama.Fore.RESET}' of type '{get_var_type(var_name)}'")
                return 1
            ccode.append(f"{indent}readline({var_name}, {BUFFER_SIZE});")
        return 0

    m = PASS_RE.match(line)
    if m:
        ccode.append(f"{indent};")
        return 0

    m = WHILE_RE.match(line)
    if m:
        condition = m.group(1)
        body = m.group(2)
        condition = convert_condition(condition, indent)
        if not check_expr_vars(condition, line):
            return 1
        ccode.append(f"{indent}while ({condition}) {{")

        declared_vars_stack.append({})
        inner_error = 0
        for inner_stmt in split_statements(body):
            if translate(inner_stmt, depth + 1) != 0:
                inner_error = 1
        declared_vars_stack.pop()

        ccode.append(f"{indent}}}")
        return inner_error

    m = IF_RE.match(line)
    if m:
        condition = m.group(1)
        body = m.group(2)
        condition = convert_condition(condition, indent)
        if not check_expr_vars(condition, line):
            return 1
        ccode.append(f"{indent}if ({condition}) {{")

        declared_vars_stack.append({})
        inner_error = 0
        for inner_stmt in split_statements(body):
            if translate(inner_stmt, depth + 1) != 0:
                inner_error = 1
        declared_vars_stack.pop()

        ccode.append(f"{indent}}}")
        return inner_error

    print(f"Error in {colorama.Fore.MAGENTA}{file}{colorama.Fore.RESET}:\n{colorama.Fore.MAGENTA}  Syntax Error{colorama.Fore.RESET}: invalid statement '{colorama.Fore.RED}{line}{colorama.Fore.RESET}'")
    return 1
