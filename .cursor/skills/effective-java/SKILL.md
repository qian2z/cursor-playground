---
name: effective-java
description: Reviews Java code specifically against the 90 items from Effective Java (Bloch, 3rd edition). Use for a deep idiomatic Java review focused on design quality, API design, and correctness.
---

# Effective Java Review Skill

This skill performs a focused review based on the principles from *Effective Java* by Joshua Bloch (3rd edition).

## When to Use

- When you need a dedicated Effective Java deep-dive beyond the general Java review.
- Invoked standalone with `/effective-java` or as part of the full review pipeline.
- Particularly useful for reviewing public APIs, library code, value objects, and complex domain models.

## Key Items to Check

### Creating and Destroying Objects (Items 1–9)

| Check | Item |
|-------|------|
| Static factory methods used where constructors would be confusing | Item 1 |
| Builder pattern used for 4+ params, especially with optionals | Item 2 |
| Singleton enforced via enum if needed | Item 3 |
| Utility classes have private constructor throwing AssertionError | Item 4 |
| Dependencies injected, not created inside class | Item 5 |
| No unnecessary object creation in hot paths (e.g., inside loops) | Item 6 |
| Obsolete references nulled out in custom collection implementations | Item 7 |
| No `finalize()` or `Cleaner` for resource management | Item 8 |
| All Closeable resources use `try-with-resources` | Item 9 |

### Methods Common to All Objects (Items 10–14)

| Check | Item |
|-------|------|
| `equals` satisfies: reflexive, symmetric, transitive, consistent, non-null | Item 10 |
| `hashCode` overridden alongside `equals`, consistent with it | Item 11 |
| `toString` overridden on value types and domain objects | Item 12 |
| `clone` avoided; copy constructors or static factories used instead | Item 13 |
| `Comparable` implemented for types with natural ordering | Item 14 |

### Classes and Interfaces (Items 15–25)

| Check | Item |
|-------|------|
| Accessibility minimized (private > package > protected > public) | Item 15 |
| No public mutable fields in non-enum classes | Item 16 |
| Mutability minimized; fields are `final` where possible | Item 17 |
| Composition preferred over inheritance | Item 18 |
| Inheritance designed and documented, or prohibited | Item 19 |
| Abstract classes replaced by interfaces + default methods | Item 20 |
| Interface design used for defining types only (not constants) | Item 22 |
| Tagged classes replaced by class hierarchies | Item 23 |
| Static member classes preferred over non-static where applicable | Item 24 |

### Generics (Items 26–33)

| Check | Item |
|-------|------|
| No raw types — all generic types parameterized | Item 26 |
| No unchecked casts; `@SuppressWarnings("unchecked")` scoped minimally | Item 27 |
| Arrays replaced by lists in generic contexts | Item 28 |
| Bounded wildcards applied (PECS: Producer Extends, Consumer Super) | Item 31 |
| Generic methods used over raw-type method overloads | Item 30 |

### Enums and Annotations (Items 34–41)

| Check | Item |
|-------|------|
| `int` constants replaced by enums | Item 34 |
| Instance fields/methods used on enums instead of switch on ordinal | Item 35 |
| `EnumSet` used instead of bit fields | Item 36 |
| `EnumMap` used instead of ordinal-indexed arrays | Item 37 |
| `@Override` present on every overriding method | Item 40 |
| Marker interfaces used instead of marker annotations when possible | Item 41 |

### Lambdas and Streams (Items 42–48)

| Check | Item |
|-------|------|
| Anonymous classes replaced by lambdas | Item 42 |
| Method references used when clearer than lambdas | Item 43 |
| Standard functional interfaces preferred over custom ones | Item 44 |
| Streams used appropriately; complex logic extracted to named methods | Item 45 |
| Streams not used where `break`/`continue`/`return` or checked exceptions are needed | Item 45 |
| `parallelStream()` not used without a demonstrated performance need | Item 48 |

### Methods (Items 49–56)

| Check | Item |
|-------|------|
| Parameters validated at entry; NPE/IAE/IOOBE thrown appropriately | Item 49 |
| Defensive copies made of mutable parameters | Item 50 |
| Overloading not confused with overriding; overloads are not confusing | Item 52 |
| Varargs used sparingly and correctly | Item 53 |
| Collections/arrays returned, never null | Item 54 |
| `Optional` returned for absent-value cases, not overused | Item 55 |

### General Programming (Items 57–67)

| Check | Item |
|-------|------|
| Scope of local variables minimized | Item 57 |
| For-each used over traditional for loops | Item 58 |
| Known library methods used instead of reimplemented logic | Item 59 |
| `float`/`double` avoided for exact values; `BigDecimal` or int/long used | Item 60 |
| Primitives preferred over boxed types | Item 61 |
| No string concatenation inside loops; `StringBuilder` used | Item 63 |
| Variable/method types declared as interfaces, not implementations | Item 64 |
| Reflection used only when genuinely necessary | Item 65 |
| Native methods avoided | Item 66 |
| Optimization not attempted without measurement | Item 67 |

### Exceptions (Items 69–77)

| Check | Item |
|-------|------|
| Exceptions used for exceptional conditions only | Item 69 |
| Checked exceptions used for recoverable cases | Item 70 |
| Unnecessary checked exceptions avoided | Item 71 |
| Standard exceptions reused (`IllegalArgumentException`, `IllegalStateException`, etc.) | Item 72 |
| Exceptions documented in Javadoc with `@throws` | Item 74 |
| Detail messages include failure-capture information | Item 75 |
| Failure atomicity maintained (object in valid state after exception) | Item 76 |
| Exceptions not ignored (catch blocks always handle or rethrow) | Item 77 |

### Concurrency (Items 78–84)

| Check | Item |
|-------|------|
| Shared mutable data synchronized properly | Item 78 |
| Excessive synchronization avoided | Item 79 |
| `ExecutorService` used instead of raw threads | Item 80 |
| `wait`/`notify` replaced by higher-level concurrency utilities | Item 81 |
| Thread safety documented | Item 82 |
| Lazy initialization uses correct idiom (`volatile` / holder class) | Item 83 |
| Thread scheduler not relied upon for correctness | Item 84 |

## Output Format

For each violation found:

```
[SEVERITY] <Item N> — <Item title>
File: <FileName>.java, Line: <N>
Issue: <what the code does wrong and the impact>
Fix: <concrete correction with code snippet>
Behaviour Impact: <explicit statement that the suggested change preserves or does not preserve original behaviour, and why. REQUIRED — a finding without this is incomplete.>
```

Group findings by Effective Java chapter. End with a count of violations per chapter and an overall quality rating:
- **Excellent** (0–2 violations)
- **Good** (3–6 violations)
- **Needs Work** (7–12 violations)
- **Major Rework Required** (13+ violations)

## Instructions

1. Read each changed `.java` file from the PR.
2. Systematically check each relevant item from the tables above.
3. Report every finding with severity, item number, file, and line.
4. Provide a concrete code fix for every `[MAJOR]` and above finding.
5. Summarize by chapter and give an overall rating.
