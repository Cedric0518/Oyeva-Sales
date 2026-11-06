# The Oyeva Sales API as Azure Container Apps runs it (B7, docs/decisions/0012).
# Built in Azure by `az acr build`: no Docker needed on the developer's computer.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Only what the API reads at run time: its code, the sample file, the Statistics Canada copy.
COPY api/ api/
COPY evals/data/atlas/atlas_sales.xlsx evals/data/atlas/atlas_sales.xlsx
COPY tests/data/statcan_on_2026-10-23.json tests/data/statcan_on_2026-10-23.json

# Not root: the API needs no rights on the container.
RUN useradd --create-home --uid 10001 oyeva
USER oyeva

EXPOSE 8000
# The ingress of Container Apps is a proxy: trust its X-Forwarded headers.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
