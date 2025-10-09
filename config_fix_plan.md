# Plan to Fix app/config.py

## Issue Identified
The `settings` instance is incorrectly defined inside the `Settings` class on line 43, which causes:
1. A recursive definition issue (class trying to instantiate itself)
2. The `settings` object not being accessible when imported from other modules

## Root Cause
The `settings = Settings()` line is indented as part of the `Settings` class, when it should be at the module level (outside the class).

## Solution
Move the `settings = Settings()` line outside the `Settings` class to make it a module-level singleton instance.

## Code Changes Required

### Current Code (lines 40-43):
```python
    PAYSTACK_ENVIRONMENT: str = "sandbox"  # or "production"


    settings = Settings()
```

### Corrected Code:
```python
    PAYSTACK_ENVIRONMENT: str = "sandbox"  # or "production"


# Create a singleton instance of Settings
settings = Settings()
```

## Impact Analysis
This fix will:
1. Resolve the "Settings is not defined" error
2. Make the settings instance properly accessible when imported
3. Maintain all existing functionality
4. Not break any existing imports (as seen in the search results)

## Files That Import settings
Based on our search, these files import settings from app/config:
- app/utils/redis_client.py
- app/services/payment_service.py
- app/main.py
- app/database.py
- app/auth/firebase_auth.py
- app/api/payment_routes.py
- alembic/env.py

The fix will ensure all these imports work correctly.