"""ngspice adapter for Lab 04 CE Voltage Divider amplifier simulator.

This module only builds netlists, runs ngspice, and parses outputs.
It does not import Flask.
"""

from __future__ import annotations

import csv
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

VCE_SAT = 0.2


class SpiceError(RuntimeError):
    """Raised when ngspice cannot be executed or returns invalid output."""


def resolve_ngspice() -> str:
    """Return ngspice executable path/name from env or PATH."""
    env = os.environ.get("NGSPICE_EXE")
    if env:
        p = Path(env)
        if p.exists():
            return str(p)
    for name in ("ngspice_con", "ngspice", "ngspice_con.exe", "ngspice.exe"):
        found = shutil.which(name)
        if found:
            return found
    # common local install location used in this workspace
    local = Path(r"C:\Users\B6812980\Documents\Default Project\ngspice\Spice64\bin\ngspice_con.exe")
    if local.exists():
        return str(local)
    raise SpiceError(
        "ไม่พบ ngspice ใน PATH กรุณาติดตั้ง ngspice และตั้งค่า PATH หรือ NGSPICE_EXE ให้ชี้ไปที่ ngspice_con.exe"
    )




def get_ngspice_version() -> str:
    try:
        exe = resolve_ngspice()
        proc = subprocess.run([exe, "-v"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, shell=False)
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        for line in text.splitlines():
            line = line.strip()
            if "ngspice" in line.lower():
                return line[:120]
        for line in text.splitlines():
            if line.strip():
                return line.strip()[:120]
    except Exception:
        pass
    return "unknown"
def _fmt_eng(value: float) -> str:
    """Format numeric value for SPICE netlist."""
    if not math.isfinite(value):
        raise SpiceError("ค่าพารามิเตอร์ไม่ถูกต้อง")
    return f"{value:.12g}"


def _parse_number(text: str) -> float | None:
    try:
        return float(text)
    except Exception:
        return None


def build_netlist(params: dict, analysis: str) -> str:
    """Build CE voltage-divider amplifier netlist for selected analysis."""
    vcc = params["vcc"]
    r1 = params["r1"]
    r2 = params["r2"]
    rc = params["rc"]
    re = params["re"]
    rl = params["rl"]
    cin = params["cin"]
    cout = params["cout"]
    vin_amp = params["vin_amp"]
    freq = params["freq"]
    ac_mag = params.get("ac_mag", vin_amp)

    model_name = params.get("model_name", "Q2N2222_LAB")
    bf = params.get("bf", 100)
    is_ = params.get("is", 14.34e-15)
    nf = params.get("nf", 1)

    lines = [
        "* Lab04 CE Voltage Divider Amplifier reference circuit",
        f"VCC vcc 0 DC {_fmt_eng(vcc)}",
        f"R1 vcc vb {_fmt_eng(r1)}",
        f"R2 vb 0 {_fmt_eng(r2)}",
        f"RC vcc vc {_fmt_eng(rc)}",
        f"RE ve 0 {_fmt_eng(re)}",
        f"Cin vin vb {_fmt_eng(cin)}",
        f"Cout vc vout {_fmt_eng(cout)}",
        f"RL vout 0 {_fmt_eng(rl)}",
        f"Q1 vc vb ve {model_name}",
        f".model {model_name} NPN(BF={_fmt_eng(bf)} IS={_fmt_eng(is_)} NF={_fmt_eng(nf)})",
    ]

    if analysis == "dc":
        lines.append(f"Vin vin 0 DC 0 AC 0 SIN(0 {_fmt_eng(vin_amp)} {_fmt_eng(freq)})")
        lines.append(".control")
        lines.append("set noaskquit")
        lines.append("set filetype=ascii")
        lines.append("op")
        lines.append("print v(vb) v(ve) v(vc) v(vout) i(VCC)")
        lines.append("quit")
        lines.append(".endc")
    elif analysis == "ac":
        fstart = params["fstart"]
        fstop = params["fstop"]
        points = int(params["points"])
        lines.append(f"Vin vin 0 DC 0 AC {_fmt_eng(ac_mag)}")
        lines.append(".control")
        lines.append("set noaskquit")
        lines.append("set filetype=ascii")
        lines.append(f"ac dec {points} {_fmt_eng(fstart)} {_fmt_eng(fstop)}")
        # wrdata writes complex as real,imag pairs in default mode; use explicit columns
        lines.append("wrdata ac_out.csv frequency v(vin) v(vout)")
        lines.append("quit")
        lines.append(".endc")
    elif analysis == "tran":
        tstop = params["tstop"]
        tstep = params["tstep"]
        lines.append(f"Vin vin 0 DC 0 AC 1 SIN(0 {_fmt_eng(vin_amp)} {_fmt_eng(freq)})")
        lines.append(".control")
        lines.append("set noaskquit")
        lines.append("set filetype=ascii")
        lines.append(f"tran {_fmt_eng(tstep)} {_fmt_eng(tstop)}")
        lines.append("wrdata tran_out.csv time v(vin) v(vout)")
        lines.append("quit")
        lines.append(".endc")
    else:
        raise SpiceError(f"ไม่รู้จักโหมดการวิเคราะห์: {analysis}")

    lines.append(".end")
    return "\n".join(lines) + "\n"


def _run_ngspice(netlist: str, workdir: Path, timeout: float = 30.0) -> tuple[str, str, int]:
    exe = resolve_ngspice()
    netlist_path = workdir / "circuit.cir"
    log_path = workdir / "run.log"
    netlist_path.write_text(netlist, encoding="utf-8", newline="\n")

    cmd = [exe, "-b", "-o", str(log_path), str(netlist_path)]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
    except FileNotFoundError as e:
        raise SpiceError(f"ไม่พบโปรแกรม ngspice: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise SpiceError(f"ngspice ทำงานเกินเวลา ({timeout:.0f}s)") from e

    log_text = ""
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined = "\n".join([log_text, stdout, stderr]).strip()
    return combined, str(log_path), proc.returncode


def _check_log(log_text: str, returncode: int) -> None:
    lowered = log_text.lower()
    fatal_markers = [
        "fatal error",
        "simulation interrupted",
        "no such vector",
        "can't open",
        "cannot open",
        "undefined",
        "syntax error",
        "doanalyses:",
    ]
    for marker in fatal_markers:
        if marker in lowered:
            # allow "no such vector" only if not present? keep strict
            raise SpiceError(f"ngspice รายงานข้อผิดพลาด: {marker}")
    if returncode not in (0,):
        # ngspice sometimes returns nonzero on warnings; only fail if log has error-ish output
        if "error" in lowered:
            raise SpiceError(f"ngspice จบด้วยรหัส {returncode}")


def _parse_wrdata(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("*"):
            continue
        parts = re.split(r"\s+", line)
        nums: list[float] = []
        for p in parts:
            n = _parse_number(p)
            if n is not None:
                nums.append(n)
        if nums:
            rows.append(nums)
    return rows


def _parse_ac_rows(path: Path) -> list[dict]:
    rows = _parse_wrdata(path)
    out = []
    for r in rows:
        # wrdata for: frequency v(vin) v(vout)
        # observed format: idx, freq_scale,freq, vin_scale,vin_r,vin_i, vout_scale,vout_r,vout_i (9 cols)
        if len(r) >= 9:
            freq = r[1]
            vin_r, vin_i = r[4], r[5]
            vout_r, vout_i = r[7], r[8]
        elif len(r) >= 6:
            # fallback: idx,freq,vin_r,vin_i,vout_r,vout_i
            freq = r[1]
            vin_r, vin_i = r[2], r[3]
            vout_r, vout_i = r[4], r[5]
        elif len(r) >= 5:
            freq, vin_r, vin_i, vout_r, vout_i = r[:5]
        else:
            continue
        vin_mag = math.sqrt(vin_r * vin_r + vin_i * vin_i)
        vout_mag = math.sqrt(vout_r * vout_r + vout_i * vout_i)
        gain = (vout_mag / vin_mag) if vin_mag > 1e-18 else float("nan")
        gain_db = 20 * math.log10(gain) if gain > 0 and math.isfinite(gain) else float("nan")
        phase = math.degrees(math.atan2(vout_i, vout_r) - math.atan2(vin_i, vin_r))
        phase = ((phase + 180) % 360) - 180
        out.append({"frequency_hz": freq, "vin_mag": vin_mag, "vout_mag": vout_mag,
                    "gain": gain, "gain_db": gain_db, "phase_deg": phase})
    dedup = {}
    for row in out:
        dedup[round(row["frequency_hz"], 9)] = row
    return [dedup[k] for k in sorted(dedup.keys())]


def _parse_tran_rows(path: Path) -> list[dict]:
    rows = _parse_wrdata(path)
    out = []
    for r in rows:
        # wrdata for: time v(vin) v(vout)
        # observed: idx, t,t, t,vin, t,vout (6 cols) i.e. (scale,val) pairs
        if len(r) >= 6:
            t = r[1]
            vin = r[3]
            vout = r[5]
        elif len(r) >= 4:
            # idx,time,vin,vout
            t, vin, vout = r[1], r[2], r[3]
        elif len(r) >= 3:
            t, vin, vout = r[0], r[1], r[2]
        else:
            continue
        out.append({"time_s": t, "vin_v": vin, "vout_v": vout})
    dedup = {}
    for row in out:
        dedup[round(row["time_s"], 15)] = row
    return [dedup[k] for k in sorted(dedup.keys())]


def _parse_op(log_text: str) -> dict:
    # ngspice print output lines like: v(vb) = 1.942157e+00
    patterns = {
        "vb": r"v\(vb\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)",
        "ve": r"v\(ve\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)",
        "vc": r"v\(vc\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)",
        "vout_dc": r"v\(vout\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)",
        "i_vcc": r"i\(vcc\)\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)",
    }
    result = {}
    low = log_text
    for key, pat in patterns.items():
        m = re.search(pat, low, flags=re.IGNORECASE)
        if not m:
            raise SpiceError(f"อ่านค่า {key} จากผล ngspice ไม่ได้")
        result[key] = float(m.group(1))

    vb, ve, vc = result["vb"], result["ve"], result["vc"]
    vce = vc - ve
    result["vce"] = vce
    # estimate currents from circuit resistors? We have node voltages and source current.
    # IC ~= (VCC-VC)/RC, IE ~= VE/RE in this reference circuit.
    return result


def run_simulation(params: dict, analysis: str) -> dict:
    """Run selected ngspice analysis and return parsed data."""
    netlist = build_netlist(params, analysis)
    with tempfile.TemporaryDirectory(prefix="bjt_lab04_") as td:
        workdir = Path(td)
        log_text, log_path, returncode = _run_ngspice(netlist, workdir)
        _check_log(log_text, returncode)
        out = {
            "engine": "ngspice",
            "engine_version": get_ngspice_version(),
            "model": f"{params.get('model_name','Q2N2222_LAB')} NPN(BF={_fmt_eng(params.get('bf',100))} IS={_fmt_eng(params.get('is',14.34e-15))} NF={_fmt_eng(params.get('nf',1))})",
            "analysis": analysis,
            "netlist": netlist,
            "log_excerpt": "\n".join(log_text.splitlines()[-40:]),
            "run_status": "ok",
        }
        if analysis == "dc":
            op = _parse_op(log_text)
            # derive currents using known resistors from params
            vcc = params["vcc"]
            rc = params["rc"]
            re = params["re"]
            r1 = params["r1"]
            r2 = params["r2"]
            ic = (vcc - op["vc"]) / rc
            ie = op["ve"] / re
            ib = ie - ic
            ir1 = (vcc - op["vb"]) / r1
            ir2 = op["vb"] / r2
            op.update({
                "ic": ic,
                "ie": ie,
                "ib": ib,
                "ir1": ir1,
                "ir2": ir2,
                "region_hint": "saturation?" if op["vce"] < VCE_SAT else "active-ish",
            })
            out["dc"] = op
        elif analysis == "ac":
            rows = _parse_ac_rows(workdir / "ac_out.csv")
            if not rows:
                raise SpiceError("ไม่พบข้อมูลผลลัพธ์ AC จาก ngspice")
            out["ac"] = rows
            # summary
            gains = [r["gain_db"] for r in rows if math.isfinite(r["gain_db"])]
            out["ac_summary"] = {
                "points": len(rows),
                "fmin_hz": rows[0]["frequency_hz"],
                "fmax_hz": rows[-1]["frequency_hz"],
                "max_gain_db": max(gains) if gains else None,
            }
        elif analysis == "tran":
            rows = _parse_tran_rows(workdir / "tran_out.csv")
            if not rows:
                raise SpiceError("ไม่พบข้อมูลผลลัพธ์ Transient จาก ngspice")
            out["tran"] = rows
            vin_pp = (max(r["vin_v"] for r in rows) - min(r["vin_v"] for r in rows))
            vout_pp = (max(r["vout_v"] for r in rows) - min(r["vout_v"] for r in rows))
            out["tran_summary"] = {
                "points": len(rows),
                "tstart_s": rows[0]["time_s"],
                "tstop_s": rows[-1]["time_s"],
                "vin_pp_v": vin_pp,
                "vout_pp_v": vout_pp,
            }
        return out
