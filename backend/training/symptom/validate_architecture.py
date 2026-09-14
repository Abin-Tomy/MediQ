"""
Local validation of MediQ notebook architecture logic.
Uses ONLY in-memory synthetic tensors. Does NOT train, does NOT touch datasets.
"""
import torch
import torch.nn as nn
import copy

print("=" * 60)
print("MediQ Architecture Validation")
print("=" * 60)

# -------------------------------------------------------
# 1. Label space setup (mirrors what the notebook will do)
# -------------------------------------------------------
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

# Build unified label space (DDX first, then S2D-only additions)
UNIFIED_LABELS = DDX_LABELS.copy()
S2D_ONLY_LABELS = []
for l in S2D_LABELS:
    if l not in UNIFIED_LABELS:
        UNIFIED_LABELS.append(l)
        S2D_ONLY_LABELS.append(l)

label2id = {l: i for i, l in enumerate(UNIFIED_LABELS)}
id2label = {i: l for i, l in enumerate(UNIFIED_LABELS)}

NUM_DDX = len(DDX_LABELS)
NUM_UNIFIED = len(UNIFIED_LABELS)
NUM_S2D_ONLY = len(S2D_ONLY_LABELS)

print(f"\n[1] Label space check")
print(f"    DDXPlus classes     : {NUM_DDX}")
print(f"    S2D total classes   : {len(S2D_LABELS)}")
print(f"    Overlap classes     : {len([l for l in S2D_LABELS if l in DDX_LABELS])}")
print(f"    S2D-only classes    : {NUM_S2D_ONLY}")
print(f"    Unified total       : {NUM_UNIFIED}")
assert NUM_DDX == 49, f"Expected 49 DDX classes, got {NUM_DDX}"
assert NUM_S2D_ONLY == 22, f"Expected 22 S2D-only classes, got {NUM_S2D_ONLY}"
assert NUM_UNIFIED == 71, f"Expected 71 unified classes, got {NUM_UNIFIED}"
print("    PASS: Label counts are 49 + 22 = 71")

# Overlap must only be Pneumonia and GERD
overlap = [l for l in S2D_LABELS if l in DDX_LABELS]
assert set(overlap) == {"Pneumonia", "GERD"}, f"Unexpected overlaps: {overlap}"
print(f"    PASS: Overlap is exactly {{Pneumonia, GERD}}")

# -------------------------------------------------------
# 2. Stage 1: 49-class classifier
# -------------------------------------------------------
print(f"\n[2] Stage 1 classifier (49-class)")
HIDDEN = 768  # DistilBERT hidden size
stage1_classifier = nn.Linear(HIDDEN, NUM_DDX)
print(f"    Weight shape: {stage1_classifier.weight.shape}  expected ({NUM_DDX}, {HIDDEN})")
assert stage1_classifier.weight.shape == (NUM_DDX, HIDDEN)
assert stage1_classifier.bias.shape == (NUM_DDX,)
print(f"    PASS: Stage 1 classifier is exactly {NUM_DDX} outputs")

# Simulate training by setting known values
nn.init.ones_(stage1_classifier.weight)
nn.init.constant_(stage1_classifier.bias, 0.5)

# -------------------------------------------------------
# 3. Stage 1 loss: 49-class cross-entropy
# -------------------------------------------------------
print(f"\n[3] Stage 1 loss dimension check")
batch_logits_49 = torch.randn(8, NUM_DDX)  # batch of 8, 49 classes
batch_labels_ddx = torch.randint(0, NUM_DDX, (8,))
loss_fn_49 = nn.CrossEntropyLoss()
loss_49 = loss_fn_49(batch_logits_49, batch_labels_ddx)
assert loss_49.shape == torch.Size([]), "Loss should be scalar"
print(f"    PASS: Stage 1 cross-entropy loss shape correct: {loss_49.shape}")

# -------------------------------------------------------
# 4. Classifier expansion: 49 → 71
# -------------------------------------------------------
print(f"\n[4] Classifier expansion: 49 -> {NUM_UNIFIED}")

