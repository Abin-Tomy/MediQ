import csv
from collections import defaultdict
import json

S2D_PATH = 'datasets/symptom2disease/Symptom2Disease.csv'

# Store all occurrences of each text
text_occurrences = defaultdict(list)
all_records = []

with open(S2D_PATH, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    for i, row in enumerate(reader):
        if len(row) < 3: continue
        label = row[1].strip()
        text = row[2].strip()
        if not text or not label: continue
        
        record = {'idx': i, 'label': label, 'text': text}
        text_occurrences[text].append(record)
        all_records.append(record)

# Find duplicates
duplicate_texts = {text: occ for text, occ in text_occurrences.items() if len(occ) > 1}

same_label_dups = 0
diff_label_dups = 0
total_duplicate_rows = 0 # number of rows that are duplicates (occurrences > 1)

for text, occ in duplicate_texts.items():
    labels = set([r['label'] for r in occ])
    if len(labels) == 1:
        same_label_dups += 1
    else:
        diff_label_dups += 1
    total_duplicate_rows += len(occ)

print(f"Number of unique texts with multiple occurrences: {len(duplicate_texts)}")
print(f"Duplicates with same label: {same_label_dups}")
print(f"Duplicates with different labels: {diff_label_dups}")
print(f"Total rows involved in duplication: {total_duplicate_rows}")

# Exactly which record is retained?
# The original preprocess.py uses:
# if text in seen_texts: continue
# seen_texts.add(text)
# This means the FIRST record encountered is retained.

# Original classes
original_counts = defaultdict(int)
for r in all_records:
    original_counts[r['label']] += 1

# After removal classes
after_counts = defaultdict(int)
seen_texts = set()
for r in all_records:
    if r['text'] not in seen_texts:
        seen_texts.add(r['text'])
        after_counts[r['label']] += 1

print("\nClass counts before -> after:")
for label in sorted(original_counts.keys()):
    print(f"{label}: {original_counts[label]} -> {after_counts[label]}")

