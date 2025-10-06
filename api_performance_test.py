# load_testing.py
import requests
import time
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tabulate import tabulate
import random
import re
import sys
from datetime import datetime

class LoadTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.results = {
            'books': {'times': [], 'success': 0, 'errors': 0},
            'students': {'times': [], 'success': 0, 'errors': 0}
        }
        self.lock = threading.Lock()
        
        # Test data
        self.subjects = ["Programming", "Mathematics", "Science", "History", "Physics"]
        self.categories = ["Computer Science", "Engineering", "Arts", "Science"]
        self.branches = ["Computer Science", "Electrical", "Mechanical", "Civil"]
        
        self.first_names = ["John", "Jane", "Alex", "Emily", "Michael", "Sarah"]
        self.last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones"]
        
        self.credentials = {"username": "Dipesh", "password": "GairidharaNP@1"}
    
    def extract_csrf_token(self, html_content):
        """Extract CSRF token from HTML"""
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html_content)
        return match.group(1) if match else None
    
    def create_user_session(self):
        """Create a new session for each virtual user"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        return session
    
    def login_user(self, session):
        """Login a virtual user"""
        try:
            login_page = session.get(f"{self.base_url}/stafflogin/", timeout=10)
            csrf_token = self.extract_csrf_token(login_page.text)
            
            if not csrf_token:
                return False
            
            login_data = {
                "loginuname": self.credentials["username"],
                "loginpassword": self.credentials["password"],
                "csrfmiddlewaretoken": csrf_token
            }
            
            response = session.post(
                f"{self.base_url}/LoginBackend/",
                data=login_data,
                headers={'Referer': f'{self.base_url}/stafflogin/'},
                allow_redirects=False,
                timeout=10
            )
            
            return response.status_code == 302 and 'dashboard' in response.headers.get('Location', '')
        except:
            return False
    
    def generate_book_data(self, user_id, operation_id):
        """Generate unique book data for each operation"""
        return {
            "bookid": f"LOAD{user_id:03d}{operation_id:03d}",
            "bookname": f"Load Test Book User{user_id} Op{operation_id}",
            "subject": random.choice(self.subjects),
            "category": random.choice(self.categories)
        }
    
    def generate_student_data(self, user_id, operation_id):
        """Generate unique student data for each operation"""
        return {
            "sname": f"Load Student {user_id}-{operation_id}",
            "enrollment": f"LOAD{user_id:03d}{operation_id:03d}",
            "studentid": f"LOAD{user_id:03d}{operation_id:03d}",
            "branch": random.choice(self.branches),
            "contact": f"98{random.randint(10000000, 99999999)}",
            "email": f"loaduser{user_id}_{operation_id}@test.com"
        }
    
    def test_book_operation(self, user_id, operation_id):
        """Test book addition for a virtual user"""
        session = self.create_user_session()
        start_time = time.time()
        success = False
        
        try:
            if not self.login_user(session):
                raise Exception("Login failed")
            
            # Get CSRF token
            add_page = session.get(f"{self.base_url}/addbook/", timeout=10)
            csrf_token = self.extract_csrf_token(add_page.text)
            
            if not csrf_token:
                raise Exception("No CSRF token")
            
            # Prepare and submit book data
            book_data = self.generate_book_data(user_id, operation_id)
            book_data["csrfmiddlewaretoken"] = csrf_token
            
            response = session.post(
                f"{self.base_url}/AddBookSubmission/",
                data=book_data,
                headers={'Referer': f'{self.base_url}/addbook/'},
                timeout=15
            )
            
            success = response.status_code in [200, 302]
            
        except Exception as e:
            success = False
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Thread-safe result recording
        with self.lock:
            self.results['books']['times'].append(response_time)
            if success:
                self.results['books']['success'] += 1
            else:
                self.results['books']['errors'] += 1
        
        return success, response_time
    
    def test_student_operation(self, user_id, operation_id):
        """Test student addition for a virtual user"""
        session = self.create_user_session()
        start_time = time.time()
        success = False
        
        try:
            if not self.login_user(session):
                raise Exception("Login failed")
            
            # Get CSRF token
            add_page = session.get(f"{self.base_url}/addstudent/", timeout=10)
            csrf_token = self.extract_csrf_token(add_page.text)
            
            if not csrf_token:
                raise Exception("No CSRF token")
            
            # Prepare and submit student data
            student_data = self.generate_student_data(user_id, operation_id)
            student_data["csrfmiddlewaretoken"] = csrf_token
            
            response = session.post(
                f"{self.base_url}/addstudentsubmission/",
                data=student_data,
                headers={'Referer': f'{self.base_url}/addstudent/'},
                timeout=15
            )
            
            success = response.status_code in [200, 302]
            
        except Exception as e:
            success = False
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Thread-safe result recording
        with self.lock:
            self.results['students']['times'].append(response_time)
            if success:
                self.results['students']['success'] += 1
            else:
                self.results['students']['errors'] += 1
        
        return success, response_time
    
    def run_load_test(self, concurrent_users=50, operations_per_user=2):
        """Run load test with specified concurrent users"""
        print(f"\n🚀 LOAD TESTING WITH {concurrent_users} CONCURRENT USERS")
        print("=" * 60)
        print(f"Operations per user: {operations_per_user}")
        print(f"Total operations: {concurrent_users * operations_per_user * 2}")  # Books + Students
        print("=" * 60)
        
        total_operations = concurrent_users * operations_per_user
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            # Submit book operations
            book_futures = []
            for user_id in range(concurrent_users):
                for op_id in range(operations_per_user):
                    future = executor.submit(self.test_book_operation, user_id, op_id)
                    book_futures.append(future)
            
            # Submit student operations
            student_futures = []
            for user_id in range(concurrent_users):
                for op_id in range(operations_per_user):
                    future = executor.submit(self.test_student_operation, user_id, op_id)
                    student_futures.append(future)
            
            # Wait for completion
            completed = 0
            total = len(book_futures) + len(student_futures)
            
            for future in as_completed(book_futures + student_futures):
                completed += 1
                if completed % 10 == 0:
                    print(f"  Progress: {completed}/{total} operations completed...")
        
        end_time = time.time()
        self.test_duration = end_time - start_time
        
        return self.generate_load_report()
    
    def calculate_percentiles(self, times):
        """Calculate percentile metrics"""
        if not times:
            return {}
        
        sorted_times = sorted(times)
        n = len(sorted_times)
        
        return {
            'p50': sorted_times[int(0.5 * n)] if n > 0 else 0,
            'p75': sorted_times[int(0.75 * n)] if n > 0 else 0,
            'p90': sorted_times[int(0.9 * n)] if n > 0 else 0,
            'p95': sorted_times[int(0.95 * n)] if n > 0 else 0,
            'p99': sorted_times[int(0.99 * n)] if n > 0 else 0
        }
    
    def generate_load_report(self):
        """Generate comprehensive load test report"""
        print("\n" + "="*100)
        print("📊 LOAD TESTING REPORT")
        print("="*100)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Duration: {self.test_duration:.2f} seconds")
        print("="*100)
        
        # Calculate metrics for books
        book_times = self.results['books']['times']
        book_success = self.results['books']['success']
        book_errors = self.results['books']['errors']
        book_total = book_success + book_errors
        
        book_percentiles = self.calculate_percentiles(book_times)
        
        # Calculate metrics for students
        student_times = self.results['students']['times']
        student_success = self.results['students']['success']
        student_errors = self.results['students']['errors']
        student_total = student_success + student_errors
        
        student_percentiles = self.calculate_percentiles(student_times)
        
        # Overall metrics
        total_operations = book_total + student_total
        total_success = book_success + student_success
        overall_success_rate = (total_success / total_operations * 100) if total_operations > 0 else 0
        overall_throughput = total_success / self.test_duration if self.test_duration > 0 else 0
        
        # Print results table
        headers = ["Metric", "Book Operations", "Student Operations", "Overall"]
        table_data = [
            ["Total Operations", book_total, student_total, total_operations],
            ["Successful", book_success, student_success, total_success],
            ["Errors", book_errors, student_errors, book_errors + student_errors],
            ["Success Rate", f"{(book_success/book_total*100) if book_total > 0 else 0:.1f}%", 
             f"{(student_success/student_total*100) if student_total > 0 else 0:.1f}%", 
             f"{overall_success_rate:.1f}%"],
            ["", "", "", ""],
            ["Avg Response Time", f"{statistics.mean(book_times) if book_times else 0:.3f}s", 
             f"{statistics.mean(student_times) if student_times else 0:.3f}s", "-"],
            ["Min Time", f"{min(book_times) if book_times else 0:.3f}s", 
             f"{min(student_times) if student_times else 0:.3f}s", "-"],
            ["Max Time", f"{max(book_times) if book_times else 0:.3f}s", 
             f"{max(student_times) if student_times else 0:.3f}s", "-"],
            ["", "", "", ""],
            ["50th Percentile", f"{book_percentiles['p50']:.3f}s", 
             f"{student_percentiles['p50']:.3f}s", "-"],
            ["90th Percentile", f"{book_percentiles['p90']:.3f}s", 
             f"{student_percentiles['p90']:.3f}s", "-"],
            ["95th Percentile", f"{book_percentiles['p95']:.3f}s", 
             f"{student_percentiles['p95']:.3f}s", "-"],
            ["", "", "", ""],
            ["Throughput", f"{(book_success/self.test_duration) if self.test_duration > 0 else 0:.2f} ops/s", 
             f"{(student_success/self.test_duration) if self.test_duration > 0 else 0:.2f} ops/s", 
             f"{overall_throughput:.2f} ops/s"]
        ]
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Performance analysis
        self.print_performance_analysis()
        
        return self.results
    
    def print_performance_analysis(self):
        """Print performance analysis and recommendations"""
        print("\n🔍 PERFORMANCE ANALYSIS")
        print("="*90)
        
        book_success_rate = (self.results['books']['success'] / (self.results['books']['success'] + self.results['books']['errors'])) * 100
        student_success_rate = (self.results['students']['success'] / (self.results['students']['success'] + self.results['students']['errors'])) * 100
        
        book_avg_time = statistics.mean(self.results['books']['times']) if self.results['books']['times'] else 0
        student_avg_time = statistics.mean(self.results['students']['times']) if self.results['students']['times'] else 0
        
        print("📈 LOAD TEST RESULTS:")
        print(f"• Book Operations: {book_success_rate:.1f}% success, {book_avg_time:.3f}s avg response")
        print(f"• Student Operations: {student_success_rate:.1f}% success, {student_avg_time:.3f}s avg response")
        
        print(f"\n🎯 PERFORMANCE ASSESSMENT:")
        if book_success_rate >= 95 and student_success_rate >= 95:
            print("✅ EXCELLENT: System handles concurrent load very well")
        elif book_success_rate >= 90 and student_success_rate >= 90:
            print("⚠️ GOOD: System handles load with minor degradation")
        else:
            print("❌ NEEDS IMPROVEMENT: System struggles under concurrent load")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if book_avg_time > 1.0 or student_avg_time > 1.0:
            print("• Optimize database queries and indexing")
            print("• Implement connection pooling")
        if self.results['books']['errors'] > 0 or self.results['students']['errors'] > 0:
            print("• Improve error handling and retry mechanisms")
            print("• Check server resource limits")
        print("• Consider implementing rate limiting")
        print("• Monitor database performance under load")

def run_progressive_load_test():
    """Run progressive load testing with increasing user loads"""
    base_url = "http://127.0.0.1:8000"
    
    print("🚀 PROGRESSIVE LOAD TESTING")
    print("=" * 60)
    print("This test will simulate increasing concurrent user loads")
    print("to identify system breaking points.")
    print("=" * 60)
    
    user_loads = [10, 25, 50, 75, 100]  # Progressive user loads
    
    for user_count in user_loads:
        print(f"\n🎯 TESTING WITH {user_count} CONCURRENT USERS")
        print("-" * 50)
        
        tester = LoadTester(base_url)
        results = tester.run_load_test(concurrent_users=user_count, operations_per_user=2)
        
        # Brief pause between tests
        if user_count != user_loads[-1]:
            print("\n⏳ Pausing for 5 seconds before next test...")
            time.sleep(5)

def main():
    """Main function"""
    print("🚀 Library Management System - Load Testing")
    print("=" * 50)
    print("This script performs load testing with concurrent users")
    print("to evaluate system performance under load.")
    print()
    
    print("Choose load test type:")
    print("1. Single load test (50 users)")
    print("2. Progressive load test (10, 25, 50, 75, 100 users)")
    print("3. Custom load test")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    base_url = "http://127.0.0.1:8000"
    
    if choice == "1":
        tester = LoadTester(base_url)
        tester.run_load_test(concurrent_users=50, operations_per_user=2)
    
    elif choice == "2":
        run_progressive_load_test()
    
    elif choice == "3":
        users = int(input("Enter number of concurrent users: "))
        operations = int(input("Enter operations per user: "))
        tester = LoadTester(base_url)
        tester.run_load_test(concurrent_users=users, operations_per_user=operations)
    
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()