# Low-pT J/psi (pT >= 0) OniaTree on Run2026C ParkingDoubleMuonLowMass AOD

Branch `CMSSW_16_0_X_lowpTJpsi2026`, based on `CMSSW_16_1_X`, adapted to run in
**CMSSW_16_0_7** on the 2026 pp parking **AOD** (no MiniAOD, no pT cut anywhere).

Feasibility report (plots, yields, trigger study):
https://sqian.web.cern.ch/check_low_pT_jpsi

What this branch adds on top of `CMSSW_16_1_X`:

| file | what |
|---|---|
| `HiSkim/HiOnia2MuMu/python/onia2MuMuPAT_cff.py` | patched: `HLT_FULL_cff` (gone in 16_0_X) replaced by SteppingHelix propagator clones under the `hltESP*` names |
| `HiAnalysis/HiOnia/test/oniatree_pp2026_ParkingDoubleMuonLowMass_AOD_cfg.py` | pp 2026 AOD config: era `Run3_2026`, GT `auto:run3_data_prompt`, pp HLT collections restored, `GlbOrTrk` muons, dimuon `2.0<m<4.5 && OS`, **no pT cut**, 2026C trigger list (verified on file) |
| `HiAnalysis/HiOnia/test/crabConfig_lowpTJpsi_2026C_AOD.py` | CRAB template: PD0 AOD, EventAwareLumiBased 200k evts/job, muon-cert JSON `401624_403937`, output to `T3_CH_CERNBOX` |
| `analysis/sweights_jpsi.py` | best-candidate-per-event, CB+expo mass fit, `RooStats::SPlot` -> sWeighted J/psi pT spectrum + low-pT / rapidity slice fits |
| `analysis/analyze_oniatree.py` | counting cross-check: sideband-subtracted yields per pT bin + per-candidate trigger-bit table |

## Setup

```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
scram project CMSSW CMSSW_16_0_7        # el9_amd64_gcc13
cd CMSSW_16_0_7/src && cmsenv

git clone -b CMSSW_16_0_X_lowpTJpsi2026 https://github.com/DickyChant/OniaTreeSubmodule .
# (or clone elsewhere and copy HiAnalysis HiSkim HeavyIonsAnalysis into src/)

scram b -j 12
```

## Run locally

```bash
cd HiAnalysis/HiOnia/test
cmsRun oniatree_pp2026_ParkingDoubleMuonLowMass_AOD_cfg.py maxEvents=10000 nThreads=4 \
    inputFiles=file:/eos/cms/store/data/Run2026C/ParkingDoubleMuonLowMass0/AOD/PromptReco-v1/000/402/536/00000/9fa9dfcc-4c0a-41f9-b582-397bc788a152.root
```

Throughput ~60 Hz with 4 threads; one 19k-event file takes ~10 min.

## CRAB

```bash
voms-proxy-init -voms cms -rfc --valid 168:00
source /cvmfs/cms.cern.ch/common/crab-setup.sh
cd HiAnalysis/HiOnia/test
python3 crabConfig_lowpTJpsi_2026C_AOD.py      # DRYRUN flag inside
```

Only `/ParkingDoubleMuonLowMass0/Run2026C-PromptReco-v1/AOD` exists as AOD (4672 files, 16 TB,
~120M events => ~600 jobs at 200k evts/job). PDs 1-7 are MINIAOD/NANOAOD only.

## Analysis on the trees

```bash
python3 analysis/sweights_jpsi.py myprefix Oniatree*.root   # mass fit + sPlot pT spectrum + slice fits
python3 analysis/analyze_oniatree.py Oniatree*.root         # counting + trigger-bit cross-check
```

Headline numbers from 282k events (run 402536): N(J/psi) = 25856 +- 179 (sigma_m = 36 MeV);
sWeighted yields pT 1-2 GeV: 65.6 +- 15.9, pT 2-3: 92.1 +- 18.1, pT < 1: 7.0 +- 6.6;
low-pT signal concentrated at |y| > 1.6 (pT<3 forward: 143.1 +- 22.0, ~6.5 sigma).

## MiniAOD variant (this branch)

`HiAnalysis/HiOnia/test/oniatree_pp2026_ParkingDoubleMuonLowMass_MiniAOD_cfg.py` runs the
identical zero-pT-cut selection on MINIAOD (slimmedMuons via `changeToMiniAOD()`), e.g. for
PDs 1-7 which have no AOD tier.

Measured on the same run 402536 (282,137 events) against the AOD workflow:

| quantity | AOD | MiniAOD | Mini/AOD |
|---|---|---|---|
| N(J/psi) total | 25856 +- 179 | 25725 +- 176 | 0.995 |
| sWeighted pT 2-3 GeV | 92.1 +- 18.1 | 92.3 +- 15.8 | 1.00 |
| sWeighted pT 1-2 GeV | 65.6 +- 15.9 | 43.8 +- 12.5 | 0.67 |
| slice fit pT < 1 GeV | 7.3 +- 6.2 | 2.9 +- 3.7 | ~0.4 (low stats) |
| slice fit pT < 3, \|y\| > 1.6 | 143.1 +- 22.0 | 116.0 +- 18.2 | 0.81 |

Cause: MiniAOD slimming keeps only PF muons below 3 GeV
(`pt>5 || isPFMuon || (pt>3 && (isGlobalMuon || isStandAloneMuon || numberOfMatches>0 || RPCMuLoose))`),
so non-PF tracker muons from very soft J/psi daughters are dropped. MiniAOD is fine down to
~2 GeV (with even less combinatorial background); below that AOD is the gold standard.

Single-muon level (`analysis/compare_muon_pt.py`): Mini/AOD muon ratio is exactly 1.000
above the pT=3 GeV slimming threshold, ~0.64 at 1-2 GeV (PF-only region), ~0.90 at 2-3 GeV;
J/psi daughters (dimuon pT<3) lose ~half the muons at 1.25-2 GeV.

## High-statistics MiniAOD campaign (41.3M events, all 8 PDs)

With `lowPtPreFilter=1` (3.7 kHz aggregate on a 12-core desktop), 41.3M events of 2026C
MiniAOD across all 8 PDs gave N(J/psi) = 157248 +- 756 in the prefiltered tree:
pT 1-2 GeV: 4915 +- 151 (33 sigma); pT 2-3: 14056 +- 199; pT<3 forward |y|>1.6:
18229 +- 248; central: 437 +- 56 (7.9 sigma); **pT < 1 GeV: 31 +- 54 — consistent with
zero** (rate < ~3 J/psi per M events at 95% CL). Conclusion: MiniAOD fully recovers
pT 1-3 GeV with statistics, but pT < 1 GeV needs AOD (no PF-only slimming) and/or a
dedicated trigger.
