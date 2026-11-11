# Integration tests

Run from the project root with the existing virtual environment activated:

```powershell
python -m pytest testing/integration -v
```

To include the existing unit tests:

```powershell
python -m pytest testing -v
```

The seven planned test functions cover 11 cases after parametrization:

| Test | File | Checks |
| --- | --- | --- |
| `test_login_and_logout_flow` | `test_auth.py` | Real credentials and JWT, 303 redirects, stored cookie, authenticated access, cookie deletion, and denial after logout. |
| `test_profile_update_integration` | `test_profile.py` | Form strings pass through validation, all academic fields are committed, and the profile displays the update. |
| `test_progress_view_access` | `test_academic.py` | Authenticated HTML response and progress context calculated from the student's own persisted history. |
| `test_semester_plan_submission` | `test_academic.py` | Form submission persists the plan, selected advisor, date, and ordered course items, then redirects. |
| `test_semester_plan_cancellation` | `test_academic.py` | A pending request becomes cancelled without losing its course items, then redirects. |
| `test_admin_role_authorization` | `test_admin.py` | Both admin pages render for admins; students see Unauthorized with no protected context or student request data (four cases). |
| `test_admin_plan_review_action` | `test_admin.py` | Approval and rejection each commit the decision, trimmed feedback, and reviewing advisor, then redirect (two cases). |

Each test uses a fresh in-memory SQLite database with foreign keys enabled.
Fixtures temporarily replace `app.database.engine` in memory, which also directs
the real application startup and schema recovery to the disposable database.
The original engine is restored afterward. No application file, configuration
file, or existing database is changed. Routes, authentication dependencies,
services, repositories, models, and templates all run without mocks. Sessions
opened after each write check committed database state.

The HTTPS test client handles Secure cookies even if the existing settings use
production mode. Redirect following is disabled so the tests can inspect each
303 response. Run from the project root because the app uses relative template
and static paths. Existing runtime dependencies and settings are still needed.

Two details reflect the existing implementation:

- `advisor_id` is the form field name, but its value is the advisor's username.
- Pending requests have status `submitted`.

The existing unauthorized exception handler renders `401.html` with HTTP 200.
As requested, denial tests check that template and the absence of protected
data; they do not require an HTTP 401/403 response. This records the current
behavior without changing application code or asserting that HTTP 200 is the
correct denial status.

These are application integration tests against SQLite. They do not validate
PostgreSQL-specific behavior or browser-side JavaScript. Test execution is left
to the student under the repository's verification guidance.
