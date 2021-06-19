from flask import Blueprint, jsonify, request
from .tasks import predict_task
import base64

bp = Blueprint('predict', __name__, url_prefix='/v1')
@bp.route('/predict', methods=('POST',))

def index():
    input_pdf = request.files['pdf']
    input_pdf.stream.seek(0)
    task = predict_task.delay(input_pdf.filename, base64.b64encode(input_pdf.read()))
    return jsonify({ "task_id": task.id, "url": "/v1/status" }), 202