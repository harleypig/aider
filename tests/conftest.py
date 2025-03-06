import os
import re
import inspect
import pytest
import importlib
import pkgutil
import aider  # Import the aider package

def discover_env_vars():
    """
    Auto-discover environment variables supported by aider by scanning the codebase.
    """
    env_vars = set()
    
    # Pattern to match environment variable references like os.environ.get("AIDER_SOMETHING")
    # or os.getenv("AIDER_SOMETHING") or os.environ["AIDER_SOMETHING"]
    env_pattern = re.compile(r'os\.environ(?:\.get)?\s*\(\s*["\']([A-Za-z0-9_]+)["\']|os\.getenv\s*\(\s*["\']([A-Za-z0-9_]+)["\']|os\.environ\[["\']([A-Za-z0-9_]+)["\']\]')
    
    # Walk through all modules in the aider package
    for _, module_name, _ in pkgutil.walk_packages(aider.__path__, aider.__name__ + '.'):
        try:
            module = importlib.import_module(module_name)
            
            # Look at the module source code
            try:
                source = inspect.getsource(module)
                for match in env_pattern.finditer(source):
                    # Extract the environment variable name from whichever group matched
                    var_name = next((g for g in match.groups() if g), None)
                    if var_name:
                        env_vars.add(var_name)
            except (TypeError, OSError):
                # Skip if we can't get source code
                pass
                
        except ImportError:
            # Skip if module can't be imported
            pass
    
    return env_vars

@pytest.fixture(scope="session", autouse=True)
def clean_environment():
    """
    Temporarily unset all aider environment variables during test runs
    and restore them after tests complete.
    """
    # Auto-discover environment variables
    aider_env_vars = discover_env_vars()
    
    # You might want to add any known variables that might be missed by auto-discovery
    aider_env_vars.update([
        "AIDER_API_KEY",
        "AIDER_OPENAI_API_KEY",
        "AIDER_ANTHROPIC_API_KEY",
        "AIDER_MODEL",
        "AIDER_EDIT_FORMAT",
        "AIDER_MAP_TOKENS",
        "AIDER_CONFIG"
    ])
    
    # Store original environment variables
    original_env = {}
    for var in aider_env_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]
    
    # Run tests with clean environment
    yield
    
    # Restore original environment variables
    for var, value in original_env.items():
        os.environ[var] = value
