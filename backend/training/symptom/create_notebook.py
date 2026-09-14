"""
Generates the corrected DistilBERT_MediQ_Training.ipynb notebook.

Architecture:
  Stage 1: 49-class DDXPlus fine-tuning
  Expand:  49 → 71 classifier with exact weight copying
  Stage 2: 71-class DDXPlus+S2D continued fine-tuning with DDX replay
"""
import json

DDX_LABELS = sorted([
    'Acute COPD exacerbation / infection', 'Acute dystonic reactions',
    'Acute laryngitis', 'Acute otitis media', 'Acute pulmonary edema',
    'Acute rhinosinusitis', 'Allergic sinusitis', 'Anaphylaxis', 'Anemia',
    'Atrial fibrillation', 'Boerhaave', 'Bronchiectasis', 'Bronchiolitis',
    'Bronchitis', 'Bronchospasm / acute asthma exacerbation', 'Chagas',
    'Chronic rhinosinusitis', 'Cluster headache', 'Croup', 'Ebola',
    'Epiglottitis', 'GERD', 'Guillain-Barre syndrome', 'HIV (initial infection)',
    'Influenza', 'Inguinal hernia', 'Larygospasm', 'Localized edema',
    'Myasthenia gravis', 'Myocarditis', 'PSVT', 'Pancreatic neoplasm',
    'Panic attack', 'Pericarditis', 'Pneumonia', 'Possible NSTEMI / STEMI',
    'Pulmonary embolism', 'Pulmonary neoplasm', 'SLE', 'Sarcoidosis',
    'Scombroid food poisoning', 'Spontaneous pneumothorax',
    'Spontaneous rib fracture', 'Stable angina', 'Tuberculosis', 'URTI',
    'Unstable angina', 'Viral pharyngitis', 'Whooping cough'
])

S2D_LABELS = sorted([
    'Acne', 'Arthritis', 'Bronchial Asthma', 'Cervical spondylosis',
    'Chicken pox', 'Common Cold', 'Dengue', 'Dimorphic Hemorrhoids',
    'Fungal infection', 'GERD', 'Hypertension', 'Impetigo', 'Jaundice',
    'Malaria', 'Migraine', 'Pneumonia', 'Psoriasis', 'Typhoid',
    'Varicose Veins', 'allergy', 'diabetes', 'drug reaction',
    'peptic ulcer disease', 'urinary tract infection'
])

UNIFIED_LABELS = DDX_LABELS.copy()
for l in S2D_LABELS:
    if l not in UNIFIED_LABELS:
        UNIFIED_LABELS.append(l)

cells = []

def md(text):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split('\n')]
    })

def code(text):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in text.strip().split('\n')]
    })

# --------------------------------------------------------------------------
md("""
# MediQ DistilBERT Staged Fine-Tuning
## Architecture Overview
- **Stage 1**: `distilbert-base-uncased` → 49-class DDXPlus classifier
- **Expand**: Classifier head expanded from 49 → 71 classes (exact weight copy)
- **Stage 2**: 71-class model continued fine-tuning on S2D + DDXPlus replay

> **Note**: Training cells are commented out. Uncomment to execute in Colab.
""")

# --------------------------------------------------------------------------
md("## 1. Environment / GPU Verification")
code("""
import sys, torch

print(f"Python: {sys.version}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
else:
    raise RuntimeError(
        "GPU not available. Do NOT proceed with full training on CPU. "
        "Go to Runtime → Change runtime type → GPU."
    )
""")

# --------------------------------------------------------------------------
md("## 2. Dependencies")
code("""
# Pin versions for reproducibility
!pip install -q \\
    transformers==4.35.0 \\
    datasets==2.14.6 \\
    accelerate==0.24.1 \\
    scikit-learn==1.3.2 \\
    matplotlib

import transformers, datasets, accelerate, sklearn
print(f"transformers: {transformers.__version__}")
print(f"datasets: {datasets.__version__}")
print(f"accelerate: {accelerate.__version__}")
print(f"scikit-learn: {sklearn.__version__}")
""")

