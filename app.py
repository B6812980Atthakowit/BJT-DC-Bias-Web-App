"""Flask application: Lab 03 DC bias + Lab 04 CE amplifier simulation via ngspice."""

from __future__ import annotations

import math

from flask import Flask, render_template, request

import dc_bias
import spice_engine

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
try:
    app.jinja_loader.encoding = "utf-8"
except Exception:
    pass

MODE_LABELS = {
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
    "divider": "Voltage Divider Bias",
    "ce_amp": "CE Amplifier (Voltage Divider, SPICE)",
}

SPICE_DEFAULTS = {
    "rl": "10",
    "cin": "10",
    "cout": "10",
    "vin_amp": "10",
    "freq": "1",
    "fstart": "10",
    "fstop": "1000000",
    "points": "10",
    "tstop": "5",
    "tstep": "10",
}

ANALYSIS_LABELS = {
    "dc": "DC (.op)",
    "ac": "AC (.ac)",
    "tran": "Transient (.tran)",
}


def _num(raw: dict, key: str, label: str, errors: list[str], *, positive=False):
    if key not in raw or raw[key] is None or str(raw[key]).strip() == "":
        errors.append(f"??????????? {label}")
        return None
    try:
        val = float(raw[key])
    except (TypeError, ValueError):
        errors.append(f"{label} ??????????????")
        return None
    if positive and val <= 0:
        errors.append(f"{label} ???????????????? 0")
        return None
    if not math.isfinite(val):
        errors.append(f"{label} ??????????????????")
        return None
    return val


def parse_spice_inputs(raw: dict) -> tuple[dict | None, list[str]]:
    """Parse/validate CE amplifier SPICE inputs. R kOhm, C uF, vin mV, freq kHz."""
    errors: list[str] = []
    vcc = _num(raw, "vcc", "VCC", errors, positive=True)
    r1 = _num(raw, "r1", "R1", errors, positive=True)
    r2 = _num(raw, "r2", "R2", errors, positive=True)
    rc = _num(raw, "rc", "RC", errors, positive=True)
    re = _num(raw, "re", "RE", errors, positive=True)
    beta = _num(raw, "beta", "?", errors, positive=True)
    vbe = _num(raw, "vbe", "VBE", errors)
    rl = _num(raw, "rl", "RL", errors, positive=True)
    cin_u = _num(raw, "cin", "Cin", errors, positive=True)
    cout_u = _num(raw, "cout", "Cout", errors, positive=True)
    vin_amp_mv = _num(raw, "vin_amp", "Vin amplitude", errors, positive=True)
    freq_khz = _num(raw, "freq", "Frequency", errors, positive=True)
    analysis = raw.get("analysis", "dc")
    if analysis not in ANALYSIS_LABELS:
        errors.append(f"?????????????????????????: {analysis}")

    fstart = fstop = points = tstop_ms = tstep_us = None
    if analysis == "ac":
        fstart = _num(raw, "fstart", "fstart", errors, positive=True)
        fstop = _num(raw, "fstop", "fstop", errors, positive=True)
        points = _num(raw, "points", "points/decade", errors, positive=True)
        if fstart is not None and fstop is not None and fstart >= fstop:
            errors.append("fstart ???????????? fstop")
        if points is not None and (points < 2 or points > 200):
            errors.append("points/decade ??????????????? 2 ??? 200")
    if analysis == "tran":
        tstop_ms = _num(raw, "tstop", "tstop", errors, positive=True)
        tstep_us = _num(raw, "tstep", "tstep", errors, positive=True)
        if tstop_ms is not None and tstop_ms > 200:
            errors.append("tstop ??????????? 200 ms")
        if tstep_us is not None and tstep_us < 0.1:
            errors.append("tstep ??????????????? 0.1 us")
        if tstop_ms is not None and tstep_us is not None:
            tstop_s = tstop_ms / 1000.0
            tstep_s = tstep_us / 1e6
            if tstep_s >= tstop_s:
                errors.append("tstep ???????????? tstop")
            if tstop_s / tstep_s > 20000:
                errors.append("???????? transient ????????? (?? tstop ????????? tstep)")

    if errors:
        return None, errors

    params = {
        "vcc": vcc, "r1": r1 * 1000.0, "r2": r2 * 1000.0, "rc": rc * 1000.0,
        "re": re * 1000.0, "beta": beta, "vbe": vbe, "rl": rl * 1000.0,
        "cin": cin_u * 1e-6, "cout": cout_u * 1e-6,
        "vin_amp": vin_amp_mv / 1000.0, "freq": freq_khz * 1000.0,
        "analysis": analysis, "model_name": "Q2N2222_LAB", "bf": beta,
    }
    if analysis == "ac":
        params["fstart"] = fstart
        params["fstop"] = fstop
        params["points"] = int(points)
        params["ac_mag"] = vin_amp_mv / 1000.0
    if analysis == "tran":
        params["tstop"] = tstop_ms / 1000.0
        params["tstep"] = tstep_us / 1e6
    return params, []


