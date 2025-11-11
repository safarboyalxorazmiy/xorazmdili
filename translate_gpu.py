#!/usr/bin/env python
import sys, re, torch
from transformers import pipeline
device = 0 if torch.cuda.is_available() else -1
print(f"Using device: {'GPU (CUDA)' if device==0 else 'CPU'}")
translator = pipeline("translation", model="./nllb_en_az", tokenizer="./nllb_en_az",
                      src_lang="eng_Latn", tgt_lang="aze_Latn", device=device,
                      max_length=512, batch_size=8)
repl_dict = {}
with open("replacements.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or "→" not in line: continue
        src, dst = line.split("→", 1)
        repl_dict[src.strip()] = dst.strip()
pattern = re.compile(r'\b(' + '|'.join(map(re.escape, repl_dict.keys())) + r')\b')
def replace_words(t): return pattern.sub(lambda m: repl_dict[m.group(0)], t)
if len(sys.argv)<2: print("Usage: python translate_gpu.py \"text\""); sys.exit(1)
raw = translator(" ".join(sys.argv[1:]))[0]["translation_text"]
print(replace_words(raw))
