## sphinx/domains/c.py
Now I have read all 3539 lines of the file. Here is the complete specification:

---

# Module Specification: `sphinx/domains/c.py`

## 1. Module-Level Preamble

### Imports

```python
import re
from typing import Any, Callable, Dict, Generator, Iterator, List, Type, Tuple, Union
from typing import cast
from docutils import nodes
from docutils.nodes import Element, Node, TextElement, system_message
from sphinx import addnodes
from sphinx.addnodes import pending_xref
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType
from sphinx.environment import BuildEnvironment
from sphinx.locale import _, __
from sphinx.roles import SphinxRole, XRefRole
from sphinx.util import logging
from sphinx.util.cfamily import (
    NoOldIdError, ASTBaseBase, verify_description_mode, StringifyTransform,
    BaseParser, DefinitionError, UnsupportedMultiCharacterCharLiteral,
    identifier_re, anon_identifier_re, integer_literal_re, octal_literal_re,
    hex_literal_re, binary_literal_re, float_literal_re, char_literal_re
)
from sphinx.util.docfields import Field, TypedField
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_refnode

logger = logging.getLogger(__name__)
```

### Constants & Globals

- **`_keywords`** — `List[str]`, ordered list of 48 C keywords: `'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'inline', 'int', 'long', 'register', 'restrict', 'return', 'short', 'signed', 'sizeof', 'static', 'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while', '_Alignas', 'alignas', '_Alignof', 'alignof', '_Atomic', '_Bool', 'bool', '_Complex', 'complex', '_Generic', '_Imaginary', 'imaginary', '_Noreturn', 'noreturn', '_Static_assert', 'static_assert', '_Thread_local', 'thread_local'`.

- **`_expression_bin_ops`** — `List[List[str]]`, binary operators ordered by precedence (highest first):
  - `[['||', 'or'], ['&&', 'and'], ['|', 'bitor'], ['^', 'xor'], ['&', 'bitand'], ['==', '!=', 'not_eq'], ['<=', '>=', '<', '>'], ['<<', '>>'], ['+', '-'], ['*', '/', '%'], ['.*', '->*']]`

- **`_expression_unary_ops`** — `List[str]`: `["++", "--", "*", "&", "+", "-", "!", "not", "~", "compl"]`.

- **`_expression_assignment_ops`** — `List[str]`: `["=", "*=", "/=", "%=", "+=", "-=", ">>=", "<<=", "&=", "and_eq", "^=", "xor_eq", "|=", "or_eq"]`.

- **`_max_id`** — `int = 1`, version counter for ID generation.

- **`_id_prefix`** — `List[Optional[str]] = [None, 'c.', 'Cv2.']`, prefix mapping by version index.

- **`_string_re`** — compiled regex: `re.compile(r"[LuU8]?('([^'\\]*(?:\\.[^'\\]*)*)'" r'|"([^"\\]*(?:\\.[^"\\]*)*)")', re.S)`.

---

## 2. Code Objects

### `_DuplicateSymbolError(Exception)`

- **`__init__(self, symbol: Symbol, declaration: ASTDeclaration) -> None`**: Asserts both args are truthy; stores them as `self.symbol`, `self.declaration`.
- **`__str__(self) -> str`**: Returns `"Internal C duplicate symbol error:\n%s" % self.symbol.dump(0)`.

### `ASTBase(ASTBaseBase)`

- **`describe_signature(self, signode: TextElement, mode: str, env: BuildEnvironment, symbol: Symbol) -> None`**: Raises `NotImplementedError(repr(self))`. Base for all AST nodes that need signature rendering.

---

### Names Section

#### `ASTIdentifier(ASTBaseBase)`
- **Attributes**: `self.identifier: str` (non-empty, non-None).
- **`is_anon(self) -> bool`**: Returns `True` if `identifier[0] == '@'`.
- **`__str__(self) -> str`**: Returns `self.identifier`.
- **`get_display_string(self) -> str`**: Returns `"[anonymous]"` if anonymous, else `self.identifier`.
- **`describe_signature(self, signode: TextElement, mode: str, env: BuildEnvironment, prefix: str, symbol: Symbol) -> None`**: Validates mode. Three modes:
  - `'markType'`: Creates a `pending_xref` with `refdomain='c', reftype='identifier'`, `reftarget=prefix+identifier`. Appends `[anonymous]` in strong text if anonymous; else plain Text. Adds to signode.
  - `'lastIsName'`: Appends `[anonymous]` (strong) or `desc_name(identifier, identifier)` to signode.
  - `'noneIsName'`: Appends `[anonymous]` (strong) or plain `Text(identifier)` to signode.

#### `ASTNestedName(ASTBase)`
- **Attributes**: `self.names: List[ASTIdentifier]` (non-empty), `self.rooted: bool`.
- **`name(self) -> ASTNestedName`** (property): Returns `self`.
- **`get_id(self, version: int) -> str`**: Returns `'.'.join(str(n) for n in self.names)`.
- **`_stringify(self, transform: StringifyTransform) -> str`**: Joins transformed names with dots; prepends `'.'` if `rooted`.
- **`describe_signature(self, signode: TextElement, mode: str, env: BuildEnvironment, symbol: Symbol) -> None`**: Validates mode. Three modes:
  - `'noneIsName'`: Appends plain `Text(str(self))`.
  - `'param'`: Appends `emphasis(name, name)` where `name = str(self)`.
  - `'markType' | 'lastIsName' | 'markName'`: Builds prefix iteratively. For each name except the last (if mode is `'lastIsName'`), appends dot separator and calls `ident.describe_signature(dest, 'markType', env, prefix, symbol)`, accumulating prefix. If `'lastIsName'`, wraps all prefix in a `desc_addname()` node before appending to signode; then renders the last name on signode with the given mode.

---

### Expressions Section

#### `ASTExpression(ASTBase)` — abstract base, no implementation.

#### `ASTLiteral(ASTExpression)` — abstract base, no implementation.

#### `ASTBooleanLiteral(ASTLiteral)`
- **Attributes**: `self.value: bool`.
- **`_stringify(self, transform) -> str`**: Returns `'true'` or `'false'`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text(str(self))`.

#### `ASTNumberLiteral(ASTLiteral)`
- **Attributes**: `self.data: str`.
- **`_stringify(self, transform) -> str`**: Returns `self.data`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text(txt, txt)` where `txt = str(self)`.

#### `ASTCharLiteral(ASTLiteral)`
- **Attributes**: `self.prefix: Optional[str]`, `self.data: str`, `self.value: int` (computed from decoding).
- **`__init__(self, prefix: str, data: str) -> None`**: Decodes `data` via `'unicode-escape'`; if decoded length is 1, stores `ord(decoded)` as `self.value`; else raises `UnsupportedMultiCharacterCharLiteral`.
- **`_stringify(self, transform) -> str`**: Returns `"'" + data + "'"` or `prefix + "'" + data + "'"`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text(txt, txt)` where `txt = str(self)`.

#### `ASTStringLiteral(ASTLiteral)`
- **Attributes**: `self.data: str`.
- **`_stringify(self, transform) -> str`**: Returns `self.data`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text(txt, txt)` where `txt = str(self)`.

#### `ASTIdExpression(ASTExpression)`
- **Attributes**: `self.name: ASTNestedName`.
- **`_stringify(self, transform) -> str`**: Returns `transform(self.name)`.
- **`get_id(self, version: int) -> str`**: Returns `self.name.get_id(version)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Calls `self.name.describe_signature(signode, mode, env, symbol)`.

#### `ASTParenExpr(ASTExpression)`
- **Attributes**: `self.expr: ASTExpression`.
- **`_stringify(self, transform) -> str`**: Returns `'(' + transform(self.expr) + ')'`.
- **`get_id(self, version: int) -> str`**: Returns `self.expr.get_id(version)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text('(')`, calls `expr.describe_signature(...)`, appends `Text(')')`.

---

### Postfix Expressions Section

#### `ASTPostfixOp(ASTBase)` — abstract base.

#### `ASTPostfixCallExpr(ASTPostfixOp)`
- **Attributes**: `self.lst: Union[ASTParenExprList, ASTBracedInitList]`.
- **`_stringify(self, transform) -> str`**: Returns `transform(self.lst)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Calls `self.lst.describe_signature(...)`.

#### `ASTPostfixArray(ASTPostfixOp)`
- **Attributes**: `self.expr: ASTExpression`.
- **`_stringify(self, transform) -> str`**: Returns `'[' + transform(self.expr) + ']'`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text('[')`, calls `expr.describe_signature(...)`, appends `Text(']')`.

#### `ASTPostfixInc(ASTPostfixOp)`
- **`_stringify(self, transform) -> str`**: Returns `'++'`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text('++')`.

