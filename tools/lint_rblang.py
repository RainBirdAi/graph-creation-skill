#!/usr/bin/env python3
"""Deterministic RBLang linter for the Rainbird graph-creation skill.

Usage: python3 tools/lint_rblang.py <graph.xml> [--strict-alt]

Encodes the mechanical checks from MEMORY.md so they never need rediscovering:
references, types, quoting, askability, alt text, expression hazards, comment
character restrictions. Exit code 1 if any ERROR-level finding; warnings are
advisory (platform-tolerated or style/requirement checks).

Run this BEFORE every upload to https://api.rainbird.ai/maps.
"""
import re
import sys
import collections
from xml.etree import ElementTree as ET

LIST_FUNCS = ('countRelationshipInstances', 'sumObjects', 'minObjects',
              'maxObjects', 'joinObjects')
# Functions whose ARGUMENTS must be plain variables/literals (no nested expressions).
ARG_FUNCS = LIST_FUNCS + (
    'round', 'ceil', 'floor', 'abs', 'min', 'max', 'mod', 'pow', 'sqrt',
    'factorial', 'addDays', 'subtractDays', 'addWeeks', 'subtractWeeks',
    'addMonths', 'subtractMonths', 'addYears', 'subtractYears',
    'secondsBetween', 'minutesBetween', 'hoursBetween', 'daysBetween',
    'weeksBetween', 'monthsBetween', 'yearsBetween', 'isBeforeDate',
    'isSameDate', 'isAfterDate', 'isWithinRange', 'dayOfWeek', 'dayOfMonth',
    'dayOfYear', 'monthOfYear', 'year', 'includes', 'startsWith', 'endsWith',
    'regexCount', 'isSubset')
VALID_CONCEPT_TYPES = {'string', 'number', 'date', 'truth'}

findings = []


def err(line, code, msg):
    findings.append(('ERROR', line, code, msg))


def warn(line, code, msg):
    findings.append(('WARN', line, code, msg))


def info(line, code, msg):
    findings.append(('INFO', line, code, msg))


def strip_quoted(expr):
    """Remove single-quoted string literals so operator scans don't hit text."""
    return re.sub(r"'[^']*'", "''", expr)


