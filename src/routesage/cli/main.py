import click
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
from rich.theme import Theme
from rich.markdown import Markdown
from rich.table import Table
from pathlib import Path
from typing import Optional
import asyncio
from ..core import FastAPIAnalyzer
from ..core.llm import enhance_documentation_with_llm
from ..export import get_exporter, list_formats
from ..providers import get_provider, list_providers
from ..utils.logger import setup_logger, get_logger

# Initialize logger first with default settings
setup_logger()
logger = get_logger()

# Setup custom theme and console
theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "command": "magenta",
    "highlight": "bold blue"
})

console = Console(theme=theme)

def print_error(message: str):
    """Print error message in red with X symbol."""
    console.print(f"❌ Error: {message}", style="error")

def print_warning(message: str):
    """Print warning message in yellow with ! symbol."""
    console.print(f"⚠️  Warning: {message}", style="warning")

def print_success(message: str):
    """Print success message in green with ✓ symbol."""
    console.print(f"✅ {message}", style="success")

class RichGroup(click.Group):
    def format_help(self, ctx, formatter):
        console.print(Panel.fit(
            "🚀 Generate and enhance API documentation using various LLM providers",
            title="[bold cyan]RouteSage[/bold cyan]",
            border_style="cyan"
        ))
        
        # Commands section
        commands_table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        commands_table.add_column("Command", style="magenta")
        commands_table.add_column("Description")
        
        for cmd_name, cmd in self.commands.items():
            commands_table.add_row(
                cmd_name,
                cmd.get_short_help_str()
            )
        
        console.print("\n[bold cyan]Commands:[/bold cyan]")
        console.print(commands_table)
        
        # Usage examples
        console.print("\n[bold cyan]Examples:[/bold cyan]")
        console.print("""
• Generate documentation:
  [magenta]routesage generate app.py --api-key your-key[/magenta]

• List available formats:
  [magenta]routesage list-formats[/magenta]

• List LLM providers:
  [magenta]routesage list-providers[/magenta]
""")

@click.group(cls=RichGroup)
def cli():
    """RouteSage: LLM-powered FastAPI documentation tool."""
    pass

@cli.command()
@click.argument('app_path', type=click.Path(exists=True))
@click.option('--output', '-o', default='./docs', help='Output directory for documentation')
@click.option('--format', '-f', default='markdown', help='Output format (markdown, json)')
@click.option('--provider', '-p', default='openai', help='LLM provider (openai, anthropic, gemini, deepseek)')
@click.option('--model', '-m', help='Model name for the selected provider')
@click.option('--api-key', required=True, help='API key for the LLM provider')
@click.option('--no-cache', is_flag=True, help='Disable LLM response caching')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def generate(app_path: str, output: str, format: str, provider: str, 
            model: str, api_key: str, no_cache: bool, verbose: bool):
    try:
        # Configure logging based on verbosity
        if verbose:
            logger.info("Verbose logging enabled")
            setup_logger(level="DEBUG")
        
        logger.debug(f"Starting documentation generation for {app_path}")
        with console.status("[bold blue]Analyzing FastAPI application...") as status:
            analyzer = FastAPIAnalyzer(app_path)
            logger.debug("FastAPI analyzer initialized")
            
            # Pass both provider and model to analyze method
            docs = asyncio.run(analyzer.analyze(
                api_key=api_key,
                provider_name=provider,  # Pass the provider name
                model_name=model        # Pass the model name
            ))
            logger.info("Documentation extracted successfully")
            
            # Enhance with LLM if provider specified
            if provider:
                if not api_key:
                    logger.error("API key missing for LLM provider")
                    raise click.UsageError("API key is required when using an LLM provider")
                
                logger.debug(f"Using LLM provider: {provider}")
                status.update(f"[bold blue]Enhancing documentation using {provider}...")
                
                # Get default model if not specified
                if not model:
                    provider_class = get_provider(provider)
                    model = provider_class.default_model
                    logger.debug(f"Using default model: {model}")
                    print_warning(f"No model specified, using default: {model}")
                
                try:
                    logger.debug("Starting LLM enhancement")
                    docs = asyncio.run(enhance_documentation_with_llm(
                        docs=docs,
                        provider_name=provider,
                        model_name=model,
                        api_key=api_key,
                        cache_enabled=not no_cache
                    ))
                    logger.info("Documentation enhanced successfully")
                except Exception as e:
                    logger.error(f"LLM enhancement failed: {str(e)}", exc_info=True)
                    raise click.UsageError(f"LLM enhancement failed: {str(e)}")

            # Export documentation
            logger.debug(f"Exporting documentation in {format} format")
            status.update(f"[bold blue]Exporting documentation in {format} format...")
            exporter = get_exporter(format, output_dir=output)
            output_path = exporter.export(docs)
            logger.info(f"Documentation exported to: {output_path}")
            
            print_success(f"Documentation generated successfully: {output_path}")
            
    except Exception as e:
        logger.error(f"Error during documentation generation: {str(e)}", exc_info=True)
        print_error(str(e))
        if verbose:
            logger.exception("Detailed error information:")
        raise click.Abort()

def main():
    """Main entry point for the CLI."""
    try:
        logger.debug("Starting RouteSage CLI")
        cli()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print_error(f"Unexpected error: {str(e)}")
        raise click.Abort()

if __name__ == '__main__':
    main()