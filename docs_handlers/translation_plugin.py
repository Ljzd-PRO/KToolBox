"""MkDocs plugin for translating documentation content."""

import os
import re
from typing import Dict, Any, Optional
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.pages import Page
from mkdocs.structure.files import Files
from mkdocs.config.defaults import MkDocsConfig


class TranslationPlugin(BasePlugin):
    """Plugin to translate documentation content using MyMemory API."""
    
    config_scheme = (
        ('enabled', config_options.Type(bool, default=False)),
        ('api_key', config_options.Type(str, default='')),
        ('target_language', config_options.Type(str, default='zh')),
        ('source_language', config_options.Type(str, default='en')),
    )
    
    def __init__(self):
        super().__init__()
        self._translator = None
        self._translation_enabled = False
        
    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        """Configure the plugin."""
        # Check environment variables
        env_enabled = os.getenv("ENABLE_TRANSLATION", "false").lower() == "true"
        env_api_key = os.getenv("MY_MEMORY_API_KEY", "")
        
        # Override config with environment variables if set
        if env_enabled:
            self.config['enabled'] = True
        if env_api_key:
            self.config['api_key'] = env_api_key
            
        self._translation_enabled = self.config['enabled']
        
        if self._translation_enabled:
            self._setup_translator()
            
        return config
    
    def _setup_translator(self):
        """Set up the translator."""
        try:
            from translate import Translator
            
            api_key = self.config['api_key']
            target_lang = self.config['target_language']
            source_lang = self.config['source_language']
            
            if api_key:
                self._translator = Translator(
                    to_lang=target_lang,
                    from_lang=source_lang,
                    provider='mymemory',
                    secret_access_key=api_key
                )
            else:
                self._translator = Translator(
                    to_lang=target_lang,
                    from_lang=source_lang,
                    provider='mymemory'
                )
                
        except ImportError:
            print("Warning: translate library not available. Translation disabled.")
            self._translation_enabled = False
            
    def _should_translate_page(self, page: Page) -> bool:
        """Determine if a page should be translated based on its path."""
        # Only translate Chinese pages
        return page.file.src_path.startswith('zh/')
        
    def _translate_text(self, text: str) -> str:
        """Translate text content."""
        if not self._translator or not text.strip():
            return text
            
        try:
            result = self._translator.translate(text)
            return result if isinstance(result, str) else str(result)
        except Exception as e:
            print(f"Translation warning: {e}")
            return text
    
    def _translate_docstring_content(self, html_content: str) -> str:
        """Translate docstring content in HTML."""
        if not self._translation_enabled:
            return html_content
            
        # Pattern to match docstring content in mkdocstrings output
        patterns = [
            # String values like __description__ = 'A useful CLI tool...' (HTML entities)
            (r"<span class=\"s[12]\">&#39;([^&#]+)&#39;</span>", 
             lambda m: f"<span class=\"s1\">&#39;{self._translate_text(m.group(1))}&#39;</span>"),
            # String values like __description__ = 'A useful CLI tool...' (regular quotes)
            (r"<span class=\"s[12]\">'([^']+)'</span>", 
             lambda m: f"<span class=\"s1\">'{self._translate_text(m.group(1))}'</span>"),
            # Double quoted strings
            (r'<span class="s[12]">"([^"]+)"</span>', 
             lambda m: f'<span class="s1">"{self._translate_text(m.group(1))}"</span>'),
        ]
        
        translated_content = html_content
        translations_made = 0
        
        for pattern, replacement in patterns:
            matches = list(re.finditer(pattern, translated_content, re.IGNORECASE | re.DOTALL))
            
            for match in reversed(matches):  # Reverse to maintain positions
                original_text = match.group(1)
                # Skip if text is too short or contains only code/numbers
                if (len(original_text.strip()) < 15 or 
                    original_text.strip().isdigit() or
                    original_text.startswith('http') or
                    original_text.count('_') > len(original_text) * 0.3 or
                    original_text.count('%') > 2):
                    continue
                    
                translated_text = self._translate_text(original_text)
                if translated_text != original_text and "MYMEMORY WARNING" not in translated_text:
                    translations_made += 1
                    if callable(replacement):
                        # Get the replacement function result
                        new_match_text = replacement(match)
                        # Replace the original text with translated text in the match
                        new_content = new_match_text.replace(original_text, translated_text)
                    else:
                        new_content = replacement.replace(original_text, translated_text)
                        
                    translated_content = (
                        translated_content[:match.start()] + 
                        new_content + 
                        translated_content[match.end():]
                    )
                
        return translated_content
    
    def on_page_content(self, html: str, page: Page, config: MkDocsConfig, files: Files) -> str:
        """Process page content after rendering."""
        if not self._translation_enabled:
            return html
            
        if self._should_translate_page(page):
            return self._translate_docstring_content(html)
            
        return html
    
    def on_post_page(self, output: str, page: Page, config: MkDocsConfig) -> str:
        """Process page output after all processing."""
        if not self._translation_enabled:
            return output
            
        if self._should_translate_page(page):
            return self._translate_docstring_content(output)
            
        return output