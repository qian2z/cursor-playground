---
name: sonarqube-java
description: Analyzes Java code specifically against SonarQube rule categories — bugs, vulnerabilities, code smells, and security hotspots. Use when you need a focused SonarQube-style static analysis pass on Java files.
---

# SonarQube Java Analysis Skill

This skill performs a targeted static analysis of Java code using SonarQube's Java rule set, organized by issue type.

## When to Use

- When you need a focused SonarQube-style review on specific files.
- Invoked as part of the full `java-review` skill or standalone with `/sonarqube-java`.
- Use when the team has a SonarQube quality gate and you need to predict gate pass/fail.

## Analysis Categories

### BUGS (Critical/Major — must fix)

Scan for:
- **Null dereferences** (squid:S2259): Dereference without null guard, `Map.get()` without `getOrDefault` or null check.
- **Resource leaks** (squid:S2095): Any `Closeable` not in a `try-with-resources` or without explicit close.
- **Equals/hashCode** (squid:S1206): `equals` overridden without `hashCode`, or vice versa.
- **Wait/notify** (squid:S2273): `wait()`/`notify()` called outside `synchronized` block.
- **Infinite loops** (squid:S2189): Loops with no reachable exit.
- **Empty loop bodies** (squid:S1116): Lone `;` on a loop line.
- **Operator precedence** (squid:S864): Mixing bitwise/logical operators without parentheses.

### VULNERABILITIES (Security — must fix)

Scan for:
- **SQL injection** (squid:S2077): String concatenation in SQL queries.
- **Command injection** (squid:S4721): User input passed to `Runtime.exec` / `ProcessBuilder`.
- **XXE** (squid:S2755): XML parsers without `XMLConstants.FEATURE_SECURE_PROCESSING`.
- **Hardcoded credentials** (squid:S2068): Strings resembling passwords, tokens, or keys.
- **Weak crypto** (squid:S2245, S4432, S5542): `Math.random()`, MD5/SHA-1 for security, DES/RC4 ciphers.
- **Path traversal** (squid:S2083): File paths from user input without canonicalization and boundary check.
- **Insecure deserialization** (squid:S5135): Object deserialization without class whitelist.

### CODE SMELLS (Major/Minor — should fix)

Scan for:
- **Cognitive complexity** (squid:S3776): Method cognitive complexity > 15.
- **Cyclomatic complexity** (squid:S1541): Method complexity > 10.
- **Too many parameters** (squid:S107): Methods with > 7 parameters.
- **Dead code** (squid:S1172, S1144, S1481): Unused parameters, private methods, or variables.
- **Duplicate string literals** (squid:S1192): String literal repeated > 3 times.
- **Empty catch** (squid:S108, S1166): Catch block with no handling or swallowed exception.
- **Catching Throwable/Error/Exception** (squid:S2221): Overly broad catch.
- **Return in finally** (squid:S1143): `return` or `throw` inside `finally` block.
- **String `==` comparison** (squid:S4973): Strings compared with `==` instead of `.equals()`.
- **size() == 0** (squid:S1155): Should be `.isEmpty()`.
- **Deprecated API** (squid:S1133): Use of deprecated methods or classes.
- **Unnecessary modifiers** (squid:S2333): `public abstract` on interface method, etc.
- **Magic numbers** (squid:S109): Unexplained numeric literals (not -1, 0, 1, 2).
- **Primitive boxing** (squid:S5411): Auto-boxing of primitives where primitive suffices.

### SECURITY HOTSPOTS (Review required)

Flag for human review:
- Logging calls containing variables that may hold sensitive data.
- Reflection or dynamic class loading from external input.
- Any cryptographic operations — confirm algorithm strength.
- HTTP cookie creation — confirm `HttpOnly` and `Secure` flags.
- Random number generation — confirm `SecureRandom` for security use.

## Output Format

Group findings by file, then by category:

```
### <FileName>.java

#### Bugs
- [BLOCKER] Line <N> (squid:S2095): Resource leak — FileInputStream opened but never closed.

#### Vulnerabilities
- [BLOCKER] Line <N> (squid:S2077): SQL injection — user input concatenated into query string.

#### Code Smells
- [MAJOR] Line <N> (squid:S3776): Cognitive complexity of method 'processOrder' is 22 (threshold: 15).
- [MINOR] Line <N> (squid:S1155): Replace 'list.size() == 0' with 'list.isEmpty()'.

#### Security Hotspots
- [INFO] Line <N>: Random number generated — confirm SecureRandom is used for security-sensitive context.
```

End with a summary count per category and a predicted SonarQube quality gate result (PASS / FAIL).

## Instructions

1. Receive the list of changed `.java` files from the PR diff.
2. For each file, apply every check listed above.
3. Report each finding with line number, squid rule ID, severity, and a brief explanation.
4. At the end, output:
   - Total counts per category.
   - Predicted SonarQube quality gate: PASS (no blockers/criticals) or FAIL (any blockers or criticals found).
