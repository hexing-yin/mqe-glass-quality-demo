# MQE Glass Quality Demo

This repository is the starting point for a future MQE glass quality demo
application. The planned project will use Python to explore and model glass
quality data, with:

- `pandas` for data loading and analysis
- `scikit-learn` for machine learning workflows
- `Streamlit` for an interactive demo interface

The repository is currently a scaffold. Its entry point prints a simple
confirmation message; no data analysis, model training, or Streamlit
interface has been implemented yet.

## Requirements

- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/) for dependency and environment management

## Setup

Clone the repository, enter the project directory, and install the locked
dependencies:

```bash
uv sync
```

This creates or updates a local `.venv` virtual environment based on
`pyproject.toml` and `uv.lock`.

## Run The Current Placeholder

Run the current Python entry point with:

```bash
uv run python main.py
```

Expected output:

```text
Hello from mqe-glass-quality-demo!
```

## Planned Direction

As the demo develops, this repository is intended to include:

- glass quality datasets or data-loading workflows
- exploratory analysis with `pandas`
- predictive modelling with `scikit-learn`
- an interactive `Streamlit` application for presenting results

Streamlit is already declared as a dependency, but there is not yet a
Streamlit app to launch.
