"""`trainer.pt` of training/train_lora.py is a pickle: --resume has to read it with
`torch.load(weights_only=True)`, and only from a torch that keeps that promise (2.6 or later).

torch is not part of this project's environment, so these tests run against a fake `torch` module
(what is asked of it, and what it answers); the one test that needs the real library is skipped
without it. training/ is not imported by the package: the module is loaded from its folder.
"""

import importlib
import os
import pickle
import sys
import types
from pathlib import Path

import pytest

TRAINING = Path(__file__).resolve().parent.parent / "training"
REFUSAL = "WeightsUnpickler error: Unsupported global: GLOBAL os.system was not an allowed global"


class FakeTorch(types.ModuleType):
    """`torch.save` and `torch.load` as far as train_lora.py uses them, with a record of both."""

    def __init__(self, version="2.11.0+cu128", refuses=False):
        super().__init__("torch")
        self.__version__ = version
        self.refuses = refuses
        self.saved = []
        self.loads = []

    def save(self, state, path):
        self.saved.append(Path(path))
        Path(path).write_bytes(b"checkpoint")

    def load(self, path, weights_only=False, map_location=None):
        self.loads.append((Path(path), weights_only, map_location))
        if self.refuses:
            raise pickle.UnpicklingError(
                "Weights only load failed. Re-running `torch.load` with `weights_only` set to "
                "`False` will likely succeed, but it can result in arbitrary code execution.\n\n"
                f"{REFUSAL}\n"
            )
        return {"step": 200}


@pytest.fixture
def train_lora(monkeypatch):
    """The module, imported from training/ and gone again (with its `common`) after the test."""
    monkeypatch.syspath_prepend(str(TRAINING))
    for name in ("train_lora", "common"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    module = importlib.import_module("train_lora")
    yield module
    for name in ("train_lora", "common"):
        sys.modules.pop(name, None)


@pytest.fixture
def torch_is(monkeypatch):
    """Put a fake torch where `import torch` finds it, and hand it back."""

    def install(**options):
        fake = FakeTorch(**options)
        monkeypatch.setitem(sys.modules, "torch", fake)
        return fake

    return install


def test_resume_reads_trainer_pt_with_weights_only(train_lora, torch_is, tmp_path):
    fake = torch_is()
    assert train_lora.load_trainer_state(tmp_path / "trainer.pt") == {"step": 200}
    assert fake.loads == [(tmp_path / "trainer.pt", True, None)]
    train_lora.load_trainer_state(tmp_path / "trainer.pt", map_location="cpu")
    assert fake.loads[-1] == (tmp_path / "trainer.pt", True, "cpu")


def test_a_trainer_pt_that_torch_refuses_is_not_returned(train_lora, torch_is, tmp_path):
    torch_is(refuses=True)
    with pytest.raises(pickle.UnpicklingError):
        train_lora.load_trainer_state(tmp_path / "trainer.pt")


def test_a_checkpoint_is_written_aside_read_back_with_weights_only_and_then_renamed(
    train_lora, torch_is, tmp_path
):
    fake = torch_is()
    target = tmp_path / "step-200" / "trainer.pt"
    target.parent.mkdir()
    train_lora.save_trainer_state({"step": 200}, target)
    partial = target.with_name("trainer.pt.part")
    assert fake.saved == [partial]  # torch never wrote the final name
    assert fake.loads == [(partial, True, "cpu")]  # the read --resume will do, on that file
    assert target.read_bytes() == b"checkpoint"
    assert not partial.exists()


def test_a_state_that_resume_would_refuse_fails_the_checkpoint_that_writes_it(
    train_lora, torch_is, tmp_path
):
    torch_is(refuses=True)
    target = tmp_path / "trainer.pt"
    with pytest.raises(RuntimeError, match=r"trainer\.pt was not written") as raised:
        train_lora.save_trainer_state({"step": 200}, target)
    message = str(raised.value)
    assert "Unsupported global: GLOBAL os.system" in message  # what torch refused
    assert "weights_only` set to `False`" not in message  # not torch's advice to turn the guard off
    assert isinstance(raised.value.__cause__, pickle.UnpicklingError)
    assert not target.exists()
    assert not target.with_name("trainer.pt.part").exists()


def test_a_refused_save_leaves_the_checkpoint_that_was_already_there(
    train_lora, torch_is, tmp_path
):
    torch_is(refuses=True)
    target = tmp_path / "trainer.pt"
    target.write_bytes(b"older checkpoint")
    with pytest.raises(RuntimeError):
        train_lora.save_trainer_state({"step": 400}, target)
    assert target.read_bytes() == b"older checkpoint"


@pytest.mark.parametrize(
    ("version", "stops"),
    [
        ("1.13.0", True),
        ("2.5.1", True),
        ("2.5.1+cu121", True),
        ("2.6.0", False),
        ("2.6.0+cpu", False),
        ("2.11.0+cu128", False),
        ("10.0.0", False),
        ("dev", True),
        ("", True),
    ],
)
def test_torch_before_2_6_is_refused(train_lora, torch_is, version, stops):
    """Up to 2.5.1 even weights_only=True could run code from a crafted file (CVE-2025-32434)."""
    torch_is(version=version)
    if stops:
        with pytest.raises(SystemExit, match=r"is not 2\.6 or later"):
            train_lora.require_torch_floor()
    else:
        train_lora.require_torch_floor()


def test_nothing_is_written_nor_read_on_an_old_torch(train_lora, torch_is, tmp_path):
    fake = torch_is(version="2.5.1")
    with pytest.raises(SystemExit):
        train_lora.save_trainer_state({"step": 200}, tmp_path / "trainer.pt")
    with pytest.raises(SystemExit):
        train_lora.load_trainer_state(tmp_path / "trainer.pt")
    assert fake.saved == []
    assert fake.loads == []
    assert list(tmp_path.iterdir()) == []


def test_no_script_in_training_loads_a_pickle_without_weights_only():
    """The call that was there before: `torch.load(..., weights_only=False)` on trainer.pt."""
    for path in sorted(TRAINING.glob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            assert "weights_only=False" not in line, f"{path.name}:{number}"
            if "torch.load(" in line:
                assert "weights_only=True" in line, f"{path.name}:{number}"


def test_real_torch_refuses_a_trainer_pt_with_a_payload_and_runs_nothing(train_lora, tmp_path):
    torch = pytest.importorskip("torch", reason="needs torch 2.6+: the training environment")
    marker = tmp_path / "ran"

    class Payload:
        def __reduce__(self):
            return (os.system, (f"touch {marker}",))

    path = tmp_path / "trainer.pt"
    torch.save({"step": 200, "history": Payload()}, path)
    with pytest.raises(pickle.UnpicklingError):
        train_lora.load_trainer_state(path)
    assert not marker.exists()
    with pytest.raises(RuntimeError, match="was not written"):
        train_lora.save_trainer_state({"step": 200, "history": Payload()}, tmp_path / "next.pt")
    assert not marker.exists()
    assert not (tmp_path / "next.pt").exists()
