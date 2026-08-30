## sphinx/directives/other.py
Now I have the complete file. Here is the natural-language specification:

---

## Module-Level Preamble

### Imports

```python
import re
from typing import TYPE_CHECKING, Any, Dict, List, cast

from docutils import nodes
from docutils.nodes import Element, Node
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.admonitions import BaseAdmonition
from docutils.parsers.rst.directives.misc import Class
from docutils.parsers.rst.directives.misc import Include as BaseInclude

from sphinx import addnodes
from sphinx.domains.changeset import VersionChange  # NOQA  # for compatibility
from sphinx.locale import _, __
from sphinx.util import docname_join, logging, url_re
from sphinx.util.docutils import SphinxDirective
from sphinx.util.matching import Matcher, patfilter
from sphinx.util.nodes import explicit_title_re
from sphinx.util.typing import OptionSpec

if TYPE_CHECKING:
    from sphinx.application import Sphinx
```

### Constants & Globals

- **`glob_re`**: `re.compile(r'.*[*?\[].*')` — regex matching any string containing a glob wildcard character (`*`, `?`, or `[`).
- **`logger`**: `logging.getLogger(__name__)` — module-level logger.

---

## Code Objects

### Function: `int_or_nothing(argument: str) -> int`

Takes a single string argument. If the argument is falsy (empty string), returns `999`. Otherwise, converts and returns `int(argument)`. Used as an option converter for the `numbered` option of `TocTree`.

---

### Class: `TocTree(SphinxDirective)`

Directive to define a table-of-contents tree structure.

**Class attributes:**
- `has_content = True` — accepts body content lines.
- `required_arguments = 0`, `optional_arguments = 0` — no arguments.
- `final_argument_whitespace = False`.
- **`option_spec`**: A dict mapping option names to converters:
  - `'maxdepth'`: `int`
  - `'name'`: `directives.unchanged`
  - `'caption'`: `directives.unchanged_required`
  - `'glob'`: `directives.flag`
  - `'hidden'`: `directives.flag`
  - `'includehidden'`: `directives.flag`
  - `'numbered'`: `int_or_nothing`
  - `'titlesonly'`: `directives.flag`
  - `'reversed'`: `directives.flag`

#### Method: `run(self) -> List[Node]`

1. Creates an `addnodes.toctree()` node (`subnode`). Sets its `'parent'` attribute to `self.env.docname`.
2. Initializes `subnode['entries'] = []` and `subnode['includefiles'] = []`.
3. Populates the subnode's attributes from options:
   - `'maxdepth'`: `self.options.get('maxdepth', -1)`
   - `'caption'`: `self.options.get('caption')` (may be `None`)
   - `'glob'`: `'glob' in self.options` (boolean)
   - `'hidden'`: `'hidden' in self.options` (boolean)
   - `'includehidden'`: `'includehidden' in self.options` (boolean)
   - `'numbered'`: `self.options.get('numbered', 0)`
   - `'titlesonly'`: `'titlesonly' in self.options` (boolean)
4. Calls `self.set_source_info(subnode)`.
5. Creates a `nodes.compound(classes=['toctree-wrapper'])` node (`wrappernode`), appends `subnode` to it, and calls `self.add_name(wrappernode)`.
6. Calls `self.parse_content(subnode)` which returns a list of nodes; stores in `ret`. Appends `wrappernode` to `ret`. Returns `ret`.

#### Method: `parse_content(self, toctree: addnodes.toctree) -> List[Node]`

1. Gets `suffixes = self.config.source_suffix` (list of source file extensions).
2. Copies all known document names from `self.env.found_docs` into `all_docnames`, then removes the current document (`self.env.docname`) to avoid self-references.
3. Initializes `ret: List[Node] = []`. Creates an `excluded = Matcher(self.config.exclude_patterns)` for checking exclusion patterns.
4. Iterates over each line in `self.content`:
   - **Skip empty lines** — if the entry is falsy, continue to next iteration.
   - Check for explicit title syntax (`"Some Title <document>"`) via `explicit_title_re.match(entry)`.
   - **Glob branch**: If all of these hold — `toctree['glob']` is true, `glob_re.match(entry)` matches the entry, no explicit title was found, and `url_re.match(entry)` does not match — then:
     1. Join the pattern with the current docname via `docname_join(self.env.docname, entry)`.
     2. Filter `all_docnames` through `patfilter(patname)` to get matching document names; sort them.
     3. For each matched `docname`: remove it from `all_docnames`, append `(None, docname)` to `toctree['entries']`, and append `docname` to `toctree['includefiles']`.
     4. If no documents matched the pattern, log a warning: `'toctree glob pattern %r didn\'t match any documents'`.
   - **Non-glob branch**: Otherwise:
     1. If explicit title was found: extract `ref = explicit.group(2)` and `title = explicit.group(1)`. Set `docname = ref`.
     2. Otherwise: set `ref = docname = entry` and `title = None`.
     3. Strip the source suffix from `docname`: iterate over `suffixes`; if `docname.endswith(suffix)`, truncate it and break.
     4. Absolutize the filename via `docname_join(self.env.docname, docname)`.
     5. **External/self reference**: If `url_re.match(ref)` matches or `ref == 'self'`: append `(title, ref)` to `toctree['entries']` only (not to `includefiles`).
     6. **Missing document**: Else if `docname not in self.env.found_docs`:
        - If the doc path is excluded (`excluded(self.env.doc2path(docname, False))`): set message `'toctree contains reference to excluded document %r'`, subtype `'excluded'`.
        - Otherwise: set message `'toctree contains reference to nonexisting document %r'`, subtype `'not_readable'`.
        - Log a warning with `type='toc', subtype=subtype, location=toctree`. Call `self.env.note_reread()`.
     7. **Valid document**: Else (docname exists in `found_docs`):
        - If `docname in all_docnames`: remove it from `all_docnames`.
        - Otherwise: log a warning `'duplicated entry found in toctree: %s'`.
        - Append `(title, docname)` to `toctree['entries']` and append `docname` to `toctree['includefiles']`.

