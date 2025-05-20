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
import sys  # Add sys import here
from ..core import FastAPIAnalyzer
from ..core.llm import enhance_documentation_with_llm
from ..export import get_exporter, list_formats
from ..export.json_exporter import JSONExporter
from ..export.markdown_exporter import MarkdownExporter  # Add MarkdownExporter import
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

# Update the CLI group with better description
@click.group()
def cli():
    """
    RouteSage: Intelligent FastAPI Documentation Generator
    
    RouteSage uses AI to analyze your FastAPI applications and generate
    comprehensive documentation automatically.
    """
    pass

# Add a new command to list available providers and models
@cli.command()
def providers():
    """List all available LLM providers and their supported models."""
    console = Console()
    
    console.print("\n[bold blue]Available LLM Providers and Models[/bold blue]\n")
    console.print("[italic]Note: If no model is specified, the default model will be used.[/italic]\n")
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Provider", style="cyan")
    table.add_column("Default Model", style="green")
    table.add_column("Supported Models", style="yellow")
    
    # OpenAI
    table.add_row(
        "openai", 
        "gpt-3.5-turbo",
        ", ".join(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"])
    )
    
    # Anthropic
    table.add_row(
        "anthropic", 
        "claude-3-opus",
        ", ".join(["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"])
    )
    
    # Gemini
    table.add_row(
        "gemini", 
        "gemini-pro",
        ", ".join(["gemini-pro", "gemini-2.0-flash"])
    )
    
    # DeepSeek
    table.add_row(
        "deepseek", 
        "deepseek-chat",
        ", ".join(["deepseek-chat", "deepseek-coder"])
    )
    
    console.print(table)
    console.print("\n")

# Add a help command to show examples
@cli.command()
def examples():
    """Show usage examples for RouteSage commands."""
    console = Console()
    
    console.print("\n[bold blue]RouteSage Usage Examples[/bold blue]\n")
    
    # Generate command examples
    console.print("[bold cyan]Generate Documentation:[/bold cyan]")
    console.print("  routesage generate ./my_fastapi_app --api-key YOUR_API_KEY")
    console.print("  routesage generate ./my_fastapi_app --provider openai --api-key YOUR_API_KEY  # Uses default model (gpt-3.5-turbo)")
    console.print("  routesage generate ./my_fastapi_app --provider openai --model gpt-4 --api-key YOUR_API_KEY")
    console.print("  routesage generate ./my_fastapi_app --output ./docs --format markdown --api-key YOUR_API_KEY")
    
    # List providers example
    console.print("\n[bold cyan]List Available Providers:[/bold cyan]")
    console.print("  routesage providers")
    
    # Show examples
    console.print("\n[bold cyan]Show These Examples:[/bold cyan]")
    console.print("  routesage examples")
    
    console.print("\n")

# Update the generate command with better help text
@cli.command()
@click.argument('app_path', type=click.Path(exists=True))
@click.option('--output', '-o', default='./docs', help='Output directory for documentation')
@click.option('--format', '-f', default='markdown', help='Output format (markdown, json)')
@click.option('--provider', '-p', default='openai', help='LLM provider (openai, anthropic, gemini, deepseek)')
@click.option('--model', '-m', help='Model name for the selected provider (use "routesage providers" to see options)')
@click.option('--api-key', required=True, help='API key for the LLM provider')
@click.option('--no-cache', is_flag=True, help='Disable LLM response caching')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--strict-verification', is_flag=True, help='Enable strict verification of routes')
@click.option('--min-confidence', type=float, default=0.5, help='Minimum confidence score for routes (0.0-1.0)')
def generate(app_path: str, output: str, format: str, provider: str, 
            model: str, api_key: str, no_cache: bool, verbose: bool,
            strict_verification: bool, min_confidence: float):
    """
    Generate documentation for a FastAPI application.
    
    APP_PATH is the path to your FastAPI application file or directory.
    
    Examples:
        routesage generate ./my_fastapi_app --api-key YOUR_API_KEY
        routesage generate ./app.py --provider anthropic --model claude-3-opus --api-key YOUR_API_KEY
    """
    try:
        # Configure logging based on verbosity
        if verbose:
            logger.info("Verbose logging enabled")
            setup_logger(level="DEBUG")
        
        logger.debug(f"Starting documentation generation for {app_path}")
        with console.status("[bold blue]Analyzing FastAPI application...") as status:
            analyzer = FastAPIAnalyzer(app_path)
            logger.debug("FastAPI analyzer initialized")
            
            # Pass both provider and model to analyze method along with verification flag
            docs = asyncio.run(analyzer.analyze(
                api_key=api_key,
                provider_name=provider,
                model_name=model,
                strict_verification=strict_verification,
                min_confidence=min_confidence
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

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--api-key', envvar='ROUTESAGE_API_KEY', help='API key for the LLM provider')
@click.option('--provider', default='openai', help='LLM provider to use')
@click.option('--model', help='Specific model to use (provider-dependent)')
@click.option('--format', 'export_format', default='markdown', help='Export format (markdown, json)')
@click.option('--output-dir', default='./docs', help='Output directory for documentation')
@click.option('--no-update', is_flag=True, help='Do not update the original code with documentation')
def generate(path, api_key, provider, model, export_format, output_dir, no_update):
    """Generate API documentation from a FastAPI file or project directory."""
    if not api_key:
        console.print("[bold red]Error:[/bold red] API key is required. Set ROUTESAGE_API_KEY environment variable or use --api-key option.")
        return
    
    try:
        path_obj = Path(path)
        if path_obj.is_file():
            console.print(f"[bold]Analyzing FastAPI file:[/bold] {path}")
        elif path_obj.is_dir():
            console.print(f"[bold]Analyzing FastAPI project directory:[/bold] {path}")
        else:
            console.print(f"[bold red]Error:[/bold red] Path {path} is neither a file nor a directory.")
            return
            
        # Initialize analyzer
        analyzer = FastAPIAnalyzer(path)
        
        with console.status(f"[bold green]Analyzing FastAPI application with {provider}...[/bold green]"):
            # Analyze the application - run the async function with asyncio
            import asyncio
            docs = asyncio.run(analyzer.analyze(api_key, provider, model))
        
        # Export documentation
        if export_format.lower() == 'json':
            exporter = JSONExporter(output_dir)
        else:
            exporter = MarkdownExporter(output_dir)
            
        output_file = exporter.export(docs)
        
        console.print(f"[bold green]Documentation generated successfully![/bold green]")
        console.print(f"Output file: [bold]{output_file}[/bold]")
        
        # Print summary
        console.print("\n[bold]API Documentation Summary:[/bold]")
        console.print(f"Title: {docs.title}")
        if docs.description:
            console.print(f"Description: {docs.description}")
        console.print(f"Version: {docs.version}")
        console.print(f"Total routes: {len(docs.routes)}")
        
        # Group routes by tags for display
        routes_by_tag = {}
        for route in docs.routes:
            tag = route.tags[0] if route.tags else "Other"
            if tag not in routes_by_tag:
                routes_by_tag[tag] = []
            routes_by_tag[tag].append(route)
        
        # Display routes by tag
        for tag, routes in routes_by_tag.items():
            console.print(f"\n[bold cyan]{tag}[/bold cyan] ({len(routes)} routes)")
            for route in routes:
                methods = ", ".join(route.methods)
                console.print(f"  [magenta]{methods}[/magenta] {route.path}")
                if route.source_file:
                    console.print(f"    Source: {route.source_file}")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if "--debug" in sys.argv:
            console.print_exception()

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