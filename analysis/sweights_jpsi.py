#!/usr/bin/env python3
"""sPlot extraction of the J/psi pT spectrum from OniaTree (2026C ParkingDoubleMuonLowMass AOD).

Per event: keep the BEST candidate (highest vertex prob) among OS dimuons with
vProb>0.01 in 2.6<m<3.5. Fit mass with CB + Chebychev(2), then RooStats::SPlot
sWeights -> signal-weighted dimuon pT spectrum (no pT cut anywhere, down to 0).

Usage: python3 sweights_jpsi.py <out_prefix> <input1.root> [input2.root ...]
"""
import sys
import math
import ctypes
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

prefix = sys.argv[1]
files = sys.argv[2:]

M_LO, M_HI = 2.6, 3.5

ch = ROOT.TChain("hionia/myTree")
for f in files:
    ch.Add(f)
nev = ch.GetEntries()
print("Files: %d  Events: %d" % (len(files), nev))

mass = ROOT.RooRealVar("mass", "m_{#mu#mu}", M_LO, M_HI, "GeV")
pt = ROOT.RooRealVar("pt", "p_{T}^{#mu#mu}", 0., 200., "GeV")
absy = ROOT.RooRealVar("absy", "|y|^{#mu#mu}", 0., 2.5)
data = ROOT.RooDataSet("data", "best J/psi candidates", ROOT.RooArgSet(mass, pt, absy))

# Flat skim input (from skim_bestcand.py): import via numpy, skip the event loop
# (the RooDataSet-from-TTree constructor was removed in ROOT 6.36)
_f0 = ROOT.TFile.Open(files[0])
if _f0.Get("bestcand"):
    _f0.Close()
    import numpy as np
    _arr = ROOT.RDataFrame("bestcand", files).AsNumpy(("mass", "pt", "absy"))
    _sel = _arr["pt"] < 200.
    _np = {k: v[_sel].astype(np.float64) for k, v in _arr.items()}
    data = ROOT.RooDataSet.from_numpy(_np, ROOT.RooArgSet(mass, pt, absy), name="data")
    nbest = data.numEntries()
    ch = None
else:
    _f0.Close()

nbest = 0 if ch is not None else nbest
for ev in (ch if ch is not None else []):
    best_i, best_vp = -1, -1.
    for i in range(ev.Reco_QQ_size):
        if ev.Reco_QQ_sign[i] != 0:
            continue
        vp = ev.Reco_QQ_VtxProb[i]
        if vp < 0.01:
            continue
        m = ev.Reco_QQ_4mom_m[i]
        if not (M_LO < m < M_HI):
            continue
        if vp > best_vp:
            best_vp, best_i = vp, i
    if best_i < 0:
        continue
    nbest += 1
    mass.setVal(ev.Reco_QQ_4mom_m[best_i])
    pt.setVal(ev.Reco_QQ_4mom_pt[best_i])
    absy.setVal(abs(ev.Reco_QQ_4mom_y[best_i]))
    data.add(ROOT.RooArgSet(mass, pt, absy))

print("Best candidates (1 per event): %d" % nbest)
if nbest < 100:
    print("WARNING: very low statistics, fit may be unreliable")

# ---- mass model: Crystal Ball + Chebychev(2) ----
m0 = ROOT.RooRealVar("m0", "m0", 3.097, 3.05, 3.15)
sigma = ROOT.RooRealVar("sigma", "sigma", 0.030, 0.012, 0.080)
alpha = ROOT.RooRealVar("alpha", "alpha", 1.6, 0.4, 5.0)
ncb = ROOT.RooRealVar("ncb", "ncb", 2.0, 0.5, 20.0)
sig = ROOT.RooCBShape("sig", "sig", mass, m0, sigma, alpha, ncb)

lam = ROOT.RooRealVar("lam", "lam", -0.5, -6.0, 6.0)
bkg = ROOT.RooExponential("bkg", "bkg", mass, lam)

nsig = ROOT.RooRealVar("nsig", "nsig", 0.3 * nbest, 0., 1.2 * nbest)
nbkg = ROOT.RooRealVar("nbkg", "nbkg", 0.7 * nbest, 0., 1.2 * nbest)
model = ROOT.RooAddPdf("model", "model", ROOT.RooArgList(sig, bkg),
                       ROOT.RooArgList(nsig, nbkg))

res = model.fitTo(data, ROOT.RooFit.Extended(True), ROOT.RooFit.Save(True),
                  ROOT.RooFit.PrintLevel(-1), ROOT.RooFit.NumCPU(4))
res.Print()
print("Nsig = %.1f +- %.1f   Nbkg = %.1f +- %.1f"
      % (nsig.getVal(), nsig.getError(), nbkg.getVal(), nbkg.getError()))
print("mean = %.4f GeV  sigma = %.1f MeV" % (m0.getVal(), 1000. * sigma.getVal()))

# ---- plot mass fit ----
c = ROOT.TCanvas("c", "", 900, 700)
fr = mass.frame(ROOT.RooFit.Bins(90), ROOT.RooFit.Title("best candidate / event"))
data.plotOn(fr)
model.plotOn(fr, ROOT.RooFit.LineColor(ROOT.kBlue))
model.plotOn(fr, ROOT.RooFit.Components("bkg"), ROOT.RooFit.LineStyle(ROOT.kDashed),
             ROOT.RooFit.LineColor(ROOT.kRed))
model.plotOn(fr, ROOT.RooFit.Components("sig"), ROOT.RooFit.LineStyle(ROOT.kDotted),
             ROOT.RooFit.LineColor(ROOT.kGreen + 2))
