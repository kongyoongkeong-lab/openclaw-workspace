#!/usr/bin/env python3
"""
LMT Pipeline - Email Generation Script
Generates personalized emails using CSV data and templating
"""

import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from jinja2 import Template

# Load environment variables
load_dotenv()

# Configuration
ENV = os.getenv("ENV", "dev")
API_KEY = os.getenv("OPENAI_API_KEY")
OUTPUT_DIR = "./emails"

def load_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Load CSV data into a list of dictionaries.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of dictionaries, where each dict represents a row
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        csv.Error: If CSV parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    except Exception as e:
        raise csv.Error(f"Failed to parse CSV: {e}")

def load_template(template_path: str) -> Template:
    """
    Load email template from file.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        Jinja2 Template object
        
    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return Template(f.read())
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file not found: {template_path}")

def generate_personalized_email(
    data_row: Dict[str, str],
    template: Template,
    output_format: str = "text"
) -> str:
    """
    Generate personalized email content.
    
    Args:
        data_row: CSV row data
        template: Jinja2 Template object
        output_format: Output format ('text', 'html', or 'markdown')
        
    Returns:
        Generated email content string
        
    Raises:
        ValueError: If output_format is not supported
    """
    try:
        # Validate output format
        valid_formats = ['text', 'html', 'markdown']
        if output_format not in valid_formats:
            raise ValueError(f"Invalid output format: {output_format}. Use one of: {valid_formats}")
        
        # Render template with data
        email_content = template.render(**data_row)
        return email_content
    except Exception as e:
        raise ValueError(f"Failed to generate email: {e}")

def save_email(
    email_content: str,
    filename: str,
    output_dir: str = "./emails",
    output_format: str = "text"
) -> str:
    """
    Save generated email to file.
    
    Args:
        email_content: Email content string
        filename: Output filename (without extension)
        output_dir: Directory to save emails
        
    Returns:
        Full path to saved file
    """
    # Determine file extension based on content
    extension = 'txt'  # default
    if output_format == 'html':
        extension = 'html'
    elif output_format == 'markdown':
        extension = 'md'
    
    filepath = os.path.join(output_dir, f"{filename}.{extension}")
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Save file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(email_content)
    
    return filepath

def process_emails(
    csv_path: str,
    template_path: str,
    output_dir: str = "./emails",
    output_format: str = "text",
    batch_size: int = 1
) -> List[str]:
    """
    Process multiple emails from CSV data.
    
    Args:
        csv_path: Path to CSV file with recipient data
        template_path: Path to email template
        output_dir: Directory to save generated emails
        output_format: Output format ('text', 'html', 'markdown')
        batch_size: Number of emails to process in one batch (for rate limiting)
        
    Returns:
        List of file paths to generated emails
        
    Raises:
        FileNotFoundError: If input files don't exist
        ValueError: If output format is invalid
    """
    try:
        # Load CSV data
        data_rows = load_csv(csv_path)
        
        # Load template
        template = load_template(template_path)
        
        # Process emails
        generated_emails = []
        
        for idx, row in enumerate(data_rows, 1):
            # Generate email
            email_content = generate_personalized_email(row, template, output_format)
            
            # Save email
            filepath = save_email(email_content, f"email_{idx}", output_dir, output_format)
            generated_emails.append(filepath)
            
            # Optional: Rate limiting (comment out for production)
            # time.sleep(0.1)  # 100ms delay between emails
        
        print(f"Generated {len(generated_emails)} emails.")
        return generated_emails
        
    except Exception as e:
        print(f"Error processing emails: {e}")
        raise


def main():
    """
    Main entry point.
    """
    # Configuration
    CSV_FILE = "recipients.csv"
    TEMPLATE_FILE = "template.html"
    
    # Validate environment
    if ENV == "dev":
        print("Running in development mode...")
    else:
        print(f"Running in {ENV} mode...")
    
    if not API_KEY:
        print("Warning: OPENAI_API_KEY not set. Skipping AI-assisted templating.")
        print("Use environment variable or .env file to set API key.")
        sys.exit(0)
    
    # Process emails
    try:
        generated = process_emails(
            csv_path=CSV_FILE,
            template_path=TEMPLATE_FILE,
            output_format="html"
        )
        
        print(f"\nSuccess! Generated {len(generated)} email(s).")
        for path in generated:
            print(f"  - {path}")
            
    except FileNotFoundError as e:
        print(f"\nFile not found: {e}")
        print("\nCreate the following files:")
        print(f"  - {CSV_FILE} (CSV with recipient data)")
        print(f"  - {TEMPLATE_FILE} (HTML email template)")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
