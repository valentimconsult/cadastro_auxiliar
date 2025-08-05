FROM python:3.11-slim

# Reduce the Python image size and ensure logs are unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies and Python packages
RUN pip install --upgrade pip

# Copy dependency list first to leverage Docker cache
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Create application directory
WORKDIR /app

# Copy application files
COPY streamlit_app.py /app/
COPY api_server.py /app/
COPY users.json /app/
COPY tables.json /app/
COPY config.json /app/
COPY data /app/data

# Expose the default Streamlit port
EXPOSE 8501

# Run the Streamlit application
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]