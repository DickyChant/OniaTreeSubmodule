#!/usr/bin/env python3
"""RDataFrame skim: best J/psi candidate per event (OS, vProb>0.01, 2.6<m<3.5,
highest vProb) -> flat tree (mass, pt, absy). Multithreaded.
Usage: python3 skim_bestcand.py <output.root> <input glob or files...>
"""
import sys
import glob
import ROOT

out = sys.argv[1]
files = []
for a in sys.argv[2:]:
    files += glob.glob(a) if any(c in a for c in "*?[") else [a]
print("inputs: %d files" % len(files))

ROOT.EnableImplicitMT(10)
ROOT.gInterpreter.Declare("""
int bestIdx(const ROOT::RVec<float>& m, const ROOT::RVec<float>& vp,
            const ROOT::RVec<short>& sign) {
  int ib = -1; float bv = 0.01;
  for (size_t i = 0; i < m.size(); ++i)
    if (sign[i] == 0 && vp[i] > bv && m[i] > 2.6 && m[i] < 3.5) { bv = vp[i]; ib = i; }
  return ib;
}
""")

v = ROOT.std.vector('string')()
for f in files:
    v.push_back(f)
df = ROOT.RDataFrame("hionia/myTree", v)
ntot = df.Count()
df2 = (df.Define("ib", "bestIdx(Reco_QQ_4mom_m, Reco_QQ_VtxProb, Reco_QQ_sign)")
         .Filter("ib >= 0")
         .Define("mass", "Reco_QQ_4mom_m[ib]")
         .Define("pt", "Reco_QQ_4mom_pt[ib]")
         .Define("absy", "abs(Reco_QQ_4mom_y[ib])"))
npass = df2.Count()
df2.Snapshot("bestcand", out, ("mass", "pt", "absy"))
print("events: %d   best candidates: %d   -> %s" % (ntot.GetValue(), npass.GetValue(), out))
