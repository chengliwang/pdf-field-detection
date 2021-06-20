import io

def test_upload_pdf_for_prediction(mocker, test_client):
    mocked_task = mocker.patch('service.tasks.predict_task.delay', return_value=type('obj', (object,), {'id' : '123'}))
    file_name = "mock.pdf"
    data = {
        'pdf': (io.BytesIO(b"test pdf data"), file_name)
    }
    response = test_client.post('/v1/predict', data=data)
    assert response.status_code == 202
    assert response.get_json()["url"] == "/v1/status"
    assert response.get_json()["task_id"] == "123"