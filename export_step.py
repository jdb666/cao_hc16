"""Exporte le bateau complet (v_pleine_0.yaml : moteur en marche, voiles pleines) en STEP nommé et coloré."""
import sys, time, yaml, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/claude/cao')
import cadquery as cq, hc16_rando as H
t = time.time()
cfg = yaml.safe_load(open('/home/claude/cao/v_pleine_0.yaml'))
A = H.build(cfg)
out = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/cao/hc16_rando_complet.step'
A.save(out)
print('STEP', out, round(time.time() - t, 1), 's')
