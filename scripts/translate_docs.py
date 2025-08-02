#!/usr/bin/env python3
"""
Translation script for KToolBox API documentation.
Translates mkdocstrings-generated API documentation from English to Chinese.
"""

import os
import re
import sys
import json
import time
from pathlib import Path
from bs4 import BeautifulSoup
from translate import Translator

def load_translation_cache(cache_file):
    """Load translation cache from file."""
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache: {e}")
    return {}

def save_translation_cache(cache_file, cache):
    """Save translation cache to file."""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def extract_translatable_content(html_file):
    """Extract translatable content from HTML documentation."""
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    texts = set()
    
    # Extract main description paragraphs
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        # Skip short text, code snippets, and already translated content
        if (text and len(text) > 10 and 
            not re.search(r'[\u4e00-\u9fff]', text) and  # Not Chinese
            not text.startswith('Source code') and
            not re.match(r'^[<>{}()\[\]]+$', text)):  # Not just symbols
            texts.add(text)
    
    # Extract section titles
    for span in soup.find_all('span', class_='doc-section-title'):
        text = span.get_text().strip().rstrip(':')
        if text and text not in ['Name', 'Type', 'Description', 'Default']:
            texts.add(text)
    
    # Extract table descriptions (parameter descriptions)
    for td in soup.find_all('td'):
        text = td.get_text().strip()
        if (text and len(text) > 15 and 
            not re.search(r'[\u4e00-\u9fff]', text) and
            not text.startswith('<') and
            not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', text)):  # Not just variable names
            texts.add(text)
    
    return list(texts)

def translate_content(texts, cache, force_retranslate=False):
    """Translate content with caching and rate limiting."""
    translator = Translator(provider='mymemory', from_lang='en', to_lang='zh')
    translated = {}
    
    # Use cache unless forced to retranslate
    new_texts = []
    for text in texts:
        if text in cache and not force_retranslate:
            translated[text] = cache[text]
        else:
            new_texts.append(text)
    
    if not new_texts:
        print(f"All {len(texts)} texts found in cache!")
        return translated
    
    print(f"Translating {len(new_texts)} new texts...")
    
    # Translate new content with error handling and rate limiting
    for i, text in enumerate(new_texts):
        try:
            print(f"[{i+1}/{len(new_texts)}] Translating: {text[:60]}...")
            result = translator.translate(text)
            translated[text] = result
            cache[text] = result
            
            # Rate limiting - be respectful to the API
            if i < len(new_texts) - 1:  # Don't delay after the last item
                time.sleep(1.5)
                
        except Exception as e:
            print(f"Translation failed for '{text[:30]}...': {e}")
            translated[text] = text  # Keep original on failure
            cache[text] = text
    
    return translated

def apply_translations(html_file, translations):
    """Apply translations to HTML file."""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply translations with careful text replacement
    changes_made = 0
    for original, translated in translations.items():
        if original != translated:
            # Use whole word matching when possible
            if re.search(r'^[A-Za-z\s]+$', original):  # Simple text
                pattern = r'\b' + re.escape(original) + r'\b'
                new_content = re.sub(pattern, translated, content)
            else:
                # For complex text, use exact matching
                new_content = content.replace(original, translated)
            
            if new_content != content:
                changes_made += 1
                content = new_content
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Applied {changes_made} translations to {html_file}")

def main():
    """Main translation function."""
    project_root = Path(__file__).parent.parent
    
    # File paths
    en_api_file = project_root / 'site' / 'api' / 'index.html'
    zh_api_file = project_root / 'site' / 'zh' / 'api' / 'index.html'
    cache_file = project_root / 'docs' / 'translations' / 'api_translations.json'
    
    # Check if files exist
    if not en_api_file.exists():
        print(f"Error: English API documentation not found: {en_api_file}")
        print("Please run 'mkdocs build' first to generate documentation.")
        sys.exit(1)
        
    if not zh_api_file.exists():
        print(f"Error: Chinese API documentation not found: {zh_api_file}")
        print("Please run 'mkdocs build' first to generate documentation.")
        sys.exit(1)
    
    # Check environment variables
    force_retranslate = os.getenv('FORCE_RETRANSLATE', '').lower() in ('true', '1', 'yes')
    
    print("KToolBox API Documentation Translation Script")
    print("=" * 50)
    print(f"Force retranslate: {force_retranslate}")
    
    # Load cache
    print("Loading translation cache...")
    cache = load_translation_cache(cache_file)
    print(f"Loaded {len(cache)} cached translations")
    
    # Extract content to translate
    print("Extracting translatable content...")
    texts = extract_translatable_content(en_api_file)
    print(f"Found {len(texts)} texts to translate")
    
    if not texts:
        print("No content found to translate.")
        return
    
    # Translate content
    print("Starting translation...")
    translations = translate_content(texts, cache, force_retranslate)
    
    # Save updated cache
    print("Saving translation cache...")
    save_translation_cache(cache_file, cache)
    
    # Apply translations
    print("Applying translations to Chinese documentation...")
    apply_translations(zh_api_file, translations)
    
    translated_count = sum(1 for orig, trans in translations.items() if orig != trans)
    print(f"\nTranslation completed successfully!")
    print(f"- Total texts processed: {len(texts)}")
    print(f"- Actual translations: {translated_count}")
    print(f"- Cache size: {len(cache)}")

if __name__ == "__main__":
    main()