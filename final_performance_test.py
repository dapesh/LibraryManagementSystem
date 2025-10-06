# final_performance_test.py
import requests
import time
import statistics
from tabulate import tabulate
import random
import re

class FinalPerformanceTest:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        self.created_books = []
        self.created_students = []
        
        self.subjects = ["Programming", "Mathematics", "Science", "History"]
        self.categories = ["Computer Science", "Engineering", "Arts"]
        
        self.working_credentials = {"username": "Dipesh", "password": "GairidharaNP@1"}
    
    def extract_csrf_token(self, html_content):
        """Extract CSRF token"""
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html_content)
        return match.group(1) if match else None
    
    def login_staff(self):
        """Login to staff account"""
        try:
            login_page = self.session.get(f"{self.base_url}/stafflogin/", timeout=5)
            csrf_token = self.extract_csrf_token(login_page.text)
            
            login_data = {
                "loginuname": self.working_credentials["username"],
                "loginpassword": self.working_credentials["password"],
            }
            
            if csrf_token:
                login_data['csrfmiddlewaretoken'] = csrf_token
            
            response = self.session.post(
                f"{self.base_url}/LoginBackend/",
                data=login_data,
                allow_redirects=False,
                timeout=10
            )
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if 'dashboard' in location:
                    self.session.get(f"{self.base_url}{location}", timeout=5)
                    return True
                    
        except Exception as e:
            print(f"Login error: {e}")
        
        return False
    
    def test_book_performance(self):
        """Test book submission performance"""
        print("📖 TESTING BOOK SUBMISSIONS")
        print("=" * 50)
        
        if not self.login_staff():
            return {}
        
        times = []
        success_count = 0
        
        for i in range(5):
            print(f"  Book {i+1}: ", end="")
            start_time = time.time()
            
            try:
                add_page = self.session.get(f"{self.base_url}/addbook/", timeout=5)
                csrf_token = self.extract_csrf_token(add_page.text)
                
                book_data = {
                    "bookid": f"BOOK{random.randint(1000, 9999)}",
                    "bookname": f"Test Book {i+1}",
                    "subject": random.choice(self.subjects),
                    "category": random.choice(self.categories),
                    "csrfmiddlewaretoken": csrf_token
                }
                
                response = self.session.post(
                    f"{self.base_url}/AddBookSubmission/",
                    data=book_data,
                    headers={'Referer': f'{self.base_url}/addbook/'},
                    timeout=10
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                times.append(response_time)
                
                if response.status_code in [200, 302]:
                    self.created_books.append(book_data)
                    success_count += 1
                    print(f"✅ Created ({response_time:.3f}s)")
                else:
                    print(f"❌ Failed")
                    
            except Exception as e:
                print(f"❌ Error")
        
        return {
            'samples': len(times),
            'success_rate': (success_count / 5) * 100,
            'avg_time': statistics.mean(times) if times else 0,
        }
    
    def test_student_performance(self):
        """Test student submission performance"""
        print("👨‍🎓 TESTING STUDENT SUBMISSIONS")
        print("=" * 50)
        
        # New session for students
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        
        if not self.login_staff():
            return {}
        
        times = []
        success_count = 0
        
        for i in range(5):
            print(f"  Student {i+1}: ", end="")
            start_time = time.time()
            
            try:
                add_page = self.session.get(f"{self.base_url}/addstudent/", timeout=5)
                csrf_token = self.extract_csrf_token(add_page.text)
                
                # Match the HTML form fields exactly
                student_data = {
                    "sname": f"Test Student {i+1}",
                    "studentid": f"STU{random.randint(10000, 99999)}",  # Matches form field name
                    "csrfmiddlewaretoken": csrf_token
                }
                
                response = self.session.post(
                    f"{self.base_url}/addstudentsubmission/",
                    data=student_data,
                    headers={'Referer': f'{self.base_url}/addstudent/'},
                    timeout=10
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                times.append(response_time)
                
                if response.status_code in [200, 302]:
                    self.created_students.append(student_data)
                    success_count += 1
                    print(f"✅ Created ({response_time:.3f}s)")
                else:
                    print(f"❌ Failed")
                    
            except Exception as e:
                print(f"❌ Error")
        
        return {
            'samples': len(times),
            'success_rate': (success_count / 5) * 100,
            'avg_time': statistics.mean(times) if times else 0,
        }
    
    def run_final_test(self):
        """Run the final performance test"""
        print("🚀 FINAL PERFORMANCE TEST - BOTH OPERATIONS")
        print("=" * 80)
        print(f"📡 Target: {self.base_url}")
        print("=" * 80)
        
        results = {}
        
        # Test books
        results['books'] = self.test_book_performance()
        
        # Test students  
        results['students'] = self.test_student_performance()
        
        # Generate report
        print("\n" + "="*90)
        print("📊 FINAL PERFORMANCE REPORT")
        print("="*90)
        
        headers = ["Operation", "Attempts", "Success", "Success Rate", "Avg Time", "Status"]
        table_data = []
        
        for operation, metrics in results.items():
            success_count = len(self.created_books) if operation == 'books' else len(self.created_students)
            success_rate = metrics.get('success_rate', 0)
            
            if success_rate >= 80:
                status = "✅ EXCELLENT"
            elif success_rate >= 60:
                status = "⚠️ GOOD"
            else:
                status = "❌ NEEDS ATTENTION"
            
            table_data.append([
                operation.title(),
                metrics.get('samples', 0),
                success_count,
                f"{success_rate:.1f}%",
                f"{metrics.get('avg_time', 0):.3f}s",
                status
            ])
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        print(f"\n📚 Books Created: {len(self.created_books)}")
        print(f"👨‍🎓 Students Created: {len(self.created_students)}")
        
        if len(self.created_books) > 0 and len(self.created_students) > 0:
            print("\n🎉 SUCCESS: Both book and student submissions are working!")
        elif len(self.created_books) > 0:
            print("\n📚 PARTIAL: Books working, check student view logic")
        else:
            print("\n❌ ISSUE: Check both operations")

if __name__ == "__main__":
    test = FinalPerformanceTest("http://127.0.0.1:8000")
    test.run_final_test()
