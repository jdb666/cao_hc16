"""Assemble la page : gabarit2.html + data2.json + global.json -> coffre_hc16_plans.html"""
import os
d = os.path.dirname(os.path.abspath(__file__))
s = open(f"{d}/gabarit2.html").read()
for tag, f in (("/*DATA*/null", "data2.json"), ("/*GLOBAL*/null", "global.json"), ("/*TENTE*/null", "tente_info.json"), ("/*PATRON*/null", "patron.json")):
    assert tag in s, tag
    s = s.replace(tag, open(f"{d}/{f}").read())
open(f"{d}/coffre_hc16_plans.html", "w").write(s)
print("OK coffre_hc16_plans.html", len(s))
