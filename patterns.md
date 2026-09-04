# Rainbird design-pattern catalogue

Proven architectures and idioms for production RBLang graphs. Pick your architecture
here BEFORE authoring. Each pattern names the example graph that demonstrates it
(see `example_graphs/INDEX.md`). Platform behaviours these rely on are recorded with
confirmation dates in `MEMORY.md` — read that too.

Abbreviations: **TM** = tm-alert-adjudication.xml, **SAN** = sanctions-hit-adjudication.xml,
**MED** = meridian-medicaid-medicare-eligibility.xml, **DOC** = document-examination-three-way-match.xml,
**LAB** = certainty-mechanics-lab.xml.

---

## 1. Choosing the overall architecture

**Interactive decision model** (humans answer questions): layered pipeline —
features → signals → context → suppression/defeaters → hard blocks → candidate
outcomes → precedence ladder → evidence layer. [TM, SAN, MED]

**Headless document/data examination** (all facts injected via API): EAV meta-model +
numbered check rels + findings records. [DOC] Use when the input is variable-shaped
records (documents, extracted fields, transactions) rather than a fixed questionnaire.

**Both**: keep systems-of-record data `askable="none"`; keep askable only what a human
could genuinely answer. Question volume is controlled ONLY by askability + input
coverage — the engine eagerly queues questions for every reachable askable
(count-gates do NOT suppress them).

## 2. The EAV document meta-model [DOC]

Model variable-shaped input generically: `Document → contains fields → Field`,
`Field → is field type → Field Type`, `Field → is data type → Data Type`, plus one
typed projection rel per primitive (`text value`, `number value`, `date value`,
`truth value`) and `table row` for line items. The ontology never names a business
field; new document layouts need no schema change. Companion idioms:

- **Reified schema registry**: `expected data type` facts per field type; one generic
  rule validates every field's declared type; an `Unmapped` catch-all instance routes
  unrecognised input.
- **Scalar/leaf discrimination**: `countRelationshipInstances(%F,'table row',*) = 0`
  restricts scalar rules; the same count `>= 1` selects line-item fields.
- **Table-row correlation join**: several fields sharing one `%ROW` binding is the only
  way to correlate columns of a line item (quantity × price = total).
- **Projection before absence**: count functions cannot traverse two hops — materialise
  an index rel (`case has document group`, `has document number`) with a projection
  rule, then test absence with one count against it.

## 3. Check suites and findings [DOC]

- **Requirement-numbered check rels**: each acceptance criterion gets its own queryable
  rel named with its requirement ID (`1.1 required documents check`), from the root
  case concept to a module-level findings concept, plural. A **run-all umbrella** rel
  is populated by one trivial copy rule per check, so one query runs the suite while
  each check stays individually queryable and regression-testable.
- **Delimited positional finding records**: relationships are binary, so a multi-field
  finding is packed as `CODE;entity;rulebook;message;label;expected;label;actual;Status`
  into the plural findings rel. Keep empty slots' delimiters so consumers can split
  on `;` positionally. Status comes from a closed vocabulary (Discrepant/Clean/Information).
- **Composite per-binding keys**: inferred string facts DEDUPE on (subject, rel, object)
  — a generic rule firing once per item MUST embed the distinguishing variables in the
  record (`'CODE-' + %ITEM + '-' + %ATTR + ';…'`) or N violations collapse into one.
- **Paired Clean rules**: failure rules populate an internal violations rel; the check
  rel copies violations AND emits an explicit Clean record gated on
  `countRelationshipInstances(%S,'<violations rel>',*) = 0`. Evaluating the count
  forces backward-chaining through the whole failure family first. Audit-grade systems
  need explicit passes, not silent absence.
- **Rule names carry requirement IDs** (`AC 2.1A …`) and generic families carry a code
  taxonomy (`GEN.C.TXT` = generic/conflict/text). Traceability lives in names.

## 4. Decision ladders and outcome exclusivity [TM, SAN, MED]

- **Two-layer ladder**: a plural grade-candidate rel (each candidate rule carries its
  own cf) + a count-gated precedence ladder into a singular outcome rel. Each ladder
  rung requires zero candidates of every higher grade. Never let a candidate rule
  count its OWN rel (self-recursion risk) — priority lives in the ladder.
- **Explicit-false clearances**: approvals require `count(explicit false clearances) = N`
  so unknown never approves. Two-sided determinations: object=true rules plus one
  object=false rule that requires the complete record — missing data leaves the gate
  unfired and the outcome conditional.