5. After processing all entries: if `'reversed' in self.options`, reverse both `toctree['entries']` and `toctree['includefiles']` in place (via `list(reversed(...))`).
6. Returns `ret`.

---

### Class: `Author(SphinxDirective)`

Directive for author attribution (`.. author::`, `.. sectionauthor::`, `.. moduleauthor::`, `.. codeauthor::`). Shown only if `show_authors` config is enabled.

**Class attributes:**
- `has_content = False`.
- `required_arguments = 1`, `optional_arguments = 0`.
- `final_argument_whitespace = True`.
- `option_spec: OptionSpec = {}` (no options).

#### Method: `run(self) -> List[Node]`

1. If `self.config.show_authors` is falsy, return `[]`.
2. Create a `nodes.paragraph(translatable=False)` node (`para`).
3. Create a `nodes.emphasis()` node (`emph`) and append it to `para`.
4. Determine the prefix text based on `self.name`:
   - `'sectionauthor'` → `'Section author: '`
   - `'moduleauthor'` → `'Module author: '`
   - `'codeauthor'` → `'Code author: '`
   - otherwise (e.g., `'author'`) → `'Author: '`
5. Append a `nodes.Text(text)` to `emph`.
6. Parse the argument text (`self.arguments[0]`) as inline RST via `self.state.inline_text(self.arguments[0], self.lineno)`, yielding `(inodes, messages)`. Extend `emph` with `inodes`.
7. Build result: `ret = [para] + messages`. Return `ret`.

---

### Class: `SeeAlso(BaseAdmonition)`

An admonition for cross-references to related content. Inherits from `docutils.parsers.rst.directives.admonitions.BaseAdmonition` (which provides the standard admonition machinery). Sets `node_class = addnodes.seealso`. No custom methods — delegates entirely to the parent class.

---

### Class: `TabularColumns(SphinxDirective)`

Directive for explicit tabulary column definitions in LaTeX output.

**Class attributes:**
- `has_content = False`.
- `required_arguments = 1`, `optional_arguments = 0`.
- `final_argument_whitespace = True`.
- `option_spec: OptionSpec = {}`.

#### Method: `run(self) -> List[Node]`

1. Create an `addnodes.tabular_col_spec()` node. Set its `'spec'` attribute to `self.arguments[0]`.
2. Call `self.set_source_info(node)`. Return `[node]`.

---

### Class: `Centered(SphinxDirective)`

Directive for a centered line of bold text.

**Class attributes:**
- `has_content = False`.
- `required_arguments = 1`, `optional_arguments = 0`.
- `final_argument_whitespace = True`.
- `option_spec: OptionSpec = {}`.

#### Method: `run(self) -> List[Node]`

1. If `self.arguments` is empty/falsy, return `[]`.
2. Create an `addnodes.centered()` node (`subnode`).
3. Parse the argument as inline RST via `self.state.inline_text(self.arguments[0], self.lineno)`, yielding `(inodes, messages)`. Extend `subnode` with `inodes`.
4. Build result: `ret = [subnode] + messages`. Return `ret`.

---

### Class: `Acks(SphinxDirective)`

Directive for a list of acknowledgments (names). Content must be a bullet list.

**Class attributes:**
- `has_content = True`.
- `required_arguments = 0`, `optional_arguments = 0`.
- `final_argument_whitespace = False`.
- `option_spec: OptionSpec = {}`.

#### Method: `run(self) -> List[Node]`

1. Create an `addnodes.acks()` node. Set `node.document = self.state.document`.
2. Parse content as nested RST via `self.state.nested_parse(self.content, self.content_offset, node)`.
3. Validate: if the parsed node has exactly one child and that child is a `nodes.bullet_list`, proceed. Otherwise, log a warning `'.. acks content is not a list'` with location `(self.env.docname, self.lineno)` and return `[]`.
4. Return `[node]`.

---

### Class: `HList(SphinxDirective)`

Directive for distributing bullet-list items across multiple horizontal columns.

**Class attributes:**
- `has_content = True`.
- `required_arguments = 0`, `optional_arguments = 0`.
- `final_argument_whitespace = False`.
- **`option_spec`**: `{'columns': int}` — number of columns (default: 2).

#### Method: `run(self) -> List[Node]`