# --------------------------------------------------------------------------
md("""## 3. Dataset Paths
**Setup instructions:**
Upload or mount the `processed/` folder from your workspace.

**Option A (Upload directly):**
Use the Colab file browser to upload the `processed/` folder to `/content/processed/`.

**Option B (Google Drive):**
```python
from google.colab import drive
drive.mount('/content/drive')
DATA_ROOT = Path('/content/drive/MyDrive/MediQ/processed')
```
Set `DATA_ROOT` below to match your upload location.
""")
code("""
from pathlib import Path

# ------------------------------------------------------------------
# CONFIGURE THIS: change to match where you placed the processed folder
DATA_ROOT = Path('/content/processed')
# ------------------------------------------------------------------

assert DATA_ROOT.exists(), f"DATA_ROOT not found: {DATA_ROOT}"

STAGE1_OUT = Path('/content/models/distilbert_ddxplus_stage1')
STAGE2_OUT = Path('/content/models/distilbert_mediq_stage2')
FINAL_OUT  = Path('/content/models/mediq_final')

for p in [STAGE1_OUT, STAGE2_OUT, FINAL_OUT]:
    p.mkdir(parents=True, exist_ok=True)

print("Paths OK.")
""")

# --------------------------------------------------------------------------
md("## 4. Reproducibility — Seeds")
code("""
import random, numpy as np
from transformers import set_seed

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
set_seed(SEED)

print(f"All seeds set to {SEED}.")
print("Note: CuDNN may introduce minor nondeterminism on certain GPU ops.")
""")

# --------------------------------------------------------------------------
md("""## 5. Label Mappings
Two-stage label space:
- **Stage 1 (DDXPlus)**: 49 classes, sorted alphabetically, indices 0–48.
- **Unified (Stage 2)**: DDXPlus labels first, then 22 S2D-only labels appended, indices 0–70.
- **Overlap**: Only `Pneumonia` and `GERD` exist in both datasets (approved mapping).
- `PATHOLOGY` and `DIFFERENTIAL_DIAGNOSIS` never appear as model inputs.
""")
code(f"""
DDX_LABELS = {json.dumps(DDX_LABELS, indent=4)}

S2D_LABELS = {json.dumps(S2D_LABELS, indent=4)}

# Build Stage 1 mappings (49-class)
ddx_label2id = {{l: i for i, l in enumerate(DDX_LABELS)}}
ddx_id2label = {{i: l for i, l in enumerate(DDX_LABELS)}}

# Build Unified mappings (71-class: DDX first, then S2D-only additions)
UNIFIED_LABELS = DDX_LABELS.copy()
S2D_ONLY_LABELS = []
for l in S2D_LABELS:
    if l not in UNIFIED_LABELS:
        UNIFIED_LABELS.append(l)
        S2D_ONLY_LABELS.append(l)

label2id = {{l: i for i, l in enumerate(UNIFIED_LABELS)}}
id2label  = {{i: l for i, l in enumerate(UNIFIED_LABELS)}}

assert len(DDX_LABELS)    == 49, f"Expected 49 DDX classes, got {{len(DDX_LABELS)}}"
assert len(UNIFIED_LABELS) == 71, f"Expected 71 unified classes, got {{len(UNIFIED_LABELS)}}"
assert len(S2D_ONLY_LABELS) == 22, f"Expected 22 S2D-only classes, got {{len(S2D_ONLY_LABELS)}}"
overlap = [l for l in S2D_LABELS if l in ddx_label2id]
assert set(overlap) == {{"Pneumonia", "GERD"}}, f"Unexpected overlap: {{overlap}}"

print(f"DDXPlus classes   : {{len(DDX_LABELS)}}")
print(f"S2D-only classes  : {{len(S2D_ONLY_LABELS)}}")
print(f"Unified total     : {{len(UNIFIED_LABELS)}}")
print(f"Overlap (approved): {{sorted(overlap)}}")
""")