#### `ASTPostfixDec(ASTPostfixOp)`
- **`_stringify(self, transform) -> str`**: Returns `'--'`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text('--')`.

#### `ASTPostfixMember(ASTPostfixOp)`
- **Attributes**: `self.name: ASTNestedName`.
- **`_stringify(self, transform) -> str`**: Returns `'.' + transform(self.name)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text('.')`, calls `name.describe_signature(signode, 'noneIsName', env, symbol)`.

#### `ASTPostfixMemberOfPointer(ASTPostfixOp)`
- **Attributes**: `self.name: ASTNestedName`.
- **`_stringify(self, transform) -> str`**: Returns `'->' + transform(self.name)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text('->')`, calls `name.describe_signature(signode, 'noneIsName', env, symbol)`.

#### `ASTPostfixExpr(ASTExpression)`
- **Attributes**: `self.prefix: ASTExpression`, `self.postFixes: List[ASTPostfixOp]`.
- **`_stringify(self, transform) -> str`**: Joins transformed prefix and each postfix op.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Calls `prefix.describe_signature(...)`, then iterates postFixes calling each's `describe_signature`.

---

### Unary Expressions Section

#### `ASTUnaryOpExpr(ASTExpression)`
- **Attributes**: `self.op: str`, `self.expr: ASTExpression`.
- **`_stringify(self, transform) -> str`**: If `op[0] in 'cn'`, returns `transform(op) + " " + transform(expr)`; else `transform(op) + transform(expr)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text(self.op)`, appends space if `op[0] in 'cn'`, calls `expr.describe_signature(...)`.

#### `ASTSizeofType(ASTExpression)`
- **Attributes**: `self.typ: ASTType`.
- **`_stringify(self, transform) -> str`**: Returns `"sizeof(" + transform(self.typ) + ")"`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text('sizeof(')`, calls `typ.describe_signature(...)`, appends `Text(')')`.

#### `ASTSizeofExpr(ASTExpression)`
- **Attributes**: `self.expr: ASTExpression`.
- **`_stringify(self, transform) -> str`**: Returns `"sizeof " + transform(self.expr)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text('sizeof ')`, calls `expr.describe_signature(...)`.

#### `ASTAlignofExpr(ASTExpression)`
- **Attributes**: `self.typ: ASTType`.
- **`_stringify(self, transform) -> str`**: Returns `"alignof(" + transform(self.typ) + ")"`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text('alignof(')`, calls `typ.describe_signature(...)`, appends `Text(')')`.

---

### Other Expressions Section

#### `ASTCastExpr(ASTExpression)`
- **Attributes**: `self.typ: ASTType`, `self.expr: ASTExpression`.
- **`_stringify(self, transform) -> str`**: Returns `'(' + transform(typ) + ')' + transform(expr)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text('(')`, calls `typ.describe_signature(...)`, appends `Text(')')`, calls `expr.describe_signature(...)`.

#### `ASTBinOpExpr(ASTBase)`
- **Attributes**: `self.exprs: List[ASTExpression]`, `self.ops: List[str]` (len(exprs) == len(ops)+1).
- **`_stringify(self, transform) -> str`**: Joins exprs with `' ' + op + '` between each pair.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Calls `exprs[0].describe_signature(...)`, then for i=1..n: appends space, appends `Text(ops[i-1])`, appends space, calls `exprs[i].describe_signature(...)`.

#### `ASTAssignmentExpr(ASTExpression)`
- **Attributes**: `self.exprs: List[ASTExpression]`, `self.ops: List[str]` (len(exprs) == len(ops)+1).
- **Same logic as `ASTBinOpExpr`** for `_stringify` and `describe_signature`.

#### `ASTFallbackExpr(ASTExpression)`
- **Attributes**: `self.expr: str`.
- **`_stringify(self, transform) -> str`**: Returns `self.expr`.
- **`get_id(self, version: int) -> str`**: Returns `str(self.expr)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `nodes.Text(self.expr)` via `+=`.

---

### Types Section

#### `ASTTrailingTypeSpec(ASTBase)` — abstract base.

#### `ASTTrailingTypeSpecFundamental(ASTTrailingTypeSpec)`
- **Attributes**: `self.name: str`.
- **`_stringify(self, transform) -> str`**: Returns `self.name`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Appends `Text(str(self.name))`.

#### `ASTTrailingTypeSpecName(ASTTrailingTypeSpec)`
- **Attributes**: `self.prefix: str`, `self.nestedName: ASTNestedName`.
- **`name(self) -> ASTNestedName`** (property): Returns `self.nestedName`.
- **`_stringify(self, transform) -> str`**: If prefix, returns `prefix + ' ' + transform(nestedName)`; else just `transform(nestedName)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: If prefix, appends `desc_annotation(prefix, prefix)` and space; calls `nestedName.describe_signature(signode, mode, env, symbol=symbol)`.

#### `ASTFunctionParameter(ASTBase)`
- **Attributes**: `self.arg: ASTTypeWithInit`, `self.ellipsis: bool` (default `False`).
- **`_stringify(self, transform) -> str`**: Returns `'...'` if ellipsis; else `transform(self.arg)`.
- **`describe_signature(self, signode: Any, mode, env, symbol) -> None`**: Validates mode. If ellipsis, appends `Text('...')`; else calls `arg.describe_signature(signode, mode, env, symbol=symbol)`.

#### `ASTParameters(ASTBase)`
- **Attributes**: `self.args: List[ASTFunctionParameter]`.
- **`function_params(self) -> List[ASTFunctionParameter]`** (property): Returns `self.args`.
- **`_stringify(self, transform) -> str`**: Joins args with `', '` inside parens.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode. Creates `desc_parameterlist()`. For each arg: creates `desc_parameter('', '', noemph=True)`; if mode is `'lastIsName'`, calls `arg.describe_signature(param, 'param', env, symbol=symbol)`; else calls with `'markType'`; appends param to list; adds list to signode.

#### `ASTDeclSpecsSimple(ASTBaseBase)`
- **Attributes**: `self.storage: str`, `self.threadLocal: str`, `self.inline: bool`, `self.restrict: bool`, `self.volatile: bool`, `self.const: bool`, `self.attrs: List[Any]`.
- **`mergeWith(self, other: ASTDeclSpecsSimple) -> ASTDeclSpecsSimple`**: Returns new instance with `storage = self.storage or other.storage`, `threadLocal = self.threadLocal or other.threadLocal`, and boolean fields using `or`; attrs concatenated.
- **`_stringify(self, transform) -> str`**: Builds list: attrs first (transformed), then storage, threadLocal, inline, restrict, volatile, const (each only if truthy); joins with space.
- **`describe_signature(self, modifiers: List[Node]) -> None`**: Inner `_add(modifiers, text)` helper appends space separator and `desc_annotation(text, text)`. Iterates attrs calling each's `describe_signature(modifiers)`, then adds storage/threadLocal/inline/restrict/volatile/const annotations if truthy.

#### `ASTDeclSpecs(ASTBase)`
- **Attributes**: `self.outer: str`, `self.leftSpecs: ASTDeclSpecsSimple`, `self.rightSpecs: ASTDeclSpecsSimple`, `self.allSpecs: ASTDeclSpecsSimple` (merged from left+right), `self.trailingTypeSpec: Optional[ASTTrailingTypeSpec]`.
- **`_stringify(self, transform) -> str`**: Builds list: left specs; if trailing exists, adds space + transformed trailing; then right specs with space separator. Joins all.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode. Calls `leftSpecs.describe_signature(modifiers)` collecting into a modifiers list; appends each modifier to signode. If trailing exists: adds space if modifiers non-empty; calls `trailingTypeSpec.describe_signature(signode, ...)`, clears modifiers, calls `rightSpecs.describe_signature(modifiers)`, appaces space if needed, appends all modifiers to signode.

---

### Declarator Section

#### `ASTArray(ASTBase)`
- **Attributes**: `self.static: bool`, `self.const: bool`, `self.volatile: bool`, `self.restrict: bool`, `self.vla: bool` (variable-length array), `self.size: Optional[ASTExpression]`. Asserts: if vla then size is None; if size not None then not vla.
- **`_stringify(self, transform) -> str`**: Builds el list with static/restrict/volatile/const keywords in that order. If vla, returns `'[' + ' '.join(el) + '*]'`. Else appends transformed size to el and returns `'[' + ' '.join(el) + ']'`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode; appends `Text('[')`. Inner `_add(signode, text)` adds space separator then annotation. Adds static/restrict/volatile/const annotations if truthy. If vla: appends `Text('*')`. Else if size: adds space and calls `size.describe_signature(...)`. Appends `Text(']')`.

