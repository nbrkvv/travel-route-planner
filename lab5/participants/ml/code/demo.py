"""Manual demonstration of cache persistence and memory-limit protection."""
 
from model_registry import (FIFOEvictionStrategy, InMemoryMinIOStorage,
                            LRUEvictionStrategy, ModelCache, ModelLoader,
                            ModelRegistry)
 
 
def main() -> None:
    storage = InMemoryMinIOStorage()
    cache = ModelCache(budget_bytes=3600, strategy=LRUEvictionStrategy())
    registry = ModelRegistry(storage, ModelLoader(), cache)
 
    storage.publish("v1", {"museum": 0.8, "park": 0.2}, padding_bytes=460)
    print("Initial load:", registry.poll_once().value)
    print("Prediction:", registry.get_active_model().predict({"museum": 1.0}))
 
    storage.online = False
    print("MinIO disconnected:", registry.poll_once().value)
    print("Prediction offline:", registry.get_active_model().predict({"museum": 1.0}))
 
    storage.online = True
    storage.publish("v2", {"museum": 0.9, "park": 0.3}, padding_bytes=480)
    print("New version:", registry.poll_once().value)
    print("In RAM:", cache.cached_versions, "reserved:", cache.used_bytes)
 
    registry.set_cache_strategy(FIFOEvictionStrategy())
    storage.publish("v3", {"museum": 0.7, "park": 0.6}, padding_bytes=490)
    print("Eviction strategy changed; new version:", registry.poll_once().value)
    print("In RAM:", cache.cached_versions, "reserved:", cache.used_bytes)
 
    storage.publish("v4", {"museum": 0.95}, padding_bytes=2500)
    print("Oversized update:", registry.poll_once().value)
    print("Still running:", cache.active_version,
          registry.get_active_model().predict({"park": 1.0}))
 
 
if __name__ == "__main__":
    main()
