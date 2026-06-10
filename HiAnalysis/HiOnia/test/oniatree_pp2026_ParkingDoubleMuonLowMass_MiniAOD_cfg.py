import FWCore.ParameterSet.Config as cms
import FWCore.ParameterSet.VarParsing as VarParsing
from Configuration.StandardSequences.Eras import eras

#----------------------------------------------------------------------------
# OniaTree on 2026 pp data, ParkingDoubleMuonLowMass MINIAOD (PromptReco)
# Same selection as the AOD config (NO pT cut) to compare the low-pT J/psi
# reach of slimmedMuons vs AOD reco::Muon.
# NB: slimmedMuons keep cut in 16_0_X:
#   pt>5 || isPFMuon || (pt>3 && (isGlobalMuon || isStandAloneMuon || numberOfMatches>0 || RPCMuLoose))
# i.e. below 3 GeV only PF muons survive the slimming.
#----------------------------------------------------------------------------

HLTProcess     = "HLT"
isMC           = False
muonSelection  = "GlbOrTrk"  # loose: tracker OR global muons, needed for pT(J/psi) -> 0
applyCuts      = False
OnlySoftMuons  = False
doTrimuons     = False
doDimuonTrk    = False
atLeastOneCand = False
OneMatchedHLTMu = -1
keepExtraColl  = False
miniAOD        = True        # input is MiniAOD: slimmedMuons via MuonUnpacker
UsePropToMuonSt = True       # L1-propagated muon coordinates (miniAOD only)
pdgId          = 443
useMomFormat   = "vector"

process = cms.Process("HIOnia", eras.Run3_2026)

options = VarParsing.VarParsing('analysis')
options.register('nThreads', 1, VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.int,
                 "number of threads/streams (keep 1 for CRAB unless JobType.numCores matches)")
options.inputFiles = [
    'file:/eos/cms/store/data/Run2026C/ParkingDoubleMuonLowMass0/MINIAOD/PromptReco-v1/000/402/536/00000/b7874954-503b-4f93-9a65-7b98cf3566e4.root',
]
options.outputFile = 'Oniatree_pp2026C_ParkingDoubleMuonLowMass0_MiniAOD.root'
options.maxEvents = -1
options.parseArguments()

# Same trigger list as the AOD config (verified on the Run2026C menu)
triggerList = {
    'DoubleMuonTrigger': cms.vstring(
        "HLT_DoubleMu4_3_LowMass_v",                # 0  parking workhorse
        "HLT_DoubleMu4_LowMass_Displaced_v",        # 1
        "HLT_DoubleMu2_Jpsi_LowPt_v",               # 2  low-pT J/psi
        "HLT_Dimuon0_LowMass_Inclusive_v",          # 3  inclusive, dimuon pT >= 0
        "HLT_Dimuon0_LowMass_v",                    # 4
        "HLT_Dimuon0_LowMass_L1_0er1p5_v",          # 5
        "HLT_Dimuon0_LowMass_L1_4_v",               # 6
        "HLT_Dimuon0_LowMass_L1_TM530_v",           # 7
        "HLT_Mu0_L1DoubleMu_v",                     # 8  fully open dimuon
        "HLT_Mu4_L1DoubleMu_v",                     # 9
        "HLT_Dimuon0_Jpsi_v",                       # 10
        "HLT_Dimuon0_Jpsi_NoVertexing_v",           # 11
        "HLT_Dimuon25_Jpsi_v",                      # 12 inclusive J/psi
        "HLT_Dimuon18_PsiPrime_v",                  # 13
        "HLT_DoubleMu4_3_Jpsi_v",                   # 14
        "HLT_DoubleMu4_Jpsi_Displaced_v",           # 15
        "HLT_DoubleMu4_JpsiTrkTrk_Displaced_v",     # 16
        "HLT_DoubleMu4_JpsiTrk_Bc_v",               # 17
        "HLT_Dimuon0_Jpsi3p5_Muon2_v",              # 18
        "HLT_DoubleMu2_Jpsi_DoubleTrk1_Phi1p05_v",  # 19
    ),
    'SingleMuonTrigger': cms.vstring(
        "HLT_Mu0_Barrel_v",
        "HLT_Mu0_Barrel_L1HP6_v",
        "HLT_Mu4_Barrel_IP4_v",
        "HLT_IsoMu24_v",
    ),
}