#### `ASTDeclarator(ASTBase)` — abstract base with three properties (all raise `NotImplementedError`):
- **`name(self) -> ASTNestedName`**
- **`function_params(self) -> List[ASTFunctionParameter]`**
- **`require_space_after_declSpecs(self) -> bool`**

#### `ASTDeclaratorNameParam(ASTDeclarator)`
- **Attributes**: `self.declId: Optional[ASTNestedName]`, `self.arrayOps: List[ASTArray]`, `self.param: Optional[ASTParameters]`.
- **`name(self) -> ASTNestedName`** (property): Returns `self.declId`.
- **`function_params(self) -> List[ASTFunctionParameter]`** (property): Returns `self.param.function_params`.
- **`require_space_after_declSpecs(self) -> bool`**: Returns `self.declId is not None`.
- **`_stringify(self, transform) -> str`**: Joins transformed declId (if present), each array op, and param (if present).
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode. Calls `declId.describe_signature(...)` if present; iterates arrayOps calling their describe_signature; calls `param.describe_signature(...)` if present.

#### `ASTDeclaratorNameBitField(ASTDeclarator)`
- **Attributes**: `self.declId: ASTNestedName`, `self.size: ASTExpression`.
- **`name(self) -> ASTNestedName`** (property): Returns `self.declId`.
- **`require_space_after_declSpecs(self) -> bool`**: Returns `self.declId is not None`.
- **`_stringify(self, transform) -> str`**: Joins transformed declId (if present), `' : '`, and transformed size.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode. Calls `declId.describe_signature(...)` if present; appends `Text(' : ')`; calls `size.describe_signature(...)`.

#### `ASTDeclaratorPtr(ASTDeclarator)`
- **Attributes**: `self.next: ASTDeclarator`, `self.restrict: bool`, `self.volatile: bool`, `self.const: bool`, `self.attrs: Any`. Asserts next is truthy.
- **`name(self) -> ASTNestedName`** (property): Returns `self.next.name`.
- **`function_params(self) -> List[ASTFunctionParameter]`** (property): Returns `self.next.function_params`.
- **`require_space_after_declSpecs(self) -> bool`**: Returns truthy if any of: const, volatile, restrict, attrs non-empty, or `next.require_space_after_declSpecs()`.
- **`_stringify(self, transform) -> str`**: Starts with `'*'`, appends transformed attrs. Adds space separator between attrs and qualifiers if needed. Appends restrict/volatile/const keywords (with spaces). Adds space before next if any qualifier/attr present and next requires it. Appends transformed next.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode; appends `Text('*')`; calls each attr's `describe_signature(signode)`; adds space separator if attrs + qualifiers both present. Inner `_add_anno(signode, text)` appends annotation. Adds restrict/volatile/const annotations with spaces between them as needed. If any qualifier/attr present and next requires space: adds space. Calls `next.describe_signature(...)`.

#### `ASTDeclaratorParen(ASTDeclarator)`
- **Attributes**: `self.inner: ASTDeclarator`, `self.next: ASTDeclarator`. Asserts both truthy.
- **`name(self) -> ASTNestedName`** (property): Returns `self.inner.name`.
- **`function_params(self) -> List[ASTFunctionParameter]`** (property): Returns `self.inner.function_params`.
- **`require_space_after_declSpecs(self) -> bool`**: Always returns `True`.
- **`_stringify(self, transform) -> str`**: Returns `'(' + transform(inner) + ')' + transform(next)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode; appends `Text('(')`; calls `inner.describe_signature(...)` with given mode; appends `Text(')')`; calls `next.describe_signature(signode, "noneIsName", env, symbol)`.

---

### Initializer Section

#### `ASTParenExprList(ASTBase)`
- **Attributes**: `self.exprs: List[ASTExpression]`.
- **`_stringify(self, transform) -> str`**: Returns `'(%s)' % ', '.join(transform(e) for e in self.exprs)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode; appends `Text('(')`; iterates exprs with comma-space separator between them calling each's describe_signature; appends `Text(')')`.

#### `ASTBracedInitList(ASTBase)`
- **Attributes**: `self.exprs: List[ASTExpression]`, `self.trailingComma: bool`.
- **`_stringify(self, transform) -> str`**: Returns `'{' + ', '.join(transform(e)) + (',' if trailingComma else '') + '}'`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode; appends `Text('{')`; iterates exprs with comma-space separator calling each's describe_signature; appends `Text(',')` if trailingComma; appends `Text('}')`.

#### `ASTInitializer(ASTBase)`
- **Attributes**: `self.value: Union[ASTBracedInitList, ASTExpression]`, `self.hasAssign: bool` (default `True`).
- **`_stringify(self, transform) -> str`**: Returns `' = ' + val` if hasAssign; else just `val`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode. If hasAssign: appends `Text(' = ')`; calls `value.describe_signature(signode, 'markType', env, symbol)`.

#### `ASTType(ASTBase)`
- **Attributes**: `self.declSpecs: ASTDeclSpecs`, `self.decl: ASTDeclarator`. Asserts both truthy.
- **`name(self) -> ASTNestedName`** (property): Returns `self.decl.name`.
- **`function_params(self) -> List[ASTFunctionParameter]`** (property): Returns `self.decl.function_params`.
- **`_stringify(self, transform) -> str`**: Joins transformed declSpecs with space (if needed and non-empty) and transformed decl.
- **`get_type_declaration_prefix(self) -> str`**: Returns `'typedef'` if `declSpecs.trailingTypeSpec`; else `'type'`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode; calls `declSpecs.describe_signature(signode, 'markType', env, symbol)`; adds space if needed and declSpecs non-empty. If mode is `'markType'`, changes to `'noneIsName'`; calls `decl.describe_signature(signode, mode, env, symbol)`.

#### `ASTTypeWithInit(ASTBase)`
- **Attributes**: `self.type: ASTType`, `self.init: Optional[ASTInitializer]`.
- **`name(self) -> ASTNestedName`** (property): Returns `self.type.name`.
- **`_stringify(self, transform) -> str`**: Joins transformed type and init (if present).
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode; calls `type.describe_signature(...)`; if init: calls `init.describe_signature(...)`.

#### `ASTMacroParameter(ASTBase)`
- **Attributes**: `self.arg: Optional[ASTNestedName]`, `self.ellipsis: bool` (default `False`).
- **`_stringify(self, transform) -> str`**: Returns `'...'` if ellipsis; else `transform(self.arg)`.
- **`describe_signature(self, signode: Any, mode, env, symbol) -> None`**: Validates mode. If ellipsis: appends `Text('...')`; else calls `arg.describe_signature(signode, mode, env, symbol=symbol)`.

#### `ASTMacro(ASTBase)`
- **Attributes**: `self.ident: ASTNestedName`, `self.args: Optional[List[ASTMacroParameter]]` (None means no-parameter macro).
- **`name(self) -> ASTNestedName`** (property): Returns `self.ident`.
- **`_stringify(self, transform) -> str`**: Joins transformed ident; if args is not None, appends `'('`, comma-separated transformed args, and `')'`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode. Calls `ident.describe_signature(...)`. If args is None: returns early. Otherwise creates `desc_parameterlist()`, adds each arg as a parameter (with `'param'` mode), appends list to signode.

#### `ASTStruct(ASTBase)`
- **Attributes**: `self.name: ASTNestedName`.
- **`get_id(self, version: int, objectType: str, symbol: Symbol) -> str`**: Returns `symbol.get_full_nested_name().get_id(version)`.
- **`_stringify(self, transform) -> str`**: Returns `transform(self.name)`.
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode; calls `name.describe_signature(signode, mode, env, symbol=symbol)`.

#### `ASTUnion(ASTBase)` — identical structure to `ASTStruct`: name attribute, same get_id/_stringify/describe_signature.

#### `ASTEnum(ASTBase)` — identical structure to `ASTStruct`: name attribute, same get_id/_stringify/describe_signature.

#### `ASTEnumerator(ASTBase)`
- **Attributes**: `self.name: ASTNestedName`, `self.init: Optional[ASTInitializer]`.
- **`get_id(self, version: int, objectType: str, symbol: Symbol) -> str`**: Returns `symbol.get_full_nested_name().get_id(version)`.
- **`_stringify(self, transform) -> str`**: Joins transformed name and init (if present).
- **`describe_signature(self, signode, mode, env, symbol) -> None`**: Validates mode; calls `name.describe_signature(signode, mode, env, symbol)`; if init: calls `init.describe_signature(signode, 'markType', env, symbol)`.