1. Get `ncolumns = self.options.get('columns', 2)` (default 2).
2. Create a `nodes.paragraph()` node (`node`). Set `node.document = self.state.document`.
3. Parse content as nested RST via `self.state.nested_parse(self.content, self.content_offset, node)`.
4. Validate: if the parsed node has exactly one child and that child is a `nodes.bullet_list`, proceed. Otherwise, log a warning `'.. hlist content is not a list'` with location `(self.env.docname, self.lineno)` and return `[]`.
5. Extract `fulllist = node.children[0]` (the bullet list).
6. Compute distribution: `npercol, nmore = divmod(len(fulllist), ncolumns)`. This gives the base items per column and how many columns get one extra item.
7. Create an `addnodes.hlist()` node (`newnode`). Set `newnode['ncolumns'] = str(ncolumns)`.
8. Iterate `column` from 0 to `ncolumns - 1`:
   - Compute `endindex = index + ((npercol + 1) if column < nmore else npercol)`.
   - Create a `nodes.bullet_list()` and populate it with `fulllist.children[index:endindex]`.
   - Append an `addnodes.hlistcol('', bullet_list)` to `newnode`.
   - Update `index = endindex`.
9. Return `[newnode]`.

---

### Class: `Only(SphinxDirective)`

Directive for conditional inclusion based on tag expressions (e.g., `.. only:: html pdf`).

**Class attributes:**
- `has_content = True`.
- `required_arguments = 1`, `optional_arguments = 0`.
- `final_argument_whitespace = True`.
- `option_spec: OptionSpec = {}`.

#### Method: `run(self) -> List[Node]`

1. Create an `addnodes.only()` node (`node`). Set `node.document = self.state.document`. Call `self.set_source_info(node)`. Set `node['expr'] = self.arguments[0]` (the tag expression string).
2. Save the surrounding state from `memo: Any = self.state.memo`:
   - `surrounding_title_styles = memo.title_styles`
   - `surrounding_section_level = memo.section_level`
3. Reset `memo.title_styles = []` and `memo.section_level = 0`.
4. In a `try/finally` block:
   - **Try:** Parse content via `self.state.nested_parse(self.content, self.content_offset, node, match_titles=True)`, which allows nested section titles to be matched.
   - Retrieve `title_styles = memo.title_styles`.
   - If any of these conditions hold — no surrounding title styles, no nested title styles, the first nested title style is not in surrounding styles, or `not self.state.parent` — then there are no nested sections needing special handling: return `[node]`.
   - Otherwise, handle section depth adjustment:
     1. Calculate `current_depth`: start at 0; walk up from `self.state.parent` through `.parent` links counting nodes (incrementing by 1 each step); subtract 2 from the final count.
     2. Determine `nested_depth`: set to `len(surrounding_title_styles)`. If `title_style = title_styles[0]` is found in `surrounding_title_styles`, set `nested_depth = surrounding_title_styles.index(title_style)`.
     3. Compute `n_sects_to_raise = current_depth - nested_depth + 1`.
     4. Walk up from `parent = cast(nodes.Element, self.state.parent)` by `.parent` links `n_sects_to_raise` times (stopping early if `.parent` is None).
     5. Append `node` to the final parent via `parent.append(node)`. Return `[]` (the node has been re-parented; no further wrapping needed).
   - **Finally:** Always restore `memo.title_styles = surrounding_title_styles` and `memo.section_level = surrounding_section_level`.

---

### Class: `Include(BaseInclude, SphinxDirective)`

Like the standard docutils Include directive, but resolves absolute paths relative to the Sphinx source directory.

**Inheritance**: Multiple inheritance from `docutils.parsers.rst.directives.misc.Include` (as `BaseInclude`) and `SphinxDirective`.

#### Method: `run(self) -> List[Node]`

