import unittest
import os
import json
from api.utils.memory_storage import (
    jobs_storage,
    extracts_storage,
    save_job_data_to_memory,
    load_job_data_from_memory,
    save_extract_data_to_memory,
    load_extract_data_from_memory,
    clear_memory_storage
)
from api.utils.helpers import is_vercel_environment, save_job_data, load_job_data, save_extract_data, load_extract_data

class TestMemoryStorage(unittest.TestCase):
    """Test the in-memory storage implementation."""
    
    def setUp(self):
        """Set up the test environment."""
        # Clear any existing data in memory storage
        clear_memory_storage()
        
        # Mock the Vercel environment
        os.environ["VERCEL"] = "1"
        
        # Test data
        self.job_id = "test-job-123"
        self.job_data = {
            "status": "success",
            "total_messages": 5,
            "messages": [
                {"text": "Test message 1", "ts": "1614556800.000000"},
                {"text": "Test message 2", "ts": "1614556900.000000"}
            ]
        }
        
        self.extract_id = "test-extract-456"
        self.extract_data = "This is test extracted content"
    
    def tearDown(self):
        """Clean up after the test."""
        # Clear memory storage
        clear_memory_storage()
        
        # Remove the Vercel environment variable
        if "VERCEL" in os.environ:
            del os.environ["VERCEL"]
    
    def test_is_vercel_environment(self):
        """Test the is_vercel_environment function."""
        self.assertTrue(is_vercel_environment())
        
        # Test with VERCEL not set
        del os.environ["VERCEL"]
        self.assertFalse(is_vercel_environment())
        
        # Reset for other tests
        os.environ["VERCEL"] = "1"
    
    def test_save_load_job_data_direct(self):
        """Test saving and loading job data directly with memory storage functions."""
        # Save job data to memory
        path = save_job_data_to_memory(self.job_id, self.job_data)
        self.assertEqual(path, f"memory://{self.job_id}")
        
        # Check that it's in the storage
        self.assertIn(self.job_id, jobs_storage)
        self.assertEqual(jobs_storage[self.job_id], self.job_data)
        
        # Load job data from memory
        loaded_data = load_job_data_from_memory(self.job_id)
        self.assertEqual(loaded_data, self.job_data)
        
        # Test loading non-existent job
        self.assertIsNone(load_job_data_from_memory("non-existent-job"))
    
    def test_save_load_job_data_through_helpers(self):
        """Test saving and loading job data through the helper functions."""
        # Save job data
        path = save_job_data(self.job_id, self.job_data)
        self.assertEqual(path, f"memory://{self.job_id}")
        
        # Load job data
        loaded_data = load_job_data(self.job_id)
        self.assertEqual(loaded_data, self.job_data)
    
    def test_save_load_extract_data_direct(self):
        """Test saving and loading extract data directly with memory storage functions."""
        # Save extract data to memory
        path = save_extract_data_to_memory(self.extract_id, self.extract_data)
        self.assertEqual(path, f"memory://{self.extract_id}")
        
        # Check that it's in the storage
        self.assertIn(self.extract_id, extracts_storage)
        self.assertEqual(extracts_storage[self.extract_id], self.extract_data)
        
        # Load extract data from memory
        loaded_data = load_extract_data_from_memory(self.extract_id)
        self.assertEqual(loaded_data, self.extract_data)
        
        # Test loading non-existent extract
        self.assertIsNone(load_extract_data_from_memory("non-existent-extract"))
    
    def test_save_load_extract_data_through_helpers(self):
        """Test saving and loading extract data through the helper functions."""
        # Save extract data
        path = save_extract_data(self.extract_id, self.extract_data)
        self.assertEqual(path, f"memory://{self.extract_id}")
        
        # Load extract data
        loaded_data = load_extract_data(self.extract_id)
        self.assertEqual(loaded_data, self.extract_data)
    
    def test_clear_memory_storage(self):
        """Test clearing memory storage."""
        # Save some data
        save_job_data_to_memory(self.job_id, self.job_data)
        save_extract_data_to_memory(self.extract_id, self.extract_data)
        
        # Verify data is saved
        self.assertIn(self.job_id, jobs_storage)
        self.assertIn(self.extract_id, extracts_storage)
        
        # Clear memory storage
        clear_memory_storage()
        
        # Verify data is cleared
        self.assertNotIn(self.job_id, jobs_storage)
        self.assertNotIn(self.extract_id, extracts_storage)
        self.assertEqual(len(jobs_storage), 0)
        self.assertEqual(len(extracts_storage), 0)


if __name__ == "__main__":
    unittest.main()
