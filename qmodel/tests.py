from django.test import TestCase
from .models import (
    compute_fingerprint,
    get_or_create_step_configs,
    create_a_job,
    get_next_job_id,
    Job,
    JobStep,
    StepConfig,
)


class TestComputeFingerprint(TestCase):
    """
    Test suite for compute_fingerprint() function.
    Tests SHA-256 hash consistency and deduplication capabilities.
    """

    def test_same_dict_produces_same_hash(self):
        """
        Test: Same dictionary always produces the same hash.
        Purpose: Ensure fingerprint consistency for identical configs.
        """
        config = {"param": "value", "nested": {"key": "data"}}

        hash1 = compute_fingerprint(config)
        hash2 = compute_fingerprint(config)

        self.assertEqual(hash1, hash2, "Same dict should produce identical hashes")

    def test_different_dict_produces_different_hash(self):
        """
        Test: Different dictionaries produce different hashes.
        Purpose: Ensure fingerprints uniquely identify different configs.
        """
        config1 = {"param": "value1"}
        config2 = {"param": "value2"}

        hash1 = compute_fingerprint(config1)
        hash2 = compute_fingerprint(config2)

        self.assertNotEqual(
            hash1, hash2, "Different dicts should produce different hashes"
        )

    def test_key_order_doesnt_matter(self):
        """
        Test: Dictionary key ordering doesn't affect the hash.
        Purpose: Ensure {'a': 1, 'b': 2} and {'b': 2, 'a': 1} produce same hash.
        This tests that json.dumps with sort_keys=True is working correctly.
        """
        # Create two dicts with same content but different insertion order
        config1 = {"z": 100, "a": 1, "m": 50}
        config2 = {"a": 1, "m": 50, "z": 100}

        hash1 = compute_fingerprint(config1)
        hash2 = compute_fingerprint(config2)

        self.assertEqual(
            hash1,
            hash2,
            "Key ordering should not affect hash - both should be identical",
        )

    def test_nested_dict_key_order_doesnt_matter(self):
        """
        Test: Nested dictionary key ordering doesn't affect the hash.
        Purpose: Ensure deep nested structures are also sorted consistently.
        """
        config1 = {"outer": {"z": 3, "a": 1, "m": 2}, "top": "value"}
        config2 = {"top": "value", "outer": {"a": 1, "m": 2, "z": 3}}

        hash1 = compute_fingerprint(config1)
        hash2 = compute_fingerprint(config2)

        self.assertEqual(hash1, hash2, "Nested key ordering should not affect hash")

    def test_hash_is_64_chars_long(self):
        """
        Test: SHA-256 hash is always 64 characters (hex format).
        Purpose: Ensure we get valid SHA-256 hex digests.
        """
        config = {"test": "data"}
        hash_value = compute_fingerprint(config)

        self.assertEqual(
            len(hash_value), 64, "SHA-256 hex digest should be 64 characters"
        )

    def test_hash_is_hexadecimal(self):
        """
        Test: Hash contains only valid hexadecimal characters (0-9, a-f).
        Purpose: Ensure the hash is properly formatted.
        """
        config = {"test": "data"}
        hash_value = compute_fingerprint(config)

        try:
            int(hash_value, 16)
            is_hex = True
        except ValueError:
            is_hex = False

        self.assertTrue(is_hex, "Hash should be valid hexadecimal")

    def test_empty_dict_produces_hash(self):
        """
        Test: Empty dictionary produces a valid hash.
        Purpose: Ensure fingerprinting works for edge cases.
        """
        config = {}
        hash_value = compute_fingerprint(config)

        self.assertEqual(
            len(hash_value), 64, "Empty dict should still produce 64-char hash"
        )

    def test_complex_nested_structure(self):
        """
        Test: Complex nested structures with lists, dicts, and primitives.
        Purpose: Ensure fingerprinting works for realistic configs.
        """
        config = {
            "recording": {
                "duration": 60,
                "channels": [0, 1, 2, 3],
                "settings": {"sample_rate": 30000, "gain": 0.195},
            },
            "preprocessing": ["filter", "whitening"],
        }

        hash_value = compute_fingerprint(config)

        self.assertEqual(
            len(hash_value), 64, "Complex structure should produce valid hash"
        )

        # Verify reproducibility
        hash_value2 = compute_fingerprint(config)
        self.assertEqual(
            hash_value, hash_value2, "Same complex structure should produce same hash"
        )

    def test_numeric_types_matter(self):
        """
        Test: Integer 1 and float 1.0 produce different hashes when serialized to JSON.
        Purpose: This documents the behavior of json.dumps - it preserves type distinction.
        Note: This is actually fine for our use case since different types = different configs.
        """
        config1 = {"value": 1}
        config2 = {"value": 1.0}

        hash1 = compute_fingerprint(config1)
        hash2 = compute_fingerprint(config2)

        # JSON distinguishes between 1 and 1.0 in serialization
        self.assertNotEqual(
            hash1,
            hash2,
            "JSON distinguishes int 1 from float 1.0, producing different hashes",
        )

    def test_string_vs_number(self):
        """
        Test: Strings and numbers with same value produce different hashes.
        Purpose: Ensure config type accuracy.
        """
        config1 = {"value": "100"}
        config2 = {"value": 100}

        hash1 = compute_fingerprint(config1)
        hash2 = compute_fingerprint(config2)

        self.assertNotEqual(
            hash1, hash2, "String '100' and number 100 should have different hashes"
        )


