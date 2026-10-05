"""Génère v_pleine_0.yaml (moteur en marche, voiles pleines) et v_releve.yaml (moteur relevé à 90°) depuis cotes.yaml."""
import yaml, copy
c = yaml.safe_load(open('/home/claude/cao/cotes.yaml'))
for f, ang in (('v_pleine_0.yaml', 0), ('v_releve.yaml', 90)):
    d = copy.deepcopy(c)
    for mode_ in ('transversal', 'arriere', 'avant2'):
        d['coffre']['moteur'][mode_]['bascule'] = ang
    v2 = d['coffre']['moteur'].get('vertical2')
    if v2:
        v2['levee'] = 0 if ang == 0 else v2['levee_max']
    d['voile'].setdefault('enroulement', {}); d['voile']['enroulement'].update(babord=0, tribord=0)
    yaml.safe_dump(d, open('/home/claude/cao/' + f, 'w'), sort_keys=False, allow_unicode=True)
