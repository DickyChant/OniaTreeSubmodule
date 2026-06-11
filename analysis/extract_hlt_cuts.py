#!/usr/bin/env python3
"""Extract muon pT / mass cuts from the HLT menu dump for the low-mass dimuon paths."""
import re

MENU = "/home/sqian/Codes/check_lowpT_jpsi/run/hlt_menu_402536.py"
PATHS = [
    "HLT_Dimuon0_LowMass_Inclusive_v2",
    "HLT_Dimuon0_LowMass_v26",
    "HLT_Dimuon0_LowMass_L1_0er1p5_v26",
    "HLT_Dimuon0_LowMass_L1_4_v26",
    "HLT_Dimuon0_Jpsi_v26",
    "HLT_Mu0_L1DoubleMu_v19",
    "HLT_DoubleMu2_Jpsi_LowPt_v12",
    "HLT_DoubleMu4_3_LowMass_v19",
]
KEYS = ("L1SeedsLogicalExpression", "MinPtMax", "MinPtMin", "MinPtPair", "MinPt ",
        "MinInvMass", "MaxInvMass", "MaxEta", "MinNhits", "MaxDr ", "MinVtxProb",
        "ChargeOpt", "inputCandCollection")

text = open(MENU).read()

# module definition blocks: process.NAME = cms.EDFilter("TYPE", ... ) up to closing line ")"
def get_block(name):
    m = re.search(r"^process\.%s = cms\.(EDFilter|EDProducer)\( \"(\w+)\"(.*?)^\)" % re.escape(name),
                  text, re.M | re.S)
    return (m.group(2), m.group(3)) if m else (None, "")

for p in PATHS:
    m = re.search(r"^process\.%s = cms\.Path\( (.*?) \)$" % re.escape(p), text, re.M)
    if not m:
        print("== %s: NOT FOUND" % p)
        continue
    mods = re.findall(r"process\.(hlt\w+)", m.group(1))
    print("=" * 70)
    print("== " + p)
    for mod in mods:
        typ, body = get_block(mod)
        if typ is None:
            continue
        if not (("L1s" in mod) or ("Filter" in typ) or typ.startswith("HLTMuon") or "Displaced" in typ):
            continue
        lines = []
        for k in KEYS:
            for mm in re.finditer(r"(%s\w*) = cms\.\w+\( ([^)]*) \)" % k.strip(), body):
                lines.append("%s=%s" % (mm.group(1), mm.group(2).strip()[:70]))
        if lines:
            print("  %-52s %s" % (mod + " [" + typ + "]", ""))
            for ln in sorted(set(lines)):
                print("      " + ln)
