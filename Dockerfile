FROM python:3.11.4-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY app ./app
COPY instance ./instance
COPY data_generators/university.py ./data_generators/university.py

EXPOSE 5000

CMD ["python", "app.py"]
