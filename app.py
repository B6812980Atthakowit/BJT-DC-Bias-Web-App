"""Flask application: ฟอร์มรับค่าวงจร → เรียก dc_bias คำนวณ → แสดงผล."""

from flask import Flask, render_template, request

import dc_bias

app = Flask(__name__)


@app.route("/")
def index():
    """หน้าหลัก: แสดงฟอร์มกรอกค่า (GET)"""
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    """รับฟอร์ม → ตรวจค่า → คำนวณ DC bias → แสดงผลในหน้าเดิม"""
    form = request.form.to_dict()
    values, errors = dc_bias.parse_inputs(form)
    if errors:
        return render_template("index.html", errors=errors, form=form)
    result = dc_bias.calculate(values)
    approx = dc_bias.calculate_approximate(values)
    return render_template("index.html", result=result, approx=approx, form=form)


if __name__ == "__main__":
    app.run(debug=True)
