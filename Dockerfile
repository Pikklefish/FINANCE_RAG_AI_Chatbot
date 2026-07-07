#Base Image
#(smaller image than full python)
FROM python:3.12-slim 

#Working Directory
WORKDIR /app

#System Dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*
    
#Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Application Code
COPY app/ ./app/
COPY app/__init__.py ./app/__init__.py

#Streamlit Config
RUN mkdir -p .streamlit
RUN echo '\
[server]\n\
headless = true\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
[browser]\n\
gatherUsageStats = false\n\
' > .streamlit/config.toml

#PORT
EXPOSE 8501

#Health Check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

#Start Command
ENTRYPOINT ["streamlit", "run", "app/main.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0"]