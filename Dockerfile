FROM python:3.14

WORKDIR /app

ADD setup.py setup.py
ADD src src

RUN pip install . && rm setup.py && rm -rf src

STOPSIGNAL SIGINT

ENTRYPOINT ["python", "-m", "enapter_mcp_server"]
