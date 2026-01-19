FROM python:3.14

ENV ENAPTER_MCP_SERVER_ADDRESS=0.0.0.0:8000

WORKDIR /app

ADD setup.py setup.py
ADD src src

RUN pip install . && rm setup.py && rm -rf src

STOPSIGNAL SIGINT

ENTRYPOINT ["python", "-m", "enapter_mcp_server"]
