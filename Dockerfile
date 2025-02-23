FROM python:3.9

WORKDIR /app

COPY . /app

COPY satelite_images_sigpac /app/satelite_images_sigpac

ENV PYTHONPATH="/app"

RUN pip install -r requirements.txt

RUN mkdir -p /app/tests/output

EXPOSE 5000

CMD ["python", "/app/sigpac-above-the-clouds/app.py"]
