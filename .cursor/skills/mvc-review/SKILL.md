---
name: mvc-review
description: Reviews Java MVC code for correct layer separation, controller design, service transaction boundaries, DTO usage, repository patterns, and input validation. Use for PRs touching controllers, services, or repositories.
---

# MVC Architecture Review Skill

This skill reviews Java MVC code for correct architectural patterns, layer separation, and best practices.

## When to Use

- When the PR includes controllers, services, repositories, DTOs, or model/entity classes.
- Invoked standalone with `/mvc-review` or as part of the full Java review pipeline.
- Auto-triggered when files contain `Controller`, `Service`, `Repository`, `Entity`, `Dto` in their name or package.

## Review Checklist by Layer

### Controller Layer Review

- [ ] Class annotated with `@RestController` or `@Controller`.
- [ ] No business logic — all processing delegated to service methods immediately.
- [ ] No direct repository access — no `@Autowired` / `@Reference` to `Repository` or `DAO` types.
- [ ] Input DTOs annotated with `@Valid` / `@Validated`; constraints defined on DTO fields.
- [ ] Response uses a dedicated response DTO or `ResponseEntity<T>`, never a raw entity.
- [ ] HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) map correctly to operation semantics.
- [ ] Correct HTTP status codes returned for all outcomes (200, 201, 204, 400, 404, 409, 500).
- [ ] Exception handling delegated to a `@ControllerAdvice` — no try/catch in controller methods.
- [ ] Controller class is stateless (no mutable instance fields beyond injected dependencies).
- [ ] Path variables and request parameters properly typed and validated.
- [ ] Method names describe the action: `createOrder`, `getOrderById`, `deleteOrder`.

### Service Layer Review

- [ ] Service defined as an interface + implementation pair.
- [ ] No HTTP/request constructs (`HttpServletRequest`, `HttpSession`) in service code.
- [ ] Transaction boundaries declared with `@Transactional` on service methods (not class-wide unless justified).
- [ ] Query-only methods annotated with `@Transactional(readOnly = true)`.
- [ ] No unchecked exceptions swallowed — all exceptions are logged and rethrown or wrapped.
- [ ] All business invariant validations are inside the service, not in the controller or repository.
- [ ] Service does not return JPA entities directly to controllers — maps to DTOs before returning.
- [ ] No circular service dependencies.
- [ ] Complex multi-step operations are atomic within a transaction boundary.
- [ ] Service methods are testable in isolation with mocked repositories.

### Repository / DAO Layer Review

- [ ] Repository contains only data access code — no business logic.
- [ ] Queries are parameterized (no string concatenation in JPQL/SQL).
- [ ] All list/search queries support pagination (no unbounded results).
- [ ] Repository returns `Optional<Entity>` for single-result lookups.
- [ ] Named queries or Spring Data method naming used over inline query strings.
- [ ] Repository does not call services or other repositories (no upward calls).

### Model / Entity Layer Review

- [ ] Entity identity is based on `@Id` field only for `equals`/`hashCode`.
- [ ] Associations use lazy loading unless proven otherwise.
- [ ] Bidirectional associations maintain both sides consistently.
- [ ] No service injection or repository calls inside entity methods.
- [ ] Entities do not implement `Serializable` unless required for specific purposes (with explicit `serialVersionUID`).
- [ ] Entities are not exposed directly at the API layer.

### DTO Review

- [ ] DTOs have no business logic.
- [ ] DTOs are immutable where possible (all-args constructor, no setters, final fields — or Java records).
- [ ] DTOs are named clearly with layer context: `CreateUserRequestDto`, `UserResponseDto`.
- [ ] Mapping between entities and DTOs is done in the service layer or via a dedicated mapper.
- [ ] No `null` response from DTO-returning methods — use empty DTOs or `Optional`.
- [ ] Request DTOs have Bean Validation annotations on all constrained fields.

### Dependency Injection Review

- [ ] Constructor injection used for all mandatory dependencies — not field injection.
- [ ] No `@Autowired` on fields.
- [ ] All injected dependencies are interfaces, not concrete classes.
- [ ] `@Primary` or qualifiers (`@Qualifier`) used only when necessary and documented.

### Configuration Review

- [ ] No hardcoded environment-specific values (URLs, ports, credentials) in code.
- [ ] All environment configuration read from externalized config (properties, environment variables, ConfigAdmin).
- [ ] Sensitive config values not logged or included in `toString` output.

## Output Format

Group findings by layer:

```
### Controller Layer — <ControllerName>.java
[SEVERITY] Line <N>: <issue title>
Problem: <description>
Fix: <improvement>

### Service Layer — <ServiceName>.java
...
```

End with:
```
## MVC Compliance Summary

| Layer       | Status  | Issues |
|-------------|---------|--------|
| Controller  | ✅/⚠️/❌ | <n>    |
| Service     | ✅/⚠️/❌ | <n>    |
| Repository  | ✅/⚠️/❌ | <n>    |
| Model/Entity| ✅/⚠️/❌ | <n>    |
| DTOs        | ✅/⚠️/❌ | <n>    |
| DI          | ✅/⚠️/❌ | <n>    |

Overall MVC Compliance: PASS / FAIL
```

## Instructions

1. Classify each changed file into its layer based on annotations, package, and class name.
2. Apply the checklist for each layer.
3. Report findings with correct severity and format.
4. For files spanning multiple layers (e.g., an aggregate service that also acts as a controller — flag as architectural issue and review both).
5. Output the compliance summary.