def _default_form(mode: str) -> dict:
    if mode == "ce_amp":
        f = dict(SPICE_DEFAULTS)
        f.setdefault("analysis", "dc")
        return f
    return {}


@app.route("/")
def index():
    mode = request.args.get("mode", "divider")
    errors = []
    if mode not in MODE_LABELS:
        errors = [f"?????????????: {mode}"]
        mode = "divider"
    return render_template("index.html", mode=mode, mode_label=MODE_LABELS[mode],
                           errors=errors, form=_default_form(mode),
                           analysis=request.args.get("analysis", "dc"))


@app.route("/calculate", methods=["POST"])
def calculate():
    form = request.form.to_dict()
    mode = form.get("mode", "divider")
    if mode not in MODE_LABELS:
        return render_template("index.html", errors=[f"?????????????: {mode}"], form=form,
                               mode=mode, mode_label=mode, analysis=form.get("analysis", "dc"))
    if mode == "ce_amp":
        return _handle_ce_amp(form)

    values, errors = dc_bias.parse_inputs(form, mode)
    if errors:
        return render_template("index.html", errors=errors, form=form, mode=mode,
                               mode_label=MODE_LABELS[mode], analysis=form.get("analysis", "dc"))

    approx = None
    if mode == "fixed":
        result = dc_bias.calculate_fixed(values)
    elif mode == "emitter":
        result = dc_bias.calculate_emitter(values)
    else:
        result = dc_bias.calculate(values)
        if result["region"] == "forward-active":
            approx = dc_bias.calculate_approximate(values)

    return render_template("index.html", result=result, approx=approx, form=form, mode=mode,
                           mode_label=MODE_LABELS[mode], analysis=form.get("analysis", "dc"))


def _handle_ce_amp(form: dict):
    analysis = form.get("analysis", "dc")
    params, errors = parse_spice_inputs(form)
    if errors:
        return render_template("index.html", errors=errors, form=form, mode="ce_amp",
                               mode_label=MODE_LABELS["ce_amp"], analysis=analysis)
    dc_values = {k: params[k] for k in ("vcc","r1","r2","rc","re","beta","vbe")}
    analytical = dc_bias.calculate(dc_values)
    try:
        spice_result = spice_engine.run_simulation(params, analysis)
        if analysis == "dc" and spice_result.get("dc"):
            d = spice_result["dc"]
            vce = d.get("vce", 0)
            if d.get("ic", 0) <= 0:
                d["region"] = "cutoff"
            elif vce < spice_engine.VCE_SAT:
                d["region"] = "saturation"
            else:
                d["region"] = "active"
    except Exception as e:
        return render_template("index.html", errors=[f"SPICE simulation failed: {e}"], form=form,
                               mode="ce_amp", mode_label=MODE_LABELS["ce_amp"],
                               analysis=analysis, analytical=analytical, spice=None)
    return render_template("index.html", form=form, mode="ce_amp", mode_label=MODE_LABELS["ce_amp"],
                           analysis=analysis, analytical=analytical, spice=spice_result)


if __name__ == "__main__":
    app.run(debug=True)
