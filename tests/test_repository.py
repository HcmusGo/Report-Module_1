from __future__ import annotations
import json
from pathlib import Path
import pytest

from repositories.json_repository import JsonRepository

class DummyEntity:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> DummyEntity:
        return cls(id=data["id"], name=data["name"])

def test_repository_missing_file(tmp_path: Path):
    repo = JsonRepository(DummyEntity, "dummy.json", "D", data_dir=tmp_path, sample_dir=tmp_path)
    assert repo.get_all() == []
    file_path = tmp_path / "dummy.json"
    assert file_path.exists()

def test_repository_corrupted_json(tmp_path: Path):
    file_path = tmp_path / "dummy.json"
    file_path.write_text("{invalid_json...", encoding="utf-8")
    
    repo = JsonRepository(DummyEntity, "dummy.json", "D", data_dir=tmp_path, sample_dir=tmp_path)
    assert repo.get_all() == []
    bak_path = tmp_path / "dummy.json.bak"
    assert bak_path.exists()

def test_repository_vietnamese_characters(tmp_path: Path):
    repo = JsonRepository(DummyEntity, "dummy.json", "D", data_dir=tmp_path, sample_dir=tmp_path)
    entity = DummyEntity(id="D1", name="Nguyễn Vũ Băng Tâm")
    repo.add(entity)

    repo2 = JsonRepository(DummyEntity, "dummy.json", "D", data_dir=tmp_path, sample_dir=tmp_path)
    fetched = repo2.get_by_id("D1")
    assert fetched is not None
    assert fetched.name == "Nguyễn Vũ Băng Tâm"

def test_repository_next_id(tmp_path: Path):
    repo = JsonRepository(DummyEntity, "dummy.json", "D", data_dir=tmp_path, sample_dir=tmp_path)
    assert repo.next_id() == "D1"
    
    repo.add(DummyEntity(id="D1", name="Test 1"))
    assert repo.next_id() == "D2"
    
    repo.add(DummyEntity(id="D5", name="Test 5"))
    assert repo.next_id() == "D6"