# Graph findings (accumulated across tasks)

Topic-organized log of platform behaviours confirmed live, with dates. Where a newer
finding corrected an older one, the correction is applied in place and noted — do not
"rediscover" the superseded version. Update this file with any new confirmed findings.

## !! LESSONS — READ FIRST !!

These are hard-won. Apply them on EVERY task.

1. NEVER DELETE A RULE THAT TRACES TO A REQUIREMENT. If an existing rule looks
   "dead"/non-firing, FIX it in place.
2. "Currently non-firing" != "should be removed". An acceptance requirement's
   rule legitimately fires only on the inverse/edge case. Distinguish that from
   a rule dead due to a real BUG (e.g. testing a non-existent field type, or the
   wrong comparator) — fix the bug, keep the requirement.
3. Consolidating genuinely-redundant overlapping rules (same requirement,
   different incidental conditions) is OK, but PRESERVE coverage and document
   the old->new mapping + which requirement, so traceability stays.
4. Dates: compare with isSameDate(%A,%B) = false / isAfterDate(...) = true, NOT
   "is not equal to". Counts/numbers use "is equal to / is greater than / is not equal to".
5. NO FUNCTION CALL may take an expression argument (round() found 3.7.26; addDays
   CONFIRMED 6.7.26 — `addDays(%DATE,8 - dayOfWeek(%DATE))` silently never bound).
   Compute each piece in its own condition and pass plain variables. A single function
   call inside a COMPARISON (`dayOfWeek(%DATE) lte 5`) is fine — proven live.
6. NO OPERATOR PRECEDENCE IN EXPRESSIONS, EVEN WITH BRACKETED SUBTERMS (20.7.26):
   '%B + (%B - 1) * 2' with B=5 returned 18, i.e. (5+(5-1))*2 — strict left-to-right
   over the remaining operators. Brackets group a subterm but do NOT restore precedence.
   Order every multi-operator expression so left-to-right evaluation is correct:
   '(%HS - 1) * %I + %B' works. Probe any collapsed arithmetic on a tiny map before
   shipping (a two-minute check that caught this).
7. XML COMMENTS must not contain double-quote (") or literal < characters — the
   platform's non-strict importer chokes on them INSIDE comments (symptom:
   "invalid character '<' looking for beginning of value", no line number; hit
   2.7.26). Write comments with apostrophes and words (LTE, GT/LT) instead.
   (The importer IS tolerant of some other strict-XML violations — bare & and
   `--` runs inside comments exist in a working production graph — but do not
   rely on that; emit strict XML.)
8. countRelationshipInstances: QUOTE THE REL NAME —
   countRelationshipInstances(%S,'rel name',*) is the confirmed-safe form (an
   unquoted-name failure was hit live pre-13.7.26). Nuance (24.7.26): a large
   production graph uses unquoted multi-word rel names in count/sum functions
   extensively and works — so unquoted can validate, but prefer quoted.
9. RELINST FACT OBJECTS MUST BE DECLARED CONCINSTS: a fact like
   `<relinst type="is excluded from X" subject="slug" object="Some reason text"/>`
   imports as "Invalid Concept Instance" unless every distinct object string has a
   `<concinst name="..." type="<object concept>"/>` declaration. (Rule-composed
   string objects need NO concinst — this applies to literal facts only.)
10. CONDITION ORDER = EVALUATION COST. The engine evaluates a rule's conditions in
   order and stops at the first that binds nothing — put the cheap, selective gate
   first and expensive derivations (joins, sub-rules) last. (This is about COST, not
   question suppression — see "Question harvesting" below.)
11. Literal '+' in a regexCount pattern: write `[+]`, not `\+` — the platform rejected
   the escaped form (leaving `/+.../` = invalid leading quantifier which silently
   killed a rule). Character classes need no escape in any engine.
12. includes() is CASE SENSITIVE (as are startsWith/endsWith). Use a case-insensitive
   regex (`regexCount(%X,'/pattern/i') >= 1`) wherever case must not matter.
13. FREE-FLOATING JOIN SILENTLY FAILS (19.7.26): a rule on subject A binding a fact of
   an unrelated subject B via an unbound variable (condition subject="%CASE" with %CASE
   never bound) never binds — no error, the rule just never fires. Only join across
   subjects through a real connecting relationship.

## Certainty algebra & weights — CONFIRMED live 13.7.26–17.7.26

