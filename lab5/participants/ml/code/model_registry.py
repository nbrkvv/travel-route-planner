"""L4 prototype of the Model Registry & Loader component (Python 3.10+).
 
Only the demo storage is in-memory. Real MinIO is behind ModelStorage.
The RAM budget is a conservative *logical cache budget*, not an OS memory limit.
"""
 
from __future__ import annotations
 
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from threading import Event
from typing import Mapping, Sequence
 
 
class StorageUnavailable(RuntimeError):
    """The external storage cannot be reached."""
 
 
class ModelUnavailable(RuntimeError):
    """No active model has been loaded yet."""
 
 
class InvalidArtifact(ValueError):
    """The downloaded artifact is invalid or does not match its metadata."""
 
 
@dataclass(frozen=True)
class ModelMetadata:
    version: str
    size_bytes: int
    priority: int = 0
 
 
@dataclass(frozen=True)
class LinearModel:
    weights: Mapping[str, float]
    bias: float
 
    def predict(self, features: Mapping[str, float]) -> float:
        return self.bias + sum(weight * features.get(name, 0.0)
                               for name, weight in self.weights.items())
 
 
@dataclass
class CachedModel:
    metadata: ModelMetadata
    model: LinearModel
    reserved_bytes: int
    last_access: int = 0
 
 
class ModelStorage(ABC):
    @abstractmethod
    def active_metadata(self) -> ModelMetadata:
        """Return the currently published model version."""
 
    @abstractmethod
    def download(self, version: str, max_bytes: int) -> bytes:
        """Return the artifact, rejecting payloads larger than max_bytes."""
 
 
class InMemoryMinIOStorage(ModelStorage):
    """Deterministic replacement for MinIO/S3, including an outage switch."""
 
    def __init__(self) -> None:
        self._artifacts: dict[str, bytes] = {}
        self._metadata: dict[str, ModelMetadata] = {}
        self._active_version: str | None = None
        self.online: bool = True
 
    def publish(self, version: str, weights: Mapping[str, float],
                bias: float = 0.0, priority: int = 0,
                padding_bytes: int = 0) -> None:
        artifact = json.dumps({"weights": dict(weights), "bias": bias,
                               "padding": "x" * padding_bytes}).encode("utf-8")
        self._artifacts[version] = artifact
        self._metadata[version] = ModelMetadata(version, len(artifact), priority)
        self._active_version = version
 
    def active_metadata(self) -> ModelMetadata:
        if not self.online:
            raise StorageUnavailable("MinIO is unreachable")
        if self._active_version is None:
            raise ModelUnavailable("No published model")
        return self._metadata[self._active_version]
 
    def download(self, version: str, max_bytes: int) -> bytes:
        if not self.online:
            raise StorageUnavailable("MinIO is unreachable")
        data = self._artifacts[version]
        if len(data) > max_bytes:
            raise InvalidArtifact("Download exceeds the allowed size")
        return data
 
 
class ModelLoader:
    """Validates and deserializes the model; no network or eviction logic."""
 
    @staticmethod
    def required_bytes(size_bytes: int) -> int:
        # Conservative demo reservation for deserialization and Python objects.
        return 2 * size_bytes + 256
 
    def load(self, metadata: ModelMetadata, artifact: bytes) -> CachedModel:
        if len(artifact) != metadata.size_bytes:
            raise InvalidArtifact("Artifact size differs from metadata")
        try:
            data = json.loads(artifact.decode("utf-8"))
            raw_weights = data["weights"]
            if not isinstance(raw_weights, dict):
                raise ValueError("Weights must be a dictionary")
            weights = {str(k): float(v) for k, v in raw_weights.items()}
            bias = float(data["bias"])
        except (ValueError, KeyError, TypeError, UnicodeError) as exc:
            raise InvalidArtifact("Unsupported artifact format") from exc
        return CachedModel(metadata, LinearModel(weights, bias),
                           self.required_bytes(len(artifact)))
 
 
class CacheEvictionStrategy(ABC):
    """Selects an eviction victim ONLY from inactive candidates."""
 
    @abstractmethod
    def choose_victim(self, candidates: Sequence[CachedModel]) -> str:
        """Return a version to remove from the cache."""
 
 
class LRUEvictionStrategy(CacheEvictionStrategy):
    def choose_victim(self, candidates: Sequence[CachedModel]) -> str:
        return min(candidates, key=lambda entry: entry.last_access).metadata.version
 
 
class PriorityEvictionStrategy(CacheEvictionStrategy):
    def choose_victim(self, candidates: Sequence[CachedModel]) -> str:
        return min(candidates, key=lambda entry: (entry.metadata.priority,
                                                   entry.last_access)).metadata.version
 
 
class FIFOEvictionStrategy(CacheEvictionStrategy):
    def choose_victim(self, candidates: Sequence[CachedModel]) -> str:
        return candidates[0].metadata.version
 
 