class TestGetOrCreateStepConfigs(TestCase):
    """Test suite for get_or_create_step_configs() function."""

    def test_creates_new_config_if_not_exists(self):
        """Test: Creates new StepConfig when fingerprint doesn't exist."""
        config = {"duration": 60, "sample_rate": 30000}
        function_name = "recording"

        fingerprint = get_or_create_step_configs(function_name, config)

        # Check that config was created
        self.assertTrue(
            StepConfig.objects.filter(config_block_hash=fingerprint).exists(),
            "StepConfig should be created",
        )

    def test_reuses_existing_config(self):
        """Test: Returns fingerprint without creating if config already exists."""
        config = {"duration": 60, "sample_rate": 30000}
        function_name = "recording"

        # Create config first time
        fingerprint1 = get_or_create_step_configs(function_name, config)
        initial_count = StepConfig.objects.count()

        # Try to create same config again
        fingerprint2 = get_or_create_step_configs(function_name, config)
        final_count = StepConfig.objects.count()

        # Should return same fingerprint without creating duplicate
        self.assertEqual(fingerprint1, fingerprint2, "Should return same fingerprint")
        self.assertEqual(initial_count, final_count, "Should not create duplicate")

    def test_stores_function_name(self):
        """Test: Stores the function name in StepConfig."""
        config = {"duration": 60}
        function_name = "kilosort"

        fingerprint = get_or_create_step_configs(function_name, config)
        step_config = StepConfig.objects.get(config_block_hash=fingerprint)

        self.assertEqual(
            step_config.function, function_name, "Function name should be stored"
        )

    def test_different_configs_different_fingerprints(self):
        """Test: Different configs produce different fingerprints."""
        config1 = {"duration": 60}
        config2 = {"duration": 120}

        fingerprint1 = get_or_create_step_configs("recording", config1)
        fingerprint2 = get_or_create_step_configs("recording", config2)

        self.assertNotEqual(
            fingerprint1,
            fingerprint2,
            "Different configs should have different fingerprints",
        )


