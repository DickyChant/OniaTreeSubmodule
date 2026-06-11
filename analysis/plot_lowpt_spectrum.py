#!/usr/bin/env python3
"""Low-pT J/psi plots from the full-AOD flat skim:
- per-pT-bin binned CB+expo mass fits (resolution free) -> yield vs pT graph
- combined mass fit plots for pT 1-3 (all y, and forward)
Usage: python3 plot_lowpt_spectrum.py <flat_bestcand.root> <outprefix>
"""
import sys
import math
import array
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

fin, prefix = sys.argv[1], sys.argv[2]
EXTRA_CUT = sys.argv[3] if len(sys.argv) > 3 else ""
M_LO, M_HI, NB = 2.2, 4.4, 220

PT_BINS = [(0.0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.0),
           (3.0, 4.0), (4.0, 5.0), (5.0, 6.0)]

df = ROOT.RDataFrame("bestcand", fin)
if EXTRA_CUT:
    df = df.Filter(EXTRA_CUT)
    print("extra selection:", EXTRA_CUT)
hists = {}
for lo, hi in PT_BINS:
    hists[(lo, hi)] = df.Filter("pt >= %g && pt < %g" % (lo, hi)).Histo1D(
        ("h_%g_%g" % (lo, hi), ";m_{#mu#mu} [GeV];Candidates", NB, M_LO, M_HI), "mass")
h13 = df.Filter("pt >= 1 && pt < 3").Histo1D(
    ("h13", "p_{T}(#mu#mu) 1-3 GeV;m_{#mu#mu} [GeV];Candidates / 10 MeV", NB, M_LO, M_HI), "mass")
h13f = df.Filter("pt >= 1 && pt < 3 && absy > 1.6").Histo1D(
    ("h13f", "p_{T}(#mu#mu) 1-3 GeV, |y|>1.6;m_{#mu#mu} [GeV];Candidates / 10 MeV", NB, M_LO, M_HI), "mass")
h01 = df.Filter("pt < 1").Histo1D(
    ("h01", "p_{T}(#mu#mu) 0-1 GeV;m_{#mu#mu} [GeV];Candidates / 10 MeV", NB, M_LO, M_HI), "mass")

mass = ROOT.RooRealVar("mass", "m_{#mu#mu}", M_LO, M_HI, "GeV")
c = ROOT.TCanvas("c", "", 900, 700)


def fit_hist(h, label, draw=False, sigma0=0.045, fix_shape=False):
    n = h.Integral()
    if n < 50:
        return 0., 0.
    dh = ROOT.RooDataHist("dh_" + label, "", ROOT.RooArgList(mass), h)
    m0 = ROOT.RooRealVar("m0_" + label, "", 3.092, 3.06, 3.13)
    sg = ROOT.RooRealVar("sg_" + label, "", sigma0, 0.02, 0.09)
    al = ROOT.RooRealVar("al_" + label, "", 1.3, 0.5, 3.0)
    nc = ROOT.RooRealVar("nc_" + label, "", 13., 13., 13.)
    nc.setConstant(True)
    if fix_shape:
        # near-zero-signal bins: shape from the neighbouring 1-2 GeV fits, yields only
        m0.setVal(3.092); m0.setConstant(True)
        sg.setVal(sigma0); sg.setConstant(True)
        al.setVal(1.3); al.setConstant(True)
    sig = ROOT.RooCBShape("sig_" + label, "", mass, m0, sg, al, nc)
    # psi(2S): PDG mass offset, resolution scaled by the mass ratio
    m2 = ROOT.RooFormulaVar("m2_" + label, "@0 + 0.5894", ROOT.RooArgList(m0))
    s2 = ROOT.RooFormulaVar("s2_" + label, "@0 * 1.19", ROOT.RooArgList(sg))
    sig2 = ROOT.RooCBShape("sig2_" + label, "", mass, m2, s2, al, nc)
    # acceptance-sculpted background (turn-over at low pT) -> Bernstein(4), >=0 by construction
    cs = [ROOT.RooRealVar("c%d_%s" % (i, label), "", 1.0, 0.0, 10.0) for i in range(5)]
    bkg = ROOT.RooBernstein("bkg_" + label, "", mass, ROOT.RooArgList(*cs))
    ns = ROOT.RooRealVar("ns_" + label, "", 0.2 * n, 0., 1.5 * n)
    ns2 = ROOT.RooRealVar("ns2_" + label, "", 0.01 * n, 0., 0.5 * n)
    nb = ROOT.RooRealVar("nb_" + label, "", 0.8 * n, 0., 1.5 * n)
    mod = ROOT.RooAddPdf("m_" + label, "", ROOT.RooArgList(sig, sig2, bkg),
                         ROOT.RooArgList(ns, ns2, nb))
    mod.fitTo(dh, ROOT.RooFit.Extended(True), ROOT.RooFit.PrintLevel(-1), ROOT.RooFit.SumW2Error(False))
    mod.fitTo(dh, ROOT.RooFit.Extended(True), ROOT.RooFit.PrintLevel(-1), ROOT.RooFit.SumW2Error(False))
    if draw:
        fr = mass.frame(ROOT.RooFit.Title(h.GetTitle()))
        dh.plotOn(fr)
        mod.plotOn(fr, ROOT.RooFit.LineColor(ROOT.kBlue))
        mod.plotOn(fr, ROOT.RooFit.Components("bkg_" + label),
                   ROOT.RooFit.LineStyle(ROOT.kDashed), ROOT.RooFit.LineColor(ROOT.kRed))
        mod.plotOn(fr, ROOT.RooFit.Components("sig2_" + label),
                   ROOT.RooFit.LineStyle(ROOT.kDotted), ROOT.RooFit.LineColor(ROOT.kGreen + 2))
        fr.Draw()
        tx = ROOT.TLatex()
        tx.SetNDC()
        tx.SetTextSize(0.04)
        tx.DrawLatex(0.15, 0.84, "N_{J/#psi} = %.0f #pm %.0f" % (ns.getVal(), ns.getError()))
        tx.DrawLatex(0.15, 0.78, "#sigma_{m} = %.1f MeV" % (1000 * sg.getVal()))
        c.SaveAs(prefix + "_massfit_" + label + ".png")
    return ns.getVal(), ns.getError()


