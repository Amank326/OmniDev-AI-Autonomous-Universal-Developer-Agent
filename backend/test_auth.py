#!/usr/bin/env python
"""Authentication System Testing Script - Test all auth endpoints"""

import sys
import os
import json
from typing import Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test data
TEST_USER = {
    "username": "test_user_" + str(os.getpid()),
    "email": f"testuser{os.getpid()}@example.com",
    "password": "TestPassword123",
    "full_name": "Test User"
}

class AuthTester:
    """Authentication system tester"""
    
    def __init__(self):
        """Initialize tester"""
        self.base_url = "http://127.0.0.1:8001/api/auth"
        self.access_token = None
        self.refresh_token = None
        self.user_data = None
        self.test_results = []
    
    def test_register(self) -> bool:
        """Test user registration"""
        try:
            import requests
            
            logger.info("🧪 Testing User Registration...")
            
            response = requests.post(
                f"{self.base_url}/register",
                json=TEST_USER,
                timeout=5
            )
            
            if response.status_code == 201:
                self.user_data = response.json()
                logger.info(f"✅ User registered: {self.user_data['username']}")
                self.test_results.append(("Register", True))
                return True
            else:
                logger.error(f"❌ Registration failed: {response.status_code} - {response.text}")
                self.test_results.append(("Register", False))
                return False
        except Exception as e:
            logger.error(f"❌ Registration error: {str(e)}")
            self.test_results.append(("Register", False))
            return False
    
    def test_login(self) -> bool:
        """Test user login"""
        try:
            import requests
            
            logger.info("🧪 Testing User Login...")
            
            response = requests.post(
                f"{self.base_url}/login",
                json={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"]
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                logger.info(f"✅ User logged in, token received")
                self.test_results.append(("Login", True))
                return True
            else:
                logger.error(f"❌ Login failed: {response.status_code} - {response.text}")
                self.test_results.append(("Login", False))
                return False
        except Exception as e:
            logger.error(f"❌ Login error: {str(e)}")
            self.test_results.append(("Login", False))
            return False
    
    def test_get_current_user(self) -> bool:
        """Test get current user endpoint"""
        if not self.access_token:
            logger.warning("⚠️ Skipping - No access token")
            return False
        
        try:
            import requests
            
            logger.info("🧪 Testing Get Current User...")
            
            response = requests.get(
                f"{self.base_url}/me",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=5
            )
            
            if response.status_code == 200:
                user = response.json()
                logger.info(f"✅ Got current user: {user['username']}")
                self.test_results.append(("Get Current User", True))
                return True
            else:
                logger.error(f"❌ Get current user failed: {response.status_code}")
                self.test_results.append(("Get Current User", False))
                return False
        except Exception as e:
            logger.error(f"❌ Get current user error: {str(e)}")
            self.test_results.append(("Get Current User", False))
            return False
    
    def test_refresh_token(self) -> bool:
        """Test token refresh"""
        if not self.refresh_token:
            logger.warning("⚠️ Skipping - No refresh token")
            return False
        
        try:
            import requests
            
            logger.info("🧪 Testing Token Refresh...")
            
            response = requests.post(
                f"{self.base_url}/refresh",
                json={"refresh_token": self.refresh_token},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                old_token = self.access_token
                self.access_token = data["access_token"]
                logger.info(f"✅ Token refreshed successfully")
                self.test_results.append(("Refresh Token", True))
                return True
            else:
                logger.error(f"❌ Token refresh failed: {response.status_code}")
                self.test_results.append(("Refresh Token", False))
                return False
        except Exception as e:
            logger.error(f"❌ Token refresh error: {str(e)}")
            self.test_results.append(("Refresh Token", False))
            return False
    
    def test_logout(self) -> bool:
        """Test logout endpoint"""
        if not self.access_token:
            logger.warning("⚠️ Skipping - No access token")
            return False
        
        try:
            import requests
            
            logger.info("🧪 Testing Logout...")
            
            response = requests.post(
                f"{self.base_url}/logout",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Logged out successfully")
                self.test_results.append(("Logout", True))
                return True
            else:
                logger.error(f"❌ Logout failed: {response.status_code}")
                self.test_results.append(("Logout", False))
                return False
        except Exception as e:
            logger.error(f"❌ Logout error: {str(e)}")
            self.test_results.append(("Logout", False))
            return False
    
    def run_all_tests(self):
        """Run all authentication tests"""
        logger.info("=" * 50)
        logger.info("🔐 Authentication System Test Suite")
        logger.info("=" * 50)
        
        # Test sequence
        self.test_register()
        self.test_login()
        self.test_get_current_user()
        self.test_refresh_token()
        self.test_logout()
        
        # Print results
        logger.info("\n" + "=" * 50)
        logger.info("📊 Test Results Summary")
        logger.info("=" * 50)
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status:10} - {test_name}")
        
        logger.info("=" * 50)
        logger.info(f"📈 Results: {passed}/{total} tests passed")
        logger.info("=" * 50)
        
        return passed == total


def main():
    """Main test runner"""
    try:
        tester = AuthTester()
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
