"""Custom Python handler with translation support for mkdocstrings."""

import os
import json
import requests
from typing import Any, Dict, Optional

from mkdocstrings_handlers.python.handler import PythonHandler


class TranslatablePythonHandler(PythonHandler):
    """Python handler with automatic translation support.
    
    This handler extends the default Python handler to provide automatic
    translation of docstrings and documentation content using MyMemory API or OpenAI API.
    Translation is enabled via the ENABLE_TRANSLATION environment variable.
    """
    
    def __init__(self, handler: str, theme: str, **kwargs: Any) -> None:
        """Initialize the translatable Python handler.
        
        Args:
            handler: Handler name.
            theme: Theme name.
            **kwargs: Keyword arguments passed to the parent handler.
        """
        super().__init__(handler=handler, theme=theme, **kwargs)
        self._translation_enabled = os.getenv("ENABLE_TRANSLATION", "false").lower() == "true"
        self._platform = os.getenv("TRANSLATE_PLATFORM", "my_memory")
        self._target_language = None
        self._translator = None
        self._openai_config = {}
        
        if self._translation_enabled:
            if self._platform == 'openai':
                self._setup_openai()
            else:
                self._setup_translator()
    
    def _setup_openai(self) -> None:
        """Set up OpenAI configuration."""
        self._openai_config = {
            'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'model': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
        }
        
        if not self._openai_config['api_key']:
            print("Warning: OPENAI_API_KEY not set. OpenAI translation disabled.")
            self._translation_enabled = False

    def _setup_translator(self) -> None:
        """Set up the translator with MyMemory API."""
        try:
            from translate import Translator
            
            # Get API key from GitHub Actions secret or environment variable
            api_key = os.getenv("MY_MEMORY_API_KEY")
            
            # The translate library constructor expects to_lang as first parameter
            # We'll create translators on demand for specific language pairs
            self._api_key = api_key
                
        except ImportError:
            print("Warning: translate library not available. Translation disabled.")
            self._translation_enabled = False
    
    def _detect_language_from_config(self) -> Optional[str]:
        """Detect target language from mkdocstrings extra configuration.
        
        Returns:
            Language code (e.g., 'zh', 'en') or None if not found.
        """
        # Try to get language from the current context
        # This would be set in the markdown files via mkdocstrings options
        config_extra = getattr(self, '_config_extra', None)
        if config_extra and isinstance(config_extra, dict):
            return config_extra.get('language')
        return None
    
    def _translate_with_openai(self, text: str, target_language: str) -> str:
        """Translate text using OpenAI API."""
        if not self._openai_config['api_key'] or not text.strip():
            return text
            
        # Skip translation if target is English
        if target_language == "en":
            return text
            
        try:
            # Fixed translation mappings
            translation_mappings = {
                'post': '帖子',
                'artist': '画师'
            }
            
            # Apply fixed mappings first
            translated_text = text
            for en_word, zh_word in translation_mappings.items():
                translated_text = translated_text.replace(en_word, zh_word)
            
            # If the text only contained mapped words, return it
            if translated_text != text:
                return translated_text
            
            # Prepare OpenAI request
            headers = {
                'Authorization': f'Bearer {self._openai_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            # Determine target language name for prompt
            lang_name = "Chinese" if target_language == "zh" else target_language
            
            # Strict prompt to ensure clean translation output
            system_prompt = f"""You are a professional English to {lang_name} translator. 
Translate the given English text to {lang_name}.
IMPORTANT RULES:
1. Return ONLY the translated {lang_name} text, no additional content
2. Do NOT wrap the response in markdown code blocks
3. Do NOT add explanations, comments, or extra formatting
4. Use these specific translations: post -> 帖子, artist -> 画师
5. Keep technical terms and code elements unchanged when appropriate"""
            
            data = {
                'model': self._openai_config['model'],
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f'Translate to {lang_name}: {text}'}
                ],
                'temperature': 0.3,
                'max_tokens': 1000
            }
            
            # Make API request
            response = requests.post(
                f"{self._openai_config['base_url']}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    translated = result['choices'][0]['message']['content'].strip()
                    # Clean up any potential markdown formatting
                    translated = translated.replace('```', '').replace('`', '')
                    return translated
            else:
                print(f"OpenAI API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"OpenAI translation error: {e}")
            
        return text

    def _translate_text(self, text: str, target_language: str) -> str:
        """Translate text to the target language.
        
        Args:
            text: Text to translate.
            target_language: Target language code.
            
        Returns:
            Translated text or original text if translation fails.
        """
        if not text.strip():
            return text
            
        if self._platform == 'openai':
            return self._translate_with_openai(text, target_language)
        elif self._platform == 'my_memory' and hasattr(self, '_api_key'):
            try:
                from translate import Translator
                
                # Skip translation if target is English
                if target_language == "en":
                    return text
                
                # Create translator for this specific language pair
                if hasattr(self, '_api_key') and self._api_key:
                    translator = Translator(
                        to_lang=target_language, 
                        from_lang="en", 
                        provider="mymemory",
                        secret_access_key=self._api_key
                    )
                else:
                    # Fallback to free tier
                    translator = Translator(
                        to_lang=target_language, 
                        from_lang="en", 
                        provider="mymemory"
                    )
                
                result = translator.translate(text)
                return result if isinstance(result, str) else str(result)
                
            except Exception as e:
                print(f"MyMemory translation warning: {e}")
                return text
        else:
            return text
    
    def collect(self, identifier: str, config: Dict[str, Any]) -> Any:
        """Collect and optionally translate documentation data.
        
        Args:
            identifier: The object identifier.
            config: The handler configuration.
            
        Returns:
            Collected and optionally translated data.
        """
        # Store extra config for language detection
        self._config_extra = config.get('extra', {})
        
        # Get the original data
        data = super().collect(identifier, config)
        
        # Apply translation if enabled
        if self._translation_enabled and data:
            target_language = self._detect_language_from_config()
            if target_language and target_language != "en":
                data = self._translate_object_data(data, target_language)
        
        return data
    
    def _translate_object_data(self, obj: Any, target_language: str) -> Any:
        """Recursively translate object data.
        
        Args:
            obj: Object data to translate.
            target_language: Target language code.
            
        Returns:
            Object data with translated strings.
        """
        if hasattr(obj, 'docstring') and obj.docstring:
            # Translate the main docstring
            if hasattr(obj.docstring, 'value'):
                obj.docstring.value = self._translate_text(obj.docstring.value, target_language)
            
            # Translate docstring sections (parameters, returns, etc.)
            if hasattr(obj.docstring, 'sections'):
                for section in obj.docstring.sections:
                    if hasattr(section, 'value') and section.value:
                        section.value = self._translate_text(section.value, target_language)
                    
                    # Translate parameter descriptions
                    if hasattr(section, 'parameters'):
                        for param in section.parameters:
                            if hasattr(param, 'description') and param.description:
                                param.description = self._translate_text(param.description, target_language)
        
        # Translate class/function names and descriptions recursively
        if hasattr(obj, 'members'):
            for member in obj.members.values():
                self._translate_object_data(member, target_language)
        
        return obj


def get_handler(**kwargs: Any) -> TranslatablePythonHandler:
    """Get the translatable Python handler.
    
    Args:
        **kwargs: Keyword arguments passed to the handler.
        
    Returns:
        An instance of TranslatablePythonHandler.
    """
    # Use 'python' as handler name to inherit templates
    kwargs['handler'] = 'python'
    return TranslatablePythonHandler(**kwargs)