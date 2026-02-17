"""YAML-based persistence for loader slash commands."""

from pathlib import Path

import yaml

from entryway.models.hook_data import LoaderCommandsData


class LoaderCommandStore:
    """Store for tracking loader slash commands by session."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self._data: LoaderCommandsData | None = None

    def load(self) -> None:
        if not self.file_path.exists():
            self._data = LoaderCommandsData()
            return
        try:
            yaml_content = self.file_path.read_text(encoding="utf-8")
            raw_data = yaml.safe_load(yaml_content) or {}
            self._data = LoaderCommandsData(**raw_data)
        except (yaml.YAMLError, ValueError, OSError):
            self._data = LoaderCommandsData()

    def has_command(self, session_id: str, command: str) -> bool:
        if self._data is None:
            raise RuntimeError("Data not loaded. Call load() first.")
        if session_id not in self._data.sessions:
            return False
        return command in self._data.sessions[session_id]

    def add_command(self, session_id: str, command: str) -> None:
        if self._data is None:
            raise RuntimeError("Data not loaded. Call load() first.")
        if session_id not in self._data.sessions:
            self._data.sessions[session_id] = []
        if command in self._data.sessions[session_id]:
            return
        self._data.sessions[session_id].append(command)

    def purge_session(self, session_id: str) -> None:
        if self._data is None:
            raise RuntimeError("Data not loaded. Call load() first.")
        if session_id not in self._data.sessions:
            return
        del self._data.sessions[session_id]

    def save(self) -> None:
        if self._data is None:
            raise RuntimeError("Data not loaded. Call load() first.")
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_content = yaml.safe_dump(
            self._data.model_dump(),
            default_flow_style=False,
            sort_keys=False,
        )
        self.file_path.write_text(yaml_content, encoding="utf-8")
