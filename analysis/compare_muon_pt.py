#!/usr/bin/env python3
"""Compare single-muon pT spectra between the AOD and MiniAOD OniaTrees
(same events of run 402536): all stored muons, by rapidity region, and
J/psi-candidate daughter muons. Shows the MiniAOD slimming effect directly.
Usage: python3 compare_muon_pt.py  (paths hardcoded to run/ trees)
"""
import ctypes
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

AOD_FILES = ["Oniatree_part%d.root" % i for i in (1, 2, 3, 4, 5, 6)]
# parts 1-3 = run 402536 block files 1-3; MiniAOD covers the same run/block via 3 files.
# For the same-events comparison use AOD parts 1-6? NO: parts 1-6 = all 11 AOD files,
# Mini parts 1-3 = all 3 MiniAOD files -> both = full run 402536 block 00000. Same events.
MINI_FILES = ["Oniatree_mini_part%d.root" % i for i in (1, 2, 3)]

M_SIG_LO, M_SIG_HI = 3.00, 3.20


def book(tag):
    h = {}
    h["mu_all"] = ROOT.TH1D("h_mu_all_" + tag, ";p_{T}^{#mu} [GeV];Muons / 0.1 GeV", 100, 0., 10.)
    h["mu_fwd"] = ROOT.TH1D("h_mu_fwd_" + tag, ";p_{T}^{#mu} [GeV];Muons / 0.1 GeV", 100, 0., 10.)
    h["mu_cen"] = ROOT.TH1D("h_mu_cen_" + tag, ";p_{T}^{#mu} [GeV];Muons / 0.1 GeV", 100, 0., 10.)
    h["dau_sig"] = ROOT.TH1D("h_dau_sig_" + tag,
                             ";p_{T}^{#mu} (J/#psi daughters) [GeV];Muons / 0.2 GeV", 50, 0., 10.)
    h["dau_lowqq"] = ROOT.TH1D("h_dau_lowqq_" + tag,
                               ";p_{T}^{#mu} (daughters, p_{T}^{#mu#mu}<3) [GeV];Muons / 0.25 GeV",
                               24, 0., 6.)
    for x in h.values():
        x.Sumw2()
    return h


def fill(files, h):
    ch = ROOT.TChain("hionia/myTree")
    for f in files:
        ch.Add(f)
    nev = ch.GetEntries()
    for ev in ch:
        for i in range(ev.Reco_mu_size):
            pt = ev.Reco_mu_4mom_pt[i]
            eta = ev.Reco_mu_4mom_eta[i]
            h["mu_all"].Fill(pt)
            if abs(eta) > 1.6:
                h["mu_fwd"].Fill(pt)
            else:
                h["mu_cen"].Fill(pt)
        for q in range(ev.Reco_QQ_size):
            if ev.Reco_QQ_sign[q] != 0 or ev.Reco_QQ_VtxProb[q] < 0.01:
                continue
            m = ev.Reco_QQ_4mom_m[q]
            if not (M_SIG_LO < m < M_SIG_HI):
                continue
            for idx in (ev.Reco_QQ_mupl_idx[q], ev.Reco_QQ_mumi_idx[q]):
                if idx < 0 or idx >= ev.Reco_mu_size:
                    continue
                dpt = ev.Reco_mu_4mom_pt[idx]
                h["dau_sig"].Fill(dpt)
                if ev.Reco_QQ_4mom_pt[q] < 3.0:
                    h["dau_lowqq"].Fill(dpt)
    return nev


h_aod = book("aod")
h_mini = book("mini")
nev_a = fill(AOD_FILES, h_aod)
nev_m = fill(MINI_FILES, h_mini)
print("events: AOD %d   MiniAOD %d" % (nev_a, nev_m))

