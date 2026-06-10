#!/usr/bin/env python3
"""Analyze OniaTree from 2026C ParkingDoubleMuonLowMass AOD:
J/psi yield vs dimuon pT, down to pT = 0 (no pT cut applied anywhere).
Usage: python3 analyze_oniatree.py <input1.root> [input2.root ...]
"""
import sys
import math
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

# trigger list as configured (bit i-1 <-> trigger i)
TRIGGERS = [
    "HLT_DoubleMu4_3_LowMass",                # bit 0
    "HLT_DoubleMu4_LowMass_Displaced",        # bit 1
    "HLT_DoubleMu2_Jpsi_LowPt",               # bit 2
    "HLT_Dimuon0_LowMass_Inclusive",          # bit 3
    "HLT_Dimuon0_LowMass",                    # bit 4
    "HLT_Dimuon0_LowMass_L1_0er1p5",          # bit 5
    "HLT_Dimuon0_LowMass_L1_4",               # bit 6
    "HLT_Dimuon0_LowMass_L1_TM530",           # bit 7
    "HLT_Mu0_L1DoubleMu",                     # bit 8
    "HLT_Mu4_L1DoubleMu",                     # bit 9
    "HLT_Dimuon0_Jpsi",                       # bit 10
    "HLT_Dimuon0_Jpsi_NoVertexing",           # bit 11
    "HLT_Dimuon25_Jpsi",                      # bit 12
    "HLT_Dimuon18_PsiPrime",                  # bit 13
    "HLT_DoubleMu4_3_Jpsi",                   # bit 14
    "HLT_DoubleMu4_Jpsi_Displaced",           # bit 15
    "HLT_DoubleMu4_JpsiTrkTrk_Displaced",     # bit 16
    "HLT_DoubleMu4_JpsiTrk_Bc",               # bit 17
    "HLT_Dimuon0_Jpsi3p5_Muon2",              # bit 18
    "HLT_DoubleMu2_Jpsi_DoubleTrk1_Phi1p05",  # bit 19
    "HLT_Mu0_Barrel",                         # bit 20
    "HLT_Mu0_Barrel_L1HP6",                   # bit 21
    "HLT_Mu4_Barrel_IP4",                     # bit 22
    "HLT_IsoMu24",                            # bit 23
]

M_SIG_LO, M_SIG_HI = 3.00, 3.20          # J/psi signal window
SB = [(2.60, 2.80), (3.40, 3.60)]        # sidebands (total width 2x signal)
SB_SCALE = (M_SIG_HI - M_SIG_LO) / sum(hi - lo for lo, hi in SB)

PT_BINS = [(0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 5.0),
           (5.0, 8.0), (8.0, 15.0), (15.0, 100.0)]

ch = ROOT.TChain("hionia/myTree")
for f in sys.argv[1:]:
    ch.Add(f)
print("Files: %d  Events: %d" % (len(sys.argv) - 1, ch.GetEntries()))

h_mass = ROOT.TH1D("h_mass", ";m_{#mu#mu} [GeV];Candidates / 20 MeV", 125, 2.0, 4.5)
h_mass_ptbin = {}
for lo, hi in PT_BINS:
    name = "h_mass_pt%g_%g" % (lo, hi)
    h_mass_ptbin[(lo, hi)] = ROOT.TH1D(name, ";m_{#mu#mu} [GeV];Candidates / 25 MeV", 100, 2.0, 4.5)
h_pt_sig = ROOT.TH1D("h_pt_sig", ";p_{T}^{#mu#mu} [GeV];Candidates / 0.25 GeV", 120, 0., 30.)
h_pt_sb = ROOT.TH1D("h_pt_sb", "", 120, 0., 30.)
h_pt_lowzoom_sig = ROOT.TH1D("h_pt_lowzoom_sig", ";p_{T}^{#mu#mu} [GeV];Candidates / 0.1 GeV", 50, 0., 5.)
h_pt_lowzoom_sb = ROOT.TH1D("h_pt_lowzoom_sb", "", 50, 0., 5.)

n_trig_sig_lowpt = [0] * len(TRIGGERS)   # trigger bits for signal-window cands with pT < 2
n_trig_sb_lowpt = [0] * len(TRIGGERS)
n_sig = {b: 0 for b in PT_BINS}
n_sb = {b: 0 for b in PT_BINS}

nc = 0
for ev in ch:
    nqq = ev.Reco_QQ_size
    for i in range(nqq):
        if ev.Reco_QQ_sign[i] != 0:
            continue
        m = ev.Reco_QQ_4mom_m[i]
        pt = ev.Reco_QQ_4mom_pt[i]
        vp = ev.Reco_QQ_VtxProb[i]
        if vp < 0.01:
            continue
        nc += 1
        h_mass.Fill(m)
        for (lo, hi) in PT_BINS:
            if lo <= pt < hi:
                h_mass_ptbin[(lo, hi)].Fill(m)
        in_sig = M_SIG_LO < m < M_SIG_HI
        in_sb = any(lo < m < hi for lo, hi in SB)
        if in_sig:
            h_pt_sig.Fill(pt)
            h_pt_lowzoom_sig.Fill(pt)
        if in_sb:
            h_pt_sb.Fill(pt)
            h_pt_lowzoom_sb.Fill(pt)
        for (lo, hi) in PT_BINS:
            if lo <= pt < hi:
                if in_sig:
                    n_sig[(lo, hi)] += 1
                elif in_sb:
                    n_sb[(lo, hi)] += 1
        if pt < 2.0 and (in_sig or in_sb):
            trig = int(ev.Reco_QQ_trig[i])
            tgt = n_trig_sig_lowpt if in_sig else n_trig_sb_lowpt
            for b in range(len(TRIGGERS)):
                if trig & (1 << b):
                    tgt[b] += 1