#### `ASTDeclaration(ASTBaseBase)`
- **Attributes**: `self.objectType: str`, `self.directiveType: str`, `self.declaration: Any` (the parsed AST node), `self.semicolon: bool`, `self.symbol: Optional[Symbol]`, `self.enumeratorScopedSymbol: Optional[Symbol]`.
- **`name(self) -> ASTNestedName`** (property): Returns `self.declaration.name`.
- **`function_params(self) -> List[ASTFunctionParameter]`** (property): If objectType is `'function'`, returns `self.declaration.function_params`; else `None`.
- **`get_id(self, version: int, prefixed: bool = True) -> str`**: If objectType is `'enumerator'` and enumeratorScopedSymbol exists: returns that symbol's declaration's get_id. Else gets full nested name id; if prefixed, prepends `_id_prefix[version]`; else returns raw id.
- **`get_newest_id(self) -> str`**: Returns `self.get_id(_max_id, True)`.
- **`_stringify(self, transform) -> str`**: Returns transformed declaration + `';'` if semicolon.
- **`describe_signature(self, signode: TextElement, mode: str, env: BuildEnvironment, options: Dict) -> None`**: Validates mode; asserts symbol is set. Sets `signode['is_multiline'] = True`. Creates `desc_signature_line()` with `sphinx_line_type='declarator'`; sets `add_permalink` to not self.symbol.isRedeclaration. Adds prefix annotation based on objectType: `'struct '` for struct, `'union '` for union, `'enum '` for enum, `'enumerator '` for enumerator; calls `declaration.get_type_declaration_prefix() + ' '` for type; asserts False otherwise. Calls `declaration.describe_signature(mainDeclNode, mode, env, self.symbol)`. Appends `Text(';')` if semicolon.

---

### Symbol Table Section

#### `SymbolLookupResult`
- **Attributes**: `self.symbols: Iterator[Symbol]`, `self.parentSymbol: Symbol`, `self.ident: ASTIdentifier`.

#### `LookupKey`
- **Attributes**: `self.data: List[Tuple[ASTIdentifier, str]]`.
- **`__str__(self) -> str`**: Returns `'[{ident, id_}, ...]'` formatted string.

#### `Symbol` — the core symbol tree node.
- **Class attributes**: `debug_indent = 0`, `debug_indent_string = "  "`, `debug_lookup = False`, `debug_show_tree = False`.
- **Static method** `debug_print(*args: Any) -> None`: Prints indented args to stdout.

- **`__setattr__(self, key: str, value: Any) -> None`**: Blocks setting `children`; delegates all others to `super().__setattr__()`.

- **`__init__(self, parent: Optional[Symbol], ident: Optional[ASTIdentifier], declaration: Optional[ASTDeclaration], docname: str) -> None`**: Sets `parent`, `siblingAbove=None`, `siblingBelow=None`, `ident`, `declaration`, `docname`, `isRedeclaration=False`. Asserts invariants (no parent → no declaration/docname; has declaration → has docname). Initializes `_children=[]`, `_anonChildren=[]`; appends self to parent's `_children` if parent exists. Sets `declaration.symbol = self` if declaration exists. Calls `_add_function_params()`.

- **`_assert_invariants(self) -> None`**: If no parent: asserts no declaration and no docname. Else: if has declaration, asserts has docname.

- **`_fill_empty(self, declaration: ASTDeclaration, docname: str) -> None`**: Asserts invariants; asserts current declaration/docname are falsy; sets both (and `declaration.symbol = self`); re-asserts invariants; calls `_add_function_params()`.

- **`_add_function_params(self) -> None`**: If debug, increments indent. If declaration exists and has function_params: for each parameter p with non-null arg and nested name nn: creates `ASTDeclaration('functionParam', None, p)`; asserts nn is not rooted and has exactly one name; calls `_add_symbols(nn, decl, self.docname)`.

- **`remove(self) -> None`**: If parent exists: removes self from parent's `_children`; sets parent to None.

- **`clear_doc(self, docname: str) -> None`**: Recursively clears children. For each child with declaration matching the given docname: nulls declaration and docname; updates sibling links (above/below); appends child to newChildren list. Replaces `_children`.

- **`get_all_symbols(self) -> Iterator[Symbol]`**: Yields self, then recursively yields all descendants via `_children`.

- **`children_recurse_anon(self) -> Iterator[Symbol]`** (property): For each child: yields it; if anonymous, also yields from its recursive children.

- **`get_lookup_key(self) -> LookupKey`**: Walks up parent chain collecting symbols; reverses to get root-first order. Builds key list of `(ident, declaration.get_newest_id())` tuples (or `(ident, None)` if no declaration). Returns `LookupKey(key)`.

- **`get_full_nested_name(self) -> ASTNestedName`**: Walks up parent chain collecting symbols; reverses to get root-first order. Builds list of ident values; returns `ASTNestedName(names, rooted=False)`.

- **`_find_first_named_symbol(self, ident: ASTIdentifier, matchSelf: bool, recurseInAnon: bool) -> Optional[Symbol]`**: Calls `_find_named_symbols(...)` with `searchInSiblings=False`; returns first yielded symbol or None.

- **`_find_named_symbols(self, ident: ASTIdentifier, matchSelf: bool, recurseInAnon: bool, searchInSiblings: bool) -> Iterator[Symbol]`**: Debug logging. Inner `candidates()` generator yields self (if matchSelf), then children (recursive anon or flat), then walks up sibling chain via `siblingAbove`. For each candidate with matching ident, yields it.

- **`_symbol_lookup(self, nestedName: ASTNestedName, onMissingQualifiedSymbol: Callable[[Symbol, ASTIdentifier], Symbol], ancestorLookupType: str, matchSelf: bool, recurseInAnon: bool, searchInSiblings: bool) -> Optional[SymbolLookupResult]`**: Debug logging. Determines starting point: if rooted, walks to root; if ancestorLookupType is set, walks up until first identifier matches. Iterates all names except last: calls `_find_first_named_symbol`; on missing, calls `onMissingQualifiedSymbol`. Sets matchSelf=False after each intermediate name. Handles last name via `_find_named_symbols`. Returns `SymbolLookupResult` or None.

- **`_add_symbols(self, nestedName: ASTNestedName, declaration: Optional[ASTDeclaration], docname: str) -> Symbol`**: Debug logging. Inner `onMissingQualifiedSymbol(parent, ident)` creates a new empty Symbol. Calls `_symbol_lookup`. If no symbols found: creates and returns new Symbol. If declaration is None (scope creation only): returns first symbol. Otherwise partitions existing symbols into noDecl/withDecl/dupDecl. For non-function types with declarations: asserts at most one; calls `handleDuplicateDeclaration` which sets `isRedeclaration=True` on candidate and raises `_DuplicateSymbolError`. For functions: compares IDs; if match, same handler. If no empty slots and candidate exists: returns candidate. Else fills first empty slot via `_fill_empty`, or creates new candidate.

- **`merge_with(self, other: Symbol, docnames: List[str], env: BuildEnvironment) -> None`**: For each child of `other`: finds matching child in self; if not found, appends and sets parent. If both have declarations with different docnames: logs warning about duplicate. Recursively merges children.

- **`add_name(self, nestedName: ASTNestedName) -> Symbol`**: Calls `_add_symbols(nestedName, declaration=None, docname=None)`; returns result.

- **`add_declaration(self, declaration: ASTDeclaration, docname: str) -> Symbol`**: Calls `_add_symbols(declaration.name, declaration, docname)`; returns result.

- **`find_identifier(self, ident: ASTIdentifier, matchSelf: bool, recurseInAnon: bool, searchInSiblings: bool) -> Optional[Symbol]`**: Walks up from self through siblings (if searchInSiblings). At each level: checks self if matchSelf; iterates children (recursive anon or flat); returns first matching ident.

- **`direct_lookup(self, key: LookupKey) -> Optional[Symbol]`**: Starting at self, for each `(name, id_)` in key.data: searches `_children` for matching name; moves to that child. Returns final symbol or None.

- **`find_declaration(self, nestedName: ASTNestedName, typ: str, matchSelf: bool, recurseInAnon: bool) -> Optional[Symbol]`**: Calls `_symbol_lookup` with `ancestorLookupType=typ` and inner `onMissingQualifiedSymbol` returning None. Returns first matching symbol or None.

- **`to_string(self, indent: int) -> str`**: Builds string representation: `'::'` if no parent; else ident/declaration name + `": "` + declaration string (with `'!!duplicate!! '` prefix if redeclaration) + tab+docname in parens. Newline terminated.

- **`dump(self, indent: int) -> str`**: Returns own to_string plus recursively dumped children with incremented indent.

