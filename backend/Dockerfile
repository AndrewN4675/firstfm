# Build state
FROM python:3.12.10-slim AS builder
# apt-get update: Refresh packages (advanced packaging tool, debian)
# build-essential: C compiler
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends \
        build-essential \ 
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Any commands such as RUN or COPY will happen within the app folder 
WORKDIR /app

# Copy python modules from requirements.txt
# and install them
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

ENV PATH="/install/bin:${PATH}"    
ENV PYTHONPATH="/install/lib/python3.12/site-packages:${PYTHONPATH}"

# Copy everything else from the project 
# First dot -> Source (Host)
# Second dot -> Destination (Container's /app)
COPY . .

# Put static assets into folder
RUN python manage.py collectstatic --noinput 
RUN python manage.py migrate --noinput

# Create runtime image

FROM python:3.12.10-slim

# Create non-privileged user to limit 
# control on the container
RUN groupadd --system appgroup \ 
    && useradd --system --gid appgroup appuser

WORKDIR /app

COPY --from=builder /install /usr/local

COPY --from=builder /app /app

ENV PATH="/usr/local/bin:${PATH}"

# Tell the project where to listen for incoming
# requests.
ENV PORT=8080
EXPOSE 8080

USER appuser

# Start django app and bind interface to 8080, will change to something
# else later. sh -c expands the port
CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"]

# To build:
# Go to the parent folder (movie_nn)
# run docker build -t gcr.io/config/music-rec-backend:latest .

# To deploy to google artifact:
# docker push gcr.io/music-rec-prof/music-rec-backend:latest