# Auto Field Detection Service

Using Machine Learning to auto detect relevant fields in PDF documents.

## Prebuilt Docker Images

index.docker.io/chengliwang/pdf-field-detection-svc:1.2

## Live Testing Endpoints

```bash
http://pdf-field-detection-svc.eastus2.azurecontainer.io/v1/predict

http://pdf-field-detection-svc.eastus2.azurecontainer.io/v1/status
```

## Usage

1. Upload a PDF file to the service  

   URL: /v1/predict   
   Method: POST   
   Params:

   ```bash
   Content-Disposition: form-data; name="pdf"; filename="sample.pdf"  
   Content-Type: application/pdf
   ```

   Response: return a task id and url for checking the task status

   ```bash
   Content-Type: application/json
   {  
      "task_id": "81d25fe8-afe8-4071-b2d2-6d70332948c4",  
      "url": "/v1/status"  
   }  
   ```
   
1. Check the task status   

   URL: /v1/status/<task_id>   
   Method: GET   
   Response: return the task status
   
   ```bash
   Content-Type: application/json
   {  
       "info": "Extracting page 2 of 7",  
       "state": "PROGRESS"  
   }  
   ```

   state will be 'PENDING', 'PROGRESS' or 'FAILURE'
   
   PDF file is returned if the task is successful
   
   ```bash
   Content-Type: application/pdf  
   Content-Disposition: inline; filename="sample.pdf"  
   ```

## How to run the service locally

Make sure you have `docker` installed.

Run the following commands from the project's folder:

```bash
docker build -t <docker image name> .
docker run -p 80:80 <docker image name>
```

API Endpoints:   

```bash
http://localhost/v1/predict

http://localhost/v1/status
```

## Unit testing

run all tests in the tests folder 

```bash
export PYTHONPATH=/app
cd tests
coverage run -m pytest -s
coverage report -i
```


## How to build the model

### Setting up local environment

1. Install Miniconda3
   
1. Create and activate the environment 

   ```bash
   conda create --name env pip
   conda activate env
   ```

1. Install Python packages

   ```bash
   pip install -r requirements.txt
   ```

### Generate the data and train the model

1. set PYTHONPATH to app folder

1. extract feature data from PDF files. here is a [sample PDF file](app/tests/data/train.pdf) for training. markup field name should start with the 'field' prefix.

   ```bash
   python pdf/extract.py -t PDF_FOLDER
   ```
   
1. copy the training.csv file in the PDF_FOLDER to ml_model

1. open the jupyter notebook 'field detection.ipynb', run all cells

1. create the tarball

   tar -czvf ml_model.tar.gz markup.pkl