---

### Parser Section

#### `DefinitionParser(BaseParser)`
- **Class attributes**: `_simple_fundamental_types = ('void', '_Bool', 'bool', 'char', 'int', 'float', 'double', '__int64')`, `_prefix_keys = ('struct', 'enum', 'union')`.
- **`language(self) -> str`** (property): Returns `'C'`.
- **`id_attributes(self)`** (property): Returns `self.config.c_id_attributes`.
- **`paren_attributes(self)`** (property): Returns `self.config.c_paren_attributes`.

- **`_parse_string(self) -> Optional[str]`**: If current char is not `'`, returns None. Scans until closing quote respecting escapes; returns the matched string slice.

- **`_parse_literal(self) -> ASTLiteral`**: Skips whitespace. Checks for `true`/`false` keywords → `ASTBooleanLiteral`. Tries float, binary, hex, integer, octal regexes in order (consuming trailing type suffix chars u/U/l/L/f/F). Returns `ASTNumberLiteral`. Parses string via `_parse_string()` → `ASTStringLiteral`. Matches char literal regex → `ASTCharLiteral` (handles UnicodeDecodeError and UnsupportedMultiCharacterCharLiteral).

- **`_parse_paren_expression(self) -> Optional[ASTExpression]`**: If not `'('`, returns None. Parses inner expression, expects `')'`, wraps in `ASTParenExpr`.

- **`_parse_primary_expression(self) -> ASTExpression`**: Tries literal → parenthesized expr → nested name (wrapped as `ASTIdExpression`). Returns first success or None.

- **`_parse_initializer_list(self, name: str, open: str, close: str) -> Tuple[List[ASTExpression], bool]`**: Parses `{...}` or `(...)` initializer list. Handles trailing comma for braces. Returns `(exprs, trailingComma)` or `(None, None)`.

- **`_parse_paren_expression_list(self) -> Optional[ASTParenExprList]`**: Calls `_parse_initializer_list('(', ')')`, returns `ASTParenExprList(exprs)` or None.

- **`_parse_braced_init_list(self) -> Optional[ASTBracedInitList]`**: Calls `_parse_initializer_list('{', '}')`, returns `ASTBracedInitList(exprs, trailingComma)` or None.

- **`_parse_postfix_expression(self) -> ASTPostfixExpr`**: Parses primary expression as prefix. Then loops: checks `[expr]` → `ASTPostfixArray`; `.` (not followed by `*` or `..`) → `ASTPostfixMember`; `->` (not followed by `*`) → `ASTPostfixMemberOfPointer`; `++` → `ASTPostfixInc`; `--` → `ASTPostfixDec`; paren expr list → `ASTPostfixCallExpr`. Returns `ASTPostfixExpr(prefix, postFixes)`.

- **`_parse_unary_expression(self) -> ASTExpression`**: Skips whitespace. Tries each unary op (`_expression_unary_ops`) — words for ops starting with c/n, strings otherwise; if matched, recursively parses cast expression → `ASTUnaryOpExpr(op, expr)`. Checks `sizeof` word: if followed by `(type)` → `ASTSizeofType(typ)`; else → `ASTSizeofExpr(expr)`. Checks `alignof`: expects `(type)` → `ASTAlignofExpr(typ)`. Falls through to `_parse_postfix_expression()`.

- **`_parse_cast_expression(self) -> ASTExpression`**: If `'('`, tries parsing as type cast: parses type, expects `')'`, recursively parses cast expression → `ASTCastExpr(typ, expr)`. On DefinitionError, backtracks and tries unary expression. Returns first success or raises multi-error.

- **`_parse_logical_or_expression(self) -> ASTExpression`**: Recursive descent parser for binary operators by precedence level (from `_expression_bin_ops`). Inner `_parse_bin_op_expr(opId)` recursively calls next-precedence level as base parser, then loops consuming matching operators and operands → `ASTBinOpExpr(exprs, ops)`.

- **`_parse_conditional_expression_tail(self, orExprHead: Any) -> None`**: Returns None (not yet implemented).

- **`_parse_assignment_expression(self) -> ASTExpression`**: Parses logical-or expression as head. Loops consuming assignment operators (`_expression_assignment_ops`) and operands → `ASTAssignmentExpr(exprs, ops)`.

- **`_parse_constant_expression(self) -> ASTExpression`**: Returns `_parse_logical_or_expression()`.

- **`_parse_expression(self) -> ASTExpression`**: Returns `_parse_assignment_expression()`.

- **`_parse_expression_fallback(self, end: List[str], parser: Callable[[], ASTExpression], allow: bool = True) -> ASTExpression`**: First tries the provided parser. On failure (and if allowed), falls back to scanning: handles strings via regex; otherwise scans character-by-character tracking bracket nesting (`{}`, `()`, `[]`) until hitting an end character or EOF → returns `ASTFallbackExpr(value.strip())`.

- **`_parse_nested_name(self) -> ASTNestedName`**: Skips whitespace. Checks for leading `'.'` (rooted). Loops: matches identifier via regex, checks not a keyword, creates `ASTIdentifier`, appends to names list; if followed by `'.'`, continues; else breaks. Returns `ASTNestedName(names, rooted)`.

- **`_parse_trailing_type_spec(self) -> ASTTrailingTypeSpec`**: Checks simple fundamental types first. Then tries signed/unsigned + long/short chain + char/int/double/__int64 → `ASTTrailingTypeSpecFundamental(' '.join(elements))`. Otherwise checks for struct/enum/union prefix, then parses nested name → `ASTTrailingTypeSpecName(prefix, nestedName)`.

- **`_parse_parameters(self, paramMode: str) -> Optional[ASTParameters]`**: If not `'('`, returns None (unless paramMode is 'function', which fails). Parses parameter list: ellipsis → `ASTFunctionParameter(None, True)`; otherwise parses type with init (`named='single'`) → `ASTFunctionParameter(arg)`. Returns `ASTParameters(args)`.

- **`_parse_decl_specs_simple(self, outer: str, typed: bool) -> ASTDeclSpecsSimple`**: Parses storage (auto/register for member; static/extern for member/function), thread_local/_Thread_local (member only), inline (function only), restrict/volatile/const (typed only), and attributes. Returns `ASTDeclSpecsSimple(storage, threadLocal, inline, restrict, volatile, const, attrs)`.

- **`_parse_decl_specs(self, outer: str, typed: bool = True) -> ASTDeclSpecs`**: Parses left specs; if typed, parses trailing type spec and right specs. Returns `ASTDeclSpecs(outer, leftSpecs, rightSpecs, trailing)`.

- **`_parse_declarator_name_suffix(self, named: Union[bool, str], paramMode: str, typed: bool) -> ASTDeclarator`**: Parses optional name (nested name or single identifier). Then loops array ops (`[` with static/const/volatile/restrict qualifiers and size/VLA `*`). Then parses parameters. If no params and no arrays but bit-field colon present → `ASTDeclaratorNameBitField`. Otherwise → `ASTDeclaratorNameParam(declId, arrayOps, param)`.

- **`_parse_declarator(self, named: Union[bool, str], paramMode: str, typed: bool = True) -> ASTDeclarator`**: If starts with `*`: parses restrict/volatile/const/attrs recursively → `ASTDeclaratorPtr(next, ...)`. If starts with `(`: tries name-suffix first; on failure, treats as `( ptr-declarator )` → `ASTDeclaratorParen(inner, next)`. Otherwise falls through to name-suffix.

- **`_parse_initializer(self, outer: str = None, allowFallback: bool = True) -> Optional[ASTInitializer]`**: If `'='`, parses braced init list or expression fallback → `ASTInitializer(value)`; else returns None.

- **`_parse_type(self, named: Union[bool, str], outer: str = None) -> ASTType`**: For `outer='type'`: tries untyped (just name) first, then typed declaration. For `outer='function'`: parses decl specs + declarator with paramMode='function'. Otherwise: parses type with init or just type → returns `ASTType(declSpecs, decl)`.

- **`_parse_type_with_init(self, named, outer) -> ASTTypeWithInit`**: Calls `_parse_type()` then `_parse_initializer()`, returns `ASTTypeWithInit(type, init)`.

- **`_parse_macro(self) -> ASTMacro`**: Parses nested name identifier. If no `'('`, returns macro with args=None. If empty parens → args=[]. Otherwise parses comma-separated parameter names (or ellipsis) → `ASTMacro(ident, args)`.

- **`_parse_struct(self) -> ASTStruct`**: Returns `ASTStruct(_parse_nested_name())`.
- **`_parse_union(self) -> ASTUnion`**: Returns `ASTUnion(_parse_nested_name())`.
- **`_parse_enum(self) -> ASTEnum`**: Returns `ASTEnum(_parse_nested_name())`.