def line_of(text, pos):
    return text.count('\n', 0, pos) + 1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    strict_alt = '--strict-alt' in sys.argv
    if not args:
        print(__doc__)
        sys.exit(2)
    path = args[0]
    text = open(path, encoding='utf-8').read()

    # ---- raw-text checks (before parsing) ----
    for m in re.finditer(r'<!--(.*?)-->', text, re.S):
        body = m.group(1)
        ln = line_of(text, m.start())
        if '"' in body:
            err(ln, 'COMMENT_QUOTE',
                'XML comment contains a double quote - the platform importer '
                'chokes on this (MEMORY lesson 7). Reword with apostrophes.')
        if '<' in body:
            err(ln, 'COMMENT_LT',
                'XML comment contains a literal < - the platform importer '
                'chokes on this (MEMORY lesson 7). Write LT/GT in words.')
        if '--' in body:
            warn(ln, 'COMMENT_DASHES',
                 'Comment contains -- (invalid strict XML; platform-tolerated '
                 'but emit strict XML).')
    for m in re.finditer(r'&(?!amp;|lt;|gt;|quot;|apos;|#)', text):
        warn(line_of(text, m.start()), 'BARE_AMP',
             'Bare & (invalid strict XML; platform-tolerated but escape it).')

    # ---- parse (leniently patched so we can continue past tolerated issues) ----
    patched = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#)', '&amp;', text)
    patched = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), patched,
                     flags=re.S)
    try:
        root = ET.fromstring(patched)
    except ET.ParseError as e:
        err(getattr(e, 'position', (0, 0))[0], 'XML_PARSE',
            'XML does not parse even after tolerated-issue patching: %s' % e)
        report(path)
        return

    def tag(el):
        return el.tag.split('}')[-1]

    # element -> approximate line numbers via source scan of name attributes
    def find_line(needle):
        i = text.find(needle)
        return line_of(text, i) if i >= 0 else 0

    concepts = {}
    for c in root.iter():
        if tag(c) != 'concept':
            continue
        nm, ty = c.get('name'), c.get('type')
        ln = find_line('<concept name="%s"' % nm)
        if nm in concepts:
            err(ln, 'DUP_CONCEPT', 'Duplicate concept "%s"' % nm)
        concepts[nm] = ty
        if ty not in VALID_CONCEPT_TYPES:
            err(ln, 'BAD_TYPE',
                'Concept "%s" has type "%s" (must be string/number/date/truth)'
                % (nm, ty))

    rels = {}
    rel_used_concepts = set()
    for r in root.iter():
        if tag(r) != 'rel':
            continue
        nm = r.get('name')
        ln = find_line('<rel name="%s"' % nm)
        if nm in rels:
            err(ln, 'DUP_REL', 'Duplicate relationship name "%s"' % nm)
        rels[nm] = r
        for side in ('subject', 'object'):
            cn = r.get(side)
            if cn not in concepts:
                err(ln, 'UNDECLARED_CONCEPT',
                    'Rel "%s" %s references undeclared concept "%s"'
                    % (nm, side, cn))
            else:
                rel_used_concepts.add(cn)
        subj_type = concepts.get(r.get('subject'))
        if subj_type and subj_type != 'string':
            err(ln, 'NONSTRING_SUBJECT',
                'Rel "%s" subject concept is %s - only string concepts may be '
                'subjects' % (nm, subj_type))
        if r.get('askable') is None:
            warn(ln, 'NO_ASKABLE',
                 'Rel "%s" has no askable attribute - defaults to ASKABLE at '
                 'runtime (MEMORY: askability defaults). Set askable="none" on '
                 'data/derived rels.' % nm)
        elif r.get('askable') not in ('none',) and r.get('allowUnknown') != 'true':
            info(ln, 'NO_ALLOWUNKNOWN',
                 'Askable rel "%s" lacks allowUnknown="true" - API consumers '
                 'cannot unknown-skip its question.' % nm)
        if r.get('askable') == 'secondFormObject':
            q = ''.join(x.text or '' for x in r if tag(x) == 'secondFormObject')
            if not q.strip():
                err(ln, 'NO_QUESTION',
                    'Rel "%s" is askable=secondFormObject but has no '
                    '<secondFormObject> question text' % nm)

    concinsts = {}
    for ci in root.iter():
        if tag(ci) != 'concinst':
            continue
        nm, ty = ci.get('name'), ci.get('type')
        ln = find_line('<concinst name="%s"' % nm)
        if ty not in concepts:
            err(ln, 'UNDECLARED_CONCEPT',
                'Concinst "%s" references undeclared concept "%s"' % (nm, ty))
        elif concepts[ty] in ('number', 'truth'):
            err(ln, 'PRIMITIVE_CONCINST',
                'Concinst "%s" instantiates %s concept "%s" - use raw values '
                'instead (guide 2.3)' % (nm, concepts[ty], ty))
        concinsts.setdefault(nm, set()).add(ty)

    # ---- relinsts: facts and rules ----
    n_rules = 0
    for ri in root.iter():
        if tag(ri) != 'relinst':
            continue
        rtype = ri.get('type')
        conds = [c for c in ri if tag(c) == 'condition']
        is_rule = bool(conds)
        label = ('rule "%s"' % ri.get('name')) if ri.get('name') else \
            ('relinst type="%s"' % rtype)
        ln = find_line('name="%s"' % ri.get('name')) if ri.get('name') else \
            find_line('<relinst type="%s"' % rtype)
        if rtype not in rels:
            err(ln, 'UNDECLARED_REL',
                '%s references undeclared relationship "%s"' % (label, rtype))
            continue
        rel_el = rels[rtype]
        obj_concept_type = concepts.get(rel_el.get('object'))

        if not is_rule:
            # data fact: check subject/object instance declarations
            subj, obj = ri.get('subject'), ri.get('object')
            if subj is not None and subj not in concinsts:
                err(ln, 'FACT_SUBJ_UNDECLARED',
                    'Fact %s: subject "%s" is not a declared concinst'
                    % (label, subj))
            if obj is not None and obj_concept_type == 'string' \
                    and obj not in concinsts:
                err(ln, 'FACT_OBJ_UNDECLARED',
                    'Fact %s: string object "%s" needs a <concinst> '
                    'declaration (MEMORY lesson 9)' % (label, obj))
            if obj is not None and obj_concept_type == 'number':
                if not re.fullmatch(r'-?\d+(\.\d+)?', obj):
                    err(ln, 'FACT_OBJ_TYPE',
                        'Fact %s: object "%s" is not a number' % (label, obj))
            if obj is not None and obj_concept_type == 'truth' \
                    and obj not in ('true', 'false'):
                err(ln, 'FACT_OBJ_TYPE',
                    'Fact %s: object "%s" is not true/false' % (label, obj))
            continue

        n_rules += 1
        cf = ri.get('cf')
        if cf is not None and not (cf.isdigit() and 0 <= int(cf) <= 100):
            err(ln, 'BAD_CF', '%s: cf="%s" not an integer 0-100' % (label, cf))
        # rule object literal of string type should be a concinst (unless var)
        robj = ri.get('object')
        if robj and not robj.startswith('%') and obj_concept_type == 'string' \
                and robj not in concinsts:
            err(ln, 'RULE_OBJ_UNDECLARED',
                '%s: asserted literal object "%s" is not a declared concinst'
                % (label, robj))

        bound = {'%S', '%O'}
        uses_minmax = False
        uses_sum = False
        has_count_guard = False
        for c in conds:
            crel = c.get('rel')
            cexpr = c.get('expression')
            calt = c.get('alt')
            if crel is not None:
                if crel not in rels:
                    err(ln, 'UNDECLARED_REL',
                        '%s: condition references undeclared rel "%s"'
                        % (label, crel))
                for side in ('subject', 'object'):
                    v = c.get(side)
                    if v and v.startswith('%'):
                        bound.add(v)
                    elif v and side == 'object' and crel in rels:
                        oc = concepts.get(rels[crel].get('object'))
                        if oc == 'string' and v not in concinsts:
                            warn(ln, 'COND_OBJ_UNDECLARED',
                                 '%s: condition literal object "%s" is not a '
                                 'declared concinst' % (label, v))
            if cexpr is not None:
                e = strip_quoted(cexpr)
                if re.search(r'\b(minObjects|maxObjects)\s*\(', cexpr):
                    uses_minmax = True
                if re.search(r'\bsumObjects\s*\(', cexpr):
                    uses_sum = True
                if 'countRelationshipInstances' in cexpr:
                    has_count_guard = True
                # quoted rel names inside list functions
                for fn in LIST_FUNCS:
                    for m in re.finditer(fn + r'\(([^()]*)\)', cexpr):
                        inner = m.group(1)
                        parts = inner.split(',')
                        if len(parts) >= 2:
                            relarg = parts[1].strip()
                            if relarg and not (relarg.startswith("'")
                                               and relarg.endswith("'")):
                                warn(ln, 'UNQUOTED_RELNAME',
                                     '%s: %s rel-name argument should be '
                                     'quoted (confirmed-safe form; unquoted '
                                     'works in one production graph but a '
                                     'quoting failure was confirmed live - '
                                     'MEMORY lesson 8): ...%s...'
                                     % (label, fn, inner[:60]))
                # function args containing arithmetic (no expression args!)
                for fn in ARG_FUNCS:
                    for m in re.finditer(fn + r'\(([^()]*)\)', e):
                        inner = m.group(1)
                        if re.search(r'[%\w\)]\s*[-+*/]\s*[%\w\(]', inner):
                            err(ln, 'EXPR_FUNC_ARG',
                                '%s: %s(...) takes an expression argument - '
                                'the platform silently never binds these '
                                '(MEMORY lesson 5). Compute in a prior '
                                'condition: %s' % (label, fn, inner[:60]))
                # multi-operator precedence hazard
                flat = re.sub(r'\b[\w]+\([^()]*\)', 'F', e)  # collapse calls
                ops = re.findall(r'[-+*/]', re.sub(r'%[A-Za-z0-9_]+', 'V', flat))
                if len(ops) >= 2 and ('*' in ops or '/' in ops) \
                        and ('+' in ops or '-' in ops):
                    warn(ln, 'PRECEDENCE',
                         '%s: expression mixes +- with */ - RBLang evaluates '
                         'STRICTLY left-to-right (brackets group but do not '
                         'restore precedence, MEMORY lesson 6). Verify the '
                         'order: %s' % (label, cexpr[:80]))
                # escaped plus in regex
                if re.search(r"/[^/']*\\\+[^/']*/", cexpr):
                    err(ln, 'REGEX_ESCAPED_PLUS',
                        '%s: use [+] not \\+ for a literal plus in regexCount '
                        'patterns (MEMORY lesson 11)' % label)
                # variable binding order
                for v in re.findall(r'%[A-Za-z0-9_]+', cexpr):
                    if c.get('value') == v:
                        continue
                    if v not in bound:
                        warn(ln, 'UNBOUND_VAR',
                             '%s: expression uses %s before any condition '
                             'binds it (free-floating variables silently '
                             'never bind, MEMORY lesson 13)' % (label, v))
                if c.get('value'):
                    bound.add(c.get('value'))
                # self-recursion: counting own rel
                if 'countRelationshipInstances' in cexpr \
                        and ("'%s'" % rtype) in cexpr:
                    warn(ln, 'SELF_COUNT',
                         '%s: counts its OWN relationship "%s" - '
                         'self-recursion risk; gate via a precedence ladder '
                         'instead (MEMORY design patterns)' % (label, rtype))
                # alt checks. Skip display-composition and pure plumbing:
                # string concatenation, a bare variable relay, or a
                # quoted-literal capture (their output IS the display).
                is_concat = c.get('value') and (
                    bool(re.search(r"'[^']*'\s*\+|\+\s*'", cexpr))
                    or re.fullmatch(r'\s*%[A-Za-z0-9_]+\s*', cexpr)
                    or re.fullmatch(r"\s*'[^']*'\s*", cexpr))
                if calt is None and not is_concat:
                    (err if strict_alt else warn)(
                        ln, 'NO_ALT',
                        '%s: expression condition lacks alt text (standing '
                        'requirement - evidence trees must read as narrative)'
                        % label)
            if calt is not None:
                if '"' in calt or '<' in calt:
                    err(ln, 'ALT_CHARS',
                        '%s: alt text contains " or <' % label)
                if len(calt) > 220:
                    warn(ln, 'ALT_LONG', '%s: alt text over 220 chars' % label)
                if calt.count('{{') != calt.count('}}'):
                    err(ln, 'ALT_BRACES',
                        '%s: unbalanced {{ }} in alt text' % label)
            w = c.get('weight')
            if w is not None and not (w.isdigit() and 0 <= int(w) <= 100):
                err(ln, 'BAD_WEIGHT', '%s: weight="%s" invalid' % (label, w))
            b = c.get('behaviour')
            if b is not None and b not in ('mandatory', 'optional'):
                err(ln, 'BAD_BEHAVIOUR',
                    '%s: behaviour="%s" invalid' % (label, b))
        # aggregation-over-empty-set guard (MEMORY: minObjects over an
        # empty set asserts a NULL fact that compares like +infinity)
        if uses_minmax and not has_count_guard:
            err(ln, 'UNGUARDED_AGG',
                '%s: uses minObjects/maxObjects with no '
                'countRelationshipInstances guard in the same rule - an '
                'empty set asserts a NULL fact that compares like '
                '+infinity downstream' % label)
        elif uses_sum and not has_count_guard:
            warn(ln, 'UNGUARDED_AGG',
                 '%s: uses sumObjects with no countRelationshipInstances '
                 'guard in the same rule (empty set sums to 0 - confirm '
                 'that is the intended meaning)' % label)

    # orphan concepts
    for nm in concepts:
        if nm not in rel_used_concepts:
            warn(find_line('<concept name="%s"' % nm), 'ORPHAN_CONCEPT',
                 'Concept "%s" is not used in any relationship' % nm)

    print('%s: %d concepts, %d rels, %d concinsts, %d rules'
          % (path, len(concepts), len(rels), len(concinsts), n_rules))
    report(path)


def report(path):
    order = {'ERROR': 0, 'WARN': 1, 'INFO': 2}
    counts = collections.Counter(f[0] for f in findings)
    # cap repeated identical codes so output stays readable
    seen = collections.Counter()
    for sev, ln, code, msg in sorted(findings, key=lambda f: (order[f[0]], f[1])):
        seen[code] += 1
        if seen[code] == 26:
            print('  ... further %s findings suppressed' % code)
        if seen[code] >= 26:
            continue
        print('%-5s L%-6d %-22s %s' % (sev, ln, code, msg))
    total = ('%d errors, %d warnings, %d info'
             % (counts['ERROR'], counts['WARN'], counts['INFO']))
    print('== %s: %s' % (path, total))
    sys.exit(1 if counts['ERROR'] else 0)


if __name__ == '__main__':
    main()