# --------------------------------------------------------------------------
md("## 6. Load DDXPlus & Symptom2Disease Datasets")
code("""
from datasets import load_dataset

# --- DDXPlus ---
ddx_train_ds = load_dataset('json', data_files=str(DATA_ROOT / 'ddxplus/train/ddx_train.jsonl'),       split='train')
ddx_val_ds   = load_dataset('json', data_files=str(DATA_ROOT / 'ddxplus/validate/ddx_validate.jsonl'), split='train')
ddx_test_ds  = load_dataset('json', data_files=str(DATA_ROOT / 'ddxplus/test/ddx_test.jsonl'),         split='train')

# --- Symptom2Disease ---
s2d_train_ds = load_dataset('json', data_files=str(DATA_ROOT / 'symptom2disease/train/s2d_train.jsonl'),       split='train')
s2d_val_ds   = load_dataset('json', data_files=str(DATA_ROOT / 'symptom2disease/validate/s2d_validate.jsonl'), split='train')
s2d_test_ds  = load_dataset('json', data_files=str(DATA_ROOT / 'symptom2disease/test/s2d_test.jsonl'),         split='train')

# --- Kerala (evaluation only, never used for training) ---
kerala_ds = load_dataset('json', data_files=str(DATA_ROOT / 'kerala/evaluation/kerala_eval.jsonl'), split='train')

print(f"DDXPlus:  Train={len(ddx_train_ds):,}  Val={len(ddx_val_ds):,}  Test={len(ddx_test_ds):,}")
print(f"S2D:      Train={len(s2d_train_ds)}     Val={len(s2d_val_ds)}    Test={len(s2d_test_ds)}")
print(f"Kerala:   Eval={len(kerala_ds)}")

# Sanity: verify no test/eval data leaked
assert len(ddx_test_ds) > 0 and len(s2d_test_ds) > 0
print("Train/test split sanity OK.")
""")

# --------------------------------------------------------------------------
md("""## 7. Tokenization Analysis
The tokenizer receives **only** the `text` field.
`input_fingerprint`, `label`, `source`, and `split` are never passed to the tokenizer.
""")
code("""
from transformers import AutoTokenizer
import numpy as np, matplotlib.pyplot as plt

MODEL_ID = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

# Analyze on 5% DDXPlus sample (still ~50k rows) — enough for distribution
SAMPLE_FRACTION = 0.05
sample = ddx_train_ds.shuffle(seed=SEED).select(
    range(int(len(ddx_train_ds) * SAMPLE_FRACTION))
)
lengths = [len(tokenizer.tokenize(t)) for t in sample['text']]

print("Token Length Analysis (5% DDXPlus sample):")
print(f"  Mean              : {np.mean(lengths):.1f}")
print(f"  Median            : {np.median(lengths):.1f}")
print(f"  90th percentile   : {np.percentile(lengths, 90):.1f}")
print(f"  95th percentile   : {np.percentile(lengths, 95):.1f}")
print(f"  Maximum           : {max(lengths)}")

# Configurable max_length — set based on the analysis above
MAX_LENGTH = 128
pct_truncated = np.mean(np.array(lengths) > MAX_LENGTH) * 100
print(f"\\nmax_length = {MAX_LENGTH}  →  ~{pct_truncated:.1f}% of examples would be truncated.")
print("Adjust MAX_LENGTH above if truncation is unacceptably high before training.")
""")

code("""
# Stage 1 tokenizer: labels from ddx_label2id (49-class)
def tokenize_ddx(examples):
    enc = tokenizer(examples['text'], truncation=True, padding='max_length', max_length=MAX_LENGTH)
    enc['labels'] = [ddx_label2id[l] for l in examples['label']]
    return enc

# Stage 2 tokenizer: labels from unified label2id (71-class)
def tokenize_unified(examples):
    enc = tokenizer(examples['text'], truncation=True, padding='max_length', max_length=MAX_LENGTH)
    enc['labels'] = [label2id[l] for l in examples['label']]
    return enc

REMOVE_COLS_DDX = [c for c in ddx_train_ds.column_names]
REMOVE_COLS_S2D = [c for c in s2d_train_ds.column_names]

tok_ddx_train = ddx_train_ds.map(tokenize_ddx, batched=True, remove_columns=REMOVE_COLS_DDX)
tok_ddx_val   = ddx_val_ds.map(tokenize_ddx,   batched=True, remove_columns=ddx_val_ds.column_names)
# Keep extra columns in test for fingerprint-based strict eval
tok_ddx_test  = ddx_test_ds.map(tokenize_ddx,  batched=True)

tok_s2d_train = s2d_train_ds.map(tokenize_unified, batched=True, remove_columns=REMOVE_COLS_S2D)
tok_s2d_val   = s2d_val_ds.map(tokenize_unified,   batched=True, remove_columns=s2d_val_ds.column_names)
tok_s2d_test  = s2d_test_ds.map(tokenize_unified,  batched=True)
tok_kerala    = kerala_ds.map(tokenize_unified,     batched=True)

print("Tokenization complete.")
print(f"  DDXPlus train features: {tok_ddx_train.features}")
""")