class TestCreateAJob(TestCase):
    """Test suite for create_a_job() function."""

    def setUp(self):
        """Create test configs before each test."""
        # Create some StepConfigs
        self.config1 = {"duration": 60, "sample_rate": 30000}
        self.config2 = {"method": "kilosort2", "threshold": 0.5}

        self.fingerprint1 = get_or_create_step_configs("recording", self.config1)
        self.fingerprint2 = get_or_create_step_configs("kilosort", self.config2)

    def test_creates_job_with_single_step(self):
        """Test: Creates job with a single step."""
        job_env = {"timeout": 3600}
        job_steps = [
            {"identifier": self.fingerprint1, "function": "recording", "depends": []}
        ]

        job = create_a_job(job_env, job_steps)

        self.assertIsNotNone(job.job_id, "Job should have ID")
        self.assertEqual(job.status, "pending", "Job should start as pending")
        self.assertEqual(job.jobstep_set.count(), 1, "Job should have 1 step")

    def test_creates_job_with_multiple_steps(self):
        """Test: Creates job with multiple steps."""
        job_env = {"timeout": 3600}
        job_steps = [
            {"identifier": self.fingerprint1, "function": "recording", "depends": []},
            {
                "identifier": self.fingerprint2,
                "function": "kilosort",
                "depends": [self.fingerprint1],
            },
        ]

        job = create_a_job(job_env, job_steps)

        self.assertEqual(job.jobstep_set.count(), 2, "Job should have 2 steps")

    def test_fails_if_steps_empty(self):
        """Test: Raises error if job_steps is empty."""
        job_env = {}
        job_steps = []

        with self.assertRaises(RuntimeError):
            create_a_job(job_env, job_steps)

    def test_fails_if_step_not_dict(self):
        """Test: Raises error if step is not a dictionary."""
        job_env = {}
        job_steps = ["not a dict"]

        with self.assertRaises(RuntimeError):
            create_a_job(job_env, job_steps)

    def test_fails_if_missing_required_field(self):
        """Test: Raises error if step missing required field."""
        job_env = {}
        job_steps = [
            {
                "identifier": self.fingerprint1,
                # Missing "function" and "depends"
            }
        ]

        with self.assertRaises(RuntimeError):
            create_a_job(job_env, job_steps)

    def test_fails_if_config_not_exists(self):
        """Test: Raises error if StepConfig doesn't exist."""
        job_env = {}
        job_steps = [
            {
                "identifier": "nonexistent_hash_12345",
                "function": "recording",
                "depends": [],
            }
        ]

        with self.assertRaises(RuntimeError):
            create_a_job(job_env, job_steps)

    def test_preserves_dependencies(self):
        """Test: Stores dependencies correctly."""
        job_env = {}
        dependencies = ["step1", "step2"]
        job_steps = [
            {
                "identifier": self.fingerprint1,
                "function": "recording",
                "depends": dependencies,
            }
        ]

        job = create_a_job(job_env, job_steps)
        step = job.jobstep_set.first()

        self.assertEqual(
            step.depends_on, dependencies, "Dependencies should be preserved"
        )


class TestGetNextJobId(TestCase):
    """Test suite for get_next_job_id() function."""

    def setUp(self):
        """Create test jobs before each test."""
        self.config_hash = get_or_create_step_configs("test", {"test": "data"})

    def test_returns_none_if_no_pending_jobs(self):
        """Test: Returns None if no pending jobs exist."""
        job = get_next_job_id()
        self.assertIsNone(job, "Should return None if no pending jobs")

    def test_fetches_oldest_pending_job(self):
        """Test: Fetches the oldest pending job first (FIFO)."""
        # Create two jobs
        job1 = Job.objects.create(job_env_config={}, status="pending")
        job2 = Job.objects.create(job_env_config={}, status="pending")

        # Get next job - should be job1 (oldest)
        fetched_job = get_next_job_id()
        self.assertEqual(
            fetched_job.job_id, job1.job_id, "Should fetch oldest job first"
        )

    def test_marks_job_as_fetched(self):
        """Test: Marks job as 'fetched' after retrieval."""
        job = Job.objects.create(job_env_config={}, status="pending")

        fetched_job = get_next_job_id()

        # Refresh from database to get updated status
        fetched_job.refresh_from_db()
        self.assertEqual(
            fetched_job.status, "fetched", "Job should be marked as fetched"
        )

    def test_skips_non_pending_jobs(self):
        """Test: Skips jobs that are not pending."""
        job1 = Job.objects.create(job_env_config={}, status="running")
        job2 = Job.objects.create(job_env_config={}, status="pending")

        fetched_job = get_next_job_id()

        self.assertEqual(
            fetched_job.job_id, job2.job_id, "Should skip non-pending jobs"
        )

    def test_fifo_order_with_multiple_jobs(self):
        """Test: Returns jobs in FIFO order."""
        # Create 3 jobs
        job1 = Job.objects.create(job_env_config={}, status="pending")
        job2 = Job.objects.create(job_env_config={}, status="pending")
        job3 = Job.objects.create(job_env_config={}, status="pending")

        # Fetch them in order
        fetched1 = get_next_job_id()
        fetched2 = get_next_job_id()
        fetched3 = get_next_job_id()

        self.assertEqual(fetched1.job_id, job1.job_id, "First fetched should be job1")
        self.assertEqual(fetched2.job_id, job2.job_id, "Second fetched should be job2")
        self.assertEqual(fetched3.job_id, job3.job_id, "Third fetched should be job3")


class test_model(TestCase):
    """Placeholder for other model tests"""

    pass
