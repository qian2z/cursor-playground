---
name: java-review
description: Performs a comprehensive Java code review on provided source files or diffs. Applies Effective Java principles, SonarQube rules, OSGi service patterns, and MVC architecture checks. Use after fetching PR context with the bitbucket-pr skill.
---

# Java Code Review Skill

This skill conducts a thorough, multi-dimensional Java code review and produces a structured review report.

## When to Use

- After running the `bitbucket-pr` skill to fetch PR context.
- When asked to "review this Java code" or "check for issues in these files".
- Invoked automatically by the `java-code-reviewer` subagent.

## Core Review Principles

> **LARGE INPUT ASSUMPTION — MANDATORY**
> Treat every collection, stream, query result, file, or method parameter as if it could contain millions of entries.
> Never assume inputs are small. Every loop, sort, filter, or in-memory operation must be evaluated for its behaviour under extreme load.
> If a method would degrade badly at scale, flag it regardless of current usage context.

> **BEHAVIOUR PRESERVATION — MANDATORY**
> Every suggestion provided MUST explicitly guarantee that the proposed change does not alter the observable behaviour or business logic of the code.
> State clearly: "This change preserves the original behaviour because …".
> If a refactoring risk cannot be fully assessed, label the finding `[CAUTION]` and explain why.

> **MODERN JAVA SYNTAX — MANDATORY**
> Prefer Java 17+ syntax in all suggestions. Use the most modern stable feature available up to Java 25+.
> Key features to actively prefer:
> - Records (`record`) for immutable data carriers (Java 14+/16 stable)
> - Sealed classes/interfaces (`sealed`, `permits`) for restricted hierarchies (Java 17)
> - Pattern matching for `instanceof` (`if (obj instanceof Foo f)`) (Java 16)
> - Switch expressions with arrow syntax and `yield` (Java 14+)
> - Pattern matching in `switch` (Java 21)
> - Text blocks (`"""..."""`) for multiline strings (Java 15)
> - `var` for local type inference where it improves readability (Java 10)
> - Virtual threads (`Thread.ofVirtual()`, structured concurrency) (Java 21+)
> - Sequenced collections (`SequencedCollection`, `getFirst()`, `getLast()`) (Java 21)
> - String templates / `StringTemplate` (Java 21+ preview → stable in 25)
> - Unnamed classes and instance main methods (Java 21+ preview)
> Never suggest pre-17 idioms when a modern equivalent exists.

---

## Review Checklist

Work through each category below for every changed `.java` file in the PR diff.

### 1. Effective Java Compliance
- [ ] Are constructors with many parameters replaced by Builder pattern (Item 2)?
- [ ] Is immutability applied where possible — `final` fields, no unnecessary setters (Item 17)?
- [ ] Does the class use composition over inheritance (Item 18)?
- [ ] Are `equals` and `hashCode` implemented together and correctly (Items 10–11)?
- [ ] Does the class return `Optional` instead of `null` for optional results (Item 55)?
- [ ] Are empty collections returned instead of `null` from collection-returning methods (Item 54)?
- [ ] Are resources managed with `try-with-resources` (Item 9)?
- [ ] Are parameters validated at entry points with `Objects.requireNonNull` or `Preconditions` (Item 49)?
- [ ] Are magic numbers extracted to named constants?
- [ ] Are interfaces used as variable types rather than concrete classes (Item 64)?
- [ ] Can any data-carrying class be replaced with a `record` (Java 16+)?
- [ ] Can any multi-branch `instanceof` chain be replaced with sealed types + pattern-matching `switch`?

### 2. SonarQube Rules
- [ ] No null dereferences without checks (S2259).
- [ ] No resource leaks — all `Closeable` types use try-with-resources (S2095).
- [ ] No empty catch blocks (S108).
- [ ] Cognitive complexity ≤ 15 per method (S3776).
- [ ] No string comparison with `==` (S4973).
- [ ] No hardcoded credentials or secrets (S2068).
- [ ] No SQL concatenation — parameterized queries only (S2077).
- [ ] No deprecated API usage (S1133).
- [ ] No dead code — unused variables, parameters, or methods (S1172, S1144).
- [ ] `collection.isEmpty()` used instead of `.size() == 0` (S1155).
- [ ] `hashCode` overridden alongside `equals` (S1206).

### 3. Logic Structure & Algorithmic Efficiency
Review every method for structural soundness and algorithmic complexity. Remember: **inputs are assumed to be huge**.

