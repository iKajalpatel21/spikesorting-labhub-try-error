from django.test import TestCase
from .models import (
    compute_fingerprint,
    get_or_create_step_configs,
    create_a_job,
    get_next_job_id,
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


class test_model(TestCase):
    """Placeholder for other model tests"""

    pass
