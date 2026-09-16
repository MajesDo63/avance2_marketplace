FROM python:3.11-slim

# 1. Crear un usuario sin privilegios para no ejecutar como root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 2. Definir directorio de trabajo seguro
WORKDIR /home/appuser/app

# 3. Copiar e instalar dependencias primero (aprovecha la cache de Docker)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el codigo de la app
COPY app/ .

# 5. Cambiar propietario de los archivos y cambiar al usuario no root
RUN chown -R appuser:appuser /home/appuser/app
USER appuser

EXPOSE 5000

# 6. Monitoreo de salud del contenedor
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/salud')" || exit 1

# 7. Servidor en produccion con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
