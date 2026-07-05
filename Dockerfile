# Container image for the optional MCP delivery adapter
# (scripts/mcp_server.py, see docs/architecture/adr/0007-mcp-delivery-adapter.md).
# Lets an MCP client run this router on a host with no local Python install
# (see LISS-0006). Not used by the CLI/skill path, which stays Python-native.
FROM python:3.12-slim

WORKDIR /app

COPY requirements-mcp.txt ./
RUN pip install --no-cache-dir -r requirements-mcp.txt

COPY scripts/ ./scripts/
COPY references/ ./references/

ENTRYPOINT ["python3", "scripts/mcp_server.py"]
