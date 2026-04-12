#!/usr/bin/env python3
"""Check pydantic version and behavior."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print(f"Python version: {sys.version}")
print()

# Check pydantic
try:
    import pydantic
    print(f"Pydantic version: {pydantic.__version__}")
except ImportError:
    print("Pydantic not installed")
    sys.exit(1)

print()

# Test simple model
from pydantic import BaseModel, Field

class TestSettings(BaseModel):
    name: str = Field(default="default_name")
    value: str = Field(default="default_value")

# Test 1: Default values
print("Test 1: Default values")
t1 = TestSettings()
print(f"  t1.name = {t1.name}")
print(f"  t1.value = {t1.value}")

# Test 2: Custom values
print("\nTest 2: Custom values")
t2 = TestSettings(name="custom_name", value="custom_value")
print(f"  t2.name = {t2.name}")
print(f"  t2.value = {t2.value}")

# Test 3: Partial values
print("\nTest 3: Partial values")
t3 = TestSettings(name="only_name")
print(f"  t3.name = {t3.name}")
print(f"  t3.value = {t3.value}")

print()
print("If Test 2 shows 'custom_value', pydantic is working correctly.")
