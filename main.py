import click
import logging
import subprocess
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def validate_iac_path(ctx, param, value):
    """Validates that the provided IaC path exists."""
    if not os.path.exists(value):
        raise click.BadParameter(f"The specified path '{value}' does not exist.")
    return value

def validate_output_format(ctx, param, value):
    """Validates that the output format is supported."""
    supported_formats = ['json', 'text']
    if value.lower() not in supported_formats:
        raise click.BadParameter(f"Invalid output format. Supported formats are: {', '.join(supported_formats)}")
    return value.lower()

@click.command()
@click.option('--iac-path', '-i', required=True, type=click.Path(exists=True), callback=validate_iac_path,
              help='Path to the Infrastructure-as-Code (IaC) directory or file.')
@click.option('--output-format', '-o', default='text', type=str, callback=validate_output_format,
              help='Output format (json or text). Default: text')
@click.option('--severity', '-s', default='MEDIUM', type=click.Choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
              help='Minimum severity level to report. Default: MEDIUM')
@click.option('--framework', '-f', default='terraform', type=click.Choice(['terraform', 'cloudformation', 'kubernetes']),
              help='IaC framework to scan. Default: terraform')
@click.option('--checkov-flags', '-cf', default='', type=str, help='Additional flags to pass to Checkov.')
@click.option('--license-check', '-lc', is_flag=True, help='Enable license compatibility checks.  Not yet fully implemented.')
def main(iac_path, output_format, severity, framework, checkov_flags, license_check):
    """
    Analyzes Infrastructure-as-Code (IaC) templates for security misconfigurations using Checkov.
    """

    try:
        logging.info(f"Starting IaC analysis for path: {iac_path}")

        # Build the Checkov command
        command = [
            "checkov",
            "-d" if os.path.isdir(iac_path) else "-f", iac_path,  # Handle both files and directories
            "--framework", framework,
            "--severity", severity,
            "--output", output_format
        ]

        if checkov_flags:
            command.extend(checkov_flags.split())

        logging.debug(f"Checkov command: {' '.join(command)}")

        # Execute Checkov
        result = subprocess.run(command, capture_output=True, text=True, check=False) #Do not raise exceptions for non-zero exit codes

        # Handle Checkov output
        if result.returncode == 0:
            logging.info("Checkov analysis completed successfully.")
            if output_format == 'json':
                try:
                    json_output = json.loads(result.stdout)
                    print(json.dumps(json_output, indent=2))  # Pretty print JSON
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON output: {e}")
                    print(result.stdout)  # Fallback to raw output
            else:
                print(result.stdout)
        else:
            logging.error(f"Checkov analysis failed with exit code {result.returncode}")
            logging.error(f"Checkov stdout: {result.stdout}")
            logging.error(f"Checkov stderr: {result.stderr}")
            print(f"Checkov analysis failed. See logs for details.  Stdout: {result.stdout}, Stderr: {result.stderr}")

        if license_check:
            logging.warning("License compatibility checks are not yet fully implemented.")
            print("Warning: License compatibility checks are not yet fully implemented.")

    except FileNotFoundError:
        logging.error("Checkov executable not found.  Please ensure Checkov is installed and in your PATH.")
        print("Error: Checkov executable not found.  Please ensure Checkov is installed and in your PATH.")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}. See logs for details.")


if __name__ == "__main__":
    # Usage example:
    # iacs-IaC-Dependency-Analyzer --iac-path path/to/your/iac/code --output-format json --severity HIGH
    # iacs-IaC-Dependency-Analyzer -i path/to/your/terraform/file.tf -o text -f terraform
    # iacs-IaC-Dependency-Analyzer -i path/to/your/kubernetes/manifests -f kubernetes -cf "--skip-check CKV_K8S_41"
    main()