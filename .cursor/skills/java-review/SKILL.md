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

## Review Checklist

Work through each category below for every changed `.java` file in the PR diff.

### 1. Architecture & Layer Boundaries
- [ ] Does the class belong to the correct MVC layer (controller/service/repository/model)?
- [ ] Are layer boundaries respected (no repository calls from controllers, no HTTP in services)?
- [ ] Are DTOs used at controller boundaries (no raw entities exposed)?
- [ ] Is the dependency direction correct (Controller → Service → Repository)?

### 2. Effective Java Compliance
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

### 3. SonarQube Rules
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

### 5. MVC Layer Rules
- [ ] Controller contains no business logic.
- [ ] Service layer owns all transactions (`@Transactional` on service, not controller/repository).
- [ ] Request DTOs use Bean Validation annotations.
- [ ] Consistent HTTP response codes.
- [ ] No field injection (`@Autowired` on fields) — constructor injection only.

### 6. Test Quality
- [ ] New logic has corresponding unit tests.
- [ ] Tests cover happy path, boundary conditions, and failure paths.
- [ ] Mocks/stubs are used correctly for external dependencies.
- [ ] Test method names describe the scenario: `shouldReturnEmptyWhenUserNotFound`.
- [ ] No real I/O, network calls, or `Thread.sleep` in unit tests.

### 7. Performance
- [ ] No N+1 query patterns (repository calls inside loops).
- [ ] Expensive object creation is not repeated unnecessarily in loops.
- [ ] Unbounded queries include pagination.
- [ ] No blocking calls on threads not designed for blocking I/O.

### 8. Security
- [ ] No secrets or credentials in source.
- [ ] All external input is validated before use.
- [ ] No XML parsers without secure processing enabled.
- [ ] No `Math.random()` for security-sensitive operations.

## Output Format

For each finding, output:

```
[SEVERITY] <FileName>.java:<line> — <Short title>

Problem: <description of the issue and its impact>

Current:
  <code snippet>

Suggested:
  <improved code>

Reference: <rule or item>
```

After all findings, output the Review Summary table as defined in the `pr-review-process` rule.

## Instructions

1. Read each changed file from the PR diff provided.
2. Work through the checklist above systematically.
3. Log every finding with the correct severity and format.
4. If a file is auto-generated (contains `@Generated` annotation or path includes `generated-sources`), skip detailed review and note it as `[INFO]`.
5. After reviewing all files, compile and output the Review Summary.
6. State a final recommendation: **APPROVE**, **REQUEST CHANGES**, or **COMMENT**.