- [ ] What is the time complexity (Big-O) of each method? Is it acceptable for large inputs?
- [ ] Are there nested loops (`O(n²)` or worse) that could be flattened or replaced with a Map-based lookup (`O(n)`)?
- [ ] Are there repeated iterations over the same collection that could be merged into a single pass?
- [ ] Are streams chained efficiently, or do intermediate operations cause unnecessary passes / boxing?
- [ ] Is `Stream.parallel()` used safely and appropriately, or would it cause thread contention?
- [ ] Are `List.contains()` or `Map.get()` calls inside loops that should use a `Set`/`Map` built upfront?
- [ ] Do any sorting operations sort the entire data set when only top-N items are needed (use min/max heap or `Comparator.naturalOrder()` with `limit`)?
- [ ] Are recursive methods at risk of `StackOverflowError` on large inputs? Can they be made iterative?
- [ ] Are there conditional branches that could be short-circuited earlier to avoid redundant computation?
- [ ] Is early-exit logic (`return`, `break`, `continue`) used to avoid processing beyond what is needed?
- [ ] Are objects or expensive resources created inside loops that could be hoisted outside?
- [ ] Are `String` concatenations inside loops replaced by `StringBuilder` or stream `joining`?
- [ ] Are batch/bulk operations preferred over row-by-row processing (e.g., `saveAll()` vs `save()` in a loop)?
- [ ] Does the logic correctly handle edge cases at scale: empty input, single element, `Integer.MAX_VALUE` size?

### 4. OSGi Service Compliance
- [ ] `@Component` annotation present and correctly configured.
- [ ] `service = { Interface.class }` explicitly declared.
- [ ] `@Reference` used for all service dependencies (no manual `BundleContext.getService()` calls).
- [ ] `@Activate` / `@Deactivate` methods correctly defined and resource-safe.
- [ ] Dynamic references use `volatile` fields or bind/unbind methods.
- [ ] No raw config dictionaries — typed config DTOs used.
- [ ] No `BundleActivator` unless absolutely necessary.
- [ ] No exported `*.internal` or `*.impl` packages.
- [ ] Thread safety maintained across lifecycle callbacks.

### 5. Test Quality
- [ ] New logic has corresponding unit tests.
- [ ] Tests cover happy path, boundary conditions, and failure paths.
- [ ] Tests include large/empty input scenarios to validate performance assumptions.
- [ ] Mocks/stubs are used correctly for external dependencies.
- [ ] Test method names describe the scenario: `shouldReturnEmptyWhenUserNotFound`.
- [ ] No real I/O, network calls, or `Thread.sleep` in unit tests.

### 6. Performance
- [ ] No N+1 query patterns (repository calls inside loops).
- [ ] Expensive object creation is not repeated unnecessarily in loops.
- [ ] Unbounded queries include pagination — **never load all rows into memory**.
- [ ] No blocking calls on threads not designed for blocking I/O.
- [ ] Collections are initialised with an appropriate initial capacity when size is known.
- [ ] `HashMap`/`HashSet` preferred over `TreeMap`/`TreeSet` unless ordering is required.
- [ ] `ConcurrentHashMap` or equivalent used for shared mutable state accessed by multiple threads.
- [ ] Large object graphs are not retained longer than necessary (GC pressure).

### 7. Security
- [ ] No secrets or credentials in source.
- [ ] All external input is validated before use.
- [ ] No XML parsers without secure processing enabled.
- [ ] No `Math.random()` for security-sensitive operations.

---

## Output Format

For each finding, output:

```
[SEVERITY] <FileName>.java:<line> — <Short title>

Problem: <description of the issue and its impact — include worst-case impact at large scale where relevant>

Current:
  <code snippet>

Suggested:
  <improved code using Java 17–25+ syntax where applicable>

Behaviour Impact: <explicit statement that the suggested change preserves or does not preserve original behaviour, and why>

Reference: <rule, Effective Java item, or Big-O analysis>
```

Severity levels: `[BLOCKER]` `[CRITICAL]` `[MAJOR]` `[MINOR]` `[INFO]`

After all findings, output the Review Summary table as defined in the `pr-review-process` rule.

---

## Instructions

1. Read each changed file from the PR diff provided.
2. **Assume all inputs (collections, streams, query results, strings, files) are huge — millions of entries.** Evaluate every operation under that assumption.
3. Work through the checklist above systematically, section by section.
4. For every logic or performance finding, include a Big-O analysis of the current code and the suggested improvement.
5. Prefer Java 17–25+ syntax in all suggestions. Explicitly call out when a modern language feature (record, sealed class, pattern switch, virtual thread, etc.) can simplify or improve the code.
6. **Every suggestion must include a `Behaviour Impact` statement** confirming that the proposed change does not alter observable behaviour or business logic. If there is any risk of behaviour change, label the finding `[CAUTION]` and describe the risk precisely.
7. Log every finding with the correct severity and format.
8. If a file is auto-generated (contains `@Generated` annotation or path includes `generated-sources`), skip detailed review and note it as `[INFO]`.
9. After reviewing all files, compile and output the Review Summary.
10. State a final recommendation: **APPROVE**, **REQUEST CHANGES**, or **COMMENT**.