- Observed cf of an inferred fact = rule cf x SUM(weight_i x antecedent_cf_i/100) / SUM(weight_i),
  over ALL conditions (expressions count as weight-100 conditions; a condition binding an inferred
  fact contributes weight x that fact's cf/100; UNMET optional conditions contribute 0).
  Examples: rule cf90 with mandatory anchor + met optionals (100+90)/450 -> 38; 5 all-met
  conditions one at cf97 -> (497/500)x100 = 99; situation cf85 feeding 4-condition cf90 rule -> 87.
- MULTIPLE RULES asserting the same fact combine by MAX of their cfs, NOT probabilistic OR
  (reconfirmed 17.7.26: cf90 + cf80 rules hitting the same string object => one fact at 90).
  So graded per-indicator rules (e.g. vulnerability cf85/80/75/70/65) beat one weighted-optionals
  rule when single indicators must stay actionable — one weighted rule scores a single strong
  indicator absurdly low (38) because unmet optionals drag the ratio down.
- WEIGHT-1 GATE PATTERN (17.7.26 — the big one for graded decision models): give each rule ONE
  weight-100 carrier condition (the signal/candidate fact binding) and weight="1" on all
  count-gates and auxiliary bindings -> the rule output cf tracks the carrier cf almost
  exactly (cf_out ~ rule_cf x (carrier + n x 0.01)/(100 + n)). Confirmed through a
  4-layer chain. Without weights, gate conditions (cf 100) inflate low-cf carriers and
  dilute high-cf ones. Also apply to rationale/reason rules so their cf tracks the outcome cf.
- weight="0" on a condition is VALID and appears in a working production graph: binds
  data without contributing to the certainty average at all (stronger form of the
  weight-1 trick; weight-1 keeps a sliver so the answer is provably data-backed).
- Corroborating-data conditions as behaviour="optional" with LOW weights (10-25) on
  alignment rules — thin data then gives the same answer at cf ~95-97 instead of failing.

## Fact semantics: dedup, injection, singular/plural — CONFIRMED 14.7.26–18.7.26

- Inferred facts with STRING objects DO dedupe on (subject, rel, object): 5 same-suit cards
  each deriving 'hand has suit X' left exactly 1 fact, so countRelationshipInstances gives a
  true DISTINCT count for string-object derived rels.
- Inferred facts with NUMBER objects do NOT dedupe: a one-pair hand produced
  has paired rank => [10,10] (both binding orders). countRelationshipInstances over a
  number-object derived rel counts EVERY derivation. Practical: distinct-count logic must
  run over string-object relationships (mirror numbers as named string instances). The
  no-dedup behaviour is what makes sumObjects over per-item derived number facts EXACT
  (each binding path = one addend; 15 live scenarios 17.7.26).
- Injecting the same fact twice collapses to one fact.
- SINGULAR REL DOUBLE-INJECTION (18.7.26): injecting two different objects into a
  non-plural rel is NOT reliably retained (engine kept one). Data contract: exactly one
  value per singular rel per session. (Ladder exclusivity under contradictory injection
  into PLURAL derived candidate rels still resolves correctly — 19.7.26.)
- INJECT REJECTS INVALID DATES with HTTP error 'Invalid date format for <rel>: <value>' —
  unparseable dates never enter the graph; completeness guards only need to handle
  MISSING entries, not malformed ones.
- Literal number objects in rule conditions validate and match (object='14'); pairwise
  instance distinctness via string inequality (%C1 is not equal to %C2) works.
- Literal concept-instance names work as condition objects AND subjects — the
  parameter-fact pattern (thresholds as facts on a policy instance, bound via conditions)
  validates and runs correctly.
- INJECTING FACTS INTO DERIVED (askable="none") RELS WORKS and drives downstream rules —
  great for truth-table regression sweeps of upper layers (15.7.26).

## Aggregations & empty sets — CONFIRMED live 15.7.26

- sumObjects over an empty derived set returns 0 (rule fires, fact object 0).
- minObjects over an empty derived set FIRES the rule and asserts a fact with object NULL
  (not 0, not absent). Downstream conditions BIND that null fact, and comparisons treat
  null like +infinity: `null is less than 1.25` = false, `null is greater than or equal
  to 1.25` = TRUE. Practical: ALWAYS guard min/max/sumObjects aggregation rules with
  `countRelationshipInstances(%S,'rel',*) is greater than or equal to 1` or an unknown
  input silently produces a best-case value downstream.
- minObjects/maxObjects over a derived plural DATE rel with count guard >= 1 works even
  when all contributing dates are the SAME DAY (span 0). Use guard >= 1 not >= 2 —
  sidesteps the (unconfirmed) dedup semantics of derived date-object facts (17.7.26).
- minObjects COMPLETENESS-EQUALITY guard (count of derived items EQUALS count of source
  entries, both >=1) proven live — elimination never fires from a partial set (18.7.26).
- countRelationshipInstances over a DERIVED relationship DOES drive full backward-chaining
  inference of that relationship at evaluation time — a gate rule counting derived facts
  works even when queried first, cold (13.7.26). The negative-targeting pattern
  (concern -> block-map fact table -> single generic block rule -> gate counting
  blocks = 0) is proven and avoids mirror-rule drift.
- countRelationshipInstances with a LITERAL MULTI-WORD STRING object filter,
  e.g. countRelationshipInstances(%S,'has strong typology signal','Structuring'),
  validates and works at runtime (17.7.26).
- A candidate rule must never countRelationshipInstances over its OWN rel
  (self-recursion risk); enforce priority in the precedence ladder instead. Counting a
  DIFFERENT derived rel inside a candidate rule is safe and verified live (19.7.26).

## Expression/function behaviours proven live

- Age-from-DOB: bind today() to a variable in its own condition, then
  yearsBetween(%DOB,%TODAY), then floor(%YEARS) into %O (lesson-5 compliant).
- year()/monthOfYear() value capture in their own conditions, then plain-variable
  comparisons (18.7.26); sign-split abs via two rules with mutually exclusive
  (%D gte 0)/(%D lt 0) conditions yields exactly one gap fact per item (no double count).
- mod(%AMT,1000) value capture works (round-amount detection, 17.7.26).
- OR of string equalities on a bound variable validates and runs:
  (%CT is equal to 'Corporate') or (%CT is equal to 'Business') (17.7.26).
- Date-ordering guard `isBeforeDate(%D2,%D1) is equal to false` in a derivation rule
  works live (daysBetween is always positive, so guard order explicitly) (17.7.26).
- ceil(%VAR), startsWith(%VAR,'literal'), addYears/addMonths/subtractMonths/subtractDays/
  monthsBetween with plain-var args, isWithinRange(dateVar,dateVar,dateVar) — all proven
  live (19.7.26). Query results render date objects as '1st July, 2026' strings — tests
  generated from live runs must capture that exact format.
- Rule-composed string objects ('Delivered ' + %SUG + ' under segment ' + %SEG into %O)
  work and need NO concinst declaration.
- Exact band-boundary tests with floats: pick inputs whose derivation is exact in binary
  (e.g. 0.85 x 175000 / 85000 = 1.75 exactly) or the boundary probe lies (15.7.26).

## Question harvesting & askability — CORRECTED 17.7.26 (supersedes 13.7/15.7 nuances)

- QUESTION HARVESTING IS FULLY EAGER: at query time the engine queues questions for
  EVERY askable relationship reachable from any candidate rule, BEFORE evaluating
  conditions. Leading countRelationshipInstances gates do NOT stop their rule's later
  askables being asked, even when the gate is already failed by injected facts. (An
  earlier 15.7.26 build observed count-gates suppressing questions in one flow — do
  NOT rely on that for question UX.)
- QUESTION VOLUME IS CONTROLLED ONLY BY ASKABILITY + INPUT COVERAGE. Design rule:
  systems-of-record data (transactions, screening outputs, reference lists, metadata)
  -> askable="none", injected/datasource only. Keep askable ONLY facts a human could
  genuinely answer. Then question count = number of askables the consumer chose not
  to state.
- Rels with NO askable attribute DEFAULT to askable="all" at runtime: the engine will
  ASK the user even when relinst data exists in the graph (14.7.26). Set askable="none"
  explicitly on pure-data and derived/query-target rels.
- Optional (behaviour="optional") conditions on askable rels DO generate questions too.
- Interactive question ORDER follows rule order then condition order for the queried
  relationship — putting a hard-stop rule first makes its question the first asked,
  giving a one-question decline (13.7.26).
- Question suppression by injection: injecting a NON-plural askable rel suppresses its
  question entirely; PLURAL askables are ALWAYS re-asked even when injected (the engine
  is asking for MORE members) — a programmatic consumer needs exactly one unknown-skip
  per plural rel. Inert filler instances (e.g. 'No Documented Explanation') let you
  inject answers for every non-plural askable and get near-question-free API runs (17.7.26).
- With two independent askable rules feeding one query rel, injecting only one input
  still asks the other question. Both unknown-skipped -> clean empty result [] (17.7.26).
- SCRIPTED ANSWERS MUST ATTACH TO EVERY QUERY in a session script: the engine can
  resolve query 1 BEFORE asking all queued questions, so an unasked askable resurfaces
  on a LATER query in the same session — use the same answers map on every query (19.7.26).
- Unknown answers: rel must carry allowUnknown="true". The /response payload for a skip
  is {"subject":...,"relationship":...,"object":"","unanswered":true,"certainty":100}.
  Without allowUnknown the API rejects with a certainty/object validation error.

## API playbook — confirmed 13.7.26–20.7.26

- Map upload: POST https://api.rainbird.ai/maps REQUIRES header `Version: v1` alongside
  `X-API-Key`, else 400 "unsupported API version". Payload {"rblang": xml, "name": str,
  "description": str}. Long/punctuated descriptions rejected with 400 DESCRIPTION_ERROR;
  short plain text (~35 chars) accepted. Success = 201 with {"kmID": guid}; the map is
  LIVE immediately (GET /start/{kmID} with no useDraft/version params). ~296KB rblang
  uploads fine.
- canAdd="all", plural, askable, allowUnknown all validate on upload.
- /inject body is a BARE ARRAY of {subject, relationship, object, certainty}; /query is
  {subject, relationship}; only /response wraps in {"answers":[...]} — a bare array to
  /response is rejected with "Please provide a valid response containing an answers array".
- Inject accepts JSON booleans and dates as 'YYYY-MM-DD' strings; query subjects that
  match no concinst are auto-instantiated (no canAdd needed for API use).
- Querying a plural rel returns one result item per inferred object (all reasons).
  Result items carry relationshipType AND relationship as plain strings; the
  .question.relationship field in /query responses can be a plain STRING — parse both shapes.
- /nl/explain WORKS (needs Version: v1): POST /nl/explain {sessionID, factID, language:'en'}
  gives an audit-quality narrative naming rule-bound thresholds. factID is the 'factID'
  field (WA:RF:... hash) on each /query result item. Caveat: it rendered derived DATE
  facts wrong once (epoch-ms misconversion; the day-span number was right) — the
  deterministic evidence tree remains the system of record.
- /nl/interact error 23 'Invalid query (selected by LLM)' with llmTokens 0 is a TRANSIENT
  LLM-BACKEND outage — NOT account gating, NOT map size/prompt wording (same map+prompts
  failed then fully worked ~30 min later; 17.7.26). Retry later before rewording anything.
  Healthy calls show real token counts. ALSO (20.7.26): the raw /nl/interact endpoint and
  the Studio NL agent are on DIFFERENT backends — /nl/explain can work via API key while
  raw /nl/interact 403s/errors and the Studio NL agent works fine. Never diagnose map
  health from raw /nl/interact; verify NL prompts through Studio.
- NL PROMPTS MUST BE CASE-EXPLICIT for query surfaces hung off a Case entity: prompts that
  only name the person make the NL agent query the wrong subject. Generate prompts
  verbatim from the injection payload (name the case, state facts in rel vocabulary, ask
  for the case's outcome rel). The narrator renders bare numbers with a currency symbol
  of its own choosing — note it in docs (20.7.26).
- The /analysis/evidence REST path 403/404s in both argument orders on the accounts
  tried — treat as unverified; use /nl/explain plus Studio's evidence tree (20.7.26).
- Docs trick: docs.rainbird.ai is GitBook — append ?ask=<urlencoded question> to any
  docs .md URL to get a synthesized answer with sources.
- POLICY-FLIP FRINGE VARIANTS: regex-edit the single policy relinst line in the XML and
  re-upload as a variant map; fact-flips run on the main map by rebuilding the inject
  list minus the replaced fact (18.7.26).

## Studio test-suite JSON — import lessons 17.7.26

- Tests JSON with guessed skip steps (then.Respond.with using unanswered/certainty
  fields) and/or NUMERIC inject object values FAILED to load in Studio. What works:
  (1) make every data-layer rel askable="none" so full-injection runs are QUESTION-FREE,
  then generate tests as pure Inject -> Query -> Expect Result with NO question steps;
  (2) stringify EVERY inject object value ('3200', 'true', 'false');
  (3) keep field names exactly as tests_examples.json: inject entries {subject,
  relationship, object, cf:100 (number)}, expect results {cf:'90' (STRING), object,
  subject, relationship}, steps expect.subtype 'Second Form', then.type
  Inject/Query/none with 'with':[]. Do not emit Respond/skip steps unless the shape has
  been captured from a real Studio export of a hand-built skip test.
- Generate tests FROM live runs so expected cfs are engine-exact.
- Driver-pack JSONs (scenarios/probes with inject+queries+expect) are NOT
  Studio-importable and fail confusingly in the UI (silent failure / TypeError on
  'length'). Label them clearly as API driver packs; ship Studio-format tests
  (generated from live runs) as the only JSON intended for the Studio test suite (20.7.26).
  Convert question-free adversarial probes into Studio-format tests as well, so the
  Studio suite carries the adversarial coverage, not just happy-path scenarios.

## Evidence & alt text — REQUIRED + CONFIRMED 20.7.26

- STANDING REQUIREMENT (all projects): every expression condition carries alt text so the
  evidence tree reads like a caseworker narrative and /nl/explain narrates faithfully.
  Enforce via lint (alt present; no double quotes or angle brackets inside; length <= 220).
  Skip alts on string-concatenation value-captures — their composed output IS the display.
- RULE-LEVEL alt VALIDATES and is shown as evidence text (alt can be set on both the rule
  and each condition). Generate rule headlines mechanically from rule names.
- ALT SUPPORTS VALUE INTERPOLATION with double curly braces {{%VAR}} incl. a condition's
  OWN value-capture variable — alts can carry actual figures ('countable {{%CI}} dollars
  is within the {{%QL}} dollar limit'). Lint brace balance.
- DECOMPOSE FUSED ARITHMETIC: a single condition doing two things (monthly x 1200) gets
  garbled by the NL narrator ("scaled annually" for x1200). Split into honest steps
  (x12 annualise, then x100 percent-units) each with its own alt.
- COLLAPSE DEGENERATE PLUMBING: pure-arithmetic chains (no function calls) can merge into
  one left-to-right-ordered expression with one interpolated alt (a three-row nonsense
  popup became one sentence). Chains touching function calls must stay decomposed (lesson 5).
- ALT AUTHORING AT SCALE: template+glossary generator over distinct expressions +
  hand-written overrides for decision-bearing arithmetic + a polish pass rewriting
  count-gate templates into domain phrasing. Watch per-file variable collisions
  (%T claimer vs threshold) — per-file glossary overlays. Generator bug to avoid: always
  emit a space before alt= when reconstructing attribute lines.
- ALTS ARE DISPLAY-ONLY (confirmed 20.7.26): a fully alt-annotated map passed the
  complete regression suite (32 scenarios, 8 flips, 18 probes) with identical outcomes
  and cfs — alt-only edits do not require behavioural re-verification.

## Design patterns proven end to end (see also patterns.md)

- Decision-graph pattern (15.7.26): triggers -> explicit-false clearances (count = N for
  approvals so unknown never approves) -> explicit matrix rows -> two-layer base outcome
  (copy-if-explicit-count>=1 else default Refer) -> tightening ladder -> cap layer ->
  final. Exactly one final outcome in 54/54 live probes including unknown-heavy cases.
- MIRROR-REASON GUARD: reason/evidence rules mirroring a gated rule must copy ALL of that
  rule's guard conditions or the reason fires when the mirrored rule does not (caught on
  three separate builds — treat as a standard review check). Gate evidence/notice
  mirrors on the outcome/category they narrate.
- BOUNDED-LEVEL OWNERSHIP DAG (18.7.26): use per-level derived rels (level-0 direct,
  level-1 stakes held by level-0 holders, level-2 via a DEDUPED string 'Caught' mark
  from level<=1) instead of self-recursive derived rels (termination UNPROVEN, guide
  warns against). EXACTLY ONE stake-derivation rule per family per level binding the
  deduped mark — number facts do not dedupe, so a second rule double counts.
- IDENTITY TWO-LAYER LADDER (18.7.26): plural grade-candidate rel (cf on the grade rule)
  then count-gated precedence ladder into a single assessment rel; 19 adversarial probes
  produced EXACTLY ONE final outcome every time on a 5-outcome ladder.
- Two-sided derived determinations (19.7.26): object=true rules + one object=false rule
  requiring the complete injected record — the false rule fires only on complete data, so
  missing records leave the gate unfired and the outcome conditional ('unknown never
  approves' verified by probe).
- COUPLE/COMBINED-UNIT ARITHMETIC (19.7.26): when a methodology applies a disregard once
  per unit (e.g. one $20 per couple), encode the combined-unit arithmetic in a single
  rule — never sum two per-member countables (double-applies the disregard).
- REPORTING-OBLIGATION ACCRUAL (18.7.26): always audit the reporting/evidence layer of
  every live true-positive run, not just outcomes and cfs — two real gaps were only
  visible in live evidence output. Evidence-layer audit has found the ONLY post-live
  fixes on three consecutive builds.

## Build-process lessons (multi-agent)

- WORKFLOW-AGENT STALL MODE (hit on 3 builds): big single agents told to read a
  100–250KB XML fully and build exhaustive cross-reference tables stall out and return
  NOTHING. What works: (a) deterministic python lint for all mechanical checks
  (references, types, literals-vs-concinsts, quoting, askable audit, alt lint);
  (b) ATTACKER agents that output RUNNABLE PROBE PAYLOADS (schema-forced JSON) which
  the main loop executes against the live engine — self-verifying; (c) HAND-WRITTEN
  deterministic probe sets when even attacker agents stall; (d) narrow auditors reading
  TRIMMED summaries (rel|subject->object|flags + policy facts + rule names), never the
  raw XML. An empty workflow result with 'stalled' failures means the agents died, NOT
  that there were no findings.
- Multi-agent adversarial review earns its cost when structured: 28 raw findings -> 15
  confirmed real on one build; verifiers correctly killed 13 plausible-but-wrong claims.
- Build pattern that worked end to end (3 builds): research fan-out (+ gap critic) ->
  design-critique panel BEFORE authoring -> central authoring in part-files ->
  deterministic lint -> /maps upload -> live scenario driver with unknown-skip loop ->
  adversarial probes -> evidence-layer audit -> regression -> tests generated FROM live
  runs so expected cfs are exact.

## Standing deliverable requirements (from Rainbird stakeholder sessions, Jul 2026)

- THREE-GRADE TEST/DEMO SETS on every project: (a) straight-through — input covers every
  askable, zero questions (verify engine-side); (b) few clarifying questions — curated
  gap set with scripted Q&A attached to every query; (c) fringe — boundary facts whose
  outcome FLIPS on one policy-fact change, verified live on both sides via a variant map.
- ALT TEXT on every expression condition (see Evidence & alt text above).
- .rbird DELIVERABLES ARE PAUSED (20.7.26): programmatically built .rbird files (format:
  gzip JSON {studioData, unicronData, readmeData}; unicronData rblang line-array is the
  source of truth) CORRUPT the Studio UI — something beyond layout/readme in hand-rolled
  unicronData diverges from real Studio exports. DO NOT ship programmatically built
  .rbird. If one is ever needed: import the validated XML into Studio, export a genuine
  .rbird, and edit ONLY readmeData/layout via gunzip -> edit -> re-gzip,
  round-trip-verifying everything else byte-identical; get explicit user sign-off first.
  Format details for that permitted edit path: canvas layout lives in
  studioData.concepts as {conceptId: {x,y}}; readmeData is an HTML string supporting
  only h1/h2/h3, p, strong, em, code, pre, ul/ol/li, br — NO TABLES (the Studio readme
  editor flattens them into run-on text; use lists). The EVENTUAL (currently paused)
  goal remains a per-project .rbird with concepts arranged in functional clusters
  (inputs left, derivations centre, outcomes right) and a readme carrying the NL test
  cases. When the user supplies a Studio-exported .rbird with a hand-arranged layout,
  preserve their layout byte-for-byte and replace only readmeData.
- Ship instead: validated RBLang XML, Studio-format tests JSON (from live runs), API
  driver packs (clearly labelled), a standalone markdown blueprint/readme including
  natural-language test cases and NL prompts.
- REGULATORY CURRENCY OF THE EXAMPLE GRAPHS: the TM / sanctions / Medicaid example
  graphs' domain grounding is frozen at 17–18 Jul 2026 (SI 2026/621; UKSL single list;
  Feb 2026 OFSI enforcement framework; EU Best Practices 2024 aggregation; OFSI
  ownership call-for-evidence pending; OBBBA effective dates 1 Oct 2026 / 1 Jan 2027;
  2026 FPL/SSI figures). Re-verify all citations, thresholds, and effective dates
  before reusing their domain content in new builds.
