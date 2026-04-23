FROM python:3.10-slim

WORKDIR /app

# 🔧 System dependencies (optimized)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libheif1 \
    libde265-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# ⚡ Prevent Python from writing .pyc files & enable logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ⚡ CPU optimizations
ENV OMP_NUM_THREADS=8
ENV MKL_NUM_THREADS=8
ENV NUMEXPR_NUM_THREADS=8
ENV CUDA_VISIBLE_DEVICES=""

# 📦 Upgrade pip
RUN pip install --upgrade pip

# 🔥 Install PyTorch CPU first (cached layer)
RUN pip install --no-cache-dir \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# 📦 Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 📁 Copy project files
COPY . .

# 🗂️ Create runtime folders (important for Docker volumes)
RUN mkdir -p uploads outputs

# 🌐 Expose only if needed (API or Streamlit)
EXPOSE 8000

# 🔁 Default command (CHANGE depending on usage)

# 👉 Option 1: FastAPI (recommended)
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# 👉 Option 2: Worker (queue processing)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# 👉 Option 3 (old): Streamlit
# CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]