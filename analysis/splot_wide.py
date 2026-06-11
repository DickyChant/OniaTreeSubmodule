#!/usr/bin/env python3
"""sPlot from ONE full-pT-range mass fit (wide window, CB Jpsi + CB psi2S + Bernstein4)
-> sWeighted dimuon pT spectrum. Runs on the wide flat skim (mass 2.2-4.4).
Usage: python3 splot_wide.py <flat_wide.root> <outprefix> [extra_cut]
"""
import sys
import array
import ctypes
import numpy as np
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

fin, prefix = sys.argv[1], sys.argv[2]
EXTRA = sys.argv[3] if len(sys.argv) > 3 else ""
M_LO, M_HI = 2.2, 4.4

rdf = ROOT.RDataFrame("bestcand", fin)
if EXTRA:
    rdf = rdf.Filter(EXTRA)
    print("extra selection:", EXTRA)
arr = rdf.AsNumpy(("mass", "pt", "absy"))
sel = arr["pt"] < 200.
npd = {k: v[sel].astype(np.float64) for k, v in arr.items()}
nbest = len(npd["mass"])
print("candidates: %d" % nbest)

mass = ROOT.RooRealVar("mass", "m_{#mu#mu}", M_LO, M_HI, "GeV")
pt = ROOT.RooRealVar("pt", "p_{T}^{#mu#mu}", 0., 200., "GeV")
absy = ROOT.RooRealVar("absy", "|y|^{#mu#mu}", 0., 2.5)
data = ROOT.RooDataSet.from_numpy(npd, ROOT.RooArgSet(mass, pt, absy), name="data")

# ---- model ----
m0 = ROOT.RooRealVar("m0", "", 3.092, 3.06, 3.13)
sg = ROOT.RooRealVar("sg", "", 0.038, 0.02, 0.09)
al = ROOT.RooRealVar("al", "", 1.3, 0.5, 3.0)
nc = ROOT.RooRealVar("nc", "", 13.)
nc.setConstant(True)
sig = ROOT.RooCBShape("sig", "", mass, m0, sg, al, nc)
m2 = ROOT.RooFormulaVar("m2", "@0 + 0.5894", ROOT.RooArgList(m0))
s2 = ROOT.RooFormulaVar("s2", "@0 * 1.19", ROOT.RooArgList(sg))
sig2 = ROOT.RooCBShape("sig2", "", mass, m2, s2, al, nc)
cs = [ROOT.RooRealVar("c%d" % i, "", 1.0, 0.0, 10.0) for i in range(5)]
bkg = ROOT.RooBernstein("bkg", "", mass, ROOT.RooArgList(*cs))
nsig = ROOT.RooRealVar("nsig", "", 0.5 * nbest, 0., 1.2 * nbest)
nsig2 = ROOT.RooRealVar("nsig2", "", 0.02 * nbest, 0., 0.3 * nbest)
nbkg = ROOT.RooRealVar("nbkg", "", 0.5 * nbest, 0., 1.2 * nbest)
model = ROOT.RooAddPdf("model", "", ROOT.RooArgList(sig, sig2, bkg),
                       ROOT.RooArgList(nsig, nsig2, nbkg))

# ---- step 1: binned fit for the shapes (fast, stable) ----
hm = ROOT.TH1D("hm", "", 440, M_LO, M_HI)
for v in npd["mass"]:
    hm.Fill(v)
dh = ROOT.RooDataHist("dh", "", ROOT.RooArgList(mass), hm)
model.fitTo(dh, ROOT.RooFit.Extended(True), ROOT.RooFit.PrintLevel(-1))
model.fitTo(dh, ROOT.RooFit.Extended(True), ROOT.RooFit.PrintLevel(-1))
print("binned fit: Nsig=%.0f+-%.0f  Nsig2=%.0f  Nbkg=%.0f  (m0=%.4f, sigma=%.1f MeV)"
      % (nsig.getVal(), nsig.getError(), nsig2.getVal(), nbkg.getVal(),
         m0.getVal(), 1000 * sg.getVal()))

c = ROOT.TCanvas("c", "", 900, 700)
fr = mass.frame(ROOT.RooFit.Bins(220), ROOT.RooFit.Title("full p_{T} range, best candidate/event"))
dh.plotOn(fr)
model.plotOn(fr, ROOT.RooFit.LineColor(ROOT.kBlue))
model.plotOn(fr, ROOT.RooFit.Components("bkg"), ROOT.RooFit.LineStyle(ROOT.kDashed),
             ROOT.RooFit.LineColor(ROOT.kRed))
model.plotOn(fr, ROOT.RooFit.Components("sig2"), ROOT.RooFit.LineStyle(ROOT.kDotted),
             ROOT.RooFit.LineColor(ROOT.kGreen + 2))
fr.Draw()
c.SaveAs(prefix + "_massfit.png")

# ---- step 2: fix shapes, sPlot on the unbinned dataset ----
for p in (m0, sg, al) + tuple(cs):
    p.setConstant(True)
sData = ROOT.RooStats.SPlot("sData", "", data, model, ROOT.RooArgList(nsig, nsig2, nbkg))
print("sPlot: sum(sw_sig)=%.0f (Nsig=%.0f)  sum(sw_bkg)=%.0f"
      % (sData.GetYieldFromSWeight("nsig"), nsig.getVal(), sData.GetYieldFromSWeight("nbkg")))

# ---- sWeighted pT spectra ----
edges = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5,
         5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 15.0, 20.0, 30.0, 50.0]
h_sw = ROOT.TH1D("h_pt_sw", ";p_{T}^{#mu#mu} [GeV];sWeighted J/#psi yield", len(edges) - 1,
                 array.array('d', edges))
h_sw.Sumw2()
h_zoom = ROOT.TH1D("h_zoom", ";p_{T}^{#mu#mu} [GeV];sWeighted J/#psi yield / 0.2 GeV", 25, 0., 5.)
h_zoom.Sumw2()
for i in range(data.numEntries()):
    v = data.get(i).getRealValue("pt")
    w = sData.GetSWeight(i, "nsig")
    h_sw.Fill(v, w)
    h_zoom.Fill(v, w)

print()
print("=== sWeighted J/psi yield in pT bins (from full-range fit) ===")
for lo, hi in [(0., 0.5), (0.5, 1.), (1., 2.), (2., 3.), (3., 5.), (5., 8.), (8., 15.), (15., 50.)]:
    b1, b2 = h_sw.FindBin(lo + 1e-6), h_sw.FindBin(hi - 1e-6)
    err = ctypes.c_double(0.)
    y = h_sw.IntegralAndError(b1, b2, err)
    print("%-10s %12.1f +- %.1f" % ("%g-%g" % (lo, hi), y, err.value))

c.SetLogy(1)
h_sw.SetLineColor(ROOT.kBlue + 1)
h_sw.SetLineWidth(2)
h_sw.SetMinimum(0.5)
h_sw.Draw("e")
c.SaveAs(prefix + "_pt_sweighted.png")
c.SetLogy(0)
h_zoom.SetLineColor(ROOT.kRed + 1)
h_zoom.SetLineWidth(2)
h_zoom.Draw("e")
ln = ROOT.TLine(0., 0., 5., 0.)
ln.SetLineStyle(2)
ln.Draw()
c.SaveAs(prefix + "_pt_sweighted_zoom0to5.png")

fout = ROOT.TFile(prefix + "_sweights.root", "RECREATE")
h_sw.Write()
h_zoom.Write()
fout.Close()
print("\nOutputs: %s_massfit.png, %s_pt_sweighted.png, %s_pt_sweighted_zoom0to5.png" % (prefix, prefix, prefix))