1. If the first argument starts with `<` and ends with `>` (docutils "standard" includes), delegate directly to `super().run()` without path processing.
2. Otherwise, resolve the argument as a relative filename via `self.env.relfn2path(self.arguments[0])`, yielding `(rel_filename, filename)`. Replace `self.arguments[0]` with the absolute `filename`. Call `self.env.note_included(filename)` to track the included file for change detection.
3. Return `super().run()` (the parent class's include logic).

---

### Function: `setup(app: "Sphinx") -> Dict[str, Any]`

Registers all directives with Sphinx and returns the extension metadata dict.

1. Registers `'toctree'` → `TocTree`.
2. Registers `'sectionauthor'`, `'moduleauthor'`, `'codeauthor'` → `Author` (three separate registrations of the same class).
3. Registers `'seealso'` → `SeeAlso`.
4. Registers `'tabularcolumns'` → `TabularColumns`.
5. Registers `'centered'` → `Centered`.
6. Registers `'acks'` → `Acks`.
7. Registers `'hlist'` → `HList`.
8. Registers `'only'` → `Only`.
9. Registers `'include'` → `Include`.
10. Registers `'cssclass'` and `'rst-class'` → `Class` (the docutils RST class directive, for backwards compatibility).
11. Returns: `{'version': 'builtin', 'parallel_read_safe': True, 'parallel_write_safe': True}`.

## sphinx/environment/adapters/toctree.py
Here is the complete natural-language specification of `sphinx/environment/adapters/toctree.py`:

---

## Module-Level Preamble

### Imports

```python
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, cast
from docutils import nodes
from docutils.nodes import Element, Node
from sphinx import addnodes
from sphinx.locale import __
from sphinx.util import logging, url_re
from sphinx.util.matching import Matcher
from sphinx.util.nodes import clean_astext, process_only_nodes

if TYPE_CHECKING:
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment
```

### Constants & Globals

- `logger`: A module-level logger instance created via `logging.getLogger(__name__)`.
- `url_re`: A precompiled regex pattern imported from `sphinx.util`, used to detect whether a string is an external URL.

---

## Code Objects

### Class `TocTree`

**Inheritance:** None (plain class).

**Constructor — `__init__(self, env: "BuildEnvironment") -> None`:**
- Stores the passed `BuildEnvironment` instance as `self.env`.

---

#### Method `note(self, docname: str, toctreenode: addnodes.toctree) -> None`

Records metadata about a TOC tree directive found in a document.

1. If `toctreenode['glob']` is truthy (the toctree uses glob patterns), adds `docname` to `self.env.glob_toctrees` (a set).
2. If `toctreenode.get('numbered')` is truthy, adds `docname` to `self.env.numbered_toctrees` (a set).
3. Retrieves the list of included files from `toctreenode['includefiles']`. For each `includefile`:
   - Adds a reverse dependency: `self.env.files_to_rebuild.setdefault(includefile, set()).add(docname)`, so that if the included file is rebuilt, this document is also marked for rebuild.
4. Extends `self.env.toctree_includes[docname]` (a list) with all `includefiles`.

---

#### Method `resolve(self, docname: str, builder: "Builder", toctree: addnodes.toctree, prune: bool = True, maxdepth: int = 0, titles_only: bool = False, collapse: bool = False, includehidden: bool = False) -> Optional[Element]`

Resolves a `toctree` node into individual bullet lists with document titles as items. Returns `None` if no containing titles are found, or returns a new docutils element node.

**Parameters:**
- `docname`: The name of the document being resolved.
- `builder`: The Sphinx builder instance (used for tag filtering and URI resolution).
- `toctree`: The `addnodes.toctree` AST node to resolve.
- `prune`: If `True`, prune the tree to `maxdepth`. Default `True`.
- `maxdepth`: Maximum depth of the resulting tree. Default `0` (unlimited, falls back to the toctree node's own `maxdepth`).
- `titles_only`: If `True`, only keep top-level document titles and sub-toctrees. Default `False`.
- `collapse`: If `True`, collapse branches not containing `docname`. Default `False`.
- `includehidden`: If `True`, include hidden toctree entries. Default `False`.

**Logic:**

1. **Hidden check:** If the toctree node has `'hidden'` set to `True` and `includehidden` is `False`, return `None` immediately.

2. **Ancestor tracking & pattern matching:**
   - Calls `self.get_toctree_ancestors(docname)` to get a list of ancestor document names for cycle detection during recursive resolution. Stores in `toctree_ancestors`.
   - Creates two `Matcher` instances from `self.env.config.include_patterns` and `self.env.config.exclude_patterns`, used later to classify missing documents.

3. **Inner function `_toctree_add_classes(node: Element, depth: int) -> None`:**
   - Adds CSS classes `'toctree-l{depth-1}'` and optionally `'current'` to the tree nodes.
   - Iterates over `node.children`. For each subnode:
     - If it is a `compact_paragraph` or `list_item`: appends `'toctree-l{depth-1}'` class, then recurses with same depth.
     - If it is a `bullet_list`: recurses with `depth + 1`.
     - If it is a `reference`: checks if `subnode['refuri'] == docname`. If so:
       - If `anchorname` is empty (no anchor), walks up the parent chain from the reference node, appending `'current'` class to every ancestor element.
       - Then marks the reference and all its ancestors with an `'iscurrent'` attribute (`subnode['iscurrent'] = True`). If any ancestor already has `'iscurrent'`, returns early (already marked).

4. **Inner function `_entries_from_toctree(toctreenode: addnodes.toctree, parents: List[str], separate: bool = False, subtree: bool = False) -> List[Element]`:**
   - Returns a list of docutils element nodes representing TOC entries for the given toctree node.
   - Extracts `refs` as a list of `(title, ref)` tuples from `toctreenode['entries']`.
   - For each `(title, ref)`:
     - **External URL case** (`url_re.match(ref)` is truthy):
       - If `title` is `None`, sets it to `ref`.
       - Creates a `nodes.reference` with `internal=False`, `refuri=ref`, `anchorname=''`, and the title as text child.
       - Wraps in `addnodes.compact_paragraph`, then in `nodes.list_item`, then in `nodes.bullet_list` (as `toc`).
     - **Self-reference case** (`ref == 'self'`):
       - Sets `ref = toctreenode['parent']` (the document from which this toctree originates).
       - If no title, derives it via `clean_astext(self.env.titles[ref])`.
       - Creates a `nodes.reference` with `internal=True`, `refuri=ref`, `anchorname=''`, and the title as text child.
       - Wraps in `compact_paragraph`, `list_item`, `bullet_list` (as `toc`). No subitems are shown.
     - **Normal internal reference case** (else):
       - If `ref` is already in `parents`, logs a warning about circular toctree references (`'circular toctree references detected, ignoring: {ref} <- ...'`) and `continue`s to the next entry.
       - Sets `refdoc = ref`.
       - Deep-copies the TOC for that document from `self.env.tocs[ref]` into `toc`.
       - Gets `maxdepth` from `self.env.metadata[ref].get('tocdepth', 0)`.
       - If `ref` is not in `toctree_ancestors` or (`prune` and `maxdepth > 0`), calls `self._toctree_prune(toc, 2, maxdepth, collapse)` to prune the subtree.
       - Calls `process_only_nodes(toc, builder.tags)` to filter out nodes tagged with non-matching `only` directives.
       - If `title` is provided and `toc.children` has exactly one child: finds all `reference` nodes in that child; if any reference's `refuri == ref` and `anchorname` is empty, replaces its text children with a single `nodes.Text(title)`.

     - **Empty TOC check:** If `not toc.children`, logs a warning (`'toctree contains reference to document %r that doesn\'t have a title: no link will be generated'`).

   - **Exception handling (KeyError):** If any referenced document does not exist in `self.env.tocs`:
     - Uses the `excluded` and `included` matchers on `self.env.doc2path(ref, False)` to classify the error.
     - Logs one of three warnings: `'toctree contains reference to excluded document %r'`, `'toctree contains reference to non-included document %r'`, or `'toctree contains reference to nonexisting document %r'`.

   - **Else (successful resolution):**
     - If `titles_only` is `True`: iterates over direct children of `toc`. For each child with more than one sub-element, finds all nested `addnodes.toctree` nodes. If found, replaces the second element (`toplevel[1]`) with those subtrees; otherwise removes that second element (the subtitle).
     - **Sub-toctree resolution:** Finds all `addnodes.toctree` nodes within `toc`. For each:
       - Skips if hidden and not including hidden.
       - Gets the insertion index (`i = subtocnode.parent.index(subtocnode) + 1`).
       - Recursively calls `_entries_from_toctree(subtocnode, [refdoc] + parents, subtree=True)` to expand sub-toctrees.
       - Inserts each returned entry at position `i`, incrementing `i` for each insertion.
       - Removes the original `subtocnode`.
     - If `separate` is `True`, appends `toc` as a whole to `entries`; otherwise extends `entries` with `toc`'s direct children.

   - **Return:** If not `subtree` and not `separate`, wraps all entries in a new `nodes.bullet_list()` and returns `[ret]`. Otherwise returns `entries` directly.

5. **Post-inner-function processing (back in `resolve`):**
   - Sets `maxdepth = maxdepth or toctree.get('maxdepth', -1)`. If `maxdepth` is 0, it means unlimited depth from the node itself; if negative, also unlimited.
   - If not already `titles_only`, checks `toctree.get('titlesonly', False)` and sets `titles_only = True` if present.
   - If not already `includehidden`, checks `toctree.get('includehidden', False)` and sets `includehidden = True` if present.

6. **Entry generation:** Calls `_entries_from_toctree(toctree, [], separate=False)`. If the result is empty (`not tocentries`), returns `None`.

7. **Caption handling:** Creates a new `addnodes.compact_paragraph('','')` as `newnode`. If `toctree.attributes.get('caption')` is truthy:
   - Creates a `nodes.title(caption, '', *[nodes.Text(caption)])`.
   - Copies `line`, `source`, and `'rawcaption'` from the toctree node.
   - If the toctree has a `uid` attribute, moves it to `caption_node` (and deletes it from the toctree).
   - Appends the caption node to `newnode`.

8. **Extend & mark:** Extends `newnode` with `tocentries`. Sets `newnode['toctree'] = True`.

9. **Class assignment & pruning:** Calls `_toctree_add_classes(newnode, 1)` then `self._toctree_prune(newnode, 1, maxdepth if prune else 0, collapse)`.

10. **Empty check:** If the last child of `newnode` is an Element with zero children (no titles found), returns `None`.

11. **URI resolution:** For every `nodes.reference` in `newnode`:
    - If its `refuri` does not match `url_re` (i.e., it's internal, not external): replaces the `refuri` with `builder.get_relative_uri(docname, refnode['refuri']) + refnode['anchorname']`.

12. **Return:** Returns `newnode`.

---

#### Method `get_toctree_ancestors(self, docname: str) -> List[str]`

Builds a list of ancestor document names for the given `docname`, walking up the parent chain defined by `self.env.toctree_includes`.

1. Builds a reverse mapping `parent`: iterates over all `(p, children)` in `self.env.toctree_includes.items()`, and for each child sets `parent[child] = p`.
2. Initializes an empty list `ancestors` and starts from `d = docname`.
3. While `d` is a key in `parent` AND `d` is not already in `ancestors`: appends `d` to `ancestors`, then sets `d = parent[d]`.
4. Returns `ancestors`.

---

#### Method `_toctree_prune(self, node: Element, depth: int, maxdepth: int, collapse: bool = False) -> None`

Utility that prunes a TOC tree in-place at a specified depth. Mutates the AST directly; returns nothing.

Iterates over `node.children[:]` (a copy of children to allow safe removal):
- If subnode is a `compact_paragraph` or `list_item`: recurses with same `depth`.
- If subnode is a `bullet_list`:
  - If `maxdepth > 0` and `depth > maxdepth`: replaces the bullet list in its parent with an empty list (`subnode.parent.replace(subnode, [])`), effectively cutting off that subtree.
  - Else: if `collapse` is `True`, `depth > 1`, and `'iscurrent'` is not in `subnode.parent`: removes the subnode from its parent (collapses non-current branches). Otherwise, recurses with `depth + 1`.

---

#### Method `get_toc_for(self, docname: str, builder: "Builder") -> Node`

Returns a TOC nodetree for use on the same page only (internal anchors).

1. Gets `tocdepth` from `self.env.metadata[docname].get('tocdepth', 0)`.
2. Tries to deep-copy the TOC from `self.env.tocs[docname]`. If a `KeyError` occurs (document does not exist), returns an empty `nodes.paragraph()`.
3. Calls `self._toctree_prune(toc, 2, tocdepth)` to prune to the configured depth.
4. Calls `process_only_nodes(toc, builder.tags)` for tag filtering.
5. For every `nodes.reference` in `toc`: sets its `refuri` to `node['anchorname'] or '#'`.
6. Returns `toc`.

---

#### Method `get_toctree_for(self, docname: str, builder: "Builder", collapse: bool, **kwargs: Any) -> Optional[Element]`

Returns the global TOC nodetree for a document.

1. Gets the full doctree of the root document via `self.env.get_doctree(self.env.config.root_doc)`.
2. Initializes an empty list `toctrees`.
3. If `'includehidden'` is not in `kwargs`, sets it to `True`.
4. If `'maxdepth'` is not in `kwargs` or its value is falsy, sets it to `0` (unlimited). Otherwise converts it to `int(kwargs['maxdepth'])`.
5. Sets `kwargs['collapse'] = collapse`.
6. For each `addnodes.toctree` node found in the root doctree: calls `self.resolve(docname, builder, toctreenode, prune=True, **kwargs)`. If the result is non-None, appends it to `toctrees`.
7. If `toctrees` is empty, returns `None`.
8. Sets `result = toctrees[0]`, then extends it with children from all remaining toctrees (`for toctree in toctrees[1:]: result.extend(toctree.children)`).
9. Returns `result`.

---

## sphinx/environment/collectors/toctree.py
Here is the complete natural-language specification of `sphinx/environment/collectors/toctree.py`:

---

## Module-Level Preamble

### Imports

```python
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, cast
from docutils import nodes
from docutils.nodes import Element, Node
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.environment.adapters.toctree import TocTree
from sphinx.environment.collectors import EnvironmentCollector
from sphinx.locale import __
from sphinx.transforms import SphinxContentsFilter
from sphinx.util import logging, url_re
```

### Constants & Globals

- **`N`** — `TypeVar('N')`, a generic type variable used in the type annotation of the inner function `traverse_in_section`.
- **`logger`** — `logging.getLogger(__name__)`, a module-level logger instance.

---

## Code Objects

### Class: `TocTreeCollector(EnvironmentCollector)`

A Sphinx build-environment collector that manages table-of-contents (TOC) data, section numbering, and figure numbering across documents. It inherits from `EnvironmentCollector`.

#### Method: `clear_doc(self, app: Sphinx, env: BuildEnvironment, docname: str) -> None`

Removes all TOC-related metadata for the given `docname` from the build environment:

1. Pops `docname` from five environment dictionaries/sets:
   - `env.tocs` — the stored TOC bullet lists per document.
   - `env.toc_secnumbers` — section numbers per document.
   - `env.toc_fignumbers` — figure numbers per document.
   - `env.toc_num_entries` — count of TOC entries per document.
   - `env.toctree_includes` — documents included via toctree directives.
2. Discards `docname` from two environment sets:
   - `env.glob_toctrees` — documents containing glob-style toctrees.
   - `env.numbered_toctrees` — documents with numbered toctrees.
3. Iterates over a snapshot of `env.files_to_rebuild.items()` (keyed by sub-document filename, valued by sets of dependent docnames). For each `(subfn, fnset)`:
   - Removes `docname` from `fnset`.
   - If `fnset` becomes empty after removal, deletes the `subfn` key entirely.

#### Method: `merge_other(self, app: Sphinx, env: BuildEnvironment, docnames: Set[str], other: BuildEnvironment) -> None`

Merges TOC metadata from a parallel build environment (`other`) into the current one for documents listed in `docnames`:

1. For each `docname` in `docnames`, copies over:
   - `env.tocs[docname] = other.tocs[docname]`
   - `env.toc_num_entries[docname] = other.toc_num_entries[docname]`
2. Conditionally copies (only if the key exists in `other`):
   - `env.toctree_includes[docname] = other.toctree_includes[docname]`
3. Conditionally adds to sets:
   - If `docname` is in `other.glob_toctrees`, adds it to `env.glob_toctrees`.
   - If `docname` is in `other.numbered_toctrees`, adds it to `env.numbered_toctrees`.
4. Merges `files_to_rebuild`: for each `(subfn, fnset)` from `other.files_to_rebuild.items()`, intersects `fnset` with `docnames` and updates the corresponding set in `env.files_to_rebuild.setdefault(subfn, set())`.

#### Method: `process_doc(self, app: Sphinx, doctree: nodes.document) -> None`

Builds a TOC from the parsed document tree and stores it in the environment. Contains two nested helper functions:

**Outer logic:**
1. Retrieves `docname = app.env.docname`.
2. Initializes `numentries = [0]` (a mutable list used as a nonlocal counter).

**Inner function: `traverse_in_section(node: Element, cls: Type[N]) -> List[N]`**

Recursively collects all nodes of type `cls` within the given node's subtree, but does **not** descend into child `nodes.section` elements (stays within the same section level). For each child:
- If it is a `nodes.section`, skip it entirely.
- If it is a `nodes.Element`, recursively traverse its children and extend the result list.
- If the node itself matches `cls`, append it to the result.

**Inner function: `build_toc(node: Element, depth: int = 1) -> Optional[nodes.bullet_list]`**

Recursively constructs a bullet-list TOC from section nodes in the doctree:

For each child of `node`:
- **If it is a `nodes.section`:**
  1. Extracts the title as `title = sectionnode[0]`.
  2. Walks the title through a `SphinxContentsFilter(doctree)` visitor to extract plain text content (stripping references and unnecessary markup).
  3. Determines the anchor name: if `numentries[0] == 0` (first TOC entry), sets `anchorname = ''`; otherwise, `anchorname = '#' + sectionnode['ids'][0]`.
  4. Increments `numentries[0]`.
  5. Creates a reference node: `nodes.reference('', '', internal=True, refuri=docname, anchorname=anchorname, *nodetext)`.
  6. Wraps the reference in an `addnodes.compact_paragraph`, then wraps that in a `nodes.list_item`.
  7. Recursively calls `build_toc(sectionnode, depth + 1)` for sub-sections; if it returns a non-None bullet list, appends it as a child of the list item.
  8. Appends the list item to `entries`.

- **If it is an `addnodes.only` node:**
  1. Creates a copy: `onlynode = addnodes.only(expr=sectionnode['expr'])`.
  2. Recursively calls `build_toc(sectionnode, depth)` (same depth, not incremented).
  3. If the result is non-None, copies its children into `onlynode` and appends `onlynode` to `entries`.

- **If it is a generic `nodes.Element`:**
  1. Uses `traverse_in_section(sectionnode, addnodes.toctree)` to find any embedded toctree nodes within this element.
  2. For each found toctree node: copies it and appends the copy to `entries`.
  3. Calls `TocTree(app.env).note(docname, toctreenode)` to register the toctree in the inventory.

After iterating all children: if `entries` is non-empty, returns `nodes.bullet_list('', *entries)`; otherwise returns `None`.

**Final steps:**
1. Calls `toc = build_toc(doctree)`.
2. Stores the result: `app.env.tocs[docname] = toc` (or an empty `nodes.bullet_list('')` if `toc` is `None`).
3. Stores the entry count: `app.env.toc_num_entries[docname] = numentries[0]`.

#### Method: `get_updated_docs(self, app: Sphinx, env: BuildEnvironment) -> List[str]`

Returns the concatenation of documents needing rewrites from both numbering passes:
```python
return self.assign_section_numbers(env) + self.assign_figure_numbers(env)
```

#### Method: `assign_section_numbers(self, env: BuildEnvironment) -> List[str]`

Assigns hierarchical section numbers to all headings under numbered toctrees. Returns a list of docnames whose section numbers changed (requiring rewrites).

**Setup:**
1. Initializes `rewrite_needed = []`.
2. Creates `assigned: Set[str] = set()` to track documents already processed.
3. Saves the old numbering state: `old_secnumbers = env.toc_secnumbers`, then resets `env.toc_secnumbers = {}`.

**Inner function: `_walk_toc(node: Element, secnums: Dict, depth: int, titlenode: Optional[nodes.title] = None) -> None`**

Walks a TOC bullet list and assigns section numbers. The `titlenode` parameter is the document's top-level title node (assigned a secnumber for next/prev/parent rellinks). For each child of `node`:
- **If it is a `nodes.bullet_list`** (sub-sections): pushes `0` onto `numstack`, recurses with `depth - 1`, then pops from `numstack`. Resets `titlenode = None`.
- **If it is a `nodes.list_item`**: recurses at the same depth. Resets `titlenode = None`.
- **If it is an `addnodes.only`**: recurses at the same depth (includes all branches regardless of expression evaluation). Resets `titlenode = None`.
- **If it is an `addnodes.compact_paragraph`** (a TOC entry):
  1. Increments `numstack[-1] += 1`.
  2. Casts the first child to a `nodes.reference`.
  3. If `depth > 0`: sets `number = list(numstack)` and stores it as `secnums[reference['anchorname']] = tuple(numstack)`.
  4. If `depth == 0`: sets `number = None` and `secnums[reference['anchorname']] = None`.
  5. Sets `reference['secnumber'] = number`.
  6. If `titlenode` is set, assigns it the same `number`, then resets `titlenode = None`.

**Inner function: `_walk_toctree(toctreenode: addnodes.toctree, depth: int) -> None`**

Walks a toctree node's entries and recursively numbers referenced documents. For each `(title, ref)` in `toctreenode['entries']`:
- If `ref` matches the URL regex or equals `'self'`, skips it.
- If `ref` is already in `assigned`, logs a warning: *"%s is already assigned section numbers (nested numbered toctree?)"*.
- If `ref` exists in `env.tocs`: creates an empty `secnums` dict, stores it as `env.toc_secnumbers[ref] = secnums`, adds `ref` to `assigned`, calls `_walk_toc(env.tocs[ref], secnums, depth, env.titles.get(ref))`. If the resulting `secnums` differs from the old state (`old_secnumbers.get(ref)`), appends `ref` to `rewrite_needed`.

**Outer loop:**
For each `docname` in `env.numbered_toctrees`:
1. Adds `docname` to `assigned`.
2. Retrieves its doctree via `env.get_doctree(docname)`.
3. Finds all `addnodes.toctree` nodes within the doctree.
4. For each, reads `depth = toctreenode.get('numbered', 0)`. If `depth > 0`, initializes `numstack = [0]` and calls `_walk_toctree(toctreenode, depth)`.

Returns `rewrite_needed`.

#### Method: `assign_figure_numbers(self, env: BuildEnvironment) -> List[str]`

Assigns figure numbers to figures under numbered toctrees. Returns a list of docnames whose figure numbers changed.

**Setup:**
1. Initializes `rewrite_needed = []`, `assigned: Set[str] = set()`.
2. Saves old state: `old_fignumbers = env.toc_fignumbers`, resets `env.toc_fignumbers = {}`.
3. Creates `fignum_counter: Dict[str, Dict[Tuple[int, ...], int]] = {}` — maps figure type → (section number tuple → counter).

**Inner function: `get_figtype(node: Node) -> Optional[str]`**

Iterates over all domains in `env.domains.values()`. For each domain:
- Calls `domain.get_enumerable_node_type(node)` to get a potential figure type.
- If the domain is `'std'` and `domain.get_numfig_title(node)` returns falsy, skips (uncaptioned nodes are excluded).
- Returns the first non-empty `figtype` found; otherwise returns `None`.

**Inner function: `get_section_number(docname: str, section: nodes.section) -> Tuple[int, ...]`**

Looks up the section number for a given section node within a document:
1. Constructs `anchorname = '#' + section['ids'][0]`.
2. Retrieves `secnumbers = env.toc_secnumbers.get(docname, {})`.
3. If `anchorname` is in `secnumbers`, uses that value; otherwise falls back to `secnumbers.get('')` (the document-level number).
4. Returns the secnumber or an empty tuple `()` if none found.

**Inner function: `get_next_fignumber(figtype: str, secnum: Tuple[int, ...]) -> Tuple[int, ...]`**

Computes the next figure number for a given type and section context:
1. Gets (or creates) the counter dict for `figtype` in `fignum_counter`.
2. Truncates `secnum` to `env.config.numfig_secnum_depth` levels.
3. Increments the counter at that secnum key, returns `secnum + (counter[secnum],)`.

**Inner function: `register_fignumber(docname: str, secnum: Tuple[int, ...], figtype: str, fignode: Element) -> None`**

Stores a figure number in the environment:
1. Ensures nested dicts exist: `env.toc_fignumbers.setdefault(docname, {})`, then `.setdefault(figtype, {})`.
2. Gets the figure's first ID from `fignode['ids'][0]`.
3. Stores `fignumbers[figure_id] = get_next_fignumber(figtype, secnum)`.

**Inner function: `_walk_doctree(docname: str, doctree: Element, secnum: Tuple[int, ...]) -> None`**

Walks a document's doctree to find and number figures. For each child of `doctree`:
- **If it is a `nodes.section`:** gets the section's own number via `get_section_number(docname, subnode)`. If non-empty, recurses with that as the new secnum; otherwise recurses with the parent's secnum.
- **If it is an `addnodes.toctree`:** for each `(title, subdocname)` in entries: skips URLs and `'self'`; calls `_walk_doc(subdocname, secnum)`.
- **For any other `nodes.Element`:** if `get_figtype(subnode)` returns a figtype and the node has IDs, calls `register_fignumber(docname, secnum, figtype, subnode)`. Then recurses with `_walk_doctree(docname, subnode, secnum)`.

**Inner function: `_walk_doc(docname: str, secnum: Tuple[int, ...]) -> None`**

Entry point for a single document: if `docname` is not in `assigned`, adds it and calls `_walk_doctree(docname, env.get_doctree(docname), secnum)`.

**Outer logic:**
If `env.config.numfig` is truthy:
1. Calls `_walk_doc(env.config.root_doc, ())` starting from the root document with an empty section number tuple.
2. After processing all documents, iterates over `env.toc_fignumbers.items()`: if any doc's fignums differ from the old state (`old_fignumbers.get(docname)`), appends the docname to `rewrite_needed`.

Returns `rewrite_needed`.

---

### Function: `setup(app: Sphinx) -> Dict[str, Any]`

Sphinx extension entry point. Registers `TocTreeCollector` as an environment collector via `app.add_env_collector(TocTreeCollector)`, then returns the standard metadata dictionary:
```python
{
    'version': 'builtin',
    'parallel_read_safe': True,
    'parallel_write_safe': True,
}
```