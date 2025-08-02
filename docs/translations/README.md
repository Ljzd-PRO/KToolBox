# Translation Files

This directory contains translation cache files for the automated documentation translation system.

## Files

- `api_translations.json` - Translation cache for API documentation
  - Contains mapping from English text to Chinese translations
  - Used by the translation CI to avoid retranslating the same content
  - Automatically updated by the translation workflow

## How it works

1. The translation workflow (`translate.yml`) extracts translatable text from the English API documentation
2. Text is translated using the MyMemory API via the `translate` Python library
3. Translations are cached in JSON files to avoid repeated API calls
4. The Chinese documentation is updated with the translated content
5. Changes are automatically committed to the repository

## Manual editing

You can manually edit the translation files to improve translations:
- Edit the JSON files directly
- Run the translation workflow with `force_retranslate: true` to refresh specific translations
- The cache will be preserved for unchanged entries

## API Rate Limits

The translation process respects MyMemory API rate limits:
- 1.5 second delay between requests
- Caching prevents unnecessary retranslation
- Failed translations fall back to original English text