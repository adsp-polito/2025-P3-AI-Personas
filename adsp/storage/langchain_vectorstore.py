"""Configurable LangChain vector store factory."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
from typing import Dict

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from adsp.config import PROCESSED_DATA_DIR
from adsp.data_pipeline.embedding_utils import get_embedding_dimension

DEFAULT_VECTORSTORE_BACKEND = "faiss"
DEFAULT_VECTORSTORE_COLLECTION_PREFIX = "adsp"
DEFAULT_VECTORSTORE_MILVUS_URI = "http://localhost:19530"

_VALID_BACKENDS = {"faiss", "chroma", "milvus"}
_NON_ALNUM_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _sanitize_name(value: str) -> str:
    cleaned = _NON_ALNUM_RE.sub("-", (value or "").strip())
    cleaned = cleaned.strip("-_").lower()
    return cleaned or "default"


@dataclass(frozen=True)
class VectorStoreConfig:
    backend: str = field(
        default_factory=lambda: os.environ.get(
            "ADSP_VECTORSTORE_BACKEND",
            DEFAULT_VECTORSTORE_BACKEND,
        ).strip().lower()
    )
    persist_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "ADSP_VECTORSTORE_PERSIST_DIR",
                str(PROCESSED_DATA_DIR / "vectorstores"),
            )
        )
    )
    collection_prefix: str = field(
        default_factory=lambda: os.environ.get(
            "ADSP_VECTORSTORE_COLLECTION_PREFIX",
            DEFAULT_VECTORSTORE_COLLECTION_PREFIX,
        ).strip()
        or DEFAULT_VECTORSTORE_COLLECTION_PREFIX
    )
    reset_on_startup: bool = field(
        default_factory=lambda: _env_flag("ADSP_VECTORSTORE_RESET_ON_STARTUP", False)
    )
    milvus_uri: str = field(
        default_factory=lambda: os.environ.get(
            "ADSP_VECTORSTORE_MILVUS_URI",
            DEFAULT_VECTORSTORE_MILVUS_URI,
        ).strip()
        or DEFAULT_VECTORSTORE_MILVUS_URI
    )
    milvus_token: str = field(
        default_factory=lambda: os.environ.get("ADSP_VECTORSTORE_MILVUS_TOKEN", "").strip()
    )
    milvus_db_name: str = field(
        default_factory=lambda: os.environ.get("ADSP_VECTORSTORE_MILVUS_DB_NAME", "").strip()
    )

    def validate(self) -> None:
        if self.backend not in _VALID_BACKENDS:
            supported = ", ".join(sorted(_VALID_BACKENDS))
            raise ValueError(
                f"Unsupported ADSP_VECTORSTORE_BACKEND={self.backend!r}. Supported values: {supported}."
            )


def get_vectorstore_config() -> VectorStoreConfig:
    config = VectorStoreConfig()
    config.validate()
    return config


def build_vectorstore(
    embeddings: Embeddings,
    *,
    namespace: str,
    config: VectorStoreConfig | None = None,
    reset: bool | None = None,
) -> VectorStore:
    config = config or get_vectorstore_config()
    reset = config.reset_on_startup if reset is None else reset
    collection_name = build_collection_name(namespace=namespace, config=config)

    if config.backend == "faiss":
        return _build_faiss(embeddings)
    if config.backend == "chroma":
        return _build_chroma(
            embeddings,
            collection_name=collection_name,
            config=config,
            reset=reset,
        )
    if config.backend == "milvus":
        return _build_milvus(
            embeddings,
            collection_name=collection_name,
            config=config,
            reset=reset,
        )

    config.validate()
    raise AssertionError("unreachable")


@dataclass
class VectorStoreProvider:
    """Cache vector stores by namespace so runtime initializes backend objects once."""

    embeddings: Embeddings
    config: VectorStoreConfig = field(default_factory=get_vectorstore_config)
    _stores: Dict[str, VectorStore] = field(default_factory=dict)

    def get(self, namespace: str) -> VectorStore:
        store = self._stores.get(namespace)
        if store is not None:
            return store

        store = build_vectorstore(
            self.embeddings,
            namespace=namespace,
            config=self.config,
        )
        self._stores[namespace] = store
        return store

    def load(self, namespace: str, *, fingerprint: str) -> VectorStore | None:
        store = self._stores.get(namespace)
        if store is not None and self._manifest_matches(namespace, fingerprint):
            return store

        if self.config.reset_on_startup or not self._manifest_matches(namespace, fingerprint):
            return None

        store = self._load_persisted(namespace)
        if store is None:
            return None

        self._stores[namespace] = store
        return store

    def create(self, namespace: str, *, reset: bool = False) -> VectorStore:
        store = build_vectorstore(
            self.embeddings,
            namespace=namespace,
            config=self.config,
            reset=reset,
        )
        self._stores[namespace] = store
        return store

    def persist(self, namespace: str, *, fingerprint: str, vectorstore: VectorStore | None = None) -> None:
        store = vectorstore or self._stores.get(namespace)
        if store is None:
            raise KeyError(f"Vector store for namespace {namespace!r} is not initialized")

        if self.config.backend == "faiss":
            path = self._faiss_write_dir(namespace)
            if path.exists():
                shutil.rmtree(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            save_local = getattr(store, "save_local", None)
            if not callable(save_local):
                raise RuntimeError("Configured FAISS vector store does not support save_local().")
            save_local(str(path))

        self._write_manifest(namespace, fingerprint=fingerprint)

    def _load_persisted(self, namespace: str) -> VectorStore | None:
        if self.config.backend == "faiss":
            try:
                from langchain_community.vectorstores import FAISS
            except Exception as exc:
                raise RuntimeError(
                    "FAISS vector store requires `faiss-cpu` and `langchain-community` to be installed."
                ) from exc
            for path in self._faiss_read_dirs(namespace):
                if not path.exists():
                    continue
                try:
                    return FAISS.load_local(
                        str(path),
                        self.embeddings,
                        allow_dangerous_deserialization=True,
                    )
                except PermissionError:
                    continue
            return None

        return build_vectorstore(
            self.embeddings,
            namespace=namespace,
            config=self.config,
            reset=False,
        )

    def _manifest_matches(self, namespace: str, fingerprint: str) -> bool:
        payload = self._read_manifest(namespace)
        return isinstance(payload, dict) and payload.get("fingerprint") == fingerprint

    def _manifest_path(self, namespace: str) -> Path:
        collection_name = build_collection_name(namespace=namespace, config=self.config)
        return self.config.persist_dir / "manifests" / self.config.backend / f"{collection_name}.json"

    def _faiss_dir(self, namespace: str) -> Path:
        collection_name = build_collection_name(namespace=namespace, config=self.config)
        return self.config.persist_dir / "faiss" / collection_name

    def _faiss_fallback_dir(self, namespace: str) -> Path:
        collection_name = build_collection_name(namespace=namespace, config=self.config)
        return self.config.persist_dir / "faiss_fallback" / f"uid-{os.getuid()}" / collection_name

    def _faiss_read_dirs(self, namespace: str) -> list[Path]:
        primary = self._faiss_dir(namespace)
        fallback = self._faiss_fallback_dir(namespace)
        if primary == fallback:
            return [primary]
        if self._is_dir_writable(primary):
            return [primary, fallback]
        return [fallback, primary]

    def _faiss_write_dir(self, namespace: str) -> Path:
        primary = self._faiss_dir(namespace)
        if self._is_dir_writable(primary):
            return primary
        return self._faiss_fallback_dir(namespace)

    @staticmethod
    def _is_dir_writable(path: Path) -> bool:
        probe = path
        while not probe.exists():
            if probe.parent == probe:
                return False
            probe = probe.parent
        return os.access(probe, os.W_OK | os.X_OK)

    def _read_manifest(self, namespace: str) -> dict | None:
        path = self._manifest_path(namespace)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _write_manifest(self, namespace: str, *, fingerprint: str) -> None:
        path = self._manifest_path(namespace)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "backend": self.config.backend,
            "collection_name": build_collection_name(namespace=namespace, config=self.config),
            "fingerprint": fingerprint,
            "namespace": namespace,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def build_collection_name(*, namespace: str, config: VectorStoreConfig | None = None) -> str:
    config = config or get_vectorstore_config()
    prefix = _sanitize_name(config.collection_prefix)
    suffix = _sanitize_name(namespace)
    return f"{prefix}-{suffix}"


def _build_faiss(embeddings: Embeddings) -> VectorStore:
    try:
        import faiss  # type: ignore
        from langchain_community.docstore.in_memory import InMemoryDocstore
        from langchain_community.vectorstores import FAISS
    except Exception as exc:
        raise RuntimeError(
            "FAISS vector store requires `faiss-cpu` and `langchain-community` to be installed."
        ) from exc

    dim = get_embedding_dimension(embeddings)
    index = faiss.IndexFlatL2(dim)
    return FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
    )


def _build_chroma(
    embeddings: Embeddings,
    *,
    collection_name: str,
    config: VectorStoreConfig,
    reset: bool,
) -> VectorStore:
    try:
        from langchain_chroma import Chroma
    except Exception as exc:
        raise RuntimeError(
            "Chroma vector store requires `langchain-chroma` and `chromadb` to be installed."
        ) from exc

    persist_directory = config.persist_dir / "chroma"
    persist_directory.mkdir(parents=True, exist_ok=True)

    if reset:
        try:
            Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=str(persist_directory),
            ).delete_collection()
        except Exception:
            pass

    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(persist_directory),
    )


def _build_milvus(
    embeddings: Embeddings,
    *,
    collection_name: str,
    config: VectorStoreConfig,
    reset: bool,
) -> VectorStore:
    try:
        from langchain_milvus import Milvus
    except Exception as exc:
        raise RuntimeError(
            "Milvus vector store requires `langchain-milvus` and `pymilvus` to be installed."
        ) from exc

    connection_args = {"uri": config.milvus_uri}
    if config.milvus_token:
        connection_args["token"] = config.milvus_token
    if config.milvus_db_name:
        connection_args["db_name"] = config.milvus_db_name

    return Milvus(
        embedding_function=embeddings,
        collection_name=collection_name,
        connection_args=connection_args,
        drop_old=reset,
        auto_id=True,
    )


__all__ = [
    "DEFAULT_VECTORSTORE_BACKEND",
    "DEFAULT_VECTORSTORE_COLLECTION_PREFIX",
    "DEFAULT_VECTORSTORE_MILVUS_URI",
    "VectorStoreConfig",
    "VectorStoreProvider",
    "build_collection_name",
    "build_vectorstore",
    "get_vectorstore_config",
]
