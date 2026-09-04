# Example graphs — what each one demonstrates

Follow these closely when building. Each graph is the reference demonstration for the
patterns listed against it (the full pattern catalogue with explanations is in
`../patterns.md`). All were linted with `../tools/lint_rblang.py`; the first three were
validated live against the Rainbird platform in July 2026.

⚠ **Regulatory currency**: the domain content of the three live-validated graphs
(TM, sanctions, Medicaid) is frozen as of 17–18 July 2026 — UK SI 2026/621
thresholds, the Feb 2026 OFSI enforcement framework, EU Best Practices 2024
aggregation, OBBBA effective dates (1 Oct 2026 / 1 Jan 2027), and 2026 FPL/SSI
figures. Copy their *patterns*, but re-verify every citation, threshold, and
effective date before reusing their domain content.

## tm-alert-adjudication.xml — transaction-monitoring alert adjudication (157 rules, live-validated)
An **interactive + API decision model**. Demonstrates:
- the layered decision architecture: features → typology signals → context scoring →
  defeater suppression map → hard blocks → candidate outcomes → precedence ladder →
  evidence/rationale layer
- the **weight-1 gate** certainty pattern (output cf tracks the carrier condition)
- graded per-indicator cf rules combined by MAX
- data-driven suppression map (skip-list as facts, zero-count consultation)
- `secondFormObject` questions, `allowUnknown`, `canAdd`, plural askables
- per-transaction derived value items summed exactly with `sumObjects`
- explicit "no indicators found" positive-evidence rule

## sanctions-hit-adjudication.xml — multi-regime sanctions hit adjudication (205 rules, live-validated)
A **regime-parameterised decision model**. Demonstrates:
- **bounded-level ownership DAG** (per-level derived rels instead of self-recursion)
- two-layer ladder: plural grade-candidate rel + count-gated precedence ladder
  resolving to exactly one outcome
- policy parameters as facts on a policy instance (one-line policy flips)
- `year()` decomposition, sign-split abs, completeness-equality guards on `minObjects`
- exactly-one count guard before singleton binding

## meridian-medicaid-medicare-eligibility.xml — US Medicaid/Medicare eligibility (297 rules, live-validated)
A **deep eligibility chain** (22 layers). Demonstrates:
- rule-level AND condition-level **alt text** everywhere, incl. `{{%VAR}}` interpolation
- household-construction cascade with exception rules
- integer-exact FPL comparison scheme (stepwise ×12, ×100 with honest alts)
- dual-eligible precedence ladder; two-sided determinations ("unknown never approves")
- date arithmetic: `addYears`, `subtractMonths`, `isWithinRange` on dates, `ceil`
- negative targeting / exclusion marks consulted by a generic sweep rule

## document-examination-three-way-match.xml — PO/Invoice/Delivery-Note examination (74 rules)
The **generic document-examination architecture** (the production pattern for checking
injected document sets). Demonstrates:
- the **EAV meta-model**: Document → Field → typed value projections
  (`text value`/`number value`/`date value`/`truth value`) with a data-type
  discriminator and a reified expected-data-type registry — the ontology never names
  a business field, so new document layouts need no schema change
- **injection-only askability posture** (`askable="none"` on every rel)
- requirement-numbered check rels (`1.1 …`, `2.1 …`) with module finding buckets and
  a run-all umbrella rel of trivial copy rules
- **delimited positional finding records**
  (`CODE;document;rulebook;message;label;expected;label;actual;Status`) with
  composite per-binding keys to defeat string-fact dedup, and paired Clean rules
- synthetic composite-key **dedup pipeline** (compose → collapse → rejoin →
  canonical-first by min ordinal → copies marked), with a lower-cf keyless fallback
- **table-row correlation joins** (line arithmetic) + scalar/leaf discrimination
- pairwise cross-document comparison with **ordinal symmetry-breaking**, and
  bidirectional **anti-join** on a possibly-reversed link rel
- the text toolkit: non-blank guards (`regexCount(%X,'/\w/')`), four-way
  bidirectional containment (includes + dynamic `/…/i` regex), data-driven
  alternation regex from vocabulary facts, emulated negative lookahead, anchored
  whole-string whitelist split across conditions, complementary includes() pair,
  free-text normaliser family with confusable-term exclusion
- alias normalization table **with identity self-mapping rows**; group taxonomy over
  document types (groups are ordinary instances) with reflexive self-membership,
  two-level chains, and the **ALL sentinel** group
- tolerance idioms: stepwise percentage band, abs-difference epsilon, whole-number
  round-trip check; working-day roll-forward date pair; flag-branched deadlines with
  `minObjects` earliest-date selection (count-guarded)
- computed companion-key join; duplicate-name rule family as disjunction; case-split
  staging rels unified by an umbrella rel; exclusion registry for generic sweeps

## certainty-mechanics-lab.xml — supplier onboarding risk screen (15 rules)
A compact **certainty laboratory** with the expected cf arithmetic worked in comments:
- graded per-indicator cf rules + MAX combination
- weight-1 gates (with the with/without arithmetic shown)
- low-weight optional corroboration (thin data still answers)
- certainty-neutral `weight="0"` optional binding, the paired weight-0 optional join
  (latest-revision resolution), and optional-chain propagation
- `minimum-rule-certainty="1"` and rule-level `behaviour="top-down-strict"`
  (production-observed attributes; semantics inferred, flagged as unprobed)
- hard-stop rule ordered first for one-question interactive declines