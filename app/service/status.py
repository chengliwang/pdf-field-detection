from flask import Blueprint, jsonify, send_file
from .tasks import predict_task
import base64, io

bp = Blueprint('status/<task_id>', __name__, url_prefix='/v1')
@bp.route('/status/<task_id>', methods=('GET',))

def index(task_id):
    task = predict_task.AsyncResult(task_id)
    response = {
        'state': task.state
    }
    if task.state == 'SUCCESS':
        data = task.info.get('data', '')
        filename = task.info.get('attachment_filename', '')
        return send_file(io.BytesIO(base64.b64decode(data)), mimetype='application/pdf', attachment_filename=filename, as_attachment=True)
    else:
        response['info'] = str(task.info)
    return jsonify(response)