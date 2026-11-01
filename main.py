import click
import logging
import subprocess
import os
import sys
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
def main(iac_path, output_format, severity, framework, checkov_flags):
    """
    Analyzes Infrastructure-as-Code (IaC) templates for security misconfigurations using Checkov.
    """

    try:
        logging.info(f"Starting IaC analysis for path: {iac_path}")

        # Build the Checkov command
        command = [
            "checkov",
            # Checkov takes -d for a directory and -f for a single file, so the
            # flag is chosen by what the path is, not by what the user said. A
            # path that is neither, a broken symlink for instance, is sent as a
            # file and fails inside Checkov.
            "-d" if os.path.isdir(iac_path) else "-f", iac_path,  # Handle both files and directories
            "--framework", framework,
            "--severity", severity,
            "--output", output_format
        ]

        if checkov_flags:
            # Extra flags are split on whitespace, with no quoting rules. A flag
            # value that legitimately contains a space, such as a quoted skip
            # list, arrives at Checkov as several arguments and will not do what
            # the user typed.
            command.extend(checkov_flags.split())

        logging.debug(f"Checkov command: {' '.join(command)}")

        # Execute Checkov
        result = subprocess.run(command, capture_output=True, text=True, check=False) #Do not raise exceptions for non-zero exit codes

        # Report Checkov output on any return code. A non-zero code is
        # Checkov's normal findings outcome, so its stdout is the scan
        # report in the requested format, not a failure dump.
        if output_format == 'json':
            try:
                # When the JSON does not parse, the raw stdout is printed instead of
                # failing. Checkov writes progress and warnings into its output often
                # enough that strictness here would hide real reports. The cost is
                # that a json run can emit text that is not JSON at all.
                json_output = json.loads(result.stdout)
                print(json.dumps(json_output, indent=2))  # Pretty print JSON
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON output: {e}")
                print(result.stdout)  # Fallback to raw output
        else:
            print(result.stdout)

        if result.stderr:
            logging.error(f"Checkov stderr: {result.stderr}")

        # The verdict reaches this wrapper's exit code: exit with the
        # Checkov return code, so findings and scanner errors gate.
        if result.returncode != 0:
            logging.error(f"Checkov exited with code {result.returncode}; its report is printed above.")
            # Checkov's exit code becomes this wrapper's, unmapped. Findings and
            # scanner errors can share a code, so a caller gating on the number
            # alone cannot tell a dirty scan from a broken one; the printed report
            # and the stderr log carry that distinction.
            sys.exit(result.returncode)

        logging.info("Checkov analysis completed successfully.")

    except FileNotFoundError:
        logging.error("Checkov executable not found.  Please ensure Checkov is installed and in your PATH.")
        print("Error: Checkov executable not found.  Please ensure Checkov is installed and in your PATH.")
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}. See logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    # Usage example:
    # python3 main.py --iac-path path/to/your/iac/code --output-format json --severity HIGH
    # python3 main.py -i path/to/your/terraform/file.tf -o text -f terraform
    # python3 main.py -i path/to/your/kubernetes/manifests -f kubernetes -cf "--skip-check CKV_K8S_41"
    main()