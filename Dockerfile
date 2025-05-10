FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gdal-bin \
    python3-gdal \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*


ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal


# Installing Python dependencies clearly
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Command to run Streamlit application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
