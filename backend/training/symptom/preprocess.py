import os
import csv
import json
import ast
import random
from pathlib import Path
from collections import defaultdict
import hashlib

# Deterministic setup
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

BASE_DIR = Path('c:/Users/abint/Desktop/MediQ/backend/training/symptom/datasets')
PROCESSED_DIR = Path('c:/Users/abint/Desktop/MediQ/backend/training/symptom/processed')

# Source paths
DDXPLUS_DIR = BASE_DIR / 'ddxplus'
DDXPLUS_TRAIN = DDXPLUS_DIR / 'raw/train/release_train_patients'
DDXPLUS_VAL = DDXPLUS_DIR / 'raw/validate/release_validate_patients'
DDXPLUS_TEST = DDXPLUS_DIR / 'raw/test/release_test_patients'
DDXPLUS_EVIDENCES = DDXPLUS_DIR / 'release_evidences.json'
DDXPLUS_CONDITIONS = DDXPLUS_DIR / 'release_conditions.json'

S2D_PATH = BASE_DIR / 'symptom2disease' / 'Symptom2Disease.csv'
KERALA_PATH = BASE_DIR.parent / 'kerala_symptoms.json'

# Label Mapping
LABEL_MAPPING = {
    "Pneumonia": "Pneumonia",
    "gastroesophageal reflux disease": "GERD"
}

def setup_directories():
    for source in ['ddxplus', 'symptom2disease']:
        for split in ['train', 'validate', 'test']:
            (PROCESSED_DIR / source / split).mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / 'kerala' / 'evaluation').mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / 'label_mapping').mkdir(parents=True, exist_ok=True)

def load_ddxplus_metadata():
    with open(DDXPLUS_EVIDENCES, 'r', encoding='utf-8') as f:
        evidences = json.load(f)
    with open(DDXPLUS_CONDITIONS, 'r', encoding='utf-8') as f:
        conditions = json.load(f)
    return evidences, conditions

def process_ddxplus(split_name, in_path, out_path, evidences_meta):
    print(f"Processing DDXPlus {split_name}...")
    count = 0
    with open(in_path, 'r', encoding='utf-8') as fin, \
         open(out_path, 'w', encoding='utf-8') as fout:
        reader = csv.reader(fin)
        header = next(reader)
        
        age_idx = header.index('AGE')
        sex_idx = header.index('SEX')
        init_ev_idx = header.index('INITIAL_EVIDENCE')
        ev_idx = header.index('EVIDENCES')
        path_idx = header.index('PATHOLOGY')
        
        for row in reader:
            age = row[age_idx]
            sex = "Male" if row[sex_idx] == 'M' else "Female"
            pathology = row[path_idx]
            init_evidence = row[init_ev_idx]
            
            # Note: DIFFERENTIAL_DIAGNOSIS is intentionally ignored to prevent leakage
            
            ev_str = row[ev_idx]
            try:
                ev_list = ast.literal_eval(ev_str)
            except:
                ev_list = []
                
            text_parts = [f"Patient is a {age}-year-old {sex}."]
            
            # Translate INITIAL_EVIDENCE if it exists
            if init_evidence and init_evidence in evidences_meta:
                init_meta = evidences_meta[init_evidence]
                init_q = init_meta.get('question_en', init_evidence).strip()
                text_parts.append(f"Initial symptom: {init_q}.")
            
            # Translate all positive EVIDENCES
            for ev_code in ev_list:
                parts = ev_code.split('_@_')
                e_id = parts[0]
                
                if e_id not in evidences_meta:
                    continue
                
                meta = evidences_meta[e_id]
                question = meta.get('question_en', e_id).strip()
                
                if len(parts) == 1:
                    # Binary (Present)
                    text_parts.append(f"Evidence: {question} - Yes.")
                else:
                    # Categorical / Multichoice
                    val_id = parts[1]
                    val_meaning = val_id
                    if val_id.startswith('V_'):
                        val_meta = meta.get('value_meaning', {}).get(val_id, {})
                        val_meaning = val_meta.get('en', val_id)
                    text_parts.append(f"Evidence: {question} - {val_meaning}.")
            
            full_text = " ".join(text_parts)
            
            # Create a deterministic fingerprint for evaluation leakage audits
            # Excludes PATHOLOGY and DIFFERENTIAL_DIAGNOSIS
            canonical_ev = ",".join(sorted(ev_list))
            canonical_str = f"{age}|{row[sex_idx]}|{init_evidence}|{canonical_ev}"
            input_fingerprint = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
            
            record = {
                "text": full_text,
                "label": pathology,
                "source": "ddxplus",
                "split": split_name,
                "input_fingerprint": input_fingerprint
            }
            fout.write(json.dumps(record) + '\n')
            count += 1
            
    return count

