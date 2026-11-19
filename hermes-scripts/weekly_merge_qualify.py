#!/usr/bin/env python3
"""
Weekly Merge & Qualify - Merge all weekly sources, qualify, and output leads
"""

import os
import sys
import json
import csv
import yaml
import argparse
from datetime import datetime
from typing import Dict, List, Any

# Add scripts to path
sys.path.insert(0, '/home/ubuntu/lead_gen_system/scripts')

from merge_dedup import load_json_file, extract_leads_from_source, deduplicate_leads

def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def merge_weekly_sources(state_dir: str, date_stamp: str, config: dict) -> List[Dict]:
    """Merge all weekly source files."""
    weekly_sources = [
        ('exa_lookalike', f'{state_dir}/exa_lookalike_{date_stamp}.json'),
        ('parallel_lookalike', f'{state_dir}/parallel_lookalike_{date_stamp}.json'),
        ('gmaps_deep', f'{state_dir}/gmaps_deep_{date_stamp}.json'),
        ('prospeo_industry_sweep', f'{state_dir}/prospeo_industry_{date_stamp}.json'),
        ('apollo_lookalike', f'{state_dir}/apollo_lookalike_{date_stamp}.json'),
    ]
    
    all_leads = []
    
    for source_name, filepath in weekly_sources:
        if os.path.exists(filepath):
            data = load_json_file(filepath)
            leads = extract_leads_from_source(source_name, data, config)
            all_leads.extend(leads)
            print(f"Loaded {len(leads)} leads from {source_name}")
        else:
            print(f"Source file not found: {filepath}")
    
    print(f"Total weekly leads: {len(all_leads)}")
    
    # Deduplicate
    unique_leads = deduplicate_leads(all_leads)
    print(f"Unique weekly leads: {len(unique_leads)}")
    
    return unique_leads

def save_csv(leads: List[Dict], output_path: str):
    """Save leads to CSV."""
    fieldnames = [
        'source', 'lead_id', 'name', 'title', 'seniority', 'company',
        'company_domain', 'company_employees', 'company_revenue',
        'company_location', 'company_phone', 'company_website',
        'email', 'personal_email', 'phone', 'linkedin_url',
        'email_status', 'search_category', 'search_location',
        'google_place_id', 'icp_fit_raw', 'discovered_at', 'raw_data'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)

def main():
    parser = argparse.ArgumentParser(description='Merge and output weekly leads')
    parser.add_argument('--config', required=True, help='Path to ICP config YAML')
    parser.add_argument('--date', required=True, help='Date stamp for input files')
    parser.add_argument('--output', required=True, help='Output CSV file')
    args = parser.parse_args()
    
    config = load_config(args.config)
    state_dir = config.get('output', {}).get('state_dir', '/home/ubuntu/lead_gen_system/state/')
    
    # Merge weekly sources
    leads = merge_weekly_sources(state_dir, args.date, config)
    
    # Save raw merged
    raw_output = args.output.replace('.csv', '_raw.csv')
    save_csv(leads, raw_output)
    print(f"Saved raw merged leads to {raw_output}")
    
    # Save final
    save_csv(leads, args.output)
    print(f"Saved {len(leads)} merged weekly leads to {args.output}")

if __name__ == '__main__':
    main()