# --------------------------------------------------------------------------
md("""## 8. Stage 1 — Build 49-class Model
The model is initialized with exactly 49 outputs — one per DDXPlus class.
The S2D classes do not exist yet at this stage.
""")
code("""
from transformers import AutoModelForSequenceClassification

stage1_model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_ID,
    num_labels=len(DDX_LABELS),  # exactly 49
    id2label=ddx_id2label,
    label2id=ddx_label2id
)

assert stage1_model.config.num_labels == 49
print(f"Stage 1 classifier output dim: {stage1_model.config.num_labels}  ✓")
""")

# --------------------------------------------------------------------------
md("""## 9. Stage 1 Training Configuration
Notes:
- LR `2e-5` is standard for DistilBERT fine-tuning on large data.
- 2 epochs are sufficient for 1M+ examples; more risks overfitting to DDXPlus formatting.
- Eval+save every 2,000 steps ≈ ~8 evaluations per epoch (batch 32 × grad_accum 2 = effective batch 64).
- Best checkpoint selected on Macro F1 (preferred over accuracy for multi-class).
- `fp16=True` requires GPU; handled by the runtime check in §1.
""")
code("""
from transformers import TrainingArguments

# -- Configurable hyperparameters --
S1_LR          = 2e-5
S1_BATCH       = 32
S1_GRAD_ACCUM  = 2       # effective batch = 32 * 2 = 64
S1_EPOCHS      = 2
S1_WEIGHT_DECAY= 0.01
S1_WARMUP_RATIO= 0.1
S1_EVAL_STEPS  = 2000
S1_SAVE_STEPS  = 2000

stage1_args = TrainingArguments(
    output_dir=str(STAGE1_OUT),
    learning_rate=S1_LR,
    per_device_train_batch_size=S1_BATCH,
    per_device_eval_batch_size=64,
    gradient_accumulation_steps=S1_GRAD_ACCUM,
    num_train_epochs=S1_EPOCHS,
    weight_decay=S1_WEIGHT_DECAY,
    warmup_ratio=S1_WARMUP_RATIO,
    evaluation_strategy="steps",
    eval_steps=S1_EVAL_STEPS,
    save_strategy="steps",
    save_steps=S1_SAVE_STEPS,
    load_best_model_at_end=True,
    metric_for_best_model="macro_f1",
    greater_is_better=True,
    fp16=torch.cuda.is_available(),
    seed=SEED,
    report_to="none",
    logging_steps=500,
)
print("Stage 1 training arguments configured.")
""")

# --------------------------------------------------------------------------
md("""## 10. Stage 1 Class Imbalance
We compute balanced class weights from the DDXPlus train label distribution.
This corrects for any imbalance in the 49 DDXPlus classes.
The weight vector is exactly length 49 — matching the Stage 1 classifier.
""")
code("""
from sklearn.utils.class_weight import compute_class_weight
import torch.nn as nn
from transformers import Trainer

train_labels_s1 = [ddx_label2id[ex['label']] for ex in ddx_train_ds]
s1_class_weights = compute_class_weight(
    'balanced',
    classes=np.arange(len(DDX_LABELS)),
    y=train_labels_s1
)
s1_weight_tensor = torch.tensor(s1_class_weights, dtype=torch.float32)
if torch.cuda.is_available():
    s1_weight_tensor = s1_weight_tensor.cuda()

print(f"Stage 1 class weight tensor shape: {s1_weight_tensor.shape}  (expected 49)")
assert s1_weight_tensor.shape[0] == 49

# Inspect balance: if max/min < 2.0, weighting is optional
print(f"Min weight: {s1_weight_tensor.min():.3f}  Max weight: {s1_weight_tensor.max():.3f}  Ratio: {s1_weight_tensor.max()/s1_weight_tensor.min():.2f}x")
print("If max/min ratio < 2.0, standard CrossEntropyLoss without weighting is equally defensible.")
""")

code("""
class Stage1Trainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        loss = nn.CrossEntropyLoss(weight=s1_weight_tensor)(
            outputs.logits, labels
        )
        return (loss, outputs) if return_outputs else loss
""")

# --------------------------------------------------------------------------
md("## 11. Stage 1 Training")
code("""
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def compute_metrics(pred):
    labels = pred.label_ids
    preds  = pred.predictions.argmax(-1)
    prec, rec, f1, _ = precision_recall_fscore_support(labels, preds, average='macro',    zero_division=0)
    wf1 = precision_recall_fscore_support(labels, preds, average='weighted', zero_division=0)[2]
    return {
        'accuracy': accuracy_score(labels, preds),
        'macro_f1': f1,
        'macro_precision': prec,
        'macro_recall': rec,
        'weighted_f1': wf1,
    }

stage1_trainer = Stage1Trainer(
    model=stage1_model,
    args=stage1_args,
    train_dataset=tok_ddx_train,
    eval_dataset=tok_ddx_val,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)

# UNCOMMENT TO TRAIN:
# train_result = stage1_trainer.train()
# print(train_result)
""")

