"""Flask application: เลือกโหมด → รับฟอร์ม → เรียก dc_bias → แสดงผล."""

from flask import Flask, render_template, request

import dc_bias

app = Flask(__name__)

MODE_LABELS = {
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
    "divider": "Voltage Divider Bias",
}


@app.route("/")
def index():
    """หน้าหลัก: แสดงฟอร์มตามโหมดที่เลือก (GET)"""
    mode = request.args.get("mode", "divider")
    errors = []
    if mode not in dc_bias.MODE_FIELDS:
        errors = [f"โหมดไม่รู้จัก: {mode}"]
        mode = "divider"
    return render_template(
        "index.html",
        mode=mode,
        mode_label=MODE_LABELS[mode],
        errors=errors,
        form={},
    )


@app.route("/calculate", methods=["POST"])
def calculate():
    """รับฟอร์ม → ตรวจตามโหมด → เลือกสมการ → แสดงผลในหน้าเดิม"""
    form = request.form.to_dict()
    mode = form.get("mode", "divider")
    if mode not in dc_bias.MODE_FIELDS:
        return render_template(
            "index.html",
            errors=[f"โหมดไม่รู้จัก: {mode}"],
            form=form,
            mode=mode,
            mode_label=mode,
        )

    values, errors = dc_bias.parse_inputs(form, mode)
    if errors:
        return render_template(
            "index.html",
            errors=errors,
            form=form,
            mode=mode,
            mode_label=MODE_LABELS[mode],
        )

    approx = None
    if mode == "fixed":
        result = dc_bias.calculate_fixed(values)
    elif mode == "emitter":
        result = dc_bias.calculate_emitter(values)
    else:
        result = dc_bias.calculate(values)
        if result["region"] == "forward-active":
            approx = dc_bias.calculate_approximate(values)

    return render_template(
        "index.html",
        result=result,
        approx=approx,
        form=form,
        mode=mode,
        mode_label=MODE_LABELS[mode],
    )


if __name__ == "__main__":
    app.run(debug=True)
