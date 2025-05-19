
<p align="center">
  <img src="assets/routesage.svg" alt="RouteSage Logo" width="200"/>
</p>


# RouteSage

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)](https://github.com/dijo-d/RouteSage)

RouteSage is a Python CLI tool and package that automatically generates human-readable documentation for FastAPI projects. It scans your codebase using Python's AST, interprets routes, and enriches them with descriptions and tags powered by your choice of LLM provider.

## Features

* **Multiple LLM Providers**: Supports OpenAI, Gemini, Anthropic, and DeepSeek.
* **Bring Your Own Key (BYOK)**: Use any provider’s API key and models.
* **LLM Caching**: Avoid repeated API calls by caching previous responses.
* **Verbose Mode**: Detailed logs for debugging and insight into the generation process.
* **Flexible Output**: Generate documentation as JSON or Markdown.
* **AST-Based Extraction**: Leverages Python’s `ast` module for robust route introspection.
* **Retry Mechanism**: Built-in efficient model retry logic to handle transient failures.

> **Note:** This is currently a Python package available via github repository and is not yet published on PyPI.

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/dijo-d/RouteSage.git
   ```
2. **Navigate to the project directory**:

   ```bash
   cd RouteSage
   ```
3. **Install in editable mode**:

   ```bash
   pip install -e .
   ```

## Usage

```bash
routesage generate <FILEPATH> \
  --provider <LLM_PROVIDER> \
  --model <LLM_MODEL> \
  --api-key <YOUR_API_KEY> \
  [--output <OUTPUT_PATH>] \
  [--format json|md] \
  [--verbose] \
  [--help]
```

* `<FILEPATH>`: Path to your FastAPI project or Python file containing route definitions.
* `--provider`: LLM provider to use (`openai`, `gemini`, `anthropic`, `deepseek`).
* `--model`: Specific model name offered by the provider.
* `--api-key`: Your API key for the chosen LLM provider.
* `--output` (optional): File path for generated docs (default: `routes_documentation.md`).
* `--format` (optional): Output format, either `json` or `md` (default: `md`).
* `--verbose` (optional): Enable verbose logging.
* `--help` (optional): Display help message for usage.

## How It Works

1. **Scan**: Recursively traverses Python files to locate FastAPI `app` and `APIRouter` route decorators.
2. **Parse**: Extracts HTTP method, path, parameters, and existing docstrings via AST.
3. **Generate**: Sends prompts to the configured LLM to produce or enhance `description` and `tags`.
4. **Output**: Writes enriched documentation to your decorated routes or as standalone JSON/Markdown.

## Roadmap

* [ ] Publish package to PyPI.
* [ ] HTML and Swagger UI integration.
* [ ] Additional language/framework support.
* [ ] Interactive Web UI for visualizing and generating route documentation live.
* [ ] Secure storage of API keys using OS-native credential managers.

## Contributions are welcome!

We encourage developers to contribute to RouteSage and support the broader open-source ecosystem. Whether it's bug fixes, new features, documentation improvements, or ideas, your input is valued and appreciated

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/xyz`
3. Commit changes: `git commit -m "feat: description of feature"`
4. Push to branch: `git push origin feature/xyz`
5. Open a Pull Request

## License

[MIT © Dijo (dijo-d)](https://github.com/dijo-d/RouteSage/blob/main/LICENSE)



