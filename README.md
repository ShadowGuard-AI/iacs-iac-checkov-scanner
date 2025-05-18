# iacs-IaC-Dependency-Analyzer
Analyzes IaC code for external dependencies (e.g., modules from public registries) and identifies potential vulnerabilities or policy violations within those dependencies, including license compatibility checks. - Focused on Analyzes Infrastructure-as-Code (IaC) templates (e.g., Terraform, CloudFormation, Kubernetes manifests) for security misconfigurations before deployment.  Identifies potential vulnerabilities, compliance violations, and other security risks. Uses `checkov` for the core scanning engine and `click` for CLI interface.

## Install
`git clone https://github.com/ShadowStrikeHQ/iacs-iac-dependency-analyzer`

## Usage
`./iacs-iac-dependency-analyzer [params]`

## Parameters
- `-h`: Show help message and exit

## License
Copyright (c) ShadowStrikeHQ
