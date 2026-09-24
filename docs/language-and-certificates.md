# Anchored inert web bundles: language and certificate specification

This document is the operational contract implemented by both the producer and
the separately packaged checker. It describes a source-level mathematical
language, not browser parsing, CSS rendering, accessibility behavior, or network
execution.

## 1. Bundle container

A bundle is a directory with exactly one `bundle.json` and the files named by its
manifest. The manifest has exactly these JSON fields:

```json
{
  "format": "iwb-1",
  "root": "index.html",
  "resources": ["index.html", "styles/base.css", "assets/dot.png"]
}
```

JSON is UTF-8 and duplicate object keys are rejected. Paths are nonempty,
normalized, relative POSIX paths. Absolute paths, `.`/`..` components,
backslashes, NUL, symlinks, non-regular nodes, unlisted files, missing files,
duplicate entries, and unreachable listed resources are rejected. The root and
manifest themselves must also be non-symlinked regular files. Metadata sizes are
checked before reads where possible; the implementation rejects a size change
observed across a read, while the model still assumes a quiescent directory. The
root is an HTML file. Limits are 64 resources, 8 MiB total bytes, 2 MiB per text
file, 10,000 HTML events, 4,000 CSS rules, 8,000 declarations, 80-character names,
and 240-character paths.

The resource graph is rooted and fully reachable. The only edge kinds are:

- `link:href` from HTML to a local CSS file, with no fragment;
- `a:href` from HTML to a local HTML file, optionally with a fragment;
- `img:src` from HTML to a local image asset, with no fragment;
- `css:url` from CSS to a local image asset, with no fragment.

Fragment names are bundle-global IDs and must be declared in the referenced HTML
resource. Schemes, authorities, queries, absolute references, escaping paths,
and backslash paths are outside the language.

## 2. HTML event language

Text files must be UTF-8 and start (apart from ignorable leading whitespace) with
one `<!doctype html>`. There is exactly one `html`, `head`, and `body`. The direct
children of `html` are exactly `head` followed by `body`. Non-void elements must
be explicitly closed and cannot use XML-style self-closing syntax.

Admitted tags are:

```text
html head body title meta link div span p h1 h2 h3 h4 h5 h6
ul ol li nav main header footer article section aside img a
strong em small figure figcaption br hr
```

Scripts, forms, inputs, buttons, text areas, selects, options, frames, embedded
objects, applets, base elements, portals, templates, style elements, and every
unknown tag are rejected. Processing instructions and unknown declarations are
rejected. Comments and whitespace-only text nodes are erased. Other text is NFC
normalized with newline normalization and remains significant.

Global attributes are `id`, `class`, `title`, `role`, and `lang`. Element-specific
attributes are:

```text
html: lang
meta: charset, name, content
link: href, rel, type, media
a: href
img: src, alt, width, height
```

Every attribute has a value. Duplicate attributes, `style`, every `on*`
attribute, an attribute on the wrong tag, and every unknown attribute are
rejected. Attribute order is immaterial. Class tokens are unique and their order
is immaterial. IDs and class names match `[A-Za-z_][A-Za-z0-9_-]{0,79}`.

IDs are globally unique across the bundle. IDs are assigned canonical names in
first declaration order after canonical resource discovery. Classes are also
global. At an ordered HTML element, the unordered class list may contain at most
one class not seen at an earlier element. That unique new class is assigned the
next canonical class name; previously seen classes are already anchored. A CSS
ID/class selector must name an ID/class declared in HTML.

## 3. CSS event language

CSS comments outside quoted strings are erased. Rule order remains significant.
Selector-list order within a rule and declaration order within a rule are
immaterial. Empty rules, nested blocks, at-rules, duplicate properties,
shorthands, custom properties, `!important`, `var()`, and unrecognized
properties are rejected.

Selectors use only type selectors, `*`, ID selectors, class selectors, and the
four combinators (descendant, child, adjacent sibling, general sibling). Attribute
selectors, pseudo-classes, pseudo-elements, functions, and malformed adjacent
type selectors are rejected. A compound contains at most one type/universal
selector followed by ID/class qualifiers.

The property allowlist contains longhands whose order is not semantically used by
this model, including color, background color/image, individual border sides,
individual box-model sides, dimensions, typography longhands, visibility,
positioning, flex/grid longhands, and alignment properties. The exact list is in
`src/limits.py` and is shared as declarative data.

