FROM rayproject/ray:2.41.0-py310

WORKDIR /app

RUN pip install --no-cache-dir httpx

COPY ray_serve/serve_app.py /app/serve_app.py

CMD ["ray", "serve", "run", "serve_app:app", "--host", "0.0.0.0", "--port", "8000"]
