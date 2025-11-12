#!/usr/bin/env python
import sys
import re
from googletrans import Translator

# -------------------------------------------------
# 1. Configuration
# -------------------------------------------------
class Config:
    SRC_LANG = "en"
    TGT_LANG = "az" 
    REPLACEMENTS_FILE = "replacements.txt"

# -------------------------------------------------
# 2. Helpers
# -------------------------------------------------
def split_sentences(text):
    """Split text into sentences more accurately"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def load_replacements(filename):
    """Load replacement rules from file with case handling"""
    repl_dict = {}
    case_variations = {}  # Store all case variations
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#') or "→" not in line:
                    continue
                try:
                    src, dst = line.split("→", 1)
                    src_clean = src.strip()
                    dst_clean = dst.strip()
                    
                    # Store the original mapping
                    repl_dict[src_clean] = dst_clean
                    
                    # Also store lowercase version for case-insensitive matching
                    repl_dict[src_clean.lower()] = dst_clean
                    
                    # Store title case version (first letter capitalized)
                    if src_clean:
                        repl_dict[src_clean[0].upper() + src_clean[1:].lower()] = dst_clean
                    
                    # Store uppercase version
                    repl_dict[src_clean.upper()] = dst_clean
                    
                except ValueError:
                    print(f"Warning: Invalid format in {filename} line {line_num}: {line}")
        
        print(f"Loaded {len([k for k in repl_dict if '→' not in k])} replacement rules from {filename}")
        return repl_dict
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Skipping replacements.")
        return {}

def create_replacer(repl_dict):
    """Create a replacement function with case-insensitive matching"""
    if not repl_dict:
        return lambda x: x
    
    # Get all unique source patterns (without case variations)
    base_patterns = set()
    for key in repl_dict.keys():
        # Skip if this looks like a case variation we created
        if '→' not in key and not any(key == v.upper() or key == v.lower() or key == v.title() for v in repl_dict.values()):
            base_patterns.add(re.escape(key))
    
    if not base_patterns:
        return lambda x: x
    
    # Sort by length (longest first) to prevent partial matches
    sorted_patterns = sorted(base_patterns, key=len, reverse=True)
    pattern = re.compile(r'\b(' + '|'.join(sorted_patterns) + r')\b', re.IGNORECASE)
    
    def replacer(text):
        def replace_match(match):
            matched_text = match.group(0)
            # Try exact match first
            if matched_text in repl_dict:
                return repl_dict[matched_text]
            # Try case variations
            elif matched_text.lower() in repl_dict:
                return repl_dict[matched_text.lower()]
            elif matched_text.title() in repl_dict:
                return repl_dict[matched_text.title()]
            elif matched_text.upper() in repl_dict:
                return repl_dict[matched_text.upper()]
            else:
                return matched_text
        
        return pattern.sub(replace_match, text)
    
    return replacer

# -------------------------------------------------
# 3. Translation functions
# -------------------------------------------------
def translate_sentence(translator, sentence, src_lang, tgt_lang):
    """Translate a single sentence with error handling"""
    try:
        result = translator.translate(sentence, src=src_lang, dest=tgt_lang)
        return result.text
    except Exception as e:
        print(f"Translation error for '{sentence}': {e}")
        return sentence  # Return original on error

def translate_text(text, translator, src_lang, tgt_lang):
    """Translate full text sentence by sentence"""
    sentences = split_sentences(text)
    
    if not sentences:
        return ""

    translated_sentences = []
    for i, sentence in enumerate(sentences, 1):
        print(f"  [{i}/{len(sentences)}] {sentence}")
        translated = translate_sentence(translator, sentence, src_lang, tgt_lang)
        print(f"        → {translated}")
        translated_sentences.append(translated)
    
    return " ".join(translated_sentences)

# -------------------------------------------------
# 4. Main execution
# -------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: ./translate.py \"Your English text\"")
        print("   or: cat file.txt | ./translate.py")
        sys.exit(1)
    
    # Handle piped input or command line argument
    if not sys.stdin.isatty():
        input_text = sys.stdin.read().strip()
    else:
        input_text = " ".join(sys.argv[1:])
    
    print(f"Input: {input_text}\n")
    
    # Initialize components
    translator = Translator()
    replacements = load_replacements(Config.REPLACEMENTS_FILE)
    replace_words = create_replacer(replacements)
    
    # Translate
    raw_translation = translate_text(input_text, translator, Config.SRC_LANG, Config.TGT_LANG)
    final_translation = replace_words(raw_translation)
    
    # Output results
    if final_translation != raw_translation:
        print(f"\nAfter replacements: {final_translation}")
        print(f"\n✓ FINAL: {final_translation}")
    else:
        print(f"\n✓ FINAL: {final_translation}")
    
    # Copy to clipboard (optional)
    try:
        import pyperclip
        pyperclip.copy(final_translation)
        print("✓ Copied to clipboard!")
    except ImportError:
        pass

if __name__ == "__main__":
    main()