- **`_parse_enumerator(self) -> ASTEnumerator`**: Parses nested name. If `'='`, parses constant expression → `ASTInitializer(initVal)`. Returns `ASTEnumerator(name, init)`.

- **`parse_declaration(self, objectType: str, directiveType: str) -> ASTDeclaration`**: Validates objectType and directiveType against allowed sets. Dispatches to appropriate `_parse_*` method based on objectType. Skips optional semicolon (not for macros). Returns `ASTDeclaration(objectType, directiveType, declaration, semicolon)`.

- **`parse_namespace_object(self) -> ASTNestedName`**: Returns `_parse_nested_name()`.

- **`parse_xref_object(self) -> ASTNestedName`**: Parses nested name; skips trailing `'()'`; asserts end.

- **`parse_expression(self) -> Union[ASTExpression, ASTType]`**: Tries expression parse first; on failure, tries type parse; raises multi-error if both fail.

---

### Helper Function

#### `_make_phony_error_name() -> ASTNestedName`
Returns `ASTNestedName([ASTIdentifier("PhonyNameDueToError")], rooted=False)`.

---

### Sphinx Directives & Objects Section

#### `CObject(ObjectDescription)` — base class for all C object descriptions.
- **Class attribute** `doc_field_types`: List of `[TypedField('parameter', ...), Field('returnvalue', ...), Field('returntype', ...)]` with specific name mappings and typerolename='type'.

- **`_add_enumerator_to_parent(self, ast: ASTDeclaration) -> None`**: If objectType is 'enumerator': finds parent symbol; if parent has a declaration that is an enum directive: searches target scope for existing ident; if not found, clones the declaration (setting `enumerationScopedSymbol`) and creates a new Symbol in the target scope.

- **`add_target_and_index(self, ast: ASTDeclaration, sig: str, signode: TextElement) -> None`**: Generates IDs for versions 1.._max_id; reverses order (newest first). If newestId not already in document ids: appends all non-conflicting compatibility ids to signode['ids']; calls `note_explicit_target(signode)`; registers object in domain via `domain.note_object(name, objtype, newestId)`. Appends single-entry index text.

- **`object_type(self) -> str`** (property): Raises NotImplementedError.
- **`display_object_type(self) -> str`** (property): Returns `self.object_type`.
- **`get_index_text(self, name: str) -> str`**: Returns `_('%s (C %s)') % (name, self.display_object_type)`.
- **`parse_definition(self, parser: DefinitionParser) -> ASTDeclaration`**: Calls `parser.parse_declaration(self.object_type, self.objtype)`.
- **`describe_signature(self, signode, ast, options) -> None`**: Calls `ast.describe_signature(signode, 'lastIsName', self.env, options)`.

- **`run(self) -> List[Node]`**: Initializes parent symbol from domain root if not set; sets up ref_context with lookup key; initializes last_symbol to None. Calls `super().run()`.

- **`handle_signature(self, sig: str, signode: TextElement) -> ASTDeclaration`**: Creates parser; tries parse_definition + assert_end. On DefinitionError: logs warning, creates phony name symbol, raises ValueError. On success: adds declaration to parent symbol tree; links sibling list (above/below); tracks last_symbol. On `_DuplicateSymbolError`: uses the existing symbol and logs warning. If objectType is 'enumerator': calls `_add_enumerator_to_parent`. Calls describe_signature with options dict. Returns ast.

- **`before_content(self) -> None`**: Saves current parent symbol and key; updates to last_symbol's scope.
- **`after_content(self) -> None`**: Restores saved parent symbol and key.
- **`make_old_id(self, name: str) -> str`**: Returns `'c.' + name`.

#### `CMemberObject(CObject)` — `object_type = 'member'`. Overrides `display_object_type` to return `self.objtype` (which can be 'member' or 'var').

#### `CFunctionObject(CObject)` — `object_type = 'function'`.

#### `CMacroObject(CObject)` — `object_type = 'macro'`.

#### `CStructObject(CObject)` — `object_type = 'struct'`.

#### `CUnionObject(CObject)` — `object_type = 'union'`.

#### `CEnumObject(CObject)` — `object_type = 'enum'`.

#### `CEnumeratorObject(CObject)` — `object_type = 'enumerator'`.

#### `CTypeObject(CObject)` — `object_type = 'type'`.

---

### Namespace Directives Section

#### `CNamespaceObject(SphinxDirective)`
- **Class attributes**: `has_content = False`, `required_arguments = 1`, `optional_arguments = 0`, `final_argument_whitespace = True`, `option_spec = {}`.
- **`run(self) -> List[Node]`**: If argument is 'NULL'/'0'/'nullptr': sets symbol to root, empty stack. Otherwise: parses namespace name; on error creates phony name; calls `rootSymbol.add_name(name)`; pushes result onto stack. Sets parent_symbol and ref_context in temp_data. Returns `[]`.

#### `CNamespacePushObject(SphinxDirective)`
- **Class attributes**: Same as CNamespaceObject.
- **`run(self) -> List[Node]`**: If argument is 'NULL'/'0'/'nullptr': returns `[]`. Parses namespace name; on error creates phony name. Gets old parent (from temp_data or root). Calls `oldParent.add_name(name)`; pushes onto stack. Sets parent_symbol, namespace_stack, ref_context. Returns `[]`.

#### `CNamespacePopObject(SphinxDirective)`
- **Class attributes**: `has_content = False`, `required_arguments = 0`, `optional_arguments = 0`, `final_argument_whitespace = True`, `option_spec = {}`.
- **`run(self) -> List[Node]`**: Pops from namespace_stack; if empty, logs warning and defaults to global scope. Sets parent_symbol (top of stack or root), namespace_stack, ref_context (`'cp:parent_key'`). Returns `[]`.

---

### Cross-Reference Roles Section

#### `CXRefRole(XRefRole)`
- **`process_link(self, env: BuildEnvironment, refnode: Element, has_explicit_title: bool, title: str, target: str) -> Tuple[str, str]`**: Updates refnode attributes from ref_context. If no explicit title: replaces anonymous identifiers via `anon_identifier_re.sub("[anonymous]", ...)`. Strips leading tilde from target; if title starts with `'~'`, strips it and removes everything up to last dot. Returns `(title, target)`.

#### `CExprRole(SphinxRole)`
- **`__init__(self, asCode: bool) -> None`**: If asCode: sets `class_type='c-expr'`, `node_type=nodes.literal`; else: `class_type='c-texpr'`, `node_type=nodes.inline`.
- **`run(self) -> Tuple[List[Node], List[system_message]]`**: Replaces newlines in text. Creates parser; tries `parse_expression()`. On error: logs warning, returns literal/inline node with raw text and classes `[xref, c, class_type]`. Gets parent symbol (from cpp temp_data or C root). Creates signode of appropriate type with classes `[xref, c, class_type]`; calls `ast.describe_signature(signode, 'markType', self.env, parentSymbol)`. Returns `[signode], []`.

---

### Domain Section

#### `CDomain(Domain)` — `"C language domain."`
- **Class attributes**: `name = 'c'`, `label = 'C'`.
- **`object_types`** (dict): Maps `'function'→ObjType('function','func')`, `'member'→ObjType('member','member')`, `'macro'→ObjType('macro','macro')`, `'type'→ObjType('type','type')`, `'var'→ObjType('variable','data')`.
- **`directives`** (dict): Maps directive names to CObject subclasses and namespace directives.
- **`roles`** (dict): Maps role names to `CXRefRole()` instances (with `fix_parens=True` for 'func'); `'expr'→CExprRole(asCode=True)`, `'texpr'→CExprRole(asCode=False)`.
- **`initial_data`**: `{'root_symbol': Symbol(None, None, None, None), 'objects': {}}`.

- **`objects(self) -> Dict[str, Tuple[str, str, str]]`** (property): Returns `self.data.setdefault('objects', {})`.
- **`note_object(self, name: str, objtype: str, node_id: str, location=None) -> None`**: If name already exists: logs warning about duplicate. Sets `self.objects[name] = (docname, node_id, objtype)`.

- **`clear_doc(self, docname: str) -> None`**: Debug logging. Calls `rootSymbol.clear_doc(docname)`. Removes all objects whose docname matches from self.objects.
- **`process_doc(self, env, docname, document) -> None`**: Debug logging only.
- **`process_field_xref(self, pnode: pending_xref) -> None`**: Updates pnode attributes from ref_context.

