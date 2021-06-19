FROM python:3.9.5-slim
USER root
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y procps vim redis-server coreutils make curl
COPY app app
COPY requirements.txt .
ADD ml_model/ml_model.tar.gz /app
RUN python -m pip install --upgrade pip && pip install -r requirements.txt
ENV FLASK_APP=/app/server.py
ENV PYTHONPATH=/app
COPY app/server.sh /app/server.sh
RUN chmod +x /app/server.sh
RUN useradd -ms /bin/bash appuser
RUN chown appuser:appuser /app -R
USER appuser
WORKDIR app
EXPOSE 80
CMD ["/bin/bash", "/app/server.sh"]