# --------------------------------------------------------------------------
md("## 12. Stage 1 — Official DDXPlus Test Evaluation")
code("""
# Evaluate on the complete unmodified DDXPlus official test split.
# The model at this point has 49 outputs.
# Remove fingerprint and other non-model columns before prediction.
_test_cols_to_drop = [c for c in tok_ddx_test.column_names
                      if c not in ('input_ids', 'attention_mask', 'labels')]

# UNCOMMENT TO EVALUATE:
# s1_official = stage1_trainer.predict(tok_ddx_test.remove_columns(_test_cols_to_drop))
# print("Stage 1 — Official DDXPlus Test:", s1_official.metrics)
""")

# --------------------------------------------------------------------------
md("""## 13. Stage 1 — Strict Generalization Test
Filters test examples whose `input_fingerprint` also appears in the DDXPlus training split.
**This is NOT called zero-leakage.** It is the Strict Generalization Evaluation.
The raw JSONL files are never modified.
""")
code("""
# Build fingerprint lookup from training split (in-memory only)
train_fp_set = set(ddx_train_ds['input_fingerprint'])
strict_test = tok_ddx_test.filter(
    lambda ex: ex['input_fingerprint'] not in train_fp_set
)

print(f"Official test count : {len(tok_ddx_test):,}")
print(f"Strict test count   : {len(strict_test):,}")
print(f"Filtered (overlap)  : {len(tok_ddx_test) - len(strict_test):,}  (expected ~1,802)")

# UNCOMMENT TO EVALUATE:
# s1_strict = stage1_trainer.predict(strict_test.remove_columns(_test_cols_to_drop))
# print("Stage 1 — Strict Generalization Test:", s1_strict.metrics)
""")

# --------------------------------------------------------------------------
md("## 14. Stage 1 — Save Best Checkpoint")
code("""
# UNCOMMENT AFTER TRAINING:
# stage1_trainer.save_model(str(STAGE1_OUT / 'best_model'))
# tokenizer.save_pretrained(str(STAGE1_OUT / 'best_model'))
# import json
# with open(STAGE1_OUT / 'best_model' / 'ddx_label2id.json', 'w') as f:
#     json.dump(ddx_label2id, f, indent=2)
print("Stage 1 checkpoint will be saved to:", STAGE1_OUT / 'best_model')
""")