print("Total OS candidates (vProb>1%%): %d" % nc)
print()
print("=== J/psi yields: signal window %.2f-%.2f, sideband-subtracted ===" % (M_SIG_LO, M_SIG_HI))
print("%-14s %10s %10s %14s" % ("pT [GeV]", "sig.win.", "sideband", "Nsig (SB-sub)"))
tot_sub = 0.
for (lo, hi) in PT_BINS:
    s, b = n_sig[(lo, hi)], n_sb[(lo, hi)] * SB_SCALE
    sub = s - b
    err = math.sqrt(s + b * SB_SCALE)
    tot_sub += sub
    print("%-14s %10d %10.1f %9.1f +- %.1f" % ("%g-%g" % (lo, hi), s, b, sub, err))
print("%-14s %35.1f" % ("TOTAL", tot_sub))

print()
print("=== Trigger bits for J/psi-window candidates with pT < 2 GeV ===")
print("%-42s %10s %10s" % ("path", "sig.win.", "sideband"))
for b, name in enumerate(TRIGGERS):
    if n_trig_sig_lowpt[b] or n_trig_sb_lowpt[b]:
        print("%-42s %10d %10d" % (name, n_trig_sig_lowpt[b], n_trig_sb_lowpt[b]))

# ---- plots ----
c = ROOT.TCanvas("c", "", 900, 700)
h_mass.SetLineColor(ROOT.kBlue + 1)
h_mass.SetLineWidth(2)
h_mass.Draw("hist")
c.SaveAs("mass_all.png")

# low-pT mass fits
for (lo, hi) in [(0.0, 0.5), (0.5, 1.0), (1.0, 2.0)]:
    h = h_mass_ptbin[(lo, hi)]
    h.SetLineColor(ROOT.kBlue + 1)
    h.SetLineWidth(2)
    h.SetTitle("p_{T}(#mu#mu) %g-%g GeV" % (lo, hi))
    f = ROOT.TF1("f_%g" % lo, "gausn(0)+pol1(3)", 2.7, 3.5)
    f.SetParameters(h.GetMaximum() * 0.05, 3.097, 0.035, h.GetBinContent(5), 0.)
    f.SetParLimits(1, 3.0, 3.2)
    f.SetParLimits(2, 0.01, 0.1)
    h.Fit(f, "RQL")
    nsig = f.GetParameter(0) / h.GetBinWidth(1)
    ensig = f.GetParError(0) / h.GetBinWidth(1)
    print("Fit pT %g-%g: Njpsi = %.0f +- %.0f  (mean=%.3f, sigma=%.0f MeV)"
          % (lo, hi, nsig, ensig, f.GetParameter(1), 1000 * f.GetParameter(2)))
    h.Draw("e")
    c.SaveAs("mass_pt%g_%g.png" % (lo, hi))

h_pt_sub = h_pt_sig.Clone("h_pt_sub")
h_pt_sub.Add(h_pt_sb, -SB_SCALE)
h_pt_sub.SetLineColor(ROOT.kRed + 1)
h_pt_sub.SetLineWidth(2)
h_pt_sig.SetLineColor(ROOT.kBlue + 1)
c.SetLogy(1)
h_pt_sig.Draw("hist")
h_pt_sub.Draw("hist same")
leg = ROOT.TLegend(0.55, 0.72, 0.88, 0.88)
leg.AddEntry(h_pt_sig, "3.0<m<3.2 (sig. window)", "l")
leg.AddEntry(h_pt_sub, "sideband-subtracted", "l")
leg.Draw()
c.SaveAs("pt_spectrum.png")

c.SetLogy(0)
h_zoom_sub = h_pt_lowzoom_sig.Clone("h_zoom_sub")
h_zoom_sub.Add(h_pt_lowzoom_sb, -SB_SCALE)
h_zoom_sub.SetLineColor(ROOT.kRed + 1)
h_zoom_sub.SetLineWidth(2)
h_pt_lowzoom_sig.SetLineColor(ROOT.kBlue + 1)
h_pt_lowzoom_sig.SetLineWidth(2)
h_pt_lowzoom_sig.Draw("hist")
h_zoom_sub.Draw("hist same")
leg.Draw()
c.SaveAs("pt_spectrum_zoom0to5.png")

fout = ROOT.TFile("jpsi_lowpt_check_histos.root", "RECREATE")
for o in ([h_mass, h_pt_sig, h_pt_sb, h_pt_sub, h_pt_lowzoom_sig, h_pt_lowzoom_sb, h_zoom_sub]
          + list(h_mass_ptbin.values())):
    o.Write()
fout.Close()
print("\nPlots: mass_all.png, mass_pt*.png, pt_spectrum.png, pt_spectrum_zoom0to5.png")
print("Histos: jpsi_lowpt_check_histos.root")