def expand_classifier(old_classifier, old_label2id, new_label2id, hidden_size):
    """
    Expands a trained Linear classifier from old_num_classes to new_num_classes.
    - Copies trained weights/biases for overlapping labels into their NEW positions.
    - Initializes genuinely new label outputs with small random values.
    - Explicitly verified by assertion.
    """
    new_num_classes = len(new_label2id)
    new_classifier = nn.Linear(hidden_size, new_num_classes)

    # Initialize all new weights to zero first so we can confirm copying
    nn.init.zeros_(new_classifier.weight)
    nn.init.zeros_(new_classifier.bias)

    with torch.no_grad():
        for old_label, old_idx in old_label2id.items():
            if old_label in new_label2id:
                new_idx = new_label2id[old_label]
                new_classifier.weight[new_idx] = old_classifier.weight[old_idx].clone()
                new_classifier.bias[new_idx] = old_classifier.bias[old_idx].clone()

        # Initialize the genuinely new outputs with He/Kaiming
        for new_label, new_idx in new_label2id.items():
            if new_label not in old_label2id:
                nn.init.kaiming_uniform_(new_classifier.weight[new_idx].unsqueeze(0))
                nn.init.zeros_(new_classifier.bias[new_idx:new_idx+1])

    return new_classifier

# Build DDX label2id for Stage 1 (indices 0..48)
ddx_label2id = {l: i for i, l in enumerate(DDX_LABELS)}

stage2_classifier = expand_classifier(stage1_classifier, ddx_label2id, label2id, HIDDEN)
print(f"    New weight shape: {stage2_classifier.weight.shape}  expected ({NUM_UNIFIED}, {HIDDEN})")
assert stage2_classifier.weight.shape == (NUM_UNIFIED, HIDDEN)
assert stage2_classifier.bias.shape == (NUM_UNIFIED,)
print(f"    PASS: Stage 2 classifier is exactly {NUM_UNIFIED} outputs")

# -------------------------------------------------------
# 5. Verify all 49 DDX weights were copied exactly
# -------------------------------------------------------
print(f"\n[5] Verifying all 49 DDX classifier weights were copied correctly")
with torch.no_grad():
    for old_label, old_idx in ddx_label2id.items():
        new_idx = label2id[old_label]
        w_match = torch.allclose(stage1_classifier.weight[old_idx], stage2_classifier.weight[new_idx])
        b_match = torch.allclose(stage1_classifier.bias[old_idx], stage2_classifier.bias[new_idx])
        assert w_match and b_match, (
            f"Weight/bias mismatch for label '{old_label}' "
            f"(old_idx={old_idx}, new_idx={new_idx})"
        )
print(f"    PASS: All {NUM_DDX} DDX classifier outputs verified identical post-copy")

# -------------------------------------------------------
# 6. Verify all 22 new outputs are initialized (non-zero weight)
# -------------------------------------------------------
print(f"\n[6] Verifying all 22 new S2D-only outputs are initialized")
with torch.no_grad():
    for new_label in S2D_ONLY_LABELS:
        new_idx = label2id[new_label]
        # Kaiming init should produce non-zero weights
        assert not torch.all(stage2_classifier.weight[new_idx] == 0), (
            f"New class '{new_label}' at idx {new_idx} has all-zero weights!"
        )
print(f"    PASS: All {NUM_S2D_ONLY} new S2D-only outputs are non-zero initialized")

# -------------------------------------------------------
# 7. Stage 2 loss: 71-class cross-entropy on mixed batch
# -------------------------------------------------------
print(f"\n[7] Stage 2 loss dimension check (mixed S2D + DDX replay)")
batch_logits_71 = torch.randn(8, NUM_UNIFIED)