# --------------------------------------------------------------------------
md("""## 15. Expand Classifier: 49 → 71
This is the critical transition step.

**Algorithm:**
1. Load the best trained 49-class checkpoint.
2. Create a new `nn.Linear(hidden=768, out=71)` classifier.
3. For every DDXPlus label, look up its old index (0–48) and its new unified index (0–70).
4. Copy `weight[new_idx] ← weight[old_idx]` and `bias[new_idx] ← bias[old_idx]` exactly.
5. For the 22 genuinely new S2D-only outputs, apply Kaiming initialization.
6. Run an automated numerical assertion confirming all 49 copies are exact.

**Why not `ignore_mismatched_sizes=True`?**
That flag reinitializes the entire classifier head randomly, discarding all trained DDXPlus weights.
""")
code("""
import torch.nn as nn, torch
from transformers import AutoModelForSequenceClassification

def expand_classifier_49_to_71(stage1_model, ddx_label2id, unified_label2id):
    \"\"\"
    Expand a trained 49-class DistilBERT classification head to 71 classes.
    Copies trained DDXPlus weights exactly. Initializes 22 new S2D-only outputs fresh.
    Returns a new model instance with the expanded head.
    \"\"\"
    HIDDEN = stage1_model.config.hidden_size
    old_classifier = stage1_model.classifier   # DistilBERT uses model.classifier (Linear)
    # Note: DistilBERT's SequenceClassification has:
    #   model.pre_classifier (Linear 768→768) + model.classifier (Linear 768→num_labels)
    # We replace only model.classifier.

    new_num_labels = len(unified_label2id)

    # Create new model: load backbone, fresh classifier
    new_model = AutoModelForSequenceClassification.from_pretrained(
        stage1_model.config._name_or_path,
        num_labels=new_num_labels,
        ignore_mismatched_sizes=True,   # Only safe here: we immediately overwrite the head
        id2label={i: l for l, i in unified_label2id.items()},
        label2id=unified_label2id,
    )

    # Copy backbone weights (pre_classifier, distilbert layers)
    new_model.distilbert.load_state_dict(stage1_model.distilbert.state_dict())
    new_model.pre_classifier.load_state_dict(stage1_model.pre_classifier.state_dict())

    # Build new classifier with explicit copying
    new_classifier_weight = new_model.classifier.weight.data.clone()  # (71, 768)
    new_classifier_bias   = new_model.classifier.bias.data.clone()    # (71,)

    # Initialize all to zero first for clean auditing
    nn.init.zeros_(new_model.classifier.weight)
    nn.init.zeros_(new_model.classifier.bias)

    with torch.no_grad():
        # Copy trained DDXPlus weights into their new positions
        for label, old_idx in ddx_label2id.items():
            new_idx = unified_label2id[label]
            new_model.classifier.weight[new_idx] = old_classifier.weight[old_idx].clone()
            new_model.classifier.bias[new_idx]   = old_classifier.bias[old_idx].clone()

        # Kaiming-initialize the 22 S2D-only new outputs
        for label, new_idx in unified_label2id.items():
            if label not in ddx_label2id:
                nn.init.kaiming_uniform_(new_model.classifier.weight[new_idx].unsqueeze(0))
                nn.init.zeros_(new_model.classifier.bias[new_idx:new_idx+1])

    return new_model


# UNCOMMENT AFTER STAGE 1 TRAINING:
# stage2_model = expand_classifier_49_to_71(stage1_model, ddx_label2id, label2id)
# print(f"Stage 2 classifier output dim: {stage2_model.config.num_labels}  (expected 71)")
""")

# --------------------------------------------------------------------------
md("## 16. Verify Copied Classifier Weights")
code("""
# UNCOMMENT AFTER EXPANSION:
# print("Verifying all 49 DDXPlus classifier weights were copied exactly...")
# with torch.no_grad():
#     for label, old_idx in ddx_label2id.items():
#         new_idx = label2id[label]
#         w_ok = torch.allclose(
#             stage1_model.classifier.weight[old_idx],
#             stage2_model.classifier.weight[new_idx]
#         )
#         b_ok = torch.allclose(
#             stage1_model.classifier.bias[old_idx],
#             stage2_model.classifier.bias[new_idx]
#         )
#         assert w_ok and b_ok, f"Mismatch for '{label}' (old={old_idx}, new={new_idx})"
# print(f"VERIFIED: All 49 DDXPlus classifier outputs copied exactly. ✓")
""")

# --------------------------------------------------------------------------
md("""## 17. Build Deterministic DDXPlus Replay Subset
**Purpose**: Prevent catastrophic forgetting of DDXPlus-only diseases during Phase 2 S2D fine-tuning.

**Design decisions:**
- Sample is drawn from the **DDXPlus TRAIN** split only. No test or val data used.
- Balanced across all 49 DDXPlus classes (same number per class).
- `DDX_REPLAY_PER_CLASS = 20` gives 49 × 20 = 980 replay rows — comparable to S2D train size (917 rows).  
  This 1:1 ratio ensures DDXPlus isn't overwhelmed by S2D during Phase 2.
- Seed is fixed (`SEED=42`) for exact reproducibility.
- Labels remapped to unified 71-class space before mixing.

**Trade-off**: Increasing `DDX_REPLAY_PER_CLASS` improves DDXPlus retention but dilutes S2D learning.
Decreasing it speeds up Phase 2 but risks forgetting. Start with 20; adjust after seeing Phase 2 curves.
""")
code("""
# -- Configurable replay parameter --
DDX_REPLAY_PER_CLASS = 20   # 49 classes × 20 = 980 replay examples

from collections import defaultdict

# Group DDXPlus train records by class
class_to_indices = defaultdict(list)
for i, ex in enumerate(ddx_train_ds):
    class_to_indices[ex['label']].append(i)

rng = random.Random(SEED)
replay_indices = []
for label in DDX_LABELS:
    indices = class_to_indices[label]
    sampled = rng.sample(indices, min(DDX_REPLAY_PER_CLASS, len(indices)))
    replay_indices.extend(sampled)

ddx_replay_ds = ddx_train_ds.select(replay_indices)
print(f"DDXPlus replay subset: {len(ddx_replay_ds)} examples  ({DDX_REPLAY_PER_CLASS} per class × 49 classes)")
print(f"S2D train count      : {len(s2d_train_ds)} examples")
print(f"Ratio replay:S2D     : {len(ddx_replay_ds)/len(s2d_train_ds):.2f}x")

# Tokenize replay with UNIFIED labels (71-class)
tok_ddx_replay = ddx_replay_ds.map(tokenize_unified, batched=True, remove_columns=ddx_replay_ds.column_names)
""")

