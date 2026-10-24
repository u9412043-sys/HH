"""Two-stage Doherty PA characterization. Simulation only; no hardware I/O."""
import argparse
import csv
import math
import json
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

VERSION = '2.3'
MODEL_BOUNDS = {'main': (-5.0, -1.0), 'peaking': (-10.0, -1.0)}
RF_MODEL_BOUNDS = (0.0, 50.0)
MODEL_ID = 'illustrative-bounded-v3'
LIMIT_A = 3.0  # Total Main + Peaking drain current, not per-branch.
FIELDS = ['mode', 'stage', 'point_id', 'main_vgs_v', 'peaking_vgs_v',
          'main_idd_a', 'peaking_idd_a', 'total_idd_a', 'status',
          'rf_output_dbm', 'aclr_lower_dbc', 'aclr_upper_dbc', 'waveform']


def axis(start, stop, step):
    a, b, s = (Decimal(str(v)) for v in (start, stop, step))
    if not all(v.is_finite() for v in (a, b, s)) or s <= 0:
        raise ValueError('起點、終點與步距須為有限數值，步距須大於 0。')
    direction = Decimal(1) if b >= a else Decimal(-1)
    n = int(abs(b-a)//s)+1
    if n > 10000:
        raise ValueError('Too many axis points')
    return [float(a+i*s*direction) for i in range(n)]


def bias(v):
    v = float(v)
    if not math.isfinite(v) or not -10 <= v <= 0:
        raise ValueError('模擬電壓須在 -10～0 V；此範圍不是 PA 安全規格。')
    return v


def check_model_bias(main, peaking):
    for name, value in [('main', main), ('peaking', peaking)]:
        lo, hi = MODEL_BOUNDS[name]
        if not math.isfinite(value) or not lo <= value <= hi:
            raise ValueError(f'{name}={value} V 超出示意模型範圍 [{lo}, {hi}] V。'
                             '尚無實測校準，不能推算此偏壓的電流。'
                             '請按「恢復模擬範例」或縮小掃描範圍；不會產生量測檔。')


def check_rf_power(rf):
    lo, hi = RF_MODEL_BOUNDS
    if not math.isfinite(rf) or not lo <= rf <= hi:
        raise ValueError(f'RF 示意模型僅支援 {lo}～{hi} dBm，不能推算 {rf} dBm 的工作電流。'
                         '這不是實機功率限制；需要實測資料才能建立其他條件的模型。')


def currents(main, peaking):
    check_model_bias(main, peaking)
    # Bounded illustrative transfer curves, NOT fitted to the real PA.
    # Plateau amplitudes are arbitrary model parameters, NOT hardware limits.
    # Current is not clipped to the 3 A protection threshold.
    main_a = 1.6 / (1.0 + math.exp(-(main + 3.66566) / 0.45))
    peaking_a = 0.8 / (1.0 + math.exp(-(peaking + 4.0982) / 0.60))
    return main_a, peaking_a


def row(stage, point_id, main, peaking, rf=None, waveform=''):
    im, ip = currents(main, peaking)
    if rf is not None:
        check_rf_power(rf)
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
    events = sum(r['status'] == 'total_current_limit' for r in rows)
    print(f'總電流 >= 3 A 模擬事件：{events} 點；僅記錄，掃描不停止。')
    print('ACLR fields intentionally empty; no pass/fail or optimum selected.')


def rf_axis(args):
    start = getattr(args, 'rf_start', None)
    stop = getattr(args, 'rf_stop', None)
    if start is None and stop is None:
        power = getattr(args, 'rf_output_dbm', None)
        if power is not None:
            check_rf_power(power)
            return [power]
        start, stop = 0.0, 50.0
    if start is None or stop is None:
        raise ValueError('RF 起點與終點必須一起設定。')
    check_rf_power(start)
    check_rf_power(stop)
    return axis(start, stop, getattr(args, 'rf_step', 1.0))


def run(args):
    if args.stage == 'static':
        mains = axis(args.main_start, args.main_stop, args.main_step)
        peaks = axis(args.peaking_start, args.peaking_stop, args.peaking_step)
        if len(mains)*len(peaks) > 100000:
            raise ValueError('At most 100000 combinations')
        pairs = [(bias(m), bias(p)) for m in mains for p in peaks]
    else:
        powers = rf_axis(args)
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
                if r['status'] not in ('simulated', 'total_current_limit'):
                    continue
                pairs.append((bias(r['main_vgs_v']), bias(r['peaking_vgs_v'])))
                if len(pairs) > 100000:
                    raise ValueError('Too many candidates')
    if not pairs:
        raise ValueError('CSV 沒有可用候選點：請確認有第一階段資料，且狀態為 simulated 或 total_current_limit。')
    config = getattr(args, 'rd_config', None)
    if config:
        for m, p in pairs:
            for name, value in [('main', m), ('peaking', p)]:
                if not config[name+'_min'] <= value <= config[name+'_max']:
                    raise ValueError(name + ' Vgs exceeds RD limits')
    # Validate every candidate BEFORE simulation or file creation.
    for m, p in pairs:
        check_model_bias(m, p)
    powers = powers if args.stage == 'rf' else [None]
    if len(pairs) * len(powers) > 1000000:
        raise ValueError('總組合超過 1,000,000 點，請加大步距或減少候選偏壓。')
    rows = []
    for main, peak in pairs:
        for power in powers:
            rows.append(row(args.stage, len(rows)+1, main, peak, power,
                            args.waveform if args.stage == 'rf' else ''))
    # Simulation-only event recording: never stop, clip, or read real hardware.
    output = args.output or Path(__file__).resolve().parent/'results'/(
        args.stage+'-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.csv')
    save(rows, output)
    if config:
        with output.with_suffix('.settings.json').open('x', encoding='utf-8') as f:
            json.dump(dict(config, total_current_limit_a=LIMIT_A, mode='simulation',
                           stage=args.stage, model_id=MODEL_ID, version=VERSION, model_bounds=MODEL_BOUNDS,
                           rf_model_bounds_dbm=RF_MODEL_BOUNDS, rf_powers_dbm=powers,
                           overcurrent_policy='record_only_simulation',
                           waveform=getattr(args, 'waveform', None),
                           input_csv=str(getattr(args, 'input', '') or '')),
                      f, ensure_ascii=False, indent=2)
    return output, rows


# Example limits only: RD must replace them before any future hardware use.
DEFAULTS = dict(main_min=-5.0, main_max=-1.0, peaking_min=-10.0, peaking_max=-1.0,
                main_start=-1.0, main_stop=-5.0, main_step=.05,
                peaking_start=-1.0, peaking_stop=-10.0, peaking_step=.05)


def validate_config(config):
    if set(config) != set(DEFAULTS):
        raise ValueError('Config must contain exactly: ' + ', '.join(DEFAULTS))
    c = {k: float(v) for k, v in config.items()}
    for name in ('main', 'peaking'):
        lo, hi = bias(c[name+'_min']), bias(c[name+'_max'])
        if lo > hi:
            raise ValueError(name + '：RD 安全下限不得大於上限。')
        values = axis(c[name+'_start'], c[name+'_stop'], c[name+'_step'])
        # Check requested stop as well, even if the step does not land on it.
        if not (lo <= c[name+'_start'] <= hi and lo <= c[name+'_stop'] <= hi):
            raise ValueError(name + '：掃描起點與終點都必須在 RD 安全上下限內。')
    count = len(axis(c['main_start'], c['main_stop'], c['main_step'])) * len(axis(c['peaking_start'], c['peaking_stop'], c['peaking_step']))
    if count > 100000:
        raise ValueError('At most 100000 combinations')
    return c, count


def gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    root = tk.Tk()
    root.title('Doherty PA — RD 範圍設定 v' + VERSION + ' / SIMULATION ONLY')
    frame = ttk.Frame(root, padding=15)
    frame.grid()
    ttk.Label(frame, text='僅模擬，無實機控制。模型：Main -5～-1 V；Peaking -10～-1 V。', foreground='red').grid(row=0, columnspan=3, pady=8)
    entries = {}
    labels = {'min':'RD 安全下限 (V)', 'max':'RD 安全上限 (V)', 'start':'掃描起點 (V)', 'stop':'掃描終點 (V)', 'step':'步距大小 (V，填正數)'}
    ttk.Label(frame, text='設定').grid(row=1,column=0)
    ttk.Label(frame, text='Main').grid(row=1,column=1)
    ttk.Label(frame, text='Peaking').grid(row=1,column=2)
    for i, (suffix, label) in enumerate(labels.items(), 2):
        ttk.Label(frame,text=label).grid(row=i,column=0,sticky='w',pady=4)
        for j,name in enumerate(('main','peaking'),1):
            key=name+'_'+suffix
            entries[key]=tk.StringVar(value=str(DEFAULTS[key]))
            ttk.Entry(frame,textvariable=entries[key],width=20).grid(row=i,column=j,padx=5)
    ttk.Label(frame,text='方向由起終點決定；總電流 3 A 僅記錄事件，不停止').grid(row=7,columnspan=3,pady=10)
    result=tk.StringVar(value='第一階段：無 RF。第二階段：載入第一階段 CSV。')
    ttk.Label(frame,textvariable=result,wraplength=610).grid(row=12,columnspan=3,pady=10)
    rf_power=tk.StringVar(value='0')
    rf_stop=tk.StringVar(value='50')
    rf_step=tk.StringVar(value='1')
    waveform=tk.StringVar(value='demo')
    ttk.Label(frame,text='RF 起點 (0～50 dBm)').grid(row=9,column=0)
    ttk.Entry(frame,textvariable=rf_power).grid(row=9,column=1)
    ttk.Label(frame,text='波形名稱').grid(row=10,column=0)
    ttk.Entry(frame,textvariable=waveform).grid(row=10,column=1)

    def config():
        return validate_config({k:v.get() for k,v in entries.items()})

    def protect(action):
        try:
            action()
        except (ValueError, OSError, KeyError, csv.Error, TypeError) as exc:
            messagebox.showerror('設定或執行錯誤',str(exc))

    def save_config():
        c,_=config()
        target=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('RD config','*.json')])
        if target:
            c['rf_sweep'] = dict(start=float(rf_power.get()), stop=float(rf_stop.get()), step=float(rf_step.get()))
            rf_axis(argparse.Namespace(rf_start=c['rf_sweep']['start'], rf_stop=c['rf_sweep']['stop'], rf_step=c['rf_sweep']['step']))
            Path(target).write_text(json.dumps(c,indent=2),encoding='utf-8')
            result.set('RD 設定已儲存：'+target)

    def load_config():
        target=filedialog.askopenfilename(filetypes=[('RD config','*.json')])
        if target:
            saved=json.loads(Path(target).read_text(encoding='utf-8'))
            rf=saved.pop('rf_sweep', None)
            c,_=validate_config(saved)
            if rf is not None:
                rf_axis(argparse.Namespace(rf_start=rf['start'],rf_stop=rf['stop'],rf_step=rf['step']))
                rf_power.set(str(rf['start']));rf_stop.set(str(rf['stop']));rf_step.set(str(rf['step']))
            for k,v in c.items():
                entries[k].set(str(v))
            result.set('RD 設定已載入：'+target)

    def restore_example():
        for key, value in DEFAULTS.items():
            entries[key].set(str(value))
        rf_power.set('0')
        rf_stop.set('50')
        rf_step.set('1')
        waveform.set('demo')
        result.set('已恢復模擬範例。RD 範圍非實機安全規格，請重新執行第一階段。')

    def execute(stage):
        c,count=config()
        source=None
        if stage=='static':
            for m in (c['main_start'],c['main_stop']):
                for p in (c['peaking_start'],c['peaking_stop']):
                    check_model_bias(m,p)
        if stage=='rf':
            rf_axis(argparse.Namespace(rf_start=float(rf_power.get()), rf_stop=float(rf_stop.get()), rf_step=float(rf_step.get())))
            source=filedialog.askopenfilename(title='選擇第一階段 CSV',filetypes=[('CSV','*.csv')])
            if not source:
                return
        summary='模擬模式；不控制硬體。\n'
        for name in ('main','peaking'):
            summary+=f"{name}: {c[name+'_start']} → {c[name+'_stop']} V; step {c[name+'_step']} V\n"
        summary+=f'總電流 3 A 僅記錄；靜態網格 {count} 點。\n'
        if source:
            summary+=f'RF: {rf_power.get()} → {rf_stop.get()} dBm；步距 {rf_step.get()} dB\n'
            summary+='RF 階段以 CSV 候選偏壓為準，並檢查 RD 安全上下限。\n'+source+'\n'
        if not messagebox.askokcancel('確認後執行',summary):
            return
        target=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if not target:
            return
        args=argparse.Namespace(**c,stage=stage,rd_config=c,output=Path(target),
                                input=Path(source) if source else None,
                                rf_start=float(rf_power.get()) if stage=='rf' else None,
                                rf_stop=float(rf_stop.get()) if stage=='rf' else None,
                                rf_step=float(rf_step.get()) if stage=='rf' else 1,
                                waveform=waveform.get())
        output,rows=run(args)
        result.set(f'完成 {len(rows)} 點：{output}；結束狀態：{rows[-1]["status"]}。ACLR 未量測。')
        events=sum(r['status']=='total_current_limit' for r in rows)
        result.set(f'完成 {len(rows)} 點，3 A 模擬事件 {events} 點（僅記錄、不停止）：{output}')

    ttk.Button(frame,text='載入 RD 設定',command=lambda:protect(load_config)).grid(row=8,column=0)
    ttk.Button(frame,text='儲存 RD 設定',command=lambda:protect(save_config)).grid(row=8,column=1)
    ttk.Button(frame,text='第一階段：靜態掃描',command=lambda:protect(lambda:execute('static'))).grid(row=11,column=0,pady=10)
    ttk.Button(frame,text='第二階段：RF 模擬',command=lambda:protect(lambda:execute('rf'))).grid(row=11,column=1,pady=10)
    ttk.Button(frame,text='恢復模擬範例',command=restore_example).grid(row=13,column=0,pady=8)
    ttk.Label(frame,text='RF 終點 (0～50 dBm)').grid(row=14,column=0)
    ttk.Entry(frame,textvariable=rf_stop).grid(row=14,column=1)
    ttk.Label(frame,text='RF 步距大小 (dB，正數)').grid(row=15,column=0)
    ttk.Entry(frame,textvariable=rf_step).grid(row=15,column=1)
    root.mainloop()


