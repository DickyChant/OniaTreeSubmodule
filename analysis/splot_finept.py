#!/usr/bin/env python3
"""Conditional sPlot with fine pT bins: run sPlot independently in pT regions
(resolution classes), each with its own fitted mass shape, and stitch the
sWeighted pT spectra. Valid where the single global-fit sPlot is not.
Usage: python3 splot_finept.py <flat_wide.root> <outprefix> [extra_cut]
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
REGIONS = [(0., 3., 0.053), (3., 6., 0.042), (6., 200., 0.036)]  # (lo, hi, sigma seed)

EDGES = ([0.25 * i for i in range(13)]            # 0 - 3 in 0.25
         + [3.5, 4.0, 4.5, 5.0, 5.5, 6.0]         # 3 - 6 in 0.5
         + [7., 8., 9., 10., 12.5, 15., 20., 30., 50.])

rdf = ROOT.RDataFrame("bestcand", fin)
if EXTRA:
    rdf = rdf.Filter(EXTRA)
    print("extra selection:", EXTRA)
arr = rdf.AsNumpy(("mass", "pt"))
gsel = arr["pt"] < 200.
a_m = arr["mass"][gsel].astype(np.float64)
a_pt = arr["pt"][gsel].astype(np.float64)
print("candidates: %d" % len(a_m))

h_sw = ROOT.TH1D("h_pt_sw_fine", ";p_{T}^{#mu#mu} [GeV];sWeighted J/#psi yield",
                 len(EDGES) - 1, array.array('d', EDGES))
h_sw.Sumw2()
c = ROOT.TCanvas("c", "", 900, 700)

for rlo, rhi, sg0 in REGIONS:
    rmask = (a_pt >= rlo) & (a_pt < rhi)
    nsub = int(rmask.sum())
    label = "pt%g_%g" % (rlo, rhi)
    print("\n=== region %g-%g GeV: %d candidates ===" % (rlo, rhi, nsub))

    mass = ROOT.RooRealVar("mass", "m_{#mu#mu}", M_LO, M_HI, "GeV")
    pt = ROOT.RooRealVar("pt", "p_{T}^{#mu#mu}", 0., 200., "GeV")
    sub = ROOT.RooDataSet.from_numpy({"mass": a_m[rmask], "pt": a_pt[rmask]},
                                     ROOT.RooArgSet(mass, pt), name="d_" + label)

    m0 = ROOT.RooRealVar("m0", "", 3.092, 3.06, 3.13)
    sg = ROOT.RooRealVar("sg", "", sg0, 0.02, 0.09)
    al = ROOT.RooRealVar("al", "", 1.3, 0.5, 3.0)
    nc = ROOT.RooRealVar("nc", "", 13.)
    nc.setConstant(True)
    sig = ROOT.RooCBShape("sig", "", mass, m0, sg, al, nc)
    m2 = ROOT.RooFormulaVar("m2", "@0 + 0.5894", ROOT.RooArgList(m0))
    s2 = ROOT.RooFormulaVar("s2", "@0 * 1.19", ROOT.RooArgList(sg))
    sig2 = ROOT.RooCBShape("sig2", "", mass, m2, s2, al, nc)
    cs = [ROOT.RooRealVar("c%d" % i, "", 1.0, 0.0, 10.0) for i in range(5)]
    bkg = ROOT.RooBernstein("bkg", "", mass, ROOT.RooArgList(*cs))
    nsig = ROOT.RooRealVar("nsig", "", 0.3 * nsub, 0., 1.2 * nsub)
    nsig2 = ROOT.RooRealVar("nsig2", "", 0.01 * nsub, 0., 0.3 * nsub)
    nbkg = ROOT.RooRealVar("nbkg", "", 0.7 * nsub, 0., 1.2 * nsub)
    model = ROOT.RooAddPdf("model", "", ROOT.RooArgList(sig, sig2, bkg),
                           ROOT.RooArgList(nsig, nsig2, nbkg))

    hm = ROOT.TH1D("hm_" + label, "", 440, M_LO, M_HI)
    for v in a_m[rmask]:
        hm.Fill(v)
    dh = ROOT.RooDataHist("dh_" + label, "", ROOT.RooArgList(mass), hm)
    model.fitTo(dh, ROOT.RooFit.Extended(True), ROOT.RooFit.PrintLevel(-1))
    model.fitTo(dh, ROOT.RooFit.Extended(True), ROOT.RooFit.PrintLevel(-1))
    print("  shapes: m0=%.4f sigma=%.1f MeV alpha=%.2f ; Nsig=%.0f+-%.0f Nbkg=%.0f"
          % (m0.getVal(), 1000 * sg.getVal(), al.getVal(),
             nsig.getVal(), nsig.getError(), nbkg.getVal()))

    fr = mass.frame(ROOT.RooFit.Bins(220),
                    ROOT.RooFit.Title("p_{T} %g-%g GeV (region fit for sPlot)" % (rlo, rhi)))
    dh.plotOn(fr)
    model.plotOn(fr, ROOT.RooFit.LineColor(ROOT.kBlue))
    model.plotOn(fr, ROOT.RooFit.Components("bkg"), ROOT.RooFit.LineStyle(ROOT.kDashed),
                 ROOT.RooFit.LineColor(ROOT.kRed))
    fr.Draw()
    c.SaveAs("%s_regionfit_%s.png" % (prefix, label))

    for p in (m0, sg, al) + tuple(cs):
        p.setConstant(True)
    sData = ROOT.RooStats.SPlot("s_" + label, "", sub, model,
                                ROOT.RooArgList(nsig, nsig2, nbkg))
    print("  sPlot closure: sum(sw)=%.0f vs Nsig=%.0f"
          % (sData.GetYieldFromSWeight("nsig"), nsig.getVal()))
    for i in range(sub.numEntries()):
        h_sw.Fill(sub.get(i).getRealValue("pt"), sData.GetSWeight(i, "nsig"))

print("\n=== conditional-sPlot sWeighted J/psi yields, fine pT bins ===")
for b in range(1, h_sw.GetNbinsX() + 1):
    lo, hi = h_sw.GetBinLowEdge(b), h_sw.GetBinLowEdge(b + 1)
    if hi > 6.001:
        break
    print("%-12s %12.1f +- %.1f" % ("%g-%g" % (lo, hi), h_sw.GetBinContent(b), h_sw.GetBinError(b)))

c.SetLogy(1)
h_sw.SetLineColor(ROOT.kBlue + 1)
h_sw.SetLineWidth(2)
h_sw.SetMinimum(0.5)
h_sw.Draw("e")
c.SaveAs(prefix + "_pt_sweighted_fine.png")
c.SetLogy(0)
h_zoom = h_sw.Clone("h_zoom")
h_zoom.GetXaxis().SetRangeUser(0., 4.)
h_zoom.SetMaximum(1.3 * max(h_sw.GetBinContent(b) for b in range(1, h_sw.FindBin(3.9))))
h_zoom.Draw("e")
ln = ROOT.TLine(0., 0., 4., 0.)
ln.SetLineStyle(2)
ln.Draw()
c.SaveAs(prefix + "_pt_sweighted_fine_zoom.png")

fout = ROOT.TFile(prefix + "_sweights_fine.root", "RECREATE")
h_sw.Write()
fout.Close()
print("\nOutputs: %s_pt_sweighted_fine(.png/_zoom.png), %s_sweights_fine.root, %s_regionfit_*.png"
      % (prefix, prefix, prefix))