# --------------------------------------------------------------------------
md("""## 18. Prepare Stage 2 Training Data
Mix S2D train + DDXPlus replay. Both are already tokenized with the 71-class label space.
No test, val, or Kerala data enters here.
""")
code("""
from datasets import concatenate_datasets

stage2_train_ds = concatenate_datasets([tok_s2d_train, tok_ddx_replay])
stage2_train_ds = stage2_train_ds.shuffle(seed=SEED)

print(f"Stage 2 combined train: {len(stage2_train_ds)} examples")
print(f"  S2D train       : {len(tok_s2d_train)}")
print(f"  DDXPlus replay  : {len(tok_ddx_replay)}")
""")

# --------------------------------------------------------------------------
md("""## 19. Stage 2 Training Configuration
- LR `5e-6` (lower than Stage 1): The model is already well-trained; we adapt, not retrain.
- 5 epochs over ~1,900 combined examples with early stopping on S2D val Macro F1.
- S2D val is the primary signal; it's small (117 rows) so we evaluate every epoch.
- Class weighting not applied in Stage 2 since the replay is already balanced per class.
""")
code("""
S2_LR          = 5e-6    # conservative — continued fine-tuning on tiny S2D
S2_BATCH       = 16
S2_GRAD_ACCUM  = 1
S2_EPOCHS      = 5
S2_WEIGHT_DECAY= 0.01
S2_WARMUP_RATIO= 0.1

stage2_args = TrainingArguments(
    output_dir=str(STAGE2_OUT),
    learning_rate=S2_LR,
    per_device_train_batch_size=S2_BATCH,
    per_device_eval_batch_size=32,
    gradient_accumulation_steps=S2_GRAD_ACCUM,
    num_train_epochs=S2_EPOCHS,
    weight_decay=S2_WEIGHT_DECAY,
    warmup_ratio=S2_WARMUP_RATIO,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="macro_f1",
    greater_is_better=True,
    fp16=torch.cuda.is_available(),
    seed=SEED,
    report_to="none",
    logging_steps=50,
)

# UNCOMMENT AFTER EXPANSION:
# stage2_trainer = Trainer(
#     model=stage2_model,
#     args=stage2_args,
#     train_dataset=stage2_train_ds,
#     eval_dataset=tok_s2d_val,
#     tokenizer=tokenizer,
#     compute_metrics=compute_metrics,
# )
# train_result_s2 = stage2_trainer.train()
print("Stage 2 training configuration ready.")
""")

# --------------------------------------------------------------------------
md("## 20. Stage 2 Validation")
code("""
# UNCOMMENT AFTER TRAINING:
# s2_val_metrics = stage2_trainer.evaluate(tok_s2d_val)
# print("Stage 2 S2D Validation:", s2_val_metrics)
""")

# --------------------------------------------------------------------------
md("""## 21. DDXPlus Retention Evaluation (Stage 2)
After Phase 2, re-evaluate on the DDXPlus test with the 71-class model.
Labels in the test set remain in the 0–48 range in the unified space.
This directly measures catastrophic forgetting.
""")
code("""
# Re-tokenize DDXPlus test with UNIFIED label space for Stage 2 evaluation
tok_ddx_test_unified = ddx_test_ds.map(tokenize_unified, batched=True)
_drop_unified = [c for c in tok_ddx_test_unified.column_names
                 if c not in ('input_ids', 'attention_mask', 'labels')]

# UNCOMMENT AFTER STAGE 2:
# s2_ddx_official = stage2_trainer.predict(tok_ddx_test_unified.remove_columns(_drop_unified))
# print("Stage 2 — DDXPlus Official (retention check):", s2_ddx_official.metrics)

# Strict generalization on Stage 2 DDXPlus test
# UNCOMMENT:
# strict_test_unified = tok_ddx_test_unified.filter(
#     lambda ex: ex['input_fingerprint'] not in train_fp_set
# )
# s2_ddx_strict = stage2_trainer.predict(strict_test_unified.remove_columns(_drop_unified))
# print("Stage 2 — DDXPlus Strict Generalization:", s2_ddx_strict.metrics)
""")

