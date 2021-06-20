import io

def test_get_prediction_state_pending(mocker, test_client):
    mocked_task = mocker.patch('service.tasks.predict_task.AsyncResult', return_value=type('obj', (object,), {'state' : 'PENDING', 'info': 'None'}))
    response = test_client.get('/v1/status/123')
    assert response.status_code == 200
    assert response.get_json()["state"] == "PENDING"
    assert response.get_json()["info"] == "None"

def test_get_prediction_state_success(mocker, test_client):
    mocked_task = mocker.patch('service.tasks.predict_task.AsyncResult', \
        return_value=type('obj', (object,), {'state' : 'SUCCESS', \
            'info': { 'data': "dGVzdCBwZGYgZGF0YQ==", 'attachment_filename': 'mock.pdf' }}))
    response = test_client.get('/v1/status/123')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/pdf'