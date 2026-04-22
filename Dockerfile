FROM python:3.10

WORKDIR /app

# System dependencies (OpenCV, image libs, etc.)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libheif1 \
    libde265-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first (IMPORTANT)
RUN pip install --upgrade pip

# Install PyTorch CPU first (faster + more reliable)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Then install the rest
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Force CPU usage
ENV CUDA_VISIBLE_DEVICES=""

# CPU optimizations (perfect for your i7-4702MQ)
ENV OMP_NUM_THREADS=8
ENV MKL_NUM_THREADS=8
ENV NUMEXPR_NUM_THREADS=8

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]