print()
print("=== stored muons per pT bin (all |eta|<2.4) ===")
print("%-10s %12s %12s %10s" % ("pT [GeV]", "AOD", "MiniAOD", "Mini/AOD"))
for lo, hi in [(0., 1.), (1., 2.), (2., 3.), (3., 4.), (4., 5.), (5., 10.)]:
    b1, b2 = h_aod["mu_all"].FindBin(lo + 1e-6), h_aod["mu_all"].FindBin(hi - 1e-6)
    na, nm = h_aod["mu_all"].Integral(b1, b2), h_mini["mu_all"].Integral(b1, b2)
    print("%-10s %12.0f %12.0f %10.3f" % ("%g-%g" % (lo, hi), na, nm, nm / na if na else 0.))

print()
print("=== J/psi (3.0<m<3.2) daughter muons, dimuon pT<3 ===")
for lo, hi in [(0., 1.), (1., 1.5), (1.5, 2.), (2., 3.), (3., 6.)]:
    b1, b2 = h_aod["dau_lowqq"].FindBin(lo + 1e-6), h_aod["dau_lowqq"].FindBin(hi - 1e-6)
    na, nm = h_aod["dau_lowqq"].Integral(b1, b2), h_mini["dau_lowqq"].Integral(b1, b2)
    print("%-10s %12.0f %12.0f %10.3f" % ("%g-%g" % (lo, hi), na, nm, nm / na if na else 0.))

# ---- plots: spectrum overlay + ratio ----
def overlay_ratio(key, fname, logy=True):
    c = ROOT.TCanvas("c_" + key, "", 900, 800)
    p1 = ROOT.TPad("p1", "", 0, 0.32, 1, 1)
    p2 = ROOT.TPad("p2", "", 0, 0, 1, 0.32)
    p1.SetBottomMargin(0.02)
    p2.SetTopMargin(0.04)
    p2.SetBottomMargin(0.3)
    p1.Draw()
    p2.Draw()
    p1.cd()
    if logy:
        p1.SetLogy(1)
    a, m = h_aod[key], h_mini[key]
    a.SetLineColor(ROOT.kBlue + 1)
    a.SetLineWidth(2)
    m.SetLineColor(ROOT.kRed + 1)
    m.SetLineWidth(2)
    a.GetXaxis().SetLabelSize(0)
    a.Draw("hist e")
    m.Draw("hist e same")
    leg = ROOT.TLegend(0.6, 0.75, 0.88, 0.88)
    leg.AddEntry(a, "AOD (reco::Muon)", "l")
    leg.AddEntry(m, "MiniAOD (slimmedMuons)", "l")
    leg.Draw()
    p2.cd()
    r = m.Clone("r_" + key)
    r.Divide(a)
    r.SetLineColor(ROOT.kBlack)
    r.SetMarkerStyle(20)
    r.SetMarkerSize(0.6)
    r.SetTitle("")
    r.GetYaxis().SetTitle("Mini/AOD")
    r.GetYaxis().SetNdivisions(505)
    r.GetYaxis().SetRangeUser(0., 1.3)
    r.GetYaxis().SetTitleSize(0.12)
    r.GetYaxis().SetLabelSize(0.10)
    r.GetYaxis().SetTitleOffset(0.4)
    r.GetXaxis().SetTitleSize(0.12)
    r.GetXaxis().SetLabelSize(0.10)
    r.GetXaxis().SetTitle(h_aod[key].GetXaxis().GetTitle())
    r.Draw("e")
    line = ROOT.TLine(r.GetXaxis().GetXmin(), 1., r.GetXaxis().GetXmax(), 1.)
    line.SetLineStyle(2)
    line.Draw()
    c.SaveAs(fname)


overlay_ratio("mu_all", "muonpt_all_AODvsMini.png")
overlay_ratio("mu_fwd", "muonpt_forward_AODvsMini.png")
overlay_ratio("mu_cen", "muonpt_central_AODvsMini.png")
overlay_ratio("dau_sig", "muonpt_jpsidaughters_AODvsMini.png")
overlay_ratio("dau_lowqq", "muonpt_jpsidaughters_lowQQpt_AODvsMini.png", logy=False)

fout = ROOT.TFile("muonpt_compare.root", "RECREATE")
for d in (h_aod, h_mini):
    for x in d.values():
        x.Write()
fout.Close()
print("\nPlots: muonpt_all/forward/central_AODvsMini.png, muonpt_jpsidaughters*_AODvsMini.png")
