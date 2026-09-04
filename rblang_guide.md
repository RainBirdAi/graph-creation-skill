# Comprehensive Guide for Creating XML Knowledge Graphs

## 1. Basic Structure

The XML knowledge graph should be structured as follows:

```xml
<?xml version="1.0" encoding="utf-8"?>
<rbl:kb xmlns:rbl="http://rbl.io/schema/RBLang">
  <!-- Graph content goes here -->
</rbl:kb>
```

## 2. Key Components

### 2.1 Concepts

Define the basic entities or ideas in your domain using the `<concept>` tag:

<concept name="Concept name" type="Type"/>

Types must be one of the following: string, number, date, truth (boolean).
Do not include any other types.

Later you will create instances of concepts to hold data.
Concepts should represent the data they will hold at an appropriate level of abstraction.

Concepts should be named for the class of data they will hold.
For example if you need to represent a numeric value for the price of something use:
<concept name="Price" type="number"/>

Do not create concepts to directly represent data, you'll use concept instances for that later, treat concepts as part of the world model that will be used to hold data later.

### 2.2 Relationships

Define how concepts relate to each other using the `<rel>` tag:

```xml
<rel name="relationship name" subject="Subject concept" object="Object concept" plural="true/false" askable="none/secondFormObject" allowUnknown="true/false" canAdd="all">
  <secondFormObject>Question format for askable relationships</secondFormObject>
</rel>
```

Use `plural="true"` if the relationship can have multiple objects.
Use `askable="secondFormObject"` if you want to define a question format for this relationship.

**Give EVERY rel an explicit `askable` attribute.** A rel with no `askable` attribute defaults to *askable* at runtime — the engine will ask the user for facts even when relinst data exists in the graph. Set `askable="none"` explicitly on all pure-data, derived, and query-target relationships. Question volume in a session is controlled only by askability and input coverage: the engine eagerly queues questions for every reachable askable relationship (leading count-gates do NOT suppress them).

On askable rels, add `allowUnknown="true"` so users and API consumers can answer "unknown" (without it the API rejects the skip payload). `canAdd="all"` allows new instances to be added in answers. Note plural askables are re-asked even when facts were injected (the engine asks for MORE members) — API consumers close the enumeration with one unknown-skip.

Relationship names must be unique - never create two relationships with the same name.
The subject and object attributes must refer to concepts you've already defined.

Give relationships names that are descriptive and read naturally in English, using the same kind of vocabulary used in the expertise you're given.
The question will be asked by running inference on a relationship. Make sure there is a relationship that can be queried for the question given.

Note only concepts with a type of "string" can be used on the subject side of a relationship. Numbers, Dates and Booleans (truth) must always be on the object side.

### 2.3 Concept Instances

Create specific instances of concepts using the `<concinst>` tag:

<concinst name="Instance name" type="Concept name"/>

Never create concept instances of the types number or boolean, instead use 'true' or 'false' for booleans, and actual numbers values where ever you need instances of these types.

### 2.4 Relationship Instances

Define specific relationships between concept instances using the `<relinst>` tag:

<relinst type="relationship name" subject="Subject instance" object="Object instance"/>

The subject and object attributes of a relationship must refer either to a concept instance you've already defined, or a number value for number concepts, or 'true' or 'false' for boolean concepts.
The instances you refer to in the subject and object attributes must be instances of concepts that have the correct type for the relationship.

### 2.5 Rules

Create rules to infer new knowledge or relationships using the `<relinst>` tag with conditions:

<relinst type="relationship name" object="Object value" cf="ConfidenceFactor" name="rule name">
  <condition rel="relationship name" subject="%S" object="%VARIABLE"/>
  <condition expression="LogicalExpression"/>
</relinst>

Variables are declared with a % character and are placeholders for concept instances.
The %S and %O variables are special variables that refer to the subject and object of the relationship.

It's important that you do not use rules to encode data - rules should *always* work for the general case, regardless of the data you're given.

#### 2.5.1 Rule naming

1. Rule names can be up to 170 characters, are optional and do not need to be unique
2. If the existing graph contains rule names, then use them when adding or updating rules and try to use the same naming convention and style.
3. If the existing graph does not contain rule names, don’t use them when adding or updating rules, unless specifically asked.

