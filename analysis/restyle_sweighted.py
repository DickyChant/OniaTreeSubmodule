#!/usr/bin/env python3
"""CMS-style redraw of the conditional-sPlot fine pT spectrum (from saved histos)."""
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
import cmsstyle as CMS

CMS.setCMSStyle()
CMS.SetExtraText("Preliminary")
try:
    CMS.SetEnergy("13.6")
    CMS.SetLumi("")
except Exception:
    pass

f = ROOT.TFile.Open("splotfine_sweights_fine.root")
h = f.Get("h_pt_sw_fine")
h.SetDirectory(0)
f.Close()

c = ROOT.TCanvas("c", "", 800, 700)
c.SetLeftMargin(0.16)
c.SetRightMargin(0.05)
c.SetTopMargin(0.07)
c.SetBottomMargin(0.12)

c.SetLogy(1)
h.SetLineColor(ROOT.kAzure + 2)
h.SetMarkerColor(ROOT.kAzure + 2)
h.SetMarkerStyle(20)
h.SetMarkerSize(0.8)
h.SetLineWidth(2)
h.SetMinimum(50)
h.GetXaxis().SetRangeUser(0., 50.)
h.GetYaxis().SetTitleOffset(1.55)
h.Draw("e")
tx = ROOT.TLatex()
tx.SetNDC()
tx.SetTextFont(42)
tx.SetTextSize(0.033)
tx.DrawLatex(0.45, 0.25, "conditional sPlot (3 resolution regions)")
tx.DrawLatex(0.45, 0.20, "ParkingDoubleMuonLowMass0 AOD (144M evts)")
try:
    CMS.CMS_lumi(c, 11)
except Exception:
    pass
c.RedrawAxis()
c.SaveAs("splotfine_pt_sweighted_fine_cms.png")

c.SetLogy(0)
h2 = h.Clone("h2")
h2.GetXaxis().SetRangeUser(0., 4.)
h2.SetMaximum(1.3 * max(h.GetBinContent(b) for b in range(1, h.FindBin(3.9))))
h2.SetMinimum(-6000)
h2.GetYaxis().SetTitleOffset(1.55)
h2.Draw("e")
ln = ROOT.TLine(0., 0., 4., 0.)
ln.SetLineStyle(2)
ln.Draw()
tx.DrawLatex(0.20, 0.72, "J/#psi turn-on, 0.25 GeV bins")
try:
    CMS.CMS_lumi(c, 11)
except Exception:
    pass
c.RedrawAxis()
c.SaveAs("splotfine_pt_sweighted_fine_zoom_cms.png")
print("CMS-styled: splotfine_pt_sweighted_fine_cms.png, splotfine_pt_sweighted_fine_zoom_cms.png")