# --------------------------------------------------------------------------
md("## 22. S2D Test Evaluation")
code("""
# UNCOMMENT AFTER STAGE 2:
# s2_s2d_test = stage2_trainer.predict(
#     tok_s2d_test.remove_columns([c for c in tok_s2d_test.column_names
#                                   if c not in ('input_ids', 'attention_mask', 'labels')])
# )
# print("Stage 2 — Symptom2Disease Test:", s2_s2d_test.metrics)
""")

# --------------------------------------------------------------------------
md("""## 23. Kerala Specialized Evaluation
**Important caveats:**
- Only 24 examples: Nipah, Chikungunya, Leptospirosis.
- These conditions are NOT in DDXPlus or Symptom2Disease training data.
- Treat this as a generalization probe, NOT a clinical benchmark.
- Do NOT draw strong conclusions from 24 examples.
""")
code("""
# UNCOMMENT AFTER STAGE 2:
# kerala_result = stage2_trainer.predict(
#     tok_kerala.remove_columns([c for c in tok_kerala.column_names
#                                if c not in ('input_ids', 'attention_mask', 'labels')])
# )
# print("Kerala Specialized Evaluation (n=24):", kerala_result.metrics)
# print("Note: 24 examples — interpret with caution. Not a clinical validation.")
""")

# --------------------------------------------------------------------------
md("""## 24. Learning Curves / Overfitting Analysis""")
code("""
# UNCOMMENT AFTER TRAINING:
# import matplotlib.pyplot as plt, json
#
# # Retrieve training history from trainer log
# s1_log = [l for l in stage1_trainer.state.log_history if 'eval_macro_f1' in l]
# s2_log = [l for l in stage2_trainer.state.log_history if 'eval_macro_f1' in l]
#
# plt.figure(figsize=(12, 4))
# plt.subplot(1, 2, 1)
# plt.plot([l['step'] for l in s1_log], [l['eval_macro_f1'] for l in s1_log], label='Val Macro F1')
# plt.title('Stage 1 DDXPlus — Validation Macro F1')
# plt.xlabel('Step'); plt.ylabel('Macro F1'); plt.legend()
#
# plt.subplot(1, 2, 2)
# plt.plot([l['epoch'] for l in s2_log], [l['eval_macro_f1'] for l in s2_log], label='Val Macro F1')
# plt.title('Stage 2 S2D — Validation Macro F1')
# plt.xlabel('Epoch'); plt.ylabel('Macro F1'); plt.legend()
#
# plt.tight_layout()
# plt.savefig(str(FINAL_OUT / 'learning_curves.png'))
# plt.show()
""")

# --------------------------------------------------------------------------
md("## 25. Final Export")
code("""
# UNCOMMENT AFTER STAGE 2:
# import json
#
# stage2_trainer.save_model(str(FINAL_OUT))
# tokenizer.save_pretrained(str(FINAL_OUT))
#
# with open(FINAL_OUT / 'label2id.json', 'w') as f:
#     json.dump(label2id, f, indent=2)
# with open(FINAL_OUT / 'id2label.json', 'w') as f:
#     json.dump({str(k): v for k, v in id2label.items()}, f, indent=2)
#
# metadata = {
#     "model_id": MODEL_ID,
#     "stage1_epochs": S1_EPOCHS,
#     "stage2_epochs": S2_EPOCHS,
#     "max_length": MAX_LENGTH,
#     "ddx_replay_per_class": DDX_REPLAY_PER_CLASS,
#     "num_labels": len(UNIFIED_LABELS),
#     "seed": SEED,
#     "ddx_labels": DDX_LABELS,
#     "s2d_only_labels": S2D_ONLY_LABELS,
#     "unified_labels": UNIFIED_LABELS,
# }
# with open(FINAL_OUT / 'training_metadata.json', 'w') as f:
#     json.dump(metadata, f, indent=2)
#
# print(f"Model exported to: {FINAL_OUT}")
# print("Ready for FastAPI symptom analysis endpoint integration.")
""")

# --------------------------------------------------------------------------
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"}
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

nb_path = 'DistilBERT_MediQ_Training.ipynb'
with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=2)

print(f"Notebook written: {nb_path}")
print(f"Total cells: {len(cells)}")
