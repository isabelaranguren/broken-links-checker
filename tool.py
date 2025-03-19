#!/usr/bin/env python3
"""
Bulk URL Status Checker - Check if multiple URLs are working or broken
"""

import requests
import concurrent.futures
import csv
import argparse
import sys
from urllib.parse import urlparse
from collections import defaultdict
import time

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UrlChecker:
    def __init__(self, timeout=10, max_workers=10, verify_ssl=False):
        """
        Initialize the URL checker
        
        Args:
            timeout (int): Timeout in seconds for each request
            max_workers (int): Maximum number of concurrent workers
            verify_ssl (bool): Whether to verify SSL certificates
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self.verify_ssl = verify_ssl
        self.results = {
            'working': [],
            'broken': [],
            'errors': []
        }
        
        # Set up a requests session for connection pooling
        self.session = requests.Session()
        # Set common headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    
    def normalize_url(self, url):
        """Add scheme if missing"""
        if not urlparse(url).scheme:
            return f"https://{url}"
        return url
    
    def check_url(self, url):
        """
        Check a single URL
        
        Args:
            url (str): URL to check
            
        Returns:
            dict: Result of the check
        """
        url = self.normalize_url(url.strip())
        result = {
            'url': url,
            'original_url': url,
            'status_code': None,
            'reason': None,
            'is_error': False,
            'error_type': None,
            'response_time': 0
        }
        
        try:
            start_time = time.time()
            # Use HEAD request first (faster) then fall back to GET if method not allowed
            response = self.session.head(
                url, 
                timeout=self.timeout,
                allow_redirects=True,
                verify=self.verify_ssl
            )
            
            # Some servers don't support HEAD, so try GET if we get 405 Method Not Allowed
            if response.status_code == 405:
                response = self.session.get(
                    url, 
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=self.verify_ssl,
                    stream=True  # Don't download the whole content
                )
                # Close the connection immediately
                response.close()
                
            result['response_time'] = round(time.time() - start_time, 2)
            result['status_code'] = response.status_code
            result['reason'] = response.reason
            result['final_url'] = response.url  # In case of redirects
            
            # Check if we got redirected
            if response.url != url:
                result['redirected'] = True
                result['redirect_url'] = response.url
            
        except requests.exceptions.RequestException as e:
            result['is_error'] = True
            result['error_type'] = type(e).__name__
            result['reason'] = str(e)
        
        return result
    
    def check_urls(self, urls):
        """
        Check multiple URLs in parallel
        
        Args:
            urls (list): List of URLs to check
            
        Returns:
            dict: Results categorized as working, broken, and errors
        """
        results = defaultdict(list)
        
        print(f"Checking {len(urls)} URLs with {self.max_workers} workers...")
        
        # Process URLs in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.check_url, url): url for url in urls}
            
            # Show progress
            total = len(future_to_url)
            completed = 0
            
            for future in concurrent.futures.as_completed(future_to_url):
                completed += 1
                if completed % 10 == 0 or completed == total:
                    print(f"Progress: {completed}/{total} URLs checked", end='\r')
                
                result = future.result()
                
                if result['is_error']:
                    results['errors'].append(result)
                elif 200 <= result['status_code'] < 400:
                    results['working'].append(result)
                else:
                    results['broken'].append(result)
        
        print("\nCheck completed!")
        return results
    
    def print_results(self, results=None):
        """Print the results to the console"""
        if results is None:
            results = self.results
            
        print("\n===== URL CHECK RESULTS =====\n")
        
        # Print working URLs
        print(f"WORKING URLs: {len(results['working'])}")
        for result in results['working']:
            print(f"  ✓ {result['url']} - {result['status_code']} {result['reason']} ({result['response_time']}s)")
        
        # Print broken URLs
        print(f"\nBROKEN URLs: {len(results['broken'])}")
        for result in results['broken']:
            print(f"  ✗ {result['url']} - {result['status_code']} {result['reason']}")
        
        # Print errors
        print(f"\nERRORS: {len(results['errors'])}")
        for result in results['errors']:
            print(f"  ! {result['url']} - {result['error_type']}: {result['reason']}")
            
        # Print summary
        total = len(results['working']) + len(results['broken']) + len(results['errors'])
        print(f"\n===== SUMMARY =====")
        print(f"Total URLs checked: {total}")
        print(f"Working: {len(results['working'])} ({round(len(results['working'])/total*100, 1)}%)")
        print(f"Broken: {len(results['broken'])} ({round(len(results['broken'])/total*100, 1)}%)")
        print(f"Errors: {len(results['errors'])} ({round(len(results['errors'])/total*100, 1)}%)")
    
    def save_csv_report(self, filename, results=None):
        """Save the results to a CSV file"""
        if results is None:
            results = self.results
            
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['url', 'status_code', 'reason', 'response_time', 'is_error', 'error_type', 'redirected', 'redirect_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            # Write all results
            for category in ['working', 'broken', 'errors']:
                for result in results[category]:
                    # Only write the fields we want
                    row = {field: result.get(field, '') for field in fieldnames}
                    writer.writerow(row)
                    
        print(f"Report saved to {filename}")

def load_urls_from_file(filename):
    """Load URLs from a text file (one URL per line)"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        return urls
    except Exception as e:
        print(f"Error loading URLs from file: {e}")
        return []

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Bulk URL Status Checker')
    parser.add_argument('file', nargs='?', help='File containing URLs (one per line)')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Timeout in seconds (default: 10)')
    parser.add_argument('-w', '--workers', type=int, default=10, help='Maximum number of workers (default: 10)')
    parser.add_argument('-o', '--output', default='url_check_results.csv', help='Output CSV file (default: url_check_results.csv)')
    parser.add_argument('-v', '--verify-ssl', action='store_true', help='Verify SSL certificates (default: False)')
    
    args = parser.parse_args()
    
    # Create URL checker
    checker = UrlChecker(
        timeout=args.timeout,
        max_workers=args.workers,
        verify_ssl=args.verify_ssl
    )
    
    urls = []
    
    if args.file:
        # Load URLs from file
        urls = load_urls_from_file(args.file)
        print(f"Loaded {len(urls)} URLs from {args.file}")
    
    if not urls:
        print("No URLs to check. Exiting.")
        return
    
    # Check the URLs
    results = checker.check_urls(urls)
    
    # Print results
    checker.print_results(results)
    
    # Save CSV report
    checker.save_csv_report(args.output, results)

if __name__ == "__main__":
    main()