fr.Draw()
c.SaveAs(prefix + "_massfit.png")

# ---- sPlot: fix shape parameters, only yields float ----
for p in (m0, sigma, alpha, ncb, lam):
    p.setConstant(True)
sData = ROOT.RooStats.SPlot("sData", "sData", data, model, ROOT.RooArgList(nsig, nbkg))
print("sPlot check: sum(sw_sig) = %.1f (Nsig=%.1f), sum(sw_bkg) = %.1f (Nbkg=%.1f)"
      % (sData.GetYieldFromSWeight("nsig"), nsig.getVal(),
         sData.GetYieldFromSWeight("nbkg"), nbkg.getVal()))

# ---- sWeighted pT spectra ----
import array
edges_fine = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0,
              4.5, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 15.0, 20.0, 30.0, 50.0]
h_pt_sw = ROOT.TH1D("h_pt_sw", ";p_{T}^{#mu#mu} [GeV];sWeighted J/#psi yield",
                    len(edges_fine) - 1, array.array('d', edges_fine))
h_pt_sw.Sumw2()
h_pt_bkg = h_pt_sw.Clone("h_pt_bkg")
h_zoom = ROOT.TH1D("h_zoom", ";p_{T}^{#mu#mu} [GeV];sWeighted J/#psi yield / 0.2 GeV",
                   25, 0., 5.)
h_zoom.Sumw2()

for i in range(data.numEntries()):
    row = data.get(i)
    v = row.getRealValue("pt")
    ws = sData.GetSWeight(i, "nsig")
    wb = sData.GetSWeight(i, "nbkg")
    h_pt_sw.Fill(v, ws)
    h_pt_bkg.Fill(v, wb)
    h_zoom.Fill(v, ws)

print()
print("=== sWeighted J/psi yield in pT bins ===")
print("%-12s %14s" % ("pT [GeV]", "N_Jpsi (sW)"))
bins_report = [(0., 0.5), (0.5, 1.), (1., 2.), (2., 3.), (3., 5.), (5., 8.),
               (8., 15.), (15., 50.)]
for lo, hi in bins_report:
    b1, b2 = h_pt_sw.FindBin(lo + 1e-6), h_pt_sw.FindBin(hi - 1e-6)
    err = ctypes.c_double(0.)
    y = h_pt_sw.IntegralAndError(b1, b2, err)
    print("%-12s %9.1f +- %.1f" % ("%g-%g" % (lo, hi), y, err.value))

c.SetLogy(1)
h_pt_sw.SetLineColor(ROOT.kBlue + 1)
h_pt_sw.SetLineWidth(2)
h_pt_sw.SetMinimum(0.5)
h_pt_sw.Draw("e")
c.SaveAs(prefix + "_pt_sweighted.png")
c.SetLogy(0)
h_zoom.SetLineColor(ROOT.kRed + 1)
h_zoom.SetLineWidth(2)
h_zoom.Draw("e")
c.SaveAs(prefix + "_pt_sweighted_zoom0to5.png")

# ---- dedicated low-pT yield fits (shape fixed from global fit, yields float) ----
print()
print("=== Low-pT J/psi yields from mass fits in slices (shape fixed) ===")


def fit_subset(cut, label):
    sub = data.reduce(cut)
    n = sub.numEntries()
    if n < 15:
        print("%-34s: only %d candidates, skip fit" % (label, n))
        return
    ns = ROOT.RooRealVar("ns_" + label, "", 0.3 * n, 0., 1.5 * n)
    nb = ROOT.RooRealVar("nb_" + label, "", 0.7 * n, 0., 1.5 * n)
    mloc = ROOT.RooAddPdf("m_" + label, "", ROOT.RooArgList(sig, bkg),
                          ROOT.RooArgList(ns, nb))
    mloc.fitTo(sub, ROOT.RooFit.Extended(True), ROOT.RooFit.PrintLevel(-1))
    print("%-34s: N = %4d   Njpsi = %7.1f +- %.1f"
          % (label, n, ns.getVal(), ns.getError()))
    frl = mass.frame(ROOT.RooFit.Bins(45), ROOT.RooFit.Title(label))
    sub.plotOn(frl)
    mloc.plotOn(frl, ROOT.RooFit.LineColor(ROOT.kBlue))
    mloc.plotOn(frl, ROOT.RooFit.Components("bkg"), ROOT.RooFit.LineStyle(ROOT.kDashed),
                ROOT.RooFit.LineColor(ROOT.kRed))
    frl.Draw()
    c.SaveAs(prefix + "_massfit_" + label + ".png")


fit_subset("pt < 1.0", "pt0to1")
fit_subset("pt > 1.0 && pt < 2.0", "pt1to2")
fit_subset("pt > 2.0 && pt < 3.0", "pt2to3")
fit_subset("pt < 3.0 && absy < 1.6", "pt0to3_central_y")
fit_subset("pt < 3.0 && absy > 1.6", "pt0to3_forward_y")
fit_subset("pt < 1.0 && absy > 1.6", "pt0to1_forward_y")

fout = ROOT.TFile(prefix + "_sweights.root", "RECREATE")
h_pt_sw.Write()
h_pt_bkg.Write()
h_zoom.Write()
fout.Close()
print("\nOutputs: %s_massfit.png, %s_pt_sweighted.png, %s_pt_sweighted_zoom0to5.png, %s_sweights.root"
      % (prefix, prefix, prefix, prefix))