Whitespace outside quoted CSS strings is collapsed to one space; whitespace
inside strings is preserved. Quote state treats a quote as escaped exactly when
it is preceded by an odd-length run of backslashes. The `url(...)` scanner runs
only outside quoted strings, preserves quoted `url(` text literally, rejects a
malformed real URL token, and rewrites every admitted local URL to the asset's
canonical resource label. This scanner deliberately implements the declared IWB
fragment, not the full CSS tokenizer or browser error-recovery algorithm.

## 4. Canonical labels

The canonical resource order is deterministic rooted depth-first discovery.
Outgoing references are encountered in ordered HTML event positions; attributes
are sorted because their source order is ignored; CSS declarations are sorted
because declaration order is ignored; multiple URLs inside one value preserve
value order. Cycles are permitted and terminate through a visited set. Every
listed resource must be discovered.

Resources receive labels `r0`, `r1`, ... in discovery order. IDs receive `i0`,
`i1`, ... in declaration order over canonical resource order. Classes receive
`c0`, `c1`, ... at their unique ordered first-introduction anchors.

Canonical HTML preserves event order, tag names, non-whitespace text, explicit
end events, and literal attribute values. It sorts attribute records and class
labels, and replaces path/fragment/name occurrences by canonical labels.
Canonical CSS preserves rule order, sorts selector lists and declarations, and
replaces selectors and local URLs by canonical labels. An image asset is encoded
by its exact base64 bytes. The resulting JSON uses sorted object keys and compact
separators.

## 5. Declared equivalence

Two admitted bundles are equivalent when there exist total bijections over their
resource paths, IDs, and classes such that:

- root maps to root;
- resource kinds and exact asset bytes agree;
- mapped HTML event sequences agree after attribute and class-token permutation,
  comment deletion, whitespace-only text deletion, and newline/NFC normalization;
- mapped CSS rule sequences agree after selector-list and declaration
  permutation, comment deletion, and outside-string whitespace normalization;
- every local reference and fragment is mapped consistently everywhere.

No element/rule/text reordering, text substitution, tag substitution, property
substitution, value substitution, asset change, insertion, deletion, active
content, external URL, or per-resource name map is included.

## 6. Certificate schemas

Certificates are UTF-8 JSON, at most 4 MiB, with duplicate-key rejection. Unknown
fields are rejected.

### Equivalent

```json
{
  "format": "iwb-cert-1",
  "decision": "equivalent",
  "resource_map": {"index.html": "home.html"},
  "id_map": {"title": "heading_id"},
  "class_map": {"card": "panel"},
  "left_digest": "...",
  "right_digest": "..."
}
```

Each map is a total bijection over exactly the endpoint symbols. The root maps to
the root. The checker maps and compares every resource; assets are compared
byte-for-byte. It also reconstructs both canonical forms and requires agreement
between replay and canonical equality. The SHA-256 endpoint digests compactly
bind the supplied endpoints but are not the only positive check.

### Different

```json
{
  "format": "iwb-cert-1",
  "decision": "different",
  "witness": {"line": 17, "left": "...", "right": "..."},
  "left_digest": "...",
  "right_digest": "..."
}
```

The checker reconstructs both canonical JSON objects and accepts only the first
line mismatch in their deterministic indented serialization. This is a complete
decision for admitted inputs because the correctness theorem equates canonical
equality with the declared equivalence. The witness is deterministic, not
minimum, local, or human-optimal.

### Out of language

```json
{
  "format": "iwb-cert-1",
  "decision": "out-of-language",
  "side": "right",
  "witness": {
    "code": "forbidden-tag",
    "location": "index.html:12:1",
    "detail": "form"
  }
}
```

The checker reparses the named endpoint and requires exact equality with its
first deterministic admission error. It does not infer a relation between two
out-of-language sources.

## 7. Trust and failure semantics

The certificate never chooses endpoint paths or changes the language. The caller
supplies both endpoints. The producer and checker share only the declarative
limits module at import time, but their parser/canonicalizer code follows the
same specification and was created in one research process; this is not
independent authorship or formal verification. The exhaustive oracle reuses the
producer's admitted parse object but does not call the canonicalizer or checker.
The test campaign checks producer/checker parse-shape agreement on tiny cases and
serialized parser-object or exact rejection-witness agreement on 512 deterministic
operator combinations. Because both implementations follow the same written design,
that differential evidence is not independent authorship or a third-party parser.

Accepted `equivalent` means the explicit total maps replay in the declared
language. Accepted `different` means the reconstructed canonical forms differ.
Accepted `out-of-language` means the named endpoint triggers the stated first
error. A rejected certificate, timeout, operating-system error, or unsupported
input has no opposite logical conclusion.
