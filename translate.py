#!/usr/bin/env python
import sys
import re
import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

# -------------------------------------------------
# 1. Load M2M100 model & tokenizer
# -------------------------------------------------
# Options:
# - "facebook/m2m100_418M" (smaller, faster)
# - "facebook/m2m100_1.2B" (better quality)

model_name = "facebook/m2m100_418M"

print(f"Loading model: {model_name}")
print("This may take a few minutes on first run...")

tokenizer = M2M100Tokenizer.from_pretrained(model_name)
model = M2M100ForConditionalGeneration.from_pretrained(model_name)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(f"Using device: {device}")

# -------------------------------------------------
# 2. Set source and target languages
# -------------------------------------------------
src_lang = "en"  # English
tgt_lang = "az"  # Azerbaijani

tokenizer.src_lang = src_lang
print(f"Source: {src_lang}, Target: {tgt_lang}\n")

# -------------------------------------------------
# 3. Translation function
# -------------------------------------------------
def split_sentences(text):
    """Split text into sentences"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def translate_sentence(text: str) -> str:
    """Translate a single sentence"""
    encoded = tokenizer(text, return_tensors="pt").to(device)
    generated_tokens = model.generate(
        **encoded,
        forced_bos_token_id=tokenizer.get_lang_id(tgt_lang),
        max_length=512,
        num_beams=5,
        early_stopping=True
    )
    return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

def translate(text: str) -> str:
    """Translate text, processing sentence by sentence"""
    sentences = split_sentences(text)
    
    if len(sentences) == 0:
        return ""
    
    if len(sentences) == 1:
        result = translate_sentence(text)
        print(f"  Translation: {result}")
        return result
    
    # Translate each sentence separately
    translated_sentences = []
    for i, sent in enumerate(sentences, 1):
        print(f"  [{i}/{len(sentences)}] {sent}")
        translated = translate_sentence(sent)
        print(f"            → {translated}")
        translated_sentences.append(translated)
    
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
        print("\nSupported models:")
        print("  - facebook/m2m100_418M (default, fast)")
        print("  - facebook/m2m100_1.2B (better quality)")
        print("\nChange model_name in the script to use a different model.")
        sys.exit(1)
    
    input_text = " ".join(sys.argv[1:])
    print(f"Input: {input_text}\n")
    
    raw = translate(input_text)
    
    final = replace_words(raw)
    if final != raw:
        print(f"\nAfter replacements: {final}")
    
    print(f"\n✓ FINAL: {final}")