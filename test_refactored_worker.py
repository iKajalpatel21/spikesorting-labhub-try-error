#!/usr/bin/env python3
"""
Test script for the refactored worker components.
This script allows you to test individual components without running the full worker.
"""

import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.constants import Environment
from services.api_service import APIService
from services.worker_service import WorkerService


def setup_logging():
    """Setup logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def test_api_service(environment=Environment.LOCAL):
    """Test API service functionality"""
    print(f"\n=== Testing API Service ({environment}) ===")
    
    api_service = APIService(environment)
    
    # Test API info
    info = api_service.get_api_info()
    print(f"API Info: {info}")
    
    # Test getting next job
    try:
        job = api_service.get_next_job()
        if job:
            print(f"Found job: {job['job_id']}")
            print(f"Job steps: {len(job.get('job_steps', []))}")
        else:
            print("No jobs available")
    except Exception as e:
        print(f"Error getting job: {e}")


def test_worker_service(environment=Environment.LOCAL):
    """Test worker service functionality"""
    print(f"\n=== Testing Worker Service ({environment}) ===")
    
    worker = WorkerService(environment)
    
    # Test worker status
    status = worker.get_status()
    print(f"Worker Status: {status}")
    
    # Test single job processing
    try:
        print("Testing single job processing...")
        success = worker.process_single_job()
        print(f"Single job processing result: {success}")
    except Exception as e:
        print(f"Error in single job processing: {e}")


def main():
    """Main test function"""
    setup_logging()
    
    print("Refactored Worker Component Test")
    print("=" * 50)
    
    # Test with local environment (change to Environment.PRODUCTION for production testing)
    test_environment = Environment.LOCAL
    
    try:
        test_api_service(test_environment)
        test_worker_service(test_environment)
        
        print("\n=== Test Summary ===")
        print("✅ API Service: Tested")
        print("✅ Worker Service: Tested")
        print("\nTo run the full worker:")
        print(f"python qmodel_worker_refactored.py --environment {test_environment}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