globalTag = 'auto:run3_data_prompt'

#----------------------------------------------------------------------------

process.load('Configuration.StandardSequences.Reconstruction_cff')
process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.Geometry.GeometryDB_cff')
process.load('Configuration.StandardSequences.MagneticField_38T_cff')

process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, globalTag, '')

#----------------------------------------------------------------------------

from HiAnalysis.HiOnia.oniaTreeAnalyzer_cff import oniaTreeAnalyzer
oniaTreeAnalyzer(process,
                 muonTriggerList=triggerList, HLTProName=HLTProcess,
                 muonSelection=muonSelection, L1Stage=2, isMC=isMC, pdgID=pdgId,
                 outputFileName=options.outputFile, doTrimu=doTrimuons,
                 OnlySingleMuons=False)

# pp data: undo the PbPb (PPOnAA) HLT muon collections hard-coded in HiSkim cff
process.muonMatchHLTL2.matchedCuts = cms.string('coll("hltL2MuonCandidates")')
process.muonMatchHLTL3.matchedCuts = cms.string('coll("hltIterL3MuonCandidates")')
process.patTrigger.collections = cms.vstring(
    [c for c in process.patTrigger.collections if 'PPOnAA' not in c])

# Single-muon selection: NO pT cut, just quality/geometry (same as AOD config)
process.onia2MuMuPatGlbGlb.lowerPuritySelection = cms.string(
    "(isGlobalMuon || isTrackerMuon) && abs(eta) < 2.4"
    " && abs(innerTrack.dxy) < 4 && abs(innerTrack.dz) < 35")
process.onia2MuMuPatGlbGlb.higherPuritySelection = cms.string("")

# Dimuon selection: J/psi (+psi') mass region, opposite sign, NO pT cut
process.onia2MuMuPatGlbGlb.dimuonSelection = cms.string(
    "2.0 < mass && mass < 4.5 && charge==0"
    " && abs(daughter('muon1').innerTrack.dz - daughter('muon2').innerTrack.dz) < 25")
process.onia2MuMuPatGlbGlb.LateDimuonSel = cms.string("userFloat(\"vProb\")>0.001")
process.onia2MuMuPatGlbGlb.onlySoftMuons = cms.bool(OnlySoftMuons)

process.hionia.minimumFlag      = cms.bool(keepExtraColl)
process.hionia.useGeTracks      = cms.untracked.bool(keepExtraColl)
process.hionia.fillRecoTracks   = cms.bool(keepExtraColl)
process.hionia.SofterSgMuAcceptance = cms.bool(True)
process.hionia.SumETvariables   = cms.bool(False)
process.hionia.applyCuts        = cms.bool(applyCuts)
process.hionia.AtLeastOneCand   = cms.bool(atLeastOneCand)
process.hionia.OneMatchedHLTMu  = cms.int32(OneMatchedHLTMu)
process.hionia.checkTrigNames   = cms.bool(False)
process.hionia.mom4format       = cms.string(useMomFormat)
process.hionia.isHI             = cms.untracked.bool(False)

process.oniaTreeAna = cms.Path(process.oniaTreeAna)

if miniAOD:
    from HiSkim.HiOnia2MuMu.onia2MuMuPAT_cff import changeToMiniAOD
    changeToMiniAOD(process)
    process.unpackedMuons.addPropToMuonSt = cms.bool(UsePropToMuonSt)

#----------------------------------------------------------------------------

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring(options.inputFiles),
)
process.TFileService = cms.Service("TFileService",
    fileName = cms.string(options.outputFile),
)
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(options.maxEvents))
process.options.wantSummary = cms.untracked.bool(True)
process.options.numberOfThreads = options.nThreads
process.options.numberOfStreams = options.nThreads

process.schedule = cms.Schedule(process.oniaTreeAna)
