FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --no-install-project ensures we don't need the source code yet
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application code
COPY . .

# Install the project
RUN uv sync --frozen --no-dev

# Set environment variables for the bot (to be overridden in K8s)
ENV LICHESS_TOKEN="" \
    OPENAI_BASE_URL="" \
    OPENAI_API_KEY="" \
    MODEL="" \
    PYTHONUNBUFFERED=1

# Use the virtual environment created by uv
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["python", "main.py"]