- **Mirror-reason guard**: any reason/evidence rule mirroring a gated outcome must copy
  ALL of that outcome's guards, or declined cases carry approve-reasons. This has been
  the highest-yield review check across builds.
- **Data-driven suppression/exclusion registry**: put skip-lists and exclusions in
  facts consulted via a zero-count, so scope changes are data edits, not rule edits.
  [TM suppression map, MED exclusion marks, DOC `is excluded from generic checks`]

## 5. Certainty design [LAB, TM]

Certainty algebra (confirmed live): output cf = rule cf × Σ(wᵢ·cfᵢ/100)/Σwᵢ over all
conditions; unmet optionals contribute 0; multiple rules on the same fact combine by MAX.

- **Graded per-indicator rules**: one rule per indicator at its own cf; MAX keeps single
  strong indicators actionable. Beats one weighted-optionals rule for detection logic.
- **Weight-1 gates**: the carrier condition keeps weight 100; count-gates and auxiliary
  bindings get `weight="1"` so output cf tracks the carrier instead of being inflated
  or diluted by cf-100 gates. Apply to rationale rules too.
- **Weight-0 optional binds**: `behaviour="optional" weight="0"` binds enrichment or
  filter data with ZERO effect on cf. The **paired weight-0 join** (two optional
  conditions sharing a variable) implements "prefer the latest revision, else any".
  **Optional-chain propagation**: any condition consuming an optionally-bound variable
  must itself be optional weight-0, or a skipped binder kills the rule.
- **Low-weight optional corroboration**: mandatory anchor + optionals at weights 10–25
  lets thin data answer at slightly reduced cf instead of failing.
- **`minimum-rule-certainty="1"`** (rule attribute): fire on any nonzero-confidence
  evidence — for rules over low-cf extracted/OCR facts. **`behaviour="top-down-strict"`**
  (rule attribute): strict written-order evaluation for rules whose global counts only
  make sense after earlier joins resolve. Both observed in production RBLang; semantics
  inferred — probe live before relying on nuances.

## 6. Reference data as facts [DOC, SAN, MED]

- **Policy parameter facts**: thresholds/windows as facts on a policy instance, bound by
  conditions. Enables one-line policy-flip variant maps for fringe testing.
- **Alias normalization tables**: variant spellings and canonicals are instances of ONE
  concept with a `maps to` rel; **include identity self-rows** (`EA → EA`) or the
  generic rule silently fails for already-canonical input.
- **Group taxonomy**: groups are ordinary instances of the same concept as leaves
  (`belongs to group` self-rel). Add **reflexive self-membership** (every value belongs
  to its own group, via `expression="%S" value="%O"`) so requirements can name a group
  OR a leaf uniformly; add an **ALL sentinel** instance populated by inference for
  universal requirements. Two-level chains work by ordinary rows.
- **Compound-key instances + decomposition table**: instance names embed a composite key
  (`10a-first-purpose`); a companion fact table maps each back to its bare code so rules
  can join on the code alone.
- **Decision-matrix fact tables**: encode outcome matrices as fact rows consumed by one
  generic rule, not one rule per cell. [SAN, MED]

## 7. Joins, dedup, and pairwise comparison [DOC, SAN]

- **Ordinal symmetry-breaking**: give each record an injected ordinal; pairwise rules
  require `%N1 is greater than %N2` so each unordered pair fires once and self-pairs are
  impossible. (String inequality `%A is not equal to %B` only removes self-pairs — you
  get both A-B and B-A.)
- **Bidirectional anti-join**: to assert two bound items are NOT linked when the link
  may be recorded either way, zero-count BOTH orientations with bound-variable
  subject AND object filters.
- **Synthetic composite-key dedup pipeline**: (1) compose `type + '-' + number` keys —
  identical keys collapse because inferred string facts dedupe; (1b) keyless fallback
  at LOWER cf using the instance's own identity, gated on a zero-count of the key
  source; (2) rejoin by rebuilding the candidate key and equality-testing; (3) pick the
  canonical member by `minObjects` over collected ordinals (count-guarded); (4) mark
  the rest `is a copy of` and report them.
- **Computed companion-key join**: when pairing is encoded only in a naming convention,
  build the expected companion name (`%CAT + '-unit'`) and equate a second binding to it.
- **Free-floating joins silently fail**: a condition whose subject variable is bound by
  no other condition never binds, with no error. Join only through real relationships.