#### 2.5.2 Typical Rule Usage

Rules are used to infer new relationship instances.
This is often done by explicitly setting a previously defined concept instance as the subject or object of the relationship. Or by using the %S or %O variables to create new relationship instances.

For example a rule that uses a previously defined concept instance for the object of the relationship instance might look like this:

<concept name="Concept one" type="string"/>
<concept name="Concept two" type="string"/>
<concept name="Concept three" type="number"/>

<concinst name="Instance of one" type="Concept one"/>
<concinst name="Instance of two" type="Concept two"/>

<rel name="relationship one" subject="Concept one" object="Concept two" askable="none"/>
<rel name="relationship two" subject="Concept one" object="Concept three" askable="none"/>

<relinst type="relationship one" object="Instance of two" name="Example rule 1">
  <condition rel="relationship two" subject="%S" object="%VARIABLE"/>
  <condition expression="%VARIABLE is equal to 5"/>
</relinst>

This rule will create a new instance of "relationship one" with the object set to "Instance of two" for any concept instance of "Concept one" that has relationship instance of "Relationship two" with a value of 5 for "Concept three".

Here is an example that sets the %S and %O variables in conditions to create a new relationship instance:

<concept name="Concept one" type="string"/>
<concept name="Concept two" type="string"/>
<concept name="Concept three" type="number"/>

<concinst name="Instance of one" type="Concept one"/>
<concinst name="Instance of two" type="Concept two"/>

<rel name="relationship one" subject="Concept one" object="Concept two" askable="none"/>
<rel name="relationship two" subject="Concept one" object="Concept two" askable="none"/>

<relinst type="relationship one" name="Example rule 2">
  <condition rel="relationship two" subject="%S" object="%O"/>
</relinst>

This rule will create a new instance of "relationship one" with the subject and object set to the subject and object of any matching "relationship two" instances.

#### 2.5.3 Expressions

Use expression conditions in rules to perform logical operations and mathematics.

Examples:
  <condition expression="%S is equal to %VARIABLE"/>
This condition will succeed if the value in %S (the subject) is equal to the value in %VARIABLE.

  <condition expression="%VARIABLE * 2" value="%VARIABLE2"/>
This condition will multiply the value in %VARIABLE by 2 and store it in %VARIABLE2

It's best practise to break complex expressions down into a series of steps using multiple conditions:
  <condition expression="%VARIABLE1 * 2" value="%VARIABLE2"/>
  <condition expression="%VARIABLE2 + 12" value="%O"/>
This condition multiplies the value in %VARIABLE1 by 2 then adds 12 to it (via an intermediate variable %VARIABLE2) and stores the result in %O (the object of the new relationship instance that will be created)

Three hard platform rules for expressions (all confirmed live — violations fail SILENTLY, the condition just never binds):

1. **No function call may take an expression argument.** `addDays(%DATE, 8 - dayOfWeek(%DATE))` never binds. Compute each piece in its own condition and pass plain variables: bind `dayOfWeek(%DATE)` into `%DOW`, compute `8 - %DOW` into `%ROLL`, then `addDays(%DATE,%ROLL)`. A single function call *inside a comparison* (`dayOfWeek(%DATE) is less than or equal to 5`) is fine.
2. **There is NO operator precedence, even with brackets.** Expressions evaluate strictly left to right; brackets group a subterm but do not restore precedence afterwards (`%B + (%B - 1) * 2` with B=5 gives 18, i.e. (5+4)*2). Order every multi-operator expression so left-to-right evaluation is correct — `(%HS - 1) * %I + %B` — and probe collapsed arithmetic on a tiny map if in doubt.

