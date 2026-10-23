import argparse
import csv
import math
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

FIELDS = ['main_vgs_v', 'peaking_vgs_v', 'main_idd_a', 'peaking_idd_a',
          'total_idd_a', 'status', 'aclr_lower_db', 'aclr_upper_db', 'rf_output_dbm']


def points(start, stop, step):
    a, b, s = map(lambda x: Decimal(str(x)), (start, stop, step))
    if not all(x.is_finite() for x in (a, b, s)) or s <= 0 or a > b:
        raise ValueError('Require finite start <= stop and step > 0')
    n = int((b - a) // s) + 1
    if n > 10000:
        raise ValueError('At most 10000 points per axis')
    return [float(a + i * s) for i in range(n)]


def simulate(main, peaking):
    # Illustrative monotonic model only; not calibrated to an actual PA.
    return (max(0.0, 1.4 + 2.0 * (main + 2.79)),
            max(0.0, 0.15 + 1.5 * (peaking + 4.978)))


def sweep(main_points, peaking_points, limit):
    for main in main_points:
        for peaking in peaking_points:
            im, ip = simulate(main, peaking)
            total = im + ip
            row = dict(zip(FIELDS, [main, peaking, im, ip, total,
                                   'current_limit' if total >= limit else 'simulated', '', '', '']))
            yield row
            if total >= limit:
                return


def write_svg(rows, target):
    values = [float(r['total_idd_a']) for r in rows]
    maximum = max(max(values, default=0), 3.0)
    dots = ' '.join(f'{60+i*680/max(len(rows)-1,1):.2f},{340-v/maximum*280:.2f}'
                    for i, v in enumerate(values))
    target.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400">'
                     '<rect width="100%" height="100%" fill="white"/>'
                     '<text x="60" y="25">SIMULATION ONLY - total Idd (A) by sweep index</text>'
                     '<path d="M60 50 V340 H760" fill="none" stroke="black"/>'
                     f'<text x="10" y="65">{maximum:.2f} A</text>'
                     f'<polyline points="{dots}" fill="none" stroke="blue"/>'
                     '<text x="350" y="380">Sweep index (Vgs pairs in CSV)</text></svg>')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--main-start', type=float, default=-2.89)
    p.add_argument('--main-stop', type=float, default=-2.69)
    p.add_argument('--main-step', type=float, default=0.05)
    p.add_argument('--peaking-start', type=float, default=-4.998)
    p.add_argument('--peaking-stop', type=float, default=-4.898)
    p.add_argument('--peaking-step', type=float, default=0.025)
    p.add_argument('--current-limit', type=float, default=3.0)
    p.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'results' / ('idd-sweep-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.csv'))
    args = p.parse_args()
    try:
        if not math.isfinite(args.current_limit) or not 0 < args.current_limit <= 3:
            raise ValueError('Current limit must be > 0 and <= 3 A')
        mains = points(args.main_start, args.main_stop, args.main_step)
        peaks = points(args.peaking_start, args.peaking_stop, args.peaking_step)
        if min(mains + peaks) < -5 or max(mains + peaks) > 0:
            raise ValueError('This simulator uses the -5 to 0 V DAC range')
        if len(mains) * len(peaks) > 100000:
            raise ValueError('At most 100000 sweep combinations')
    except ValueError as exc:
        p.error(str(exc))
    rows = list(sweep(mains, peaks, args.current_limit))
    # Exclusive creation protects earlier measurements from accidental overwrite.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    svg = args.output.with_suffix('.svg')
    if not svg.exists():
        write_svg(rows, svg)
    print(f'SIMULATION ONLY: {len(rows)} points; CSV: {args.output}; curve: {svg}')
    print('ACLR not measured; no optimal operating point selected.')
    if rows[-1]['status'] == 'current_limit':
        print('Sweep stopped at total Idd current limit.')


if __name__ == '__main__':
    try:
        main()
    except OSError as exc:
        print(f'File error: {exc}', file=sys.stderr)
        raise SystemExit(1)
    finally:
        if len(sys.argv) == 1 and sys.stdin.isatty():
            try:
                input('Press Enter to close...')
            except EOFError:
                pass
