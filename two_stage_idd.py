"""Two-stage Doherty PA characterization. Simulation only; no hardware I/O."""
import argparse
import csv
import math
from datetime import datetime
from decimal import Decimal
from pathlib import Path

LIMIT_A = 3.0  # Total Main + Peaking drain current, not per-branch.
FIELDS = ['mode', 'stage', 'point_id', 'main_vgs_v', 'peaking_vgs_v',
          'main_idd_a', 'peaking_idd_a', 'total_idd_a', 'status',
          'rf_output_dbm', 'aclr_lower_dbc', 'aclr_upper_dbc', 'waveform']


def axis(start, stop, step):
    a, b, s = (Decimal(str(v)) for v in (start, stop, step))
    if not all(v.is_finite() for v in (a, b, s)) or s <= 0 or a > b:
        raise ValueError('Require finite start <= stop and step > 0')
    n = int((b-a)//s)+1
    if n > 10000:
        raise ValueError('Too many axis points')
    return [float(a+i*s) for i in range(n)]


def bias(v):
    v = float(v)
    if not math.isfinite(v) or not -5 <= v <= 0:
        raise ValueError('Simulation bias must be between -5 and 0 V')
    return v


def currents(main, peaking):
    # Illustrative nonlinear transfer model; NOT calibrated device data.
    return 1.4 * (max(0, main+3.5)/0.71)**2, 0.15 * (max(0, peaking+5)/0.022)**2


def row(stage, point_id, main, peaking, rf=None, waveform=''):
    im, ip = currents(main, peaking)
    if rf is not None:
        # Arbitrary demonstration of RF-dependent current, not a PA prediction.
        factor = 10**((rf-30)/10)
        im += .35*factor
        ip += .25*factor
    total = im+ip
    return dict(zip(FIELDS, ['simulation', stage, point_id, main, peaking,
                             im, ip, total,
                             'total_current_limit' if total >= LIMIT_A else 'simulated',
                             '' if rf is None else rf, '', '', waveform]))


def save(rows, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f'SIMULATION ONLY: {len(rows)} points saved to {output}')
    if rows[-1]['status'] == 'total_current_limit':
        print('STOP: total Main + Peaking current reached/exceeded 3 A.')
    print('ACLR fields intentionally empty; no pass/fail or optimum selected.')


def run(args):
    if args.stage == 'static':
        mains = axis(args.main_start, args.main_stop, args.main_step)
        peaks = axis(args.peaking_start, args.peaking_stop, args.peaking_step)
        if len(mains)*len(peaks) > 100000:
            raise ValueError('At most 100000 combinations')
        pairs = [(bias(m), bias(p)) for m in mains for p in peaks]
    else:
        if not math.isfinite(args.rf_output_dbm) or not -100 <= args.rf_output_dbm <= 60:
            raise ValueError('Simulation RF output must be finite and between -100 and 60 dBm')
        if not args.waveform.strip():
            raise ValueError('Waveform label must not be empty')
        pairs = []
        with args.input.open(newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            if not {'main_vgs_v', 'peaking_vgs_v', 'stage', 'mode', 'status'} <= set(reader.fieldnames or []):
                raise ValueError('Input must be a static-stage CSV')
            for r in reader:
                if r['stage'] != 'static' or r['mode'] != 'simulation':
                    raise ValueError('Only simulated static-stage CSV is supported')
                if r['status'] != 'simulated':
                    continue
                pairs.append((bias(r['main_vgs_v']), bias(r['peaking_vgs_v'])))
                if len(pairs) > 100000:
                    raise ValueError('Too many candidates')
    if not pairs:
        raise ValueError('No eligible candidate points')
    rows = []
    for index, (main, peak) in enumerate(pairs, 1):
        result = row(args.stage, index, main, peak,
                     args.rf_output_dbm if args.stage == 'rf' else None,
                     args.waveform if args.stage == 'rf' else '')
        rows.append(result)
        if result['total_idd_a'] >= LIMIT_A:
            break
    output = args.output or Path(__file__).resolve().parent/'results'/(
        args.stage+'-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.csv')
    save(rows, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='stage', required=True)
    static = sub.add_parser('static', help='No-RF bias characterization (simulated)')
    for name, default in [('main-start', -2.89), ('main-stop', -2.69), ('main-step', .05),
                          ('peaking-start', -4.998), ('peaking-stop', -4.978), ('peaking-step', .005)]:
        static.add_argument('--'+name, type=float, default=default)
    rf = sub.add_parser('rf', help='Simulate RF current at static-stage candidate biases')
    rf.add_argument('--input', type=Path, required=True)
    rf.add_argument('--rf-output-dbm', type=float, required=True)
    rf.add_argument('--waveform', required=True)
    for command in (static, rf):
        command.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, OSError, KeyError, csv.Error) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    import sys
    # Double-click defaults to static simulation and retains the console.
    interactive = len(sys.argv) == 1
    if interactive:
        sys.argv.append('static')
    try:
        main()
    finally:
        if interactive and sys.stdin.isatty():
            try:
                input('Press Enter to close...')
            except EOFError:
                pass