3. **A variable used in an expression must already be bound** by an earlier condition in the same rule (or be %S/%O, or be this condition's own `value` capture). A condition referencing an unbound variable — including a rel condition whose subject variable nothing binds — silently never fires.

#### 2.5.4 Using the results of expressions

Use the "value" attribute to store the result of an expression.

For example to express "%O = %X * 2" you would use:
  <condition expression="%X * 2" value="%O"/>

Importantly note that "=" is a test for equivalence and is not ever used to assign values to variables.
The following is NEVER valid and must not be used:
  <condition expression="%O = %X * 2" />

#### 2.5.5 Available Expressions

Expressions enable data comparison and transformation during rule processing. All functions return specific data types (Boolean, Number, String, Date).

## Comparison Functions

### Operators
Support symbol or natural language syntax (e.g., `=` or `equals`).

**Supported by data type:**
- **String**: `=`, `!=`, `isSubset`
- **Number**: `=`, `!=`, `>`, `>=`, `<`, `<=`, `isWithinRange`
- **Date**: `isWithinRange`
- **Boolean**: `=`, `!=`

### isWithinRange
**Syntax**: `isWithinRange(value, min, max)`  
**Output**: Boolean  
**Supports**: Numbers (including decimals, negatives), Dates  
**Behavior**: Inclusive range; min/max order irrelevant  
**Examples**:
- `isWithinRange(%AGE, 0, 17)` → checks age 0-17
- Checking the next 7 days must be built stepwise (hard rule 1 — no function-call arguments):
  ```xml
  <condition expression="today()" value="%TODAY"/>
  <condition expression="addDays(%TODAY, 7)" value="%WEEK_AHEAD"/>
  <condition expression="isWithinRange(%DATE, %TODAY, %WEEK_AHEAD)"/>
  ```

## String Functions

### includes
**Syntax**: `includes(string, substring)`  
**Output**: Boolean  
**Behavior**: Case-sensitive, whitespace-sensitive  
**Negation**: Append `= false`

### startsWith / endsWith
**Syntax**: `startsWith(string, prefix)` / `endsWith(string, suffix)`  
**Output**: Boolean  
**Behavior**: Case-sensitive, whitespace-sensitive

### regexCount
**Syntax**: `regexCount(value, '/pattern/flags')`  
**Output**: Number (count of matches)  
**Format**: Regex must be wrapped in `/pattern/flags` (JavaScript/ECMAScript)  
**Common flags**: `g` (global), `i` (case-insensitive)  
**Error codes** (negative numbers):
- `-1`: Unsafe pattern
- `-2`: Evaluation failed
- `-3`: Invalid syntax
- `-4`: Pattern >500 chars
- `-5`: Input >10,000 chars
- `-6`: Invalid format
- `-7`: Timeout

**Examples**:
- `regexCount(%TEXT, '/cat/i')` → case-insensitive count
- `regexCount(%TEXT, '/cat/gi') >= 1` → boolean check

### String Concatenation
**Operator**: `+`  
**Output**: String  
**Behavior**: Auto-converts dates (to timestamp), numbers, booleans to strings  
**Example**: `%FIRST + ' ' + %LAST` → `"John Smith"`

## Mathematical Functions

**Output**: Number  
**Operators**: `+`, `-`, `/`, `*`  
**Functions**:
- `round(X, Y)` → round to Y decimal places (default 0, max 15)
- `ceil(X)`, `floor(X)`, `abs(X)`
- `min(A,B,C,...)`, `max(A,B,C,...)`
- `mod(X,Y)` → modulus
- `pow(X,Y)` → X^Y
- `sqrt(X)`, `factorial(X)`
- `tan(X)`, `csc(X)`, `cot(X)`, `sec(X)`

**Note**: There is NO operator precedence and brackets do NOT restore it (see the expression rules above) — order operations for strict left-to-right evaluation. `round(X, 0) is equal to X` is the whole-number test.

## Date Functions

**Input**: Date-type concepts only  
**Format**: `YYYY-MM-DD`  
**Output**: Varies by function

### Current Date/Time
- `today()` → current date (midnight)
- `now()` → current date and time
- **Output**: Unix timestamp

### Date Indices
**Output**: Number
- `dayOfWeek(date)` → 1-7 (Monday=1, Sunday=7)
- `dayOfMonth(date)`, `dayOfYear(date)`
- `monthOfYear(date)` → 1-12
- `year(date)`

### Date Arithmetic
**Syntax**: `addDays(date, n)`, `subtractDays(date, n)` (also Weeks, Months, Years)  
**Output**: Date/timestamp  
**Behavior**: Accepts variables for both arguments

### Date Differences
**Syntax**: `secondsBetween(date1, date2)` (also Minutes, Hours, Days, Weeks, Months, Years)  
**Output**: Number (always positive)

### Date Comparisons
**Output**: Boolean
- `isBeforeDate(date1, date2)`
- `isSameDate(date1, date2)`
- `isAfterDate(date1, date2)`

Always compare dates with these functions (`isSameDate(%A,%B) is equal to false`), never with `is not equal to`. Numeric `>` comparison between two date variables also works (dates are timestamps underneath) — useful for deadline checks.

## List Functions

**Syntax**: `functionName(subject, 'relationship', object)` — always single-quote the relationship name.  
**Filtering**: Use `*` for "all"; variables or literals to constrain (multi-word literal strings work: `countRelationshipInstances(%S,'has signal','Structuring')`)  
**Common pattern**: `functionName(%SUBJECT, 'relationship', *)` → all objects for given subject

**Aggregation over an EMPTY set (confirmed live)**: `sumObjects` returns 0, but `minObjects`/`maxObjects` assert a fact with object NULL, which downstream comparisons treat like +infinity (`null >= 1.25` is TRUE). ALWAYS guard min/max/sum aggregation rules with `countRelationshipInstances(%S,'rel',*) is greater than or equal to 1`.

**Dedup semantics (confirmed live)**: inferred facts with STRING objects dedupe on (subject, rel, object) — counts over string-object derived rels are true distinct counts. Facts with NUMBER objects do NOT dedupe — every derivation counts (which is what makes `sumObjects` over per-item derived values exact). Run distinct-count logic over string-object rels; mirror numbers as named string instances where needed.

**Counting derived relationships works**: a count over a derived rel drives full backward-chaining of that rel at evaluation time. But a rule must never count its OWN target relationship (self-recursion risk) — enforce priority in a precedence ladder instead.

### countRelationshipInstances
**Output**: Number  
**Behavior**: Counts facts matching filter; object can be any type

### sumObjects
**Output**: Number  
**Requirement**: Object must be number type

### minObjects / maxObjects
**Output**: Number or Date  
**Requirement**: Object must be number or date  
**Behavior**: Returns lowest/highest value or earliest/latest date

### joinObjects
**Output**: String (comma-separated)  
**Behavior**: Concatenates all objects into single string

### isSubset
**Syntax**: `isSubset(subject1, 'rel1', *, subject2, 'rel2', *)`  
**Output**: Boolean  
**Behavior**: Checks if all objects from rel1 exist in objects from rel2

## Logical Operators

**Operators**: `and`, `or`  
**Output**: Boolean  
**Behavior**:
- `and` → all conditions must be true
- `or` → at least one condition must be true
- Use parentheses to control evaluation order

**Truth table**:
- `true AND true` → true
- `true AND false` → false
- `true OR false` → true
- `false OR false` → false

**Example**: `((%AGE < 25) or (%DRIVING_YEARS < 3)) and (%ACCIDENT_COUNT > 0)`

## Advanced Patterns

### Dynamic Regex Construction
Build regex pattern in one expression, use in another:
```
'/pattern_start' + %VARIABLE + 'pattern_end/flags'  → %REGEX
regexCount(%TEXT, %REGEX) >= 1
```
**Requirement**: Pattern must be built in separate expression before use in `regexCount`.

### Evidence Text (alt attributes)
Put an `alt` attribute on every expression condition so the evidence tree and the natural-language explain endpoint read like a domain expert's narrative (this is a standing requirement on all projects — enforced by `tools/lint_rblang.py`):

```xml
<condition expression="%PT * %TOL / 100" value="%MARGIN"
           alt="The order total {{%PT}} times {{%TOL}} percent gives a margin of {{%MARGIN}}"/>
```

- `{{%VAR}}` interpolates actual values into the narrative, including the condition's own value capture.
- `alt` is also valid at rule level (on the `<relinst>`) — it becomes the evidence headline.
- No double quotes or angle brackets inside alt text; keep it under 220 characters; balance the `{{ }}` braces.
- Skip alt on pure plumbing whose output IS the display: bare variable relays (`expression="%DATE" value="%O"`) and string concatenations into a value.
- Decompose arithmetic that fuses two meanings (a single ×1200 for annualise-then-percent) into honest steps, each with its own alt — the NL narrator garbles fused steps.

## Key Constraints
- Date functions require date-type concepts
- List functions require plural relationships for full functionality
- Case sensitivity applies to all string functions (`includes`, `startsWith`, `endsWith`) — use a case-insensitive regex (`/pattern/i`) wherever case must not matter
- Mathematical operations ALWAYS evaluate left-to-right; brackets group but do not restore precedence
- Regex patterns limited to 500 chars (split long anchored whitelists across multiple conditions); input strings to 10,000 chars; regexCount errors are NEGATIVE return values
- A literal `+` inside a regexCount pattern must be written `[+]`, never `\+` (the platform rejects the escaped form)
- Function calls must not take expression arguments (compute stepwise into variables first)


## 3. Best Practices and Rules

1. **Unique Names**: Ensure all relationship names are unique across the graph.

2. **Variable Usage**: When defining variables in conditions (using %VARIABLE)

3. **Type Consistency**: Maintain consistency in the types suggested by different conditions within a rule.

4. **Subject/Object in Rules**: For `<relinst>` tags in rules, you can omit `subject="%S"` or `object="%O"` as they are implied.

5. **Certainty Factors**: Use `cf` attribute in `<relinst>` to indicate the confidence level of a rule (0-100).

6. **Order of Definitions**: Define concepts before using them in relationships, and define relationships before creating relationship instances or rules.

7. **Circular References**: Where possible try to avoid circular references in rules. Use separate flags or concepts if necessary.

8. **Askable Relationships**: Use `askable="secondFormObject"` and provide a question format for relationships that are allowed to ask a user or system for this additional information. Do not define the relationship a second time, just include this when you first define the relationship.


## 4. Advanced Modeling Techniques

### 4.1 Hierarchical Relationships

Model hierarchies using same-concept relationships:

<rel name="is parent of" subject="Person" object="Person" askable="none"/>

Do NOT write self-recursive derived rules over such relationships (rules for a rel whose conditions consult the same rel) — termination is unproven. For bounded-depth traversal (e.g. ownership chains), encode one derived relationship per level (level 0 = direct, level 1 = via level-0 holders, and so on), deduplicating through a string-object mark between levels — see patterns.md section 11 and the sanctions example.

A flat group taxonomy is often better than a hierarchy: make groups ordinary instances of the same concept as leaves with a `belongs to group` relationship, add reflexive self-membership and an ALL sentinel by rule — see the document-examination example.

### 4.2 Many-to-Many Relationships

Use intermediate concepts to model many-to-many relationships:

<concept name="Enrollment" type="string"/>
<rel name="has student" subject="Enrollment" object="Student" askable="none"/>
<rel name="has course" subject="Enrollment" object="Course" askable="none"/>

Be sure to keep relationship names unique.

### 4.3 Temporal Reasoning

Include date concepts and use them in rules with the date comparison functions listed above:

<concept name="Date" type="date"/>
<rel name="has start date" subject="Event" object="Date" askable="none"/>
<rel name="has end date" subject="Event" object="Date" askable="none"/>

### 4.4 Uncertainty Handling

Use certainty factors (cf) in rules to handle uncertain knowledge:

<relinst type="is risky" object="true" cf="75">
  <!-- conditions; the subject %S is implied -->
</relinst>

### 4.5 Condition Weighting and the certainty formula

Optionally use weight in conditions to specify the relative importance of each condition.
If not included weight defaults to 100:

<relinst type="RelationshipName" object="ObjectValue" cf="ConfidenceFactor" name="Example rule 3">
  <condition rel="RelationshipA" subject="%S" object="%VARIABLE1" weight="80"/>
  <condition rel="RelationshipB" subject="%S" object="%VARIABLE3" weight="40"/>
  <condition rel="RelationshipC" subject="%S" object="%VARIABLE3"/>
  ...
</relinst>

The engine computes an inferred fact's certainty as (confirmed live):

    output cf = rule cf x SUM(weight_i x condition_cf_i / 100) / SUM(weight_i)

over ALL conditions — expression conditions count as weight-100 at certainty 100, a condition binding an inferred fact contributes that fact's cf, and unmet optional conditions contribute 0. Multiple rules asserting the same fact combine by MAX (not probabilistic OR).

Design consequences (see patterns.md section 5 and the certainty-mechanics-lab example):
- **weight="1" gates**: give count-gates and auxiliary bindings weight 1 so the output cf tracks the main (carrier) condition instead of being inflated or diluted by cf-100 gates.
- **weight="0"**: valid — the condition binds data or filters with zero effect on certainty.
- **minimum-rule-certainty="1"** (attribute on the relinst): lets a rule fire on very low-confidence upstream facts instead of being suppressed by the default firing threshold. Observed in production graphs.
- **behaviour="top-down-strict"** (attribute on the relinst): forces strict written-order condition evaluation. Observed in production graphs.

### 4.6 Condition Behaviour

Optionally use behaviour to specify if a condition is optional. Optional conditions do not have to be met for the rule to succeed, but will result in a lower certainty fact being inferred if not met (per the formula in 4.5).
If not included behaviour defaults to "mandatory":

<relinst type="RelationshipName" object="ObjectValue" cf="ConfidenceFactor" name="Example rule 4">
  <condition rel="RelationshipA" subject="%S" object="%VARIABLE1" behaviour="optional"/>
  <condition rel="RelationshipB" subject="%S" object="%VARIABLE3" behaviour="mandatory"/>
  <condition rel="RelationshipC" subject="%S" object="%VARIABLE3"/>
  ...
</relinst>

Notes (confirmed live):
- Optional conditions on askable relationships still generate questions.
- `behaviour="optional" weight="0"` binds enrichment/filter data with no certainty impact; two consecutive weight-0 optionals sharing a variable act as a skippable join (prefer-latest-revision pattern).
- **Optional-chain propagation**: any condition consuming a variable bound by an optional condition must itself be optional weight-0 — otherwise a skipped binder leaves the variable unbound and the mandatory consumer kills the rule.

### 4.7 Testing for missing facts

To determine if a fact is not known you must use the countRelationshipInstances() function in an expression. You cannot just test for null.
countRelationshipInstances() returns the number of relationship instances (facts) known for any given relationship, it allows the inclusion of variables and wildcards (*). If it returns 0 no facts are known for the relationship.

<!-- Create new fact %S-RelationshipName-ObjectValue if there are no known facts for %S-RelationshipA -->
<relinst type="Relationship Name" object="Object Value" cf="ConfidenceFactor" name="Example rule 5">
    <condition expression="countRelationshipInstances(%S,'RelationshipA',*) is equal to 0"/>
</relinst>

Count functions cannot traverse two hops: to test "no field of type X exists on this record" you must first materialise a projection relationship (record to type) with a simple rule, then count against the projection. See patterns.md section 2.

### 4.8 Comparing strings
When using an expression to compare a variable against a string value always enclose the string in single quotes

...
    <condition expression="%S is equal to 'Test Value'"/>
...


## 5. Extensibility

Design your graph to be easily extensible:

1. Use generic concepts where possible.
2. Create a modular structure with related concepts and rules grouped together.
3. Comment complex rules or structures for future reference.


## 6. Performance Considerations

1. Avoid overly complex rules with many conditions.
2. Use appropriate data types for concepts to enable efficient querying.
3. Consider the order of conditions in rules for optimal evaluation.


## 7. Complete Example Graph

Here's a small, complete example graph that demonstrates the key features of the XML knowledge modeling language. This graph represents a simplified library system:

<rbl:kb xmlns:rbl="http://rbl.io/schema/RBLang">
  <!-- Concepts -->
  <concept name="Book" type="string"/>
  <concept name="Author" type="string"/>
  <concept name="Genre" type="string"/>
  <concept name="User" type="string"/>
  <concept name="Date" type="date"/>
  <concept name="LoanStatus" type="string"/>
  <concept name="Rating" type="number"/>
  <concept name="returned" type="truth"/>
  <concept name="prolific" type="truth"/>
  <concept name="over due" type="truth"/>

  <!-- Relationships. Every rel carries an explicit askable attribute:
       data and derived rels are askable none; only genuinely
       human-answerable facts are askable. -->
  <rel name="has author" subject="Book" object="Author" askable="none"/>
  <rel name="has genre" subject="Book" object="Genre" plural="true" askable="none"/>
  <rel name="borrowed by" subject="Book" object="User" askable="none"/>
  <rel name="has borrow date" subject="Book" object="Date" askable="none"/>
  <rel name="has due date" subject="Book" object="Date" askable="none"/>
  <rel name="has loan status" subject="Book" object="LoanStatus" askable="none"/>
  <rel name="has rating" subject="Book" object="Rating" askable="none"/>
  <rel name="has book rating" subject="Author" object="Rating" plural="true" askable="none"/>
  <rel name="has average rating" subject="Author" object="Rating" askable="none"/>
  <rel name="is returned" subject="Book" object="returned" askable="none"/>
  <rel name="is prolific" subject="Author" object="prolific" askable="none"/>
  <rel name="recommended" subject="User" object="Book" askable="none"/>
  <rel name="enjoys" subject="User" object="Genre" plural="true" askable="secondFormObject" allowUnknown="true">
    <secondFormObject>Which genre of books does %S enjoy?</secondFormObject>
  </rel>
  <rel name="has over due book" subject="User" object="over due" askable="none"/>

  <!-- Concept Instances -->
  <concinst name="Fiction" type="Genre"/>
  <concinst name="Non-Fiction" type="Genre"/>
  <concinst name="Overdue" type="LoanStatus"/>
  <concinst name="On Time" type="LoanStatus"/>
  <concinst name="Returned" type="LoanStatus"/>
  <concinst name="The Great Gatsby" type="Book"/>
  <concinst name="F. Scott Fitzgerald" type="Author"/>

  <!-- Relationship Instances -->
  <relinst type="has genre" subject="The Great Gatsby" object="Fiction"/>
  <relinst type="has author" subject="The Great Gatsby" object="F. Scott Fitzgerald"/>

<!-- Rules -->
  <relinst type="has loan status" object="Overdue" cf="100" name="Determine if a book is overdue">
    <condition rel="has due date" subject="%S" object="%DUE_DATE"/>
    <condition expression="today()" value="%TODAY"/>
    <condition expression="isBeforeDate(%DUE_DATE,%TODAY)" alt="The due date {{%DUE_DATE}} is before today"/>
    <condition rel="is returned" subject="%S" object="%RETURNED"/>
    <condition expression="%RETURNED is not equal to true" alt="The book has not been returned"/>
  </relinst>

  <!-- Aggregating across an author's books needs a projection first:
       count functions cannot traverse two hops (book to author to rating).
       The projection rel is plural so every book contributes one value. -->
  <relinst type="has book rating" cf="100" name="Project each book rating onto its author">
    <condition rel="has author" subject="%BOOK" object="%S"/>
    <condition rel="has rating" subject="%BOOK" object="%O"/>
  </relinst>

  <relinst type="has average rating" cf="100" name="Calculate average rating for an author">
    <condition expression="countRelationshipInstances(%S,'has book rating',*) is greater than or equal to 1" alt="The author has at least one rated book"/>
    <condition expression="sumObjects(%S,'has book rating',*)" value="%TOTAL_RATING" alt="The ratings of the author's books sum to {{%TOTAL_RATING}}"/>
    <condition expression="countRelationshipInstances(%S,'has book rating',*)" value="%TOTAL_BOOKS" alt="The author has {{%TOTAL_BOOKS}} rated books"/>
    <condition expression="%TOTAL_RATING / %TOTAL_BOOKS" value="%O" alt="The average rating is {{%O}}"/>
  </relinst>

  <relinst type="is prolific" object="true" cf="100" name="Identify prolific authors (with more than 5 books)">
    <condition expression="countRelationshipInstances(*,'has author',%S) is greater than 5" alt="The author has written more than five books"/>
  </relinst>
  <relinst type="is prolific" object="false" cf="100" name="Identify non-prolific authors (five or fewer books)">
    <condition expression="countRelationshipInstances(*,'has author',%S) is less than or equal to 5" alt="The author has written five or fewer books"/>
  </relinst>
  
  <!-- Rule to recommend books (same genre, ideally highly rated).
       The rating binder and the rating check form an optional chain:
       both are optional so an UNRATED same-genre book still qualifies
       (at lower certainty); a mandatory binder would exclude it. -->
  <relinst type="recommended" cf="100" name="Recommend books (same genre, ideally highly rated)">
    <condition rel="enjoys" subject="%S" object="%GENRE"/>
    <condition rel="has genre" subject="%O" object="%GENRE"/>
    <condition rel="has rating" subject="%O" object="%RATING" behaviour="optional" weight="0"/>
    <condition expression="%RATING is greater than 4" weight="80" behaviour="optional" alt="The rating {{%RATING}} is above four"/>
  </relinst>
  
  <relinst type="has over due book" object="true" cf="100" name="Identify users with overdue books">
    <condition rel="borrowed by" subject="%BOOK" object="%S"/>
    <condition rel="is returned" subject="%BOOK" object="%RETURNED"/>
    <condition expression="%RETURNED is not equal to true" alt="The book has not been returned"/>
    <condition rel="has loan status" subject="%BOOK" object="Overdue"/>
  </relinst>
</rbl:kb>


By following these guidelines and referencing this example, you should be able to create comprehensive, logically sound, and effective XML knowledge graphs for any given subject matter.

Once you've produced your graph please check it against these validation points:

1. Always define concepts before using them in relationships or rules.
2. Ensure the only concept types used are string, number, date, or truth (for boolean values).
3. Ensure all relationship names are unique, multiple relationships with the same name are not allowed.
4. Ensure concept and relationship names are easy to read in natural language (English)
5. Concept instances of number and boolean types are not allowed. Make sure no instances of concepts of these types are created - instead number values or 'true'/'false' should be used directly where required.
6. Make sure concepts represent the best level of abstraction you can.  For example, do not create a concept called "Two", instead create a concept of type number that represented the reason for storing the value, then use the number value '2' where required.
7. Ensure that every concept used in relationships and rules is properly defined as a `<concept>` element.
8. Ensure concept instances are defined before being used in relationship instances.
9. Ensure relationships are defined before being used in rules or relationship instances.
10. When creating relationship instances or rules that reference specific values ensure these are defined as concept instances (`<concinst>`) of the appropriate concept type.
11. Do not use primitive types (like "string", "number", "truth", "true", "false" etc.) directly in relationships or rules. Instead, create and use specific concepts for these purposes.
12. Double-check that all relationships used in rules are properly defined in the `<rel>` section.
13. Ensure that the object type and subject type in relationships match the type of the concept it refers to.
14. When creating rules, verify that all conditions use properly defined relationships and concepts.
15. Make sure variable names are consistent within rules.
16. Ensure every defined concept is connected to the graph. Each <concept> should appear at least once in the subject or object of a <rel> definition. No concepts should be orphaned.
17. Make sure that rules will work for any data. Rules must not have any hard coded values from the data given, or any hard coded pre-calculated expected values.
18. Make absolutely sure conditions with expressions only use valid expressions from the list given, and no other key words at all.
19. Critically - queries are run on relationships.  Make sure there is a relationship that can be queried for the question given.
20. If examples were given check that the patterns in the examples have been adopted where relevant.
21. Every rel carries an explicit askable attribute; data/derived rels are askable="none"; askable rels carry allowUnknown="true" and a question form.
22. Relationship names inside list functions (countRelationshipInstances, sumObjects, minObjects, maxObjects, joinObjects) are single-quoted.
23. Every literal string object asserted by a data relinst has a matching concinst declaration.
24. Every expression condition carries alt text (except bare relays and string concatenations); alt text contains no double quotes or angle brackets and balanced double-brace interpolation.
25. No function call takes an expression argument; every multi-operator expression is ordered for left-to-right evaluation.
26. XML comments contain no double quotes, no angle brackets, and no double hyphens; text content escapes ampersands.
27. Aggregation rules (minObjects/maxObjects/sumObjects) are guarded by a count greater-than-or-equal-to-1 condition.

Run `python3 tools/lint_rblang.py <graph.xml>` — it checks the mechanical points deterministically (declarations and references, types, concinsts for literal objects, quoted rel names, explicit askable, alt-text rules, aggregation count-guards, orphan concepts, unbound variables, expression hazards, comment restrictions). The judgement points — abstraction level, naming quality, rule generality, queryability, pattern adoption — remain yours to verify by reading. Fix every ERROR and review every WARN before uploading.

Delivery rules:
1. Always work with, and deliver, the ENTIRE knowledge graph as a file — never fragments or diffs.
2. For a new graph, also provide a description of the graph created, including an overview of the logic and which relationship(s) to query to test it.
3. For an updated graph, explain what updates were made and why, professionally and without embellishment.
4. Deliver files per project_instructions.md (validated XML, Studio tests JSON, documentation) — do not paste raw XML into chat as the deliverable.