class ModelCache:
    """Cache with an explicit RAM reservation budget and pinned active model."""
 
    def __init__(self, budget_bytes: int, strategy: CacheEvictionStrategy) -> None:
        if budget_bytes <= 0:
            raise ValueError("RAM budget must be positive")
        self._budget_bytes = budget_bytes
        self._strategy = strategy
        self._entries: dict[str, CachedModel] = {}
        self._active_version: str | None = None
        self._clock = 0
 
    def set_strategy(self, strategy: CacheEvictionStrategy) -> None:
        self._strategy = strategy
 
    @property
    def budget_bytes(self) -> int:
        return self._budget_bytes
 
    @property
    def active_version(self) -> str | None:
        return self._active_version
 
    @property
    def used_bytes(self) -> int:
        return sum(entry.reserved_bytes for entry in self._entries.values())
 
    @property
    def cached_versions(self) -> tuple[str, ...]:
        return tuple(self._entries)
 
    def get_active_model(self) -> LinearModel:
        if self._active_version is None:
            raise ModelUnavailable("No model is cached")
        self._clock += 1
        entry = self._entries[self._active_version]
        entry.last_access = self._clock
        return entry.model
 
    def reserve_for_update(self, required_bytes: int) -> bool:
        """Evict inactive versions BEFORE download to bound staging memory.
 
        The active model is pinned, so a failed update never removes it.
        """
        if required_bytes > self._budget_bytes:
            return False
        kept = dict(self._entries)
        used = sum(entry.reserved_bytes for entry in kept.values())
        while used + required_bytes > self._budget_bytes:
            inactive = [entry for version, entry in kept.items()
                        if version != self._active_version]
            if not inactive:
                return False
            victim = self._strategy.choose_victim(inactive)
            if victim not in kept or victim == self._active_version:
                raise ValueError("Eviction strategy returned an invalid victim")
            used -= kept.pop(victim).reserved_bytes
        self._entries = kept
        return True
 
    def admit_and_activate(self, new_entry: CachedModel) -> bool:
        """Activate only after download and validation have succeeded."""
        version = new_entry.metadata.version
        if version in self._entries:
            self._active_version = version
            return True
        if self.used_bytes + new_entry.reserved_bytes > self._budget_bytes:
            return False
        self._clock += 1
        new_entry.last_access = self._clock
        self._entries[version] = new_entry
        self._active_version = version
        return True
 
 
class PollStatus(str, Enum):
    LOADED = "loaded"
    UNCHANGED = "unchanged"
    OFFLINE_CACHED = "offline_using_cached_model"
    MEMORY_LIMIT = "update_rejected_memory_limit"
    INVALID_ARTIFACT = "update_rejected_invalid_artifact"
 
 
class ModelRegistry:
    """L4 component responsible for polling, loading and serving cached models."""
 
    def __init__(self, storage: ModelStorage, loader: ModelLoader,
                 cache: ModelCache) -> None:
        self._storage = storage
        self._loader = loader
        self._cache = cache
 
    def get_active_model(self) -> LinearModel:
        return self._cache.get_active_model()
 
    def set_cache_strategy(self, strategy: CacheEvictionStrategy) -> None:
        self._cache.set_strategy(strategy)
 
    def poll_once(self) -> PollStatus:
        try:
            metadata = self._storage.active_metadata()
        except StorageUnavailable:
            if self._cache.active_version is None:
                raise ModelUnavailable("Storage is offline and no model was cached")
            return PollStatus.OFFLINE_CACHED
 
        if metadata.version == self._cache.active_version:
            return PollStatus.UNCHANGED
 
        # Preflight: prevent excessive downloads and unsafe hot replacements.
        required = self._loader.required_bytes(metadata.size_bytes)
        if metadata.size_bytes <= 0 or required > self._cache.budget_bytes:
            return PollStatus.MEMORY_LIMIT
        # Reserve room for payload + deserialization BEFORE allocating it.
        if not self._cache.reserve_for_update(required):
            return PollStatus.MEMORY_LIMIT
        try:
            payload = self._storage.download(metadata.version, metadata.size_bytes)
            entry = self._loader.load(metadata, payload)
        except StorageUnavailable:
            if self._cache.active_version is None:
                raise ModelUnavailable("Storage failed before the first load")
            return PollStatus.OFFLINE_CACHED
        except InvalidArtifact:
            return PollStatus.INVALID_ARTIFACT
 
        if not self._cache.admit_and_activate(entry):
            return PollStatus.MEMORY_LIMIT
        return PollStatus.LOADED
 
    def poll_periodically(self, interval_seconds: float, stop: Event) -> None:
        """An application may run this loop in its polling worker/thread."""
        if interval_seconds <= 0:
            raise ValueError("Polling interval must be positive")
        while not stop.is_set():
            self.poll_once()
            stop.wait(interval_seconds)