- **`merge_domaindata(self, docnames: List[str], otherdata: Dict) -> None`**: Debug logging. Calls `rootSymbol.merge_with(otherdata['root_symbol'], docnames, self.env)`. For each object in otherdata with docname in docnames: if already exists, logs warning; else copies into our objects dict.

- **`_resolve_xref_inner(self, env, fromdocname, builder, typ, target, node, contnode) -> Tuple[Element, str]`**: Parses target as xref object. Gets parent key from node or root symbol. Calls `parentSymbol.find_declaration(name, typ, matchSelf=True, recurseInAnon=True)`. If found: creates refnode via `make_refnode(builder, fromdocname, docname, declaration.get_newest_id(), contnode, displayName)`; returns `(refnode, objectType)`. Else returns `(None, None)`.

- **`resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode) -> Element`**: Calls `_resolve_xref_inner`, returns first element.
- **`resolve_any_xref(self, env, fromdocname, builder, target, node, contnode) -> List[Tuple[str, Element]]`**: Calls `_resolve_xref_inner` with typ='any' under suppressed logging; if found, returns `[('c:' + role_for_objtype(objtype), retnode)]`; else `[]`.

- **`get_objects(self) -> Iterator[Tuple[str, str, str, str, str, int]]`**: Yields `(refname, refname, objtype, docname, node_id, 1)` for each object.

---

### Setup Function

#### `setup(app: Sphinx) -> Dict[str, Any]`
- Calls `app.add_domain(CDomain)`.
- Adds config value `"c_id_attributes"` defaulting to `[]`, scope `'env'`.
- Adds config value `"c_paren_attributes"` defaulting to `[]`, scope `'env'`.
- Returns: `{'version': 'builtin', 'env_version': 2, 'parallel_read_safe': True, 'parallel_write_safe': True}`.

## sphinx/domains/cpp.py
The comprehensive module description has been written to `cpp_module_description.md` (909 lines, ~74KB). It covers all 15 major sections:

1. **Imports and Globals** — All imports from docutils/sphinx/util.cfamily; all regex patterns (`_string_re`, `_visibility_re`, `_operator_re`, etc.); all ID mapping dictionaries for v1/v2 mangling (`_id_fundamental_v1/v2`, `_id_operator_v1/v2`, `_expression_bin_ops`, etc.)
2. **Exception Classes** — `_DuplicateSymbolError`
3. **AST Base Classes** — `ASTBase`
4. **Name AST Classes** — `ASTIdentifier`, `ASTNestedNameElement`, `ASTNestedName` with full method signatures and logic
5. **Expression AST Classes** — All primary expressions (literals, this, fold), postfix ops (array/member/inc/dec/call), other expressions (casts, sizeof, alignof, noexcept, new/delete, binary ops, braced init lists, comma, fallback, pack expansion)
6. **Type AST Classes** — Operators, template args, trailing type specs, function parameters, noexcept spec, parameter qualifiers, decl specs (simple/full), declarators (name-param-qual, name-bitfield, ptr, ref, param-pack, memptr, paren), arrays, types with init, type using
7. **Other Declaration AST Classes** — Concept, base class, class, union, enum, enumerator
8. **Template AST Classes** — Template params (type/template-type/non-type/constrained), template introductions, declaration prefix
9. **Declaration AST Classes** — `ASTDeclaration` with full clone/get_id/stringify/describe_signature logic; `ASTNamespace`
10. **Symbol/LookupKey Infrastructure** — Full Symbol class: init, lookup methods (`_symbol_lookup`, `find_name`, `find_declaration`, `direct_lookup`), tree management (`merge_with`, `_add_symbols`, `clear_doc`), dump/stringify
11. **DefinitionParser Class** — All parsing methods from `_parse_attribute` through `parse_expression` with dispatch logic
12. **Sphinx Directive/Role Classes** — CPPObject base + all 9 subclasses, namespace push/pop, AliasNode/AliasTransform, CPPXRefRole, CPPExprRole
13. **CPPDomain Class** — Full domain implementation: xref resolution, object indexing, merge/clear, setup() function

## sphinx/util/cfamily.py
Now I have the complete file (437 lines). Here is the full natural-language specification:

---

## Module-Level Preamble

### Imports

```python
import re
import warnings
from copy import deepcopy
from typing import Any, Callable, List, Match, Pattern, Tuple, Union
from docutils import nodes
from docutils.nodes import TextElement
from sphinx.config import Config
from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.util import logging
```

### Constants & Globals

- **`logger`** — `logging.getLogger(__name__)`, the module-level logger.
- **`StringifyTransform`** — type alias: `Callable[[Any], str]`.
- **`_whitespace_re`** — compiled regex `re.compile(r'(?u)\s+')`, matches any Unicode whitespace.
- **`anon_identifier_re`** — compiled regex `r'(@[a-zA-Z0-9_])[a-zA-Z0-9_]*\b'`, matches anonymous entity identifiers starting with `@`.
- **`identifier_re`** — compiled multiline (`(?x)`) regex matching either: `( ~?\b[a-zA-Z_] )[a-zA-Z0-9_]*\b` (ordinary identifiers, optionally prefixed by `~`) or `(@[a-zA-Z0-9_])[a-zA-Z0-9_]*\b` (anonymous entity names).
- **`integer_literal_re`** — compiled regex `r'[1-9][0-9]*'`, matches non-zero-prefixed decimal integers.
- **`octal_literal_re`** — compiled regex `r'0[0-7]*'`, matches octal literals starting with `0`.
- **`hex_literal_re`** — compiled regex `r'0[xX][0-9a-fA-F][0-9a-fA-F]*'`, matches hex literals.
- **`binary_literal_re`** — compiled regex `r'0[bB][01][01]*'`, matches binary literals.
- **`float_literal_re`** — compiled multiline (`(?x)`) regex matching decimal floats (`[0-9]+[eE][+-]?[0-9]+`, `[0-9]*\.[0-9]+([eE][+-]?[0-9]+)?`, `[0-9]+\.` with optional exponent), or hex floats (`0[xX]...[pP][+-]?...`).
- **`char_literal_re`** — compiled multiline (`(?x)`) regex matching C/C++ character literals: optional prefix `(u8|u|U|L)?`, single-quoted content allowing either a non-backslash/non-quote char or an escape sequence (`\'`, `\"`, `\?`, `\\`, `\a`, `\b`, `\f`, `\n`, `\r`, `\t`, `\v`, octal `[0-7]{1,3}`, hex `\x[0-9a-fA-F]{2}`, unicode `\u[0-9a-fA-F]{4}`, or wide unicode `\U[0-9a-fA-F]{8}`).

### Module-Level Function

**`verify_description_mode(mode: str) -> None`**
- Validates that `mode` is one of the five allowed strings: `'lastIsName'`, `'noneIsName'`, `'markType'`, `'markName'`, `'param'`.
- Raises `Exception` with message `"Description mode '%s' is invalid." % mode` if not.

---

## Classes

### `NoOldIdError(Exception)`

An exception used to avoid implementing unneeded ID generation for old ID schemes.

**Attribute:**
- **`description: str`** (property) — emits a `RemovedInSphinx40Warning` deprecation warning and returns `str(self)`.

---

### `ASTBaseBase`

Abstract base class for all AST definition-expression nodes. Provides equality, cloning, stringification, and representation.

**Methods:**
- **`__eq__(self, other: Any) -> bool`** — Returns `False` if `type(self)` differs from `type(other)`. Otherwise iterates over `self.__dict__.items()` and compares each `(key, value)` pair against the corresponding attribute on `other` via `getattr`; returns `False` on any mismatch or `AttributeError`, else `True`.
- **`__hash__ = None`** — Explicitly sets hash to `None` (makes instances unhashable).
- **`clone(self) -> Any`** — Returns a deep copy of `self` via `deepcopy(self)`.
- **`_stringify(self, transform: StringifyTransform) -> str`** — Abstract; raises `NotImplementedError(repr(self))`. Subclasses override to produce the string representation.
- **`__str__(self) -> str`** — Calls `_stringify(lambda ast: str(ast))`.
- **`get_display_string(self) -> str`** — Calls `_stringify(lambda ast: ast.get_display_string())`.
- **`__repr__(self) -> str`** — Returns `'<%s>' % self.__class__.__name__`.

---

### `ASTAttribute(ASTBaseBase)`

Abstract base for attribute AST nodes.

**Methods:**
- **`describe_signature(self, signode: TextElement) -> None`** — Abstract; raises `NotImplementedError(repr(self))`. Subclasses append text to `signode`.

---

### `ASTCPPAttribute(ASTAttribute)`

Represents a C++11-style attribute (`[[arg]]`).

**Attributes:**
- **`arg: str`** — The raw argument string inside the double brackets.

