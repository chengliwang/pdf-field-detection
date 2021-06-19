from . import celery
import tempfile
import pikepdf
import csv
from pdf import pdf_parser, pdfUtil
import os, io, base64
import time
import pickle
import pandas as pd
from sklearn.feature_extraction import FeatureHasher
from sklearn.compose import ColumnTransformer

@celery.task(bind=True)
def predict_task(current_task, filename, data):
    start_time = time.time()

    # remove password
    current_task.update_state(state='PROGRESS', meta="Removing password on " + filename)
    print("Predict: " + filename)
    input_pdf = io.BytesIO(base64.b64decode(data))
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file_name = temp_file.name
    with pikepdf.open(input_pdf) as pdf:
        pdf.save(temp_file)
    
    # extract features
    stats = [0, 0]
    pages = pdf_parser.parse_pdf(temp_file_name, False, stats, current_task)
    temp_csv_file = tempfile.NamedTemporaryFile(delete=False)
    temp_csv_file_name = temp_csv_file.name
    pdfUtil.save_pdf_pages_tocsv(filename, pages, temp_csv_file_name)

    # prepare data
    markup_data = pd.read_csv(temp_csv_file_name)
    markup_data["HasCentLine"] = markup_data["HasCentLine"].astype(int)
    markup_data["HasComboLine"] = markup_data["HasComboLine"].astype(int)
    markup_data["IsMarkupField"] = markup_data["IsMarkupField"].astype(int)
    x = markup_data.drop(labels=['FileName', 'PageNum', 'LineLeft', 'LineRight', 'LineTop', 'LineBottom','Prefix','Suffix','FieldCode','FieldLeft',
'FieldRight', 'FieldTop', 'FieldBottom', "IsMarkupField"], axis=1)
    transformer = ColumnTransformer([("hash", FeatureHasher(n_features=2, input_type='string'), 'TopElement')], remainder="passthrough")
    transformed_x = transformer.fit_transform(x)
    
    # Get the model's prediction
    current_task.update_state(state='PROGRESS', meta="Get the model's prediction ")
    pdf_model = pickle.load(open("/app/ml_model/markup.pkl", "rb"))
    markup_data['IsMarkupField'] = pdf_model.predict_proba(transformed_x)[:,1]
    
    # markup the PDF
    temp_output_file = tempfile.NamedTemporaryFile(delete=False)
    temp_output_file_name = temp_output_file.name
    pdfUtil.markup_pdf(markup_data, temp_file_name, temp_output_file_name)

    # return marked up PDF
    return_data = io.BytesIO()
    with open(temp_output_file_name, 'rb') as fo:
        return_data.write(fo.read())
    return_data.seek(0)

    # clean up
    temp_file.close()
    temp_csv_file.close()
    temp_output_file.close()
    os.remove(temp_file_name)
    os.remove(temp_csv_file_name)
    os.remove(temp_output_file_name)

    total_time = "total time spent: " + str(time.time() - start_time)
    current_task.update_state(state='PROGRESS', meta=total_time)
    print(total_time)

    return { 'data': base64.b64encode(return_data.read()), 'attachment_filename': filename, 'mimetype': 'application/pdf' }