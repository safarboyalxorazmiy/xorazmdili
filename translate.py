#!/usr/bin/env python
import sys
import re
from googletrans import Translator

# -------------------------------------------------
# 1. Initialize Google Translator
# -------------------------------------------------
translator = Translator()
print("Using Google Translate\n")

# -------------------------------------------------
# 2. Set source and target languages
# -------------------------------------------------
src_lang = "en"  # English
tgt_lang = "az"  # Azerbaijani
print(f"Source: {src_lang}, Target: {tgt_lang}\n")

# -------------------------------------------------
# 3. Helpers
# -------------------------------------------------
def split_sentences(text):
    """Split text into sentences"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def translate_sentence(sentence):
    """Translate a single sentence using Google Translate"""
    result = translator.translate(sentence, src=src_lang, dest=tgt_lang)
    return result.text

def translate(text):
    """Translate full text sentence by sentence"""
    sentences = split_sentences(text)
    
    if not sentences:
        return ""

    translated_sentences = []
    for i, s in enumerate(sentences, 1):
        print(f"  [{i}/{len(sentences)}] {s}")
        tr = translate_sentence(s)
        print(f"            → {tr}")
        translated_sentences.append(tr)
    
    return " ".join(translated_sentences)

# -------------------------------------------------
# 4. Load replacements
# -------------------------------------------------
repl_dict = {}
try:
    with open("replacements.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "→" not in line:
                continue
            src, dst = line.split("→", 1)
            repl_dict[src.strip()] = dst.strip()
    print(f"Loaded {len(repl_dict)} replacement rules\n")
except FileNotFoundError:
    print("Warning: replacements.txt not found. Skipping replacements.\n")

if repl_dict:
    pattern = re.compile(r'\b(' + '|'.join(map(re.escape, repl_dict.keys())) + r')\b', re.IGNORECASE)
    def replace_words(t):
        return pattern.sub(lambda m: repl_dict.get(m.group(0), m.group(0)), t)
else:
    def replace_words(t):
        return t

# -------------------------------------------------
# 5. CLI
# -------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./translate.py \"Your English text\"")
        sys.exit(1)
    
    input_text = " ".join(sys.argv[1:])
    print(f"Input: {input_text}\n")
    
    raw = translate(input_text)
    final = replace_words(raw)
    
    if final != raw:
        print(f"\nAfter replacements: {final}")
    
    print(f"\n✓ FINAL: {final}")
