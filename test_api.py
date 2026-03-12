"""
Comprehensive API Test Script for Spidy License Server
Tests all endpoints including validate API with PC binding
"""
import requests
import json
import uuid
from datetime import datetime

BASE_URL = "http://localhost:5000"
ADMIN_AUTH = ('admin', 'changeme123')

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}TEST: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")

# Test 1: Get Statistics
def test_get_stats():
    print_test("GET /api/stats - Get Statistics")
    try:
        response = requests.get(f"{BASE_URL}/api/stats", auth=ADMIN_AUTH)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Statistics retrieved successfully")
            print(json.dumps(data, indent=2))
            return True
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False


# Test 2: Create License
def test_create_license():
    print_test("POST /api/licenses - Create New License")
    try:
        payload = {
            "duration_days": 30,
            "max_activations": 1,
            "notes": "Test license created by API test script"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/licenses",
            auth=ADMIN_AUTH,
            json=payload
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("License created successfully")
                print(json.dumps(data, indent=2))
                return data.get('license_key')
            else:
                print_error(f"Failed: {data.get('error')}")
                return None
        else:
            print_error(f"Failed: {response.text}")
            return None
    except Exception as e:
        print_error(f"Exception: {e}")
        return None

# Test 3: Get All Licenses
def test_get_licenses():
    print_test("GET /api/licenses - Get All Licenses")
    try:
        response = requests.get(f"{BASE_URL}/api/licenses", auth=ADMIN_AUTH)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {len(data)} licenses")
            for license in data[:3]:  # Show first 3
                print(f"  - {license['license_key']} | Status: {'Active' if license['is_active'] else 'Blocked'} | Expires: {license['expires_at']}")
            return True
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False


# Test 4: Validate License (First Time - PC Binding)
def test_validate_license_first_time(license_key):
    print_test("POST /api/validate - First Time Validation (PC Binding)")
    try:
        machine_id = str(uuid.uuid4())
        print_info(f"Machine ID: {machine_id}")
        
        payload = {
            "license_key": license_key,
            "machine_id": machine_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/validate",
            json=payload
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                print_success("License validated and bound to machine")
                print(json.dumps(data, indent=2))
                return machine_id
            else:
                print_error(f"Validation failed: {data.get('error')}")
                return None
        else:
            print_error(f"Failed: {response.text}")
            return None
    except Exception as e:
        print_error(f"Exception: {e}")
        return None

# Test 5: Validate License (Same Machine - Should Pass)
def test_validate_license_same_machine(license_key, machine_id):
    print_test("POST /api/validate - Same Machine Validation (Should Pass)")
    try:
        payload = {
            "license_key": license_key,
            "machine_id": machine_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/validate",
            json=payload
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                print_success("License validated successfully on same machine")
                print(json.dumps(data, indent=2))
                return True
            else:
                print_error(f"Validation failed: {data.get('error')}")
                return False
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False


# Test 6: Validate License (Different Machine - Should Fail)
def test_validate_license_different_machine(license_key):
    print_test("POST /api/validate - Different Machine Validation (Should Fail)")
    try:
        different_machine_id = str(uuid.uuid4())
        print_info(f"Different Machine ID: {different_machine_id}")
        
        payload = {
            "license_key": license_key,
            "machine_id": different_machine_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/validate",
            json=payload
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('valid'):
                print_success(f"Correctly rejected: {data.get('error')}")
                return True
            else:
                print_error("Should have failed but passed!")
                return False
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

# Test 7: Update License
def test_update_license(license_key):
    print_test("PUT /api/licenses/<key> - Update License")
    try:
        payload = {
            "extend_days": 15,
            "notes": "Updated by API test script",
            "max_activations": 2
        }
        
        response = requests.put(
            f"{BASE_URL}/api/licenses/{license_key}",
            auth=ADMIN_AUTH,
            json=payload
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("License updated successfully")
                return True
            else:
                print_error(f"Failed: {data.get('error')}")
                return False
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False


# Test 8: Block License
def test_block_license(license_key):
    print_test("PUT /api/licenses/<key> - Block License")
    try:
        payload = {"is_active": False}
        
        response = requests.put(
            f"{BASE_URL}/api/licenses/{license_key}",
            auth=ADMIN_AUTH,
            json=payload
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("License blocked successfully")
                return True
            else:
                print_error(f"Failed: {data.get('error')}")
                return False
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

# Test 9: Validate Blocked License (Should Fail)
def test_validate_blocked_license(license_key, machine_id):
    print_test("POST /api/validate - Validate Blocked License (Should Fail)")
    try:
        payload = {
            "license_key": license_key,
            "machine_id": machine_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/validate",
            json=payload
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('valid') and 'blocked' in data.get('error', '').lower():
                print_success(f"Correctly rejected blocked license: {data.get('error')}")
                return True
            else:
                print_error("Should have failed but passed!")
                return False
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

# Test 10: Delete License
def test_delete_license(license_key):
    print_test("DELETE /api/licenses/<key> - Delete License")
    try:
        response = requests.delete(
            f"{BASE_URL}/api/licenses/{license_key}",
            auth=ADMIN_AUTH
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("License deleted successfully")
                return True
            else:
                print_error(f"Failed: {data.get('error')}")
                return False
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {e}")
        return False

# Run all tests
def run_all_tests():
    print(f"\n{Colors.BLUE}{'='*60}")
    print("🕷️  SPIDY LICENSE SERVER API TEST SUITE")
    print(f"{'='*60}{Colors.END}\n")
    
    results = []
    
    # Test 1: Get Stats
    results.append(("Get Statistics", test_get_stats()))
    
    # Test 2: Create License
    license_key = test_create_license()
    results.append(("Create License", license_key is not None))
    
    if not license_key:
        print_error("Cannot continue tests without a license key")
        return
    
    # Test 3: Get All Licenses
    results.append(("Get All Licenses", test_get_licenses()))
    
    # Test 4: First Time Validation (PC Binding)
    machine_id = test_validate_license_first_time(license_key)
    results.append(("First Time Validation (PC Binding)", machine_id is not None))
    
    if not machine_id:
        print_error("Cannot continue validation tests without machine binding")
        return
    
    # Test 5: Same Machine Validation
    results.append(("Same Machine Validation", test_validate_license_same_machine(license_key, machine_id)))
    
    # Test 6: Different Machine Validation (Should Fail)
    results.append(("Different Machine Validation", test_validate_license_different_machine(license_key)))
    
    # Test 7: Update License
    results.append(("Update License", test_update_license(license_key)))
    
    # Test 8: Block License
    results.append(("Block License", test_block_license(license_key)))
    
    # Test 9: Validate Blocked License (Should Fail)
    results.append(("Validate Blocked License", test_validate_blocked_license(license_key, machine_id)))
    
    # Test 10: Delete License
    results.append(("Delete License", test_delete_license(license_key)))
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}{Colors.END}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{status} - {name}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    run_all_tests()
