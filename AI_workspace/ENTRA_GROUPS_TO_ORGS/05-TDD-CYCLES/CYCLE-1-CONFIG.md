# Cycle 1: Configuration Flag Recognition

## Goal

The system should recognize the `entra_groups_also_create_orgs` configuration flag.

---

## 1.1 RED: Write Failing Tests

Add these tests to your test file:

```python
# ============================================================================
# CYCLE 1: Configuration Flag Recognition
# ============================================================================

class TestConfigurationFlag:
    """Tests for entra_groups_also_create_orgs configuration flag."""

    def test_flag_exists_in_litellm_module(self):
        """
        GIVEN: The litellm module
        WHEN: Checking for entra_groups_also_create_orgs attribute
        THEN: The attribute should exist and default to False
        """
        assert hasattr(litellm, 'entra_groups_also_create_orgs'), \
            "litellm module should have 'entra_groups_also_create_orgs' attribute"
        assert litellm.entra_groups_also_create_orgs is False, \
            "Default value should be False"

    def test_flag_can_be_set_to_true(self):
        """
        GIVEN: The litellm module
        WHEN: Setting entra_groups_also_create_orgs to True
        THEN: The value should be True
        """
        litellm.entra_groups_also_create_orgs = True
        assert litellm.entra_groups_also_create_orgs is True
```

### Run Test (Should FAIL)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestConfigurationFlag -v
```

Expected output:
```
FAILED test_ui_sso_entra_orgs.py::TestConfigurationFlag::test_flag_exists_in_litellm_module - AttributeError: module 'litellm' has no attribute 'entra_groups_also_create_orgs'
```

---

## 1.2 GREEN: Implement Configuration Flag

**File:** `litellm/__init__.py`

Find the section where `default_team_params` is defined (around line 377) and add the new flag:

```python
default_team_params: Optional[Union[DefaultTeamSSOParams, Dict]] = None
entra_groups_also_create_orgs: bool = False  # NEW
```

### Run Test (Should PASS)

```bash
poetry run pytest tests/test_litellm/proxy/management_endpoints/test_ui_sso_entra_orgs.py::TestConfigurationFlag -v
```

Expected output:
```
PASSED test_ui_sso_entra_orgs.py::TestConfigurationFlag::test_flag_exists_in_litellm_module
PASSED test_ui_sso_entra_orgs.py::TestConfigurationFlag::test_flag_can_be_set_to_true
```

---

## 1.3 REFACTOR

No refactoring needed for this simple change. The flag is properly initialized at module level.

---

## 1.4 Configuration Loading Integration

Understanding how the flag is loaded from different sources is essential for production use.

### How the Flag Gets Loaded

The proxy server's config loader (`proxy_server.py:2160-2421`) automatically handles `litellm_settings`:

```python
# From proxy_server.py (simplified)
litellm_settings = config.get("litellm_settings", {})
for key, value in litellm_settings.items():
    setattr(litellm, key, value)  # Sets litellm.entra_groups_also_create_orgs = True
```

### Configuration Methods

**1. YAML Configuration (Recommended):**
```yaml
litellm_settings:
  entra_groups_also_create_orgs: true
```
The loader reads this and calls `setattr(litellm, "entra_groups_also_create_orgs", True)`

**2. Environment Variable:**
```bash
export ENTRA_GROUPS_ALSO_CREATE_ORGS=true
```
Environment variables are mapped to `litellm_settings` keys during config loading.

**3. Runtime Assignment:**
```python
import litellm
litellm.entra_groups_also_create_orgs = True
```
Direct assignment works because the attribute exists at module level.

### No Additional Config Code Required

Because we're adding the flag to `litellm/__init__.py`, the **existing** config loader will automatically recognize and set it. The `setattr(litellm, key, value)` mechanism at `proxy_server.py:2421` handles this.

### Verification Test (Optional)

To verify the setattr mechanism works as expected:

```python
def test_flag_settable_via_setattr(self):
    """Verify config loader mechanism works for this flag."""
    import litellm

    # Simulate what proxy_server.py does
    setattr(litellm, 'entra_groups_also_create_orgs', True)
    assert litellm.entra_groups_also_create_orgs is True

    setattr(litellm, 'entra_groups_also_create_orgs', False)
    assert litellm.entra_groups_also_create_orgs is False
```

---

## Verification Checklist

- [ ] Both tests pass
- [ ] Flag defaults to `False`
- [ ] Flag can be set to `True`
- [ ] Flag can be read via `litellm.entra_groups_also_create_orgs`
- [ ] Flag is properly typed as `bool`

---

## Summary

**What changed:**
- Added `entra_groups_also_create_orgs: bool = False` to `litellm/__init__.py`

**Why:**
- Provides a global configuration flag to enable/disable the feature
- Defaults to `False` to preserve current behavior
- Can be set via environment variables or runtime assignment

**Dependencies:**
- None (standalone configuration)

**Next:** [Cycle 2: Organization Creation →](./CYCLE-2-ORG-CREATION.md)

---

[← Back to Cycles README](./README.md) | [← Previous: Cycle 0](./CYCLE-0-SETUP.md) | [Next: Cycle 2 →](./CYCLE-2-ORG-CREATION.md)