print("%-12s %14s" % ("pT [GeV]", "N_Jpsi"))
gx, gy, gex, gey = [], [], [], []
for lo, hi in PT_BINS:
    y, e = fit_hist(hists[(lo, hi)].GetValue(), "pt%g_%g" % (lo, hi),
                    draw=(hi <= 3.001), sigma0=0.055 if hi <= 1.001 else (0.05 if hi < 3 else 0.04),
                    fix_shape=(hi <= 1.001))
    print("%-12s %8.0f +- %.0f" % ("%g-%g" % (lo, hi), y, e))
    gx.append(0.5 * (lo + hi))
    gex.append(0.5 * (hi - lo))
    gy.append(y / (hi - lo))
    gey.append(e / (hi - lo))

y13, e13 = fit_hist(h13.GetValue(), "pt1to3", draw=True)
y13f, e13f = fit_hist(h13f.GetValue(), "pt1to3_fwd", draw=True)
y01, e01 = fit_hist(h01.GetValue(), "pt0to1", draw=True, sigma0=0.055, fix_shape=True)
print("combined 1-3: %.0f +- %.0f   (forward |y|>1.6: %.0f +- %.0f)" % (y13, e13, y13f, e13f))
print("combined 0-1: %.0f +- %.0f" % (y01, e01))

g = ROOT.TGraphErrors(len(gx), array.array('d', gx), array.array('d', gy),
                      array.array('d', gex), array.array('d', gey))
g.SetTitle(";p_{T}^{#mu#mu} [GeV];dN_{J/#psi}/dp_{T} [per GeV]")
g.SetMarkerStyle(20)
g.SetMarkerColor(ROOT.kBlue + 1)
g.SetLineColor(ROOT.kBlue + 1)
g.SetLineWidth(2)

c.SetLogy(1)
g.SetMinimum(5)
g.Draw("AP")
tx = ROOT.TLatex()
tx.SetNDC()
tx.SetTextSize(0.035)
tx.DrawLatex(0.45, 0.25, "Run2026C ParkingDoubleMuonLowMass0 AOD (144M evts)")
tx.DrawLatex(0.45, 0.20, "p_{T} < 1 GeV: consistent with zero")
c.SaveAs(prefix + "_yield_vs_pt_log.png")

c.SetLogy(0)
g2 = g.Clone("g2")
g2.GetXaxis().SetRangeUser(0., 3.)
g2.SetMaximum(1.25 * max(gy[:6]))
g2.SetMinimum(-2000)
g2.Draw("AP")
ln = ROOT.TLine(0., 0., 3., 0.)
ln.SetLineStyle(2)
ln.Draw()
tx.DrawLatex(0.18, 0.84, "J/#psi yield turn-on at p_{T} #approx 1 GeV")
c.SaveAs(prefix + "_yield_vs_pt_zoom.png")
print("plots written with prefix", prefix)
