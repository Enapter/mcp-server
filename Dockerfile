FROM python:3.14

ENV ENAPTER_MCP_SERVER_ADDRESS=0.0.0.0:8000

WORKDIR /app

RUN pip install --no-cache-dir pipenv

COPY Pipfile Pipfile.lock setup.py ./
COPY src ./src

RUN pipenv install --system --deploy

STOPSIGNAL SIGINT

ENTRYPOINT ["python", "-m", "enapter_mcp_server"]

CMD ["serve"]