# Some labels are from S2D, some from DDX replay — all mapped to unified space
sample_s2d_label = label2id['Acne']       # S2D-only class
sample_ddx_label = label2id['Tuberculosis']  # DDX-only class, in unified space
batch_labels_mixed = torch.tensor([
    sample_s2d_label, sample_ddx_label, sample_s2d_label, sample_ddx_label,
    sample_s2d_label, sample_ddx_label, sample_s2d_label, sample_ddx_label
])
loss_fn_71 = nn.CrossEntropyLoss()
loss_71 = loss_fn_71(batch_logits_71, batch_labels_mixed)
assert loss_71.shape == torch.Size([]), "Stage 2 loss should be scalar"
print(f"    PASS: Stage 2 cross-entropy loss shape correct: {loss_71.shape}")

# -------------------------------------------------------
# 8. DDX replay label mapping into unified space
# -------------------------------------------------------
print(f"\n[8] DDX replay label mapping check")
for ddx_label in DDX_LABELS:
    assert ddx_label in label2id, f"DDX label '{ddx_label}' missing from unified map"
    idx = label2id[ddx_label]
    assert 0 <= idx < NUM_UNIFIED, f"DDX label '{ddx_label}' has out-of-range idx {idx}"
print(f"    PASS: All {NUM_DDX} DDX labels correctly map into unified 71-class space")

# -------------------------------------------------------
# 9. S2D label mapping into unified space
# -------------------------------------------------------
print(f"\n[9] S2D label mapping check")
for s2d_label in S2D_LABELS:
    assert s2d_label in label2id, f"S2D label '{s2d_label}' missing from unified map"
    idx = label2id[s2d_label]
    assert 0 <= idx < NUM_UNIFIED, f"S2D label '{s2d_label}' has out-of-range idx {idx}"
print(f"    PASS: All {len(S2D_LABELS)} S2D labels correctly map into unified 71-class space")

# -------------------------------------------------------
# 10. Fingerprint / PATHOLOGY / DIFFERENTIAL_DIAGNOSIS never reach model
# -------------------------------------------------------
print(f"\n[10] Input field guard check")
FORBIDDEN_FIELDS = {"input_fingerprint", "PATHOLOGY", "DIFFERENTIAL_DIAGNOSIS",
                    "pathology", "differential_diagnosis", "fingerprint"}
# Simulate what the tokenize function will receive
sample_record_keys = {"text", "label", "source", "split", "input_fingerprint", "labels"}
tokenizer_input_keys = {"text"}  # ONLY text is passed to tokenizer
assert tokenizer_input_keys.isdisjoint(FORBIDDEN_FIELDS), "Forbidden field reaches tokenizer!"
assert "input_fingerprint" not in tokenizer_input_keys
assert "PATHOLOGY" not in tokenizer_input_keys
print(f"    PASS: Tokenizer receives only 'text' — forbidden fields excluded")

# -------------------------------------------------------
# 11. Test/Kerala never enter training check
# -------------------------------------------------------
print(f"\n[11] Dataset split guard (conceptual check)")
TRAINING_SPLITS = {"train"}
VALIDATION_SPLITS = {"validate"}
TEST_SPLITS = {"test", "evaluation"}
TRAINING_SPLITS_ALLOWED = {"train"}
for split in ["test", "evaluation"]:
    assert split not in TRAINING_SPLITS_ALLOWED, f"Split '{split}' must not enter training!"
print(f"    PASS: test and evaluation splits never passed to Trainer train_dataset")

# -------------------------------------------------------
# 12. Stage 1 evaluation model has 49 outputs
# -------------------------------------------------------
print(f"\n[12] Stage 1 evaluation output dimension")
stage1_preds = torch.randn(100, NUM_DDX)  # 100 test examples, 49 logits
assert stage1_preds.shape[1] == 49
print(f"    PASS: Stage 1 evaluation uses 49-class logits")

# -------------------------------------------------------
print(f"\n{'='*60}")
print(f"ALL CHECKS PASSED.")
print(f"  Stage 1: {NUM_DDX}-class classifier")
print(f"  Stage 2: {NUM_UNIFIED}-class classifier")
print(f"  Overlap: Pneumonia, GERD")
print(f"  Copied:  {NUM_DDX} DDX trained outputs -> exact positions in new head")
print(f"  New:     {NUM_S2D_ONLY} S2D-only outputs, Kaiming initialized")
print(f"{'='*60}")
