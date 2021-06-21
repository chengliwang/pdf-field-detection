FROM python:3.9.5-slim
USER root
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y procps vim redis-server coreutils make curl authbind
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
RUN touch /etc/authbind/byport/443
RUN chmod 500 /etc/authbind/byport/443
RUN chown appuser:appuser /etc/authbind/byport/443
USER appuser
WORKDIR app
EXPOSE 443
CMD ["/bin/bash", "/app/server.sh"]