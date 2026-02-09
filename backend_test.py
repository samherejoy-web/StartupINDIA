import requests
import sys
import json
import io
import csv
from datetime import datetime

class DataScrapingAPITester:
    def __init__(self, base_url="https://startup-data-mine.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.api_key = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        
        if self.api_key and 'Authorization' not in test_headers:
            test_headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    test_headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=test_headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if success:
                try:
                    response_data = response.json()
                    details += f", Response: {json.dumps(response_data, indent=2)[:200]}..."
                except:
                    details += f", Response: {response.text[:200]}..."
            else:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Error: {error_data}"
                except:
                    details += f", Error: {response.text[:200]}"

            self.log_test(name, success, details)
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_single_url_scraping(self):
        """Test single URL scraping"""
        test_url = "https://www.startupindia.gov.in/content/sih/en/profile.Startup.67174376e4b005ffcd401cd3.html"
        success, response = self.run_test(
            "Single URL Scraping",
            "POST",
            "scrape",
            200,
            data={"url": test_url}
        )
        return success, response

    def test_bulk_url_scraping(self):
        """Test bulk URL scraping"""
        test_urls = [
            "https://www.startupindia.gov.in/content/sih/en/profile.Startup.67174376e4b005ffcd401cd3.html"
        ]
        success, response = self.run_test(
            "Bulk URL Scraping",
            "POST",
            "scrape/bulk",
            200,
            data={"urls": test_urls}
        )
        return success, response

    def test_csv_upload_scraping(self):
        """Test CSV upload for scraping"""
        # Create a test CSV file
        csv_content = "url\nhttps://www.startupindia.gov.in/content/sih/en/profile.Startup.67174376e4b005ffcd401cd3.html\n"
        csv_file = io.StringIO(csv_content)
        
        files = {'file': ('test_urls.csv', csv_content, 'text/csv')}
        
        success, response = self.run_test(
            "CSV Upload Scraping",
            "POST",
            "scrape/upload-csv",
            200,
            files=files
        )
        return success, response

    def test_get_results(self):
        """Test getting all results"""
        success, response = self.run_test(
            "Get All Results",
            "GET",
            "results?limit=10",
            200
        )
        return success, response

    def test_export_csv(self):
        """Test CSV export"""
        url = f"{self.api_url}/export/csv"
        try:
            response = requests.get(url, timeout=30)
            success = response.status_code == 200 and 'text/csv' in response.headers.get('content-type', '')
            details = f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}"
            if success:
                details += f", CSV Content Length: {len(response.text)} chars"
            self.log_test("Export CSV", success, details)
            return success, {}
        except Exception as e:
            self.log_test("Export CSV", False, f"Exception: {str(e)}")
            return False, {}

    def test_export_json(self):
        """Test JSON export"""
        success, response = self.run_test(
            "Export JSON",
            "GET",
            "export/json",
            200
        )
        return success, response

    def test_create_api_key(self):
        """Test API key creation"""
        success, response = self.run_test(
            "Create API Key",
            "POST",
            "api-keys",
            200,
            data={"name": f"Test Key {datetime.now().strftime('%H%M%S')}"}
        )
        
        if success and 'key' in response:
            self.api_key = response['key']
            print(f"    Created API Key: {self.api_key[:20]}...")
        
        return success, response

    def test_get_api_keys(self):
        """Test getting all API keys"""
        success, response = self.run_test(
            "Get API Keys",
            "GET",
            "api-keys",
            200
        )
        return success, response

    def test_protected_single_scrape(self):
        """Test protected single URL scraping"""
        if not self.api_key:
            self.log_test("Protected Single Scrape", False, "No API key available")
            return False, {}
        
        test_url = "https://www.startupindia.gov.in/content/sih/en/profile.Startup.67174376e4b005ffcd401cd3.html"
        success, response = self.run_test(
            "Protected Single Scrape",
            "POST",
            "protected/scrape",
            200,
            data={"url": test_url},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return success, response

    def test_protected_bulk_scrape(self):
        """Test protected bulk URL scraping"""
        if not self.api_key:
            self.log_test("Protected Bulk Scrape", False, "No API key available")
            return False, {}
        
        test_urls = [
            "https://www.startupindia.gov.in/content/sih/en/profile.Startup.67174376e4b005ffcd401cd3.html"
        ]
        success, response = self.run_test(
            "Protected Bulk Scrape",
            "POST",
            "protected/scrape/bulk",
            200,
            data={"urls": test_urls},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return success, response

    def test_unauthorized_protected_access(self):
        """Test accessing protected endpoints without API key"""
        success, response = self.run_test(
            "Unauthorized Protected Access",
            "POST",
            "protected/scrape",
            401,
            data={"url": "https://example.com"},
            headers={}  # No Authorization header
        )
        return success, response

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Data Scraping API Tests")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 60)

        # Basic API tests
        self.test_root_endpoint()
        
        # Scraping tests
        self.test_single_url_scraping()
        self.test_bulk_url_scraping()
        self.test_csv_upload_scraping()
        
        # Results and export tests
        self.test_get_results()
        self.test_export_csv()
        self.test_export_json()
        
        # API key management tests
        self.test_create_api_key()
        self.test_get_api_keys()
        
        # Protected endpoint tests
        self.test_unauthorized_protected_access()
        self.test_protected_single_scrape()
        self.test_protected_bulk_scrape()

        # Print summary
        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return 1

def main():
    tester = DataScrapingAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())