## 8. The text-analysis toolkit [DOC]

- **Non-blank guard**: `regexCount(%X,'/\w/') is greater than 0` — there is no
  isEmpty(); blank extractions otherwise satisfy containment tests vacuously.
- **Four-way bidirectional containment**: names "match" if either contains the other at
  either case sensitivity — `includes` both ways, then dynamic `'/' + %A + '/i'`
  patterns tested both ways. All four must fail before declaring conflict.
- **Dynamic regex construction**: build the pattern into its own variable in a separate
  condition before `regexCount` (required by the platform).
- **Data-driven vocabulary regex**: keep alternations as facts (`'INVOICE|TAX INVOICE|BILL'`)
  and build `'/\b(' + %VOCAB + ')\b/i'` in the rule — vocabulary grows by data edits.
- **Normaliser family with confusable exclusion**: one rule per canonical value:
  positive word-boundary alternation ≥ 1 AND zero-count of confusable sibling terms
  (stops USD matching inside AUD wordings, a keyword matching inside its own negation).
- **Emulated negative lookahead**: phrase present (`≥ 1`) AND extended-phrase absent
  (`'…phrase [a-z]' = 0`) distinguishes a bare phrase from one followed by content.
- **Anchored whole-string whitelist**: `regexCount(%V,'/^(A|B|C)$/') = 0` per part,
  split across conditions to stay under the 500-char pattern cap; non-membership
  requires ALL parts zero (give each part alt text naming its range).
- **Duplicate-name rule families = disjunction**: several rules, same target rel, same
  rule name, one phrasing/alternative each.
- includes()/startsWith/endsWith are case-sensitive; literal `+` in a pattern is `[+]`
  never `\+`; regexCount errors are NEGATIVE numbers (pattern >500 chars = -4).

## 9. Dates and tolerance [DOC, MED, TM]

- **Working-day roll-forward pair**: weekday branch relays the date unchanged
  (`dayOfWeek(%D) lte 5`); weekend branch decomposes stepwise — bind `dayOfWeek(%D)`
  into `%DOW`, compute `8 - %DOW`, then `addDays(%D,%ROLL)` — because function calls
  must NOT take expression arguments (they silently never bind).
- **Variable-offset deadlines**: `addDays(%BASE,%N)` where `%N` comes from a policy
  fact; violations compare with `isAfterDate` (use the complementary =true/=false rule
  pair so both outcomes are explicit facts).
- **Flag-branched deadlines**: branch rules on a boolean scenario flag; one branch
  selects the earliest date inline via count-guarded `minObjects`, the other uses a
  singular derived date; both share the same arithmetic tail.
- **Epsilon equality**: never compare computed floats exactly — compute the difference,
  take `abs`, compare to a small epsilon, all in separate conditions.
- **Symmetric tolerance band**: margin = base × pct / 100 (ordered left-to-right!),
  bounds = base ∓ margin, then `isWithinRange(...) is equal to false`.
- **Whole-number check**: `round(%N,0) is equal to %N`.
- Expressions have NO operator precedence — even bracketed subterms evaluate strictly
  left-to-right afterwards. Order every multi-operator expression accordingly.
- Guard EVERY min/max/sum aggregation with a count ≥ 1 — `minObjects` over an empty set
  asserts a NULL fact that compares like +infinity downstream.

## 10. Evidence and explanation [MED, DOC]

- alt text on every expression condition (skip pure relays/concats — their output IS
  the display); `{{%VAR}}` interpolation carries actual figures into the narrative;
  rule-level alt gives the evidence tree a headline. No `"` or `<` in alt; ≤220 chars.
- Decompose fused arithmetic (×1200) into honest steps (×12 then ×100) or the NL
  narrator garbles it; collapse degenerate pure-arithmetic plumbing chains into one
  ordered expression with one interpolated alt.
- Gate every evidence/notice rule on exactly the outcome it narrates (§4 mirror guard).
- Audit the evidence layer of every live run — it has produced the only post-live bugs
  on multiple consecutive builds.

## 11. Hierarchies without recursion [SAN]

Do not write self-recursive derived rels (termination unproven). Encode bounded-depth
traversal as per-level derived rels (level-0 direct, level-1 via level-0 holders,
level-2 via a DEDUPED string mark from levels ≤1), with EXACTLY ONE derivation rule
per level binding the deduped mark — number facts do not dedupe, so a second rule
double-counts.
