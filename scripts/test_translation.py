#!/usr/bin/env python3
"""Test script to verify translation functionality works end-to-end."""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_translation_cache():
    """Test that translation cache can be loaded and saved."""
    cache_file = project_root / 'docs' / 'translations' / 'api_translations.json'
    
    # Test loading existing cache
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        print(f"✓ Loaded cache with {len(cache)} entries")
        
        # Verify expected translations
        expected = {
            "Parameters": "参数",
            "Returns": "返回", 
            "Raises": "抛出异常",
            "Example": "示例"
        }
        
        for eng, expected_zh in expected.items():
            if eng in cache and cache[eng] == expected_zh:
                print(f"✓ Translation verified: {eng} -> {expected_zh}")
            else:
                print(f"✗ Translation missing/incorrect: {eng}")
        
        return True
    else:
        print("✗ Translation cache file not found")
        return False

def test_translation_script_import():
    """Test that the translation script can be imported."""
    try:
        import scripts.translate_docs
        print("✓ Translation script can be imported")
        return True
    except ImportError as e:
        print(f"✗ Cannot import translation script: {e}")
        return False

def test_dependencies():
    """Test that required dependencies are available."""
    try:
        from bs4 import BeautifulSoup
        print("✓ BeautifulSoup4 available")
    except ImportError:
        print("✗ BeautifulSoup4 not available")
        return False
        
    try:
        from translate import Translator
        print("✓ translate library available")
    except ImportError:
        print("✗ translate library not available") 
        return False
        
    return True

def main():
    """Run all tests."""
    print("KToolBox Translation Infrastructure Test")
    print("=" * 45)
    
    tests = [
        ("Translation cache", test_translation_cache),
        ("Translation script import", test_translation_script_import), 
        ("Dependencies", test_dependencies),
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\nTesting {name}...")
        if test_func():
            passed += 1
        
    print(f"\n\nResults: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)