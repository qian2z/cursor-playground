---
name: osgi-review
description: Reviews Java OSGi component code for correct use of Declarative Services annotations, service lifecycle, bundle structure, and OSGi configuration patterns. Use for any PR touching OSGi service components.
---

# OSGi Component Review Skill

This skill performs a focused review of OSGi Declarative Services (DS) component code.

## When to Use

- When the PR includes any class annotated with `@Component`, `@Reference`, `@Activate`, or similar DS annotations.
- Invoked standalone with `/osgi-review` or as part of the full Java review pipeline.
- Triggered automatically when reviewing files in packages containing `service`, `component`, or `osgi` in the path.

## Review Checklist

### @Component Configuration

- [ ] `@Component` is from `org.osgi.service.component.annotations` (not `org.apache.felix` unless intentional).
- [ ] `service = { Interface.class }` is explicitly set — no ambiguous auto-detection.
- [ ] `immediate` is set to `true` only with justification comment. Default (lazy) is preferred.
- [ ] `name` is explicitly set for well-known components to avoid rename issues.
- [ ] `configurationPid` is set when the component reads OSGi configuration (ConfigAdmin).
- [ ] `configurationPolicy` is set correctly:
  - `OPTIONAL` (default): component activates even without configuration.
  - `REQUIRE`: component only activates when configuration is present.
  - `IGNORE`: component never uses configuration.

### @Activate / @Deactivate / @Modified

- [ ] `@Activate` method exists and is non-blocking (no I/O, no sleeps, no blocking calls).
- [ ] `@Deactivate` method exists and releases all resources (threads, connections, files, listeners).
- [ ] `@Modified` is present if the component supports runtime reconfiguration without restart.
- [ ] Activate/deactivate methods are package-private or protected (not public — public exposes them to callers).
- [ ] Typed config DTO `@interface` is used as the parameter; not raw `Map` or `Dictionary`.
- [ ] Config DTO defaults are defined in the annotation attributes and are sensible.

### @Reference Service Dependencies

- [ ] All external services are injected via `@Reference`, never via `BundleContext.getService()`.
- [ ] Cardinality is correct:
  - `MANDATORY` (default): component won't start without the service.
  - `OPTIONAL`: service may or may not be present; null-checked before use.
  - `MULTIPLE` / `AT_LEAST_ONE`: multiple instances accepted; stored in a `List` or `CopyOnWriteArrayList`.
- [ ] `policy = ReferencePolicy.DYNAMIC` is used only when service changes must be handled at runtime without restart; otherwise use `STATIC`.
- [ ] Dynamic references use either:
  - A `volatile` field, or
  - Explicit `bind`/`unbind` annotated methods.
- [ ] `ServiceReference` objects are never stored beyond the scope of a single method call.
- [ ] For optional references, null is checked before every use.
- [ ] `target` filter is set on `@Reference` when filtering by service properties is necessary.

### Bundle Hygiene

- [ ] `bnd.bnd` or `pom.xml` `<Export-Package>` lists only API packages, never `*.impl` or `*.internal`.
- [ ] `Import-Package` uses version ranges (e.g., `[1.0,2.0)`) rather than exact versions.
- [ ] No `Require-Bundle` in manifests — prefer `Import-Package`.
- [ ] No `Class.forName()` used to load classes from another bundle.
- [ ] No static `BundleContext` references cached globally.

### Lifecycle & Thread Safety

- [ ] Shared mutable state is protected: `volatile`, `synchronized`, or `AtomicReference`.
- [ ] No raw threads created inside components — use an `ExecutorService` from `@Reference` or `ScheduledExecutorService`.
- [ ] Background tasks started in `@Activate` are cancelled/awaited in `@Deactivate`.
- [ ] No `Thread.sleep` or blocking calls in `@Activate` or `@Deactivate`.

### Logging

- [ ] SLF4J or OSGi `LogService` is used, not `System.out` / `System.err`.
- [ ] Logger is obtained via `LoggerFactory.getLogger(MyComponent.class)` or via `@Reference`.
- [ ] Log levels are appropriate: DEBUG for trace/diagnostic, INFO for significant lifecycle events, WARN for recoverable anomalies, ERROR for failures.

### Configuration Security

- [ ] No default values for passwords, tokens, or secrets in config DTO attributes.
- [ ] Sensitive config properties are documented in Javadoc as required external configuration.

### Testing

- [ ] Component can be unit-tested by instantiating it directly and calling `activate(mockConfig)`.
- [ ] Integration tests exist using PAX Exam, Bnd Testing, or equivalent framework for lifecycle and injection verification.

## Output Format

```
### <FileName>.java — OSGi Component Review

[SEVERITY] <Issue title>
Line: <N>
Problem: <description>
Fix: <corrected approach or code snippet>
Reference: OSGi DS Spec / component annotation field
```

Group findings by component annotation category. End with:
- Total issues per category.
- Overall OSGi compliance: **Compliant** / **Minor Issues** / **Non-Compliant** (blockers present).

## Instructions

1. Identify all classes annotated with `@Component` in the changed files.
2. For each component, work through the entire checklist above.
3. Report every issue with the format above.
4. For non-component Java files in the PR, skip this review (delegate to `java-review` skill).
5. Output the compliance summary at the end.
