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
