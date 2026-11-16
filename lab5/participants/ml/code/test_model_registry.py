"""Behavioral checks for the LR3 registry using its in-memory storage boundary."""
import unittest

from model_registry import (FIFOEvictionStrategy, InMemoryMinIOStorage,
                            LRUEvictionStrategy, ModelCache, ModelLoader,
                            ModelRegistry, ModelUnavailable, PollStatus,
                            PriorityEvictionStrategy, StorageUnavailable)


class ObservedStorage(InMemoryMinIOStorage):
    def __init__(self):
        super().__init__()
        self.download_calls = 0
        self.fail_download = False
        self.corrupt_download = False

    def download(self, version, max_bytes):
        self.download_calls += 1
        if self.fail_download:
            raise StorageUnavailable("Download interrupted")
        payload = super().download(version, max_bytes)
        return b"x" * len(payload) if self.corrupt_download else payload


class RegistryBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.storage = ObservedStorage()
        self.storage.publish("v1", {"museum": 0.8})
        self.cache = ModelCache(4096, LRUEvictionStrategy())
        self.registry = ModelRegistry(self.storage, ModelLoader(), self.cache)

    def load(self):
        self.assertEqual(self.registry.poll_once(), PollStatus.LOADED)
        return self.registry.get_active_model()

    def test_first_load_serves_expected_prediction(self):
        self.assertAlmostEqual(self.load().predict({"museum": 1.0}), 0.8)
        self.assertEqual(self.cache.active_version, "v1")

    def test_unchanged_version_does_not_download_again(self):
        model = self.load()
        self.assertEqual(self.registry.poll_once(), PollStatus.UNCHANGED)
        self.assertEqual(self.storage.download_calls, 1)
        self.assertIs(self.registry.get_active_model(), model)

    def test_storage_outage_keeps_loaded_model_usable(self):
        model = self.load()
        self.storage.online = False
        self.assertEqual(self.registry.poll_once(), PollStatus.OFFLINE_CACHED)
        self.assertIs(self.registry.get_active_model(), model)
        self.assertAlmostEqual(model.predict({"museum": 1.0}), 0.8)

    def test_cold_start_offline_does_not_claim_model_available(self):
        self.storage.online = False
        with self.assertRaises(ModelUnavailable):
            self.registry.poll_once()
        with self.assertRaises(ModelUnavailable):
            self.registry.get_active_model()

    def test_oversized_update_rejected_before_download(self):
        model = self.load()
        self.storage.publish("v2", {"museum": 0.9}, padding_bytes=5000)
        self.assertEqual(self.registry.poll_once(), PollStatus.MEMORY_LIMIT)
        self.assertEqual(self.storage.download_calls, 1)
        self.assertEqual(self.cache.active_version, "v1")
        self.assertIs(self.registry.get_active_model(), model)

    def test_active_model_is_pinned_when_replacement_cannot_fit(self):
        size = ModelLoader.required_bytes(self.storage.active_metadata().size_bytes)
        self.cache = ModelCache(size, FIFOEvictionStrategy())
        self.registry = ModelRegistry(self.storage, ModelLoader(), self.cache)
        model = self.load()
        self.storage.publish("v2", {"museum": 0.9})
        self.assertEqual(self.registry.poll_once(), PollStatus.MEMORY_LIMIT)
        self.assertEqual(self.storage.download_calls, 1)
        self.assertIs(self.registry.get_active_model(), model)

    def test_corrupt_update_does_not_replace_active_model(self):
        model = self.load()
        self.storage.publish("v2", {"museum": 0.9})
        self.storage.corrupt_download = True
        self.assertEqual(self.registry.poll_once(), PollStatus.INVALID_ARTIFACT)
        self.assertEqual(self.cache.active_version, "v1")
        self.assertIs(self.registry.get_active_model(), model)

    def test_interrupted_update_keeps_old_model(self):
        model = self.load()
        self.storage.publish("v2", {"museum": 0.9})
        self.storage.fail_download = True
        self.assertEqual(self.registry.poll_once(), PollStatus.OFFLINE_CACHED)
        self.assertIs(self.registry.get_active_model(), model)

    def test_interrupted_first_download_has_no_cached_fallback(self):
        self.storage.fail_download = True
        with self.assertRaises(ModelUnavailable):
            self.registry.poll_once()
        self.assertIsNone(self.cache.active_version)

    def test_recovery_loads_new_version_after_outage(self):
        self.load()
        self.storage.online = False
        self.assertEqual(self.registry.poll_once(), PollStatus.OFFLINE_CACHED)
        self.storage.online = True
        self.storage.publish("v2", {"museum": 0.9})
        self.assertEqual(self.registry.poll_once(), PollStatus.LOADED)
        self.assertEqual(self.cache.active_version, "v2")
        self.assertAlmostEqual(self.registry.get_active_model().predict({"museum": 1.0}), 0.9)

    def test_switchable_strategies_evict_only_inactive_versions(self):
        for strategy in (FIFOEvictionStrategy(), LRUEvictionStrategy(),
                         PriorityEvictionStrategy()):
            with self.subTest(strategy=type(strategy).__name__):
                storage = ObservedStorage()
                storage.publish("v1", {"museum": 0.8})
                size = ModelLoader.required_bytes(storage.active_metadata().size_bytes)
                cache = ModelCache(2 * size, LRUEvictionStrategy())
                registry = ModelRegistry(storage, ModelLoader(), cache)
                self.assertEqual(registry.poll_once(), PollStatus.LOADED)
                storage.publish("v2", {"museum": 0.8})
                self.assertEqual(registry.poll_once(), PollStatus.LOADED)
                registry.set_cache_strategy(strategy)
                storage.publish("v3", {"museum": 0.8})
                self.assertEqual(registry.poll_once(), PollStatus.LOADED)
                self.assertEqual(cache.cached_versions, ("v2", "v3"))
                self.assertEqual(cache.active_version, "v3")
                self.assertLessEqual(cache.used_bytes, cache.budget_bytes)


if __name__ == "__main__":
    unittest.main()