def main():
    if len(sys.argv)==1:
        gui()
        return
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['static','rf'])
    parser.add_argument('--config',type=Path,required=True,help='RD JSON configuration')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--input',type=Path)
    parser.add_argument('--rf-output-dbm',type=float,help='相容舊版單點 RF 功率')
    parser.add_argument('--rf-start',type=float)
    parser.add_argument('--rf-stop',type=float)
    parser.add_argument('--rf-step',type=float,default=1)
    parser.add_argument('--waveform',default='demo')
    args=parser.parse_args()
    try:
        saved=json.loads(args.config.read_text(encoding='utf-8'))
        rf=saved.pop('rf_sweep',None)
        c,_=validate_config(saved)
        if rf is not None and args.rf_start is None and args.rf_stop is None and args.rf_output_dbm is None:
            args.rf_start,args.rf_stop,args.rf_step=rf['start'],rf['stop'],rf['step']
        for k,v in c.items():
            setattr(args,k,v)
        args.rd_config=c
        if args.stage=='rf' and not args.input:
            raise ValueError('RF stage requires --input static.csv')
        run(args)
    except (ValueError,OSError,KeyError,TypeError,csv.Error) as exc:
        parser.error(str(exc))


if __name__=='__main__':
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        if sys.stdin.isatty():
            input('Error. Press Enter to close...')
        raise SystemExit(1)