def process_symptom2disease():
    print("Processing Symptom2Disease...")
    rows_by_class = defaultdict(list)
    seen_texts = set()
    
    with open(S2D_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        for row in reader:
            if len(row) < 3: continue
            label = row[1].strip()
            text = row[2].strip()
            
            if not text or not label:
                continue
                
            # Exact duplicate check to prevent leakage
            if text in seen_texts:
                continue
            seen_texts.add(text)
                
            # Apply normalisation
            norm_label = LABEL_MAPPING.get(label, label)
            
            record = {
                "text": text,
                "label": norm_label,
                "source": "symptom2disease"
            }
            rows_by_class[norm_label].append(record)
            
    # Stratified split 80-10-10
    train_recs, val_recs, test_recs = [], [], []
    for cls, recs in rows_by_class.items():
        random.shuffle(recs)
        n = len(recs)
        tr_end = int(0.8 * n)
        val_end = int(0.9 * n)
        
        for r in recs[:tr_end]:
            r['split'] = 'train'
            train_recs.append(r)
        for r in recs[tr_end:val_end]:
            r['split'] = 'validate'
            val_recs.append(r)
        for r in recs[val_end:]:
            r['split'] = 'test'
            test_recs.append(r)
            
    # Check duplicate leakage within S2D newly created splits
    tr_texts = set([r['text'] for r in train_recs])
    te_texts = set([r['text'] for r in test_recs])
    val_texts = set([r['text'] for r in val_recs])
    assert len(tr_texts.intersection(te_texts)) == 0, "Leakage between S2D Train and Test!"
    assert len(tr_texts.intersection(val_texts)) == 0, "Leakage between S2D Train and Validate!"
    assert len(val_texts.intersection(te_texts)) == 0, "Leakage between S2D Validate and Test!"
            
    # Write files
    def write_jsonl(recs, path):
        with open(path, 'w', encoding='utf-8') as f:
            for r in recs:
                f.write(json.dumps(r) + '\n')
                
    write_jsonl(train_recs, PROCESSED_DIR / 'symptom2disease' / 'train' / 's2d_train.jsonl')
    write_jsonl(val_recs, PROCESSED_DIR / 'symptom2disease' / 'validate' / 's2d_validate.jsonl')
    write_jsonl(test_recs, PROCESSED_DIR / 'symptom2disease' / 'test' / 's2d_test.jsonl')
    
    return len(train_recs), len(val_recs), len(test_recs)

def process_kerala():
    print("Processing Kerala data...")
    with open(KERALA_PATH, 'r', encoding='utf-8') as f:
        kerala_data = json.load(f)
        
    eval_recs = []
    for c in kerala_data.get('conditions', []):
        cond_name = c['condition']
        for prof in c.get('symptom_profiles', []):
            if prof.strip():
                eval_recs.append({
                    "text": prof.strip(),
                    "label": cond_name,
                    "source": "kerala",
                    "split": "evaluation"
                })
                
    out_path = PROCESSED_DIR / 'kerala' / 'evaluation' / 'kerala_eval.jsonl'
    with open(out_path, 'w', encoding='utf-8') as f:
        for r in eval_recs:
            f.write(json.dumps(r) + '\n')
            
    return len(eval_recs)

def save_label_mapping():
    out_path = PROCESSED_DIR / 'label_mapping' / 'label_mapping.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(LABEL_MAPPING, f, indent=2)

if __name__ == '__main__':
    setup_directories()
    save_label_mapping()
    
    evidences_meta, conditions_meta = load_ddxplus_metadata()
    
    tr_ddx = process_ddxplus('train', DDXPLUS_TRAIN, PROCESSED_DIR / 'ddxplus/train/ddx_train.jsonl', evidences_meta)
    val_ddx = process_ddxplus('validate', DDXPLUS_VAL, PROCESSED_DIR / 'ddxplus/validate/ddx_validate.jsonl', evidences_meta)
    te_ddx = process_ddxplus('test', DDXPLUS_TEST, PROCESSED_DIR / 'ddxplus/test/ddx_test.jsonl', evidences_meta)
    
    tr_s2d, val_s2d, te_s2d = process_symptom2disease()
    k_eval = process_kerala()
    
    report = {
        "random_seed": RANDOM_SEED,
        "format": "JSONL (Chosen for minimal dependency overhead and excellent streaming I/O for 1.3M+ records)",
        "label_mapping_applied": LABEL_MAPPING,
        "counts": {
            "ddxplus_train": tr_ddx,
            "ddxplus_validate": val_ddx,
            "ddxplus_test": te_ddx,
            "s2d_train": tr_s2d,
            "s2d_validate": val_s2d,
            "s2d_test": te_s2d,
            "kerala_evaluation": k_eval
        }
    }
    
    with open(PROCESSED_DIR / 'preprocessing_summary.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print("Preprocessing completed successfully.")