**Methods:**
- **`__init__(self, arg: str) -> None`** — Sets `self.arg = arg`.
- **`_stringify(self, transform: StringifyTransform) -> str`** — Returns `"[[[" + self.arg + "]]]"`.
- **`describe_signature(self, signode: TextElement) -> None`** — Converts `str(self)` to text and appends it as a `nodes.Text(txt, txt)` node.

---

### `ASTGnuAttribute(ASTBaseBase)`

Represents a single GNU-style attribute name (e.g., `noreturn`).

**Attributes:**
- **`name: str`** — The attribute name.
- **`args: Any`** — Attribute arguments (typically `None`; parameterized attributes are not yet supported).

**Methods:**
- **`__init__(self, name: str, args: Any) -> None`** — Sets both attributes.
- **`_stringify(self, transform: StringifyTransform) -> str`** — Returns the attribute name; if `self.args` is truthy, appends `'('`, the transformed args string, and `')'`.

---

### `ASTGnuAttributeList(ASTAttribute)`

Represents a list of GNU-style attributes inside `__attribute__((...))`.

**Attributes:**
- **`attrs: List[ASTGnuAttribute]`** — The ordered list of attribute nodes.

**Methods:**
- **`__init__(self, attrs: List[ASTGnuAttribute]) -> None`** — Sets `self.attrs = attrs`.
- **`_stringify(self, transform: StringifyTransform) -> str`** — Returns `"__attribute__(("` followed by comma-separated transformed attribute strings, then `"))"`.
- **`describe_signature(self, signode: TextElement) -> None`** — Converts `str(self)` to text and appends it as a `nodes.Text(txt, txt)` node.

---

### `ASTIdAttribute(ASTAttribute)`

Represents a simple user-defined attribute (no arguments).

**Attributes:**
- **`id: str`** — The attribute identifier string.

**Methods:**
- **`__init__(self, id: str) -> None`** — Sets `self.id = id`.
- **`_stringify(self, transform: StringifyTransform) -> str`** — Returns `self.id`.
- **`describe_signature(self, signode: TextElement) -> None`** — Appends a `nodes.Text(self.id, self.id)` node.

---

### `ASTParenAttribute(ASTAttribute)`

Represents a user-defined parenthesized attribute (e.g., `deprecated(msg)`).

**Attributes:**
- **`id: str`** — The attribute identifier.
- **`arg: str`** — The raw argument string inside parentheses.

**Methods:**
- **`__init__(self, id: str, arg: str) -> None`** — Sets both attributes.
- **`_stringify(self, transform: StringifyTransform) -> str`** — Returns `self.id + '(' + self.arg + ')'`.
- **`describe_signature(self, signode: TextElement) -> None`** — Converts `str(self)` to text and appends it as a `nodes.Text(txt, txt)` node.

---

### `UnsupportedMultiCharacterCharLiteral(Exception)`

Raised when a multi-character character literal is encountered (not supported).

**Attribute:**
- **`decoded: str`** (property) — Emits a `RemovedInSphinx40Warning` deprecation warning and returns `str(self)`.

---

### `DefinitionError(Exception)`

Raised for definition parsing errors.

**Attribute:**
- **`description: str`** (property) — Emits a `RemovedInSphinx40Warning` deprecation warning and returns `str(self)`.

---

### `BaseParser`

Abstract base class for C/C++ definition parsers. Provides position-tracking, regex/string matching, whitespace skipping, balanced-token parsing, and attribute parsing.

**Attributes (set in `__init__`):**
- **`definition: str`** — The stripped input definition string.
- **`location`** — Location metadata (`nodes.Node` or `Tuple[str, int]`) for warning context.
- **`config: Config`** — Sphinx configuration object.
- **`pos: int`** — Current parse position (starts at 0).
- **`end: int`** — Length of the definition string.
- **`last_match: Match`** — The most recent successful regex match object.
- **`_previous_state: Tuple[int, Match]`** — Saved `(pos, last_match)` for backtracking.
- **`otherErrors: List[DefinitionError]`** — Accumulated secondary errors.
- **`allowFallbackExpressionParsing: bool`** — Defaults to `True`; set to `False` in tests.

**Methods:**

- **`__init__(self, definition: str, *, location: Union[nodes.Node, Tuple[str, int]], config: Config) -> None`** — Strips `definition`, stores all attributes, initializes `pos=0`, `end=len(definition)`.

- **`_make_multi_error(self, errors: List[Any], header: str) -> DefinitionError`** — Combines multiple `(error_obj, label)` tuples into a single `DefinitionError`. If only one error and non-empty header, prepends the header. Otherwise joins with labels (`"Main error"` / `"Potential other error"`) and indented multi-line formatting.

- **`language: str`** (property) — Abstract; raises `NotImplementedError`. Subclasses return their language name.

- **`status(self, msg: str) -> None`** — Debug helper; prints the message, definition, and a caret indicator at `self.pos`.

- **`fail(self, msg: str) -> None`** — Constructs a `DefinitionError` with language, message, position, definition text, and caret indicator. Appends any accumulated `otherErrors` as secondary errors. Clears `otherErrors`, then raises the combined error via `_make_multi_error`.

- **`warn(self, msg: str) -> None`** — Logs a warning at `self.location` using the module logger.

- **`match(self, regex: Pattern) -> bool`** — Attempts to match `regex` against `self.definition` starting at `self.pos`. On success: saves previous state `(pos, last_match)`, advances `pos` to `match.end()`, stores `last_match`, returns `True`. Returns `False` on no match.

- **`skip_string(self, string: str) -> bool`** — Checks if the substring at `self.pos` equals `string`; if so, advances `pos` by its length and returns `True`.

- **`skip_word(self, word: str) -> bool`** — Matches `\bword\b` (word-boundary-delimited) via `self.match()`.

- **`skip_ws(self) -> bool`** — Matches whitespace via `_whitespace_re`; advances position on success.

- **`skip_word_and_ws(self, word: str) -> bool`** — Calls `skip_word(word)`; if true, also calls `skip_ws()` and returns `True`.

- **`skip_string_and_ws(self, string: str) -> bool`** — Calls `skip_string(string)`; if true, also calls `skip_ws()` and returns `True`.

- **`eof: bool`** (property) — Returns `self.pos >= self.end`.

- **`current_char: str`** (property) — Returns the character at `self.definition[self.pos]`, or `'EOF'` if out of bounds.

- **`matched_text: str | None`** (property) — Returns `self.last_match.group()` if a match exists, else `None`.

- **`read_rest(self) -> str`** — Returns the remaining substring from `self.pos` to end, then sets `pos = end`.

- **`assert_end(self, *, allowSemicolon: bool = False) -> None`** — Skips trailing whitespace. If `allowSemicolon=False`, calls `fail()` if not at EOF. If `True`, fails unless the remaining text is exactly `';'`.

- **`id_attributes`** (property) — Abstract; raises `NotImplementedError`. Subclasses return a list of simple attribute identifier strings.

- **`paren_attributes`** (property) — Abstract; raises `NotImplementedError`. Subclasses return a list of parenthesized attribute identifier strings.

- **`_parse_balanced_token_seq(self, end: List[str]) -> str`** — Parses a balanced sequence of brackets/braces/parens until one of the characters in `end` is found at depth zero. Maintains a stack mapping opening to closing delimiters (`{`, `[`, `(`). On an unmatched closing delimiter, calls `fail()`. On EOF before finding end, calls `fail()` with position info. Returns the matched substring from start position to current `pos`.

- **`_parse_attribute(self) -> ASTAttribute | None`** — Parses a single attribute at the current position:
  1. Skips whitespace. Saves start position.
  2. **C++11 style:** If `'[['` is found, parses balanced token content up to `']'`, verifies two closing `]]` tokens (with optional whitespace), and returns `ASTCPPAttribute(arg)`.
  3. **GNU style:** If the word `'__attribute__'` is matched, expects `'(('`, then iterates: matches identifiers via `identifier_re`, optionally followed by `'('` (which triggers a "not yet supported" failure for parameterized attributes), appends each as `ASTGnuAttribute(name, None)`. Separated by commas or terminated by `')'`. Expects final closing `')'`. Returns `ASTGnuAttributeList(attrs)`.
  4. **User-defined simple id:** Iterates over `self.id_attributes`; if any word matches via `skip_word_and_ws`, returns `ASTIdAttribute(id)`.
  5. **User-defined paren attributes:** Iterates over `self.paren_attributes`; if an identifier is matched, expects `'('`, parses balanced token content up to `')'`, verifies closing `')'`, and returns `ASTParenAttribute(id, arg)`.
  6. If none match, returns `None`.