FROM python:3.12.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir semgrep==1.185.0 bandit==1.9.4
# amd64 release binary verified against upstream release asset checksum.
RUN test "$(uname -m)" = x86_64 && curl -fsSL https://github.com/opengrep/opengrep/releases/download/v1.33.1/opengrep_manylinux_x86 -o /usr/local/bin/opengrep && echo '46e8133cc490f9f50518061590ce2f6be5a08afaeda034471c0ceda4b3899808  /usr/local/bin/opengrep' | sha256sum -c - && chmod +x /usr/local/bin/opengrep
RUN pip freeze > /opt/python-packages.txt
WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1 SEMGREP_SEND_METRICS=off SEMGREP_ENABLE_VERSION_CHECK=0
ENTRYPOINT ["python", "shared/lab.py"]
