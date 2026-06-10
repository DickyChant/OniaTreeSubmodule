"""CRAB submission for the low-pT J/psi OniaTree over Run2026C ParkingDoubleMuonLowMass AOD.

Usage (from this directory, after cmsenv + voms-proxy-init + crab-setup.sh):
    python3 crabConfig_lowpTJpsi_2026C_AOD.py            # submit all datasets in dataMap
Set DRYRUN = True below for a test round-trip without real submission.

Only ParkingDoubleMuonLowMass0 has an AOD tier for Run2026C (checked on EOS, June 2026);
add more entries to dataMap when more AOD appears (e.g. Run2026D) or for a re-reco.
"""
from CRABAPI.RawCommand import crabCommand
from CRABClient.ClientExceptions import ClientException
from http.client import HTTPException

from CRABClient.UserUtilities import config, getUsername

config = config()
username = getUsername()

DRYRUN = False
TAG = 'lowpTJpsi_noPtCut_20260611'   # bump the date when resubmitting

##########################

config.section_("General")
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True
config.General.transferLogs = False

config.section_("JobType")
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'oniatree_pp2026_ParkingDoubleMuonLowMass_AOD_cfg.py'
config.JobType.pyCfgParams = ['nThreads=1']   # must match numCores below
config.JobType.numCores = 1
config.JobType.maxMemoryMB = 2500
config.JobType.maxJobRuntimeMin = 1000
config.JobType.allowUndistributedCMSSW = True

config.section_("Data")
config.Data.inputDBS = 'global'
# ~200k events/job ≈ 2h at the measured ~30 Hz/core (PAT muons + vertexing on AOD)
config.Data.splitting = 'EventAwareLumiBased'
config.Data.unitsPerJob = 200000
config.Data.publication = False
config.Data.allowNonValidInputDataset = True
# Muon certification (tracker+muon good) is what a J/psi->mumu check needs;
# switch to ..._golden.json for the full-detector selection.
config.Data.lumiMask = ('https://cms-service-dqmdc.web.cern.ch/CAF/certification/'
                        'Collisions26/Cert_Collisions2026_401624_403937_muon.json')
# config.Data.runRange = '402536-403937'   # optional further restriction
config.Data.outLFNDirBase = '/store/user/%s/lowpTJpsi/Run2026C/' % username

config.section_("Site")
config.Site.storageSite = 'T3_CH_CERNBOX'   # output to your CERNBox EOS
# config.Site.storageSite = 'T2_CH_CERN'    # alternative if you have group quota
# config.Data.ignoreLocality = True; config.Site.whitelist = ['T2_*','T1_*']  # only if needed

##########################

dataMap = {
    'ParkingDoubleMuonLowMass0_Run2026C_AOD': {
        'PD': '/ParkingDoubleMuonLowMass0/Run2026C-PromptReco-v1/AOD',
    },
    # only PD0 has AOD for Run2026C; PDs 1-7 are MINIAOD/NANOAOD only
}


def submit(cfg):
    try:
        crabCommand('submit', config=cfg, dryrun=DRYRUN)
    except HTTPException as hte:
        print("Failed submitting task: %s" % (hte.headers))
    except ClientException as cle:
        print("Failed submitting task: %s" % (cle))


for key, val in dataMap.items():
    config.General.requestName = '%s_%s' % (key, TAG)
    config.Data.inputDataset = val['PD']
    config.Data.outputDatasetTag = config.General.requestName
    print("Submitting CRAB task for: " + val['PD'])
    submit(config)
