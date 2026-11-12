"""`trainer.pt` of training/train_lora.py is a pickle: --resume has to read it with
`torch.load(weights_only=True)`, and only from a torch that keeps that promise (2.6.0 or later,
pre-releases of it excluded). Every script of training/ that loads weights through torch checks
the same floor first.

torch is not part of this project's environment, so most tests run against a fake `torch` module
(what is asked of it, and what it answers); the ones that need the real library are skipped
without it. training/ is not imported by the package: the modules are loaded from their folder.
"""

import ast
import importlib
import os
import pickle
import random
import sys
import types
from pathlib import Path

import pytest

TRAINING = Path(__file__).resolve().parent.parent / "training"
REFUSAL = (
    "Weights only load failed. In PyTorch 2.6, we changed the default value of the "
    "`weights_only` argument in `torch.load` from `False` to `True`. Re-running `torch.load` "
    "with `weights_only` set to `False` will likely succeed, but it can result in arbitrary code "
    "execution.\n\n"
    "WeightsUnpickler error: Unsupported global: GLOBAL pathlib.PosixPath was not an allowed "
    "global by default. Please use `torch.serialization.add_safe_globals([pathlib.PosixPath])` "
    "or the `torch.serialization.safe_globals([pathlib.PosixPath])` context manager.\n"
)
ADVICE = ("weights_only", "add_safe_globals", "safe_globals", "False", "arbitrary code")


class FakeTorch(types.ModuleType):
    """`torch.save` and `torch.load` as far as train_lora.py uses them, with a record of both."""

    def __init__(self, version="2.11.0+cu128", refusal=None, save_error=None):
        super().__init__("torch")
        self.__version__ = version
        self.refusal = refusal  # the message of the UnpicklingError that load raises
        self.save_error = save_error  # raised by save after it wrote part of the file
        self.saved = []
        self.loads = []
        self.bfloat16 = "bfloat16"
        self.cuda = types.SimpleNamespace(set_per_process_memory_fraction=lambda fraction: None)

    def save(self, state, path):
        self.saved.append(Path(path))
        Path(path).write_bytes(b"checkpoint")
        if self.save_error:
            raise self.save_error

    def load(self, path, weights_only=False, map_location=None):
        self.loads.append((Path(path), weights_only, map_location))
        if self.refusal:
            raise pickle.UnpicklingError(self.refusal)
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


def test_a_trainer_pt_that_torch_refuses_is_refused_with_our_message_alone(
    train_lora, torch_is, tmp_path
):
    torch_is(refusal=REFUSAL)
    path = tmp_path / "trainer.pt"
    with pytest.raises(train_lora.TrainerStateRefused) as raised:
        train_lora.load_trainer_state(path)
    message = str(raised.value)
    assert message == (
        f"{path} holds objects other than tensors and plain data (the first one refused: "
        "pathlib.PosixPath), and was refused. Do not load checkpoint files from sources you do "
        "not trust."
    )
    assert not [word for word in ADVICE if word in message]  # no way round the protection
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__  # torch's own text is not in the traceback either


def test_a_refusal_that_names_no_object_is_still_ours(train_lora, torch_is, tmp_path):
    torch_is(refusal="Weights only load failed.\n\nUnsupported operand 149\n")
    with pytest.raises(train_lora.TrainerStateRefused) as raised:
        train_lora.load_trainer_state(tmp_path / "trainer.pt")
    assert "plain data, and was refused" in str(raised.value)
    assert "first one refused" not in str(raised.value)
    assert "Unsupported operand" not in str(raised.value)


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
    torch_is(refusal=REFUSAL)
    target = tmp_path / "trainer.pt"
    with pytest.raises(RuntimeError, match=r"trainer\.pt was not written") as raised:
        train_lora.save_trainer_state({"step": 200}, target)
    message = str(raised.value)
    assert (
        "objects other than tensors and plain data (the first one refused: pathlib.PosixPath)"
        in message
    )
    assert not [word for word in ADVICE if word in message]  # ours alone, no torch hint
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__
    assert not target.exists()
    assert not target.with_name("trainer.pt.part").exists()


def test_a_refused_save_leaves_the_checkpoint_that_was_already_there(
    train_lora, torch_is, tmp_path
):
    torch_is(refusal=REFUSAL)
    target = tmp_path / "trainer.pt"
    target.write_bytes(b"older checkpoint")
    with pytest.raises(RuntimeError):
        train_lora.save_trainer_state({"step": 400}, target)
    assert target.read_bytes() == b"older checkpoint"


@pytest.mark.parametrize("error", [OSError("No space left on device"), KeyboardInterrupt()])
def test_a_write_that_fails_leaves_no_part_file_and_the_error_comes_through(
    train_lora, torch_is, tmp_path, error
):
    fake = torch_is(save_error=error)
    target = tmp_path / "trainer.pt"
    with pytest.raises(type(error)):
        train_lora.save_trainer_state({"step": 200}, target)
    assert fake.saved == [target.with_name("trainer.pt.part")]  # torch did write some of it
    assert fake.loads == []  # and nothing was read back from a file that did not finish
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("version", "accepted"),
    [
        ("2.6.0", True),
        ("2.6.0+cpu", True),
        ("2.6.1", True),
        ("2.11.0+cu128", True),
        ("2.7.0.dev20250101+cu126", True),  # a nightly of a later version has the fix
        ("10.0.0", True),
        ("2.6.0.dev20241010", False),  # pre-releases of 2.6.0 may predate the fix
        ("2.6.0.dev", False),
        ("2.6.0a0", False),
        ("2.6.0rc1", False),
        ("2.5.1+cu121", False),
        ("2.5.1", False),
        ("1.13.0", False),
        ("dev", False),  # a version that cannot be read
        ("", False),
    ],
)
def test_torch_before_2_6_0_and_its_pre_releases_are_refused(
    train_lora, torch_is, version, accepted
):
    """Up to 2.5.1 even weights_only=True could run code from a crafted file (CVE-2025-32434)."""
    torch_is(version=version)
    if accepted:
        train_lora.require_torch_floor()
    else:
        with pytest.raises(SystemExit, match=r"older than 2\.6\.0") as raised:
            train_lora.require_torch_floor()
        assert "CVE-2025-32434" in str(raised.value)


def test_nothing_is_written_nor_read_on_an_old_torch(train_lora, torch_is, tmp_path):
    fake = torch_is(version="2.5.1")
    with pytest.raises(SystemExit):
        train_lora.save_trainer_state({"step": 200}, tmp_path / "trainer.pt")
    with pytest.raises(SystemExit):
        train_lora.load_trainer_state(tmp_path / "trainer.pt")
    assert fake.saved == []
    assert fake.loads == []
    assert list(tmp_path.iterdir()) == []


def fake_transformers(monkeypatch):
    """`AutoModelForCausalLM.from_pretrained` that only says it was called."""
    calls = []

    def from_pretrained(folder, **options):
        calls.append((folder, options))
        return "model"

    model = types.SimpleNamespace(from_pretrained=from_pretrained)
    module = types.ModuleType("transformers")
    module.AutoModelForCausalLM = model  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "transformers", module)
    return calls


def test_load_model_checks_the_torch_floor_before_it_reads_any_weights(
    train_lora, torch_is, monkeypatch
):
    calls = fake_transformers(monkeypatch)
    common = sys.modules["common"]
    torch_is(version="2.5.1+cu121")
    with pytest.raises(SystemExit, match=r"older than 2\.6\.0"):
        common.load_model("bf16")
    assert calls == []
    torch_is(version="2.6.0")
    assert common.load_model("bf16") == "model"
    assert [folder for folder, _ in calls] == [common.MODEL_DIR]


def test_export_gguf_checks_the_torch_floor_before_it_makes_its_output_folder(
    train_lora, torch_is, monkeypatch
):
    calls = fake_transformers(monkeypatch)
    export = importlib.import_module("export_gguf")
    try:
        torch_is(version="2.5.1")
        monkeypatch.setattr(sys, "argv", ["export_gguf.py", "--base", "refused-by-the-floor"])
        with pytest.raises(SystemExit, match=r"older than 2\.6\.0"):
            export.main()
        assert not (export.ROOT / ".research" / "merged" / "refused-by-the-floor").exists()
        assert calls == []
    finally:
        sys.modules.pop("export_gguf", None)


# --- what the scripts of training/ may call ------------------------------------------------------


def torch_load_calls_without_weights_only_true(source):
    """Line numbers of every call of torch.load that does not say weights_only=True: through
    `torch.load`, `import torch as t`, `from torch import load [as name]` or `torch.serialization`,
    on one line or many."""
    tree = ast.parse(source)
    modules, functions = {"torch"}, set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {a.asname or a.name for a in node.names if a.name.split(".")[0] == "torch"}
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "torch":
            functions |= {a.asname or a.name for a in node.names if a.name == "load"}
            modules |= {a.asname or a.name for a in node.names if a.name == "serialization"}
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Attribute) and target.attr == "load":
            root = target.value
            while isinstance(root, ast.Attribute):
                root = root.value
            is_load = isinstance(root, ast.Name) and root.id in modules
        else:
            is_load = isinstance(target, ast.Name) and target.id in functions
        if not is_load:
            continue
        keywords = {k.arg: k.value for k in node.keywords}
        safe = isinstance(keywords.get("weights_only"), ast.Constant) and (
            keywords["weights_only"].value is True  # type: ignore[attr-defined]
        )
        if not safe:
            found.append(node.lineno)
    return found


@pytest.mark.parametrize(
    "source",
    [
        "import torch\ntorch.load(path, weights_only=False)",
        "import torch\ntorch.load(\n    path,\n    map_location='cpu',\n    weights_only=False,\n)",
        "import torch\ntorch.load(path)",
        "import torch\ntorch.load(path, weights_only=flag)",
        "import torch\ntorch.load(path, **options)",
        "import torch as t\nt.load(path)",
        "from torch import load\nload(path)",
        "from torch import load as read\nread(path, weights_only=False)",
        "import torch.serialization\ntorch.serialization.load(path)",
        "from torch import serialization as s\ns.load(path)",
        "def f():\n    import torch\n\n    return torch.load(path)",
    ],
    ids=[
        "false",
        "multiline",
        "default",
        "variable",
        "kwargs",
        "alias",
        "from",
        "from-as",
        "serialization",
        "serialization-as",
        "nested",
    ],
)
def test_the_guard_finds_an_unsafe_torch_load_however_it_is_spelled(source):
    assert torch_load_calls_without_weights_only_true(source) != []


@pytest.mark.parametrize(
    "source",
    [
        "import torch\ntorch.load(path, weights_only=True, map_location='cpu')",
        "import torch\ntorch.load(\n    path,\n    weights_only=True,\n)",
        "from torch import load\nload(path, weights_only=True)",
        "import json\njson.load(stream)",
        "import pickle\nloaded = pickle.UnpicklingError",
        "def load(path):\n    return path\n\nload(1)",
    ],
    ids=["true", "multiline", "from", "json", "exception-class", "own-function"],
)
def test_the_guard_leaves_a_guarded_load_and_other_loads_alone(source):
    assert torch_load_calls_without_weights_only_true(source) == []


def test_no_script_in_training_loads_a_pickle_without_weights_only_true():
    for path in sorted(TRAINING.glob("*.py")):
        found = torch_load_calls_without_weights_only_true(path.read_text(encoding="utf-8"))
        assert found == [], f"{path.name}: torch.load without weights_only=True at lines {found}"


def lines_of_calls(source, names, skip=()):
    """Line numbers of calls of a function or method called one of `names`, in `source`, outside
    the functions named in `skip`."""
    tree = ast.parse(source)
    skipped = {
        id(inner)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name in skip
        for inner in ast.walk(node)
    }
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and id(node) not in skipped:
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name in names:
                lines.append(node.lineno)
    return sorted(lines)


def test_a_script_checks_the_torch_floor_before_it_loads_weights_through_transformers_or_peft():
    """`from_pretrained` reads a model or an adapter; an adapter folder with a pickle in it is
    unguarded on an old torch. The check is `require_torch_floor`, or `load_model`, which makes it."""
    checked = []
    for path in sorted(TRAINING.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        # The tokenizer reads no weights, and common.load_model is checked on its own just below.
        loads = lines_of_calls(source, {"from_pretrained"}, skip={"tokenizer", "load_model"})
        if not loads:
            continue
        checked.append(path.name)
        checks = lines_of_calls(source, {"require_torch_floor", "load_model"}, skip={"tokenizer"})
        assert checks, f"{path.name} loads weights and never checks the torch floor"
        assert min(checks) < min(loads), f"{path.name}: loads weights at line {min(loads)} first"
    assert "export_gguf.py" in checked  # it loads an adapter: the test is not vacuous


def test_load_model_calls_the_floor_before_from_pretrained():
    tree = ast.parse((TRAINING / "common.py").read_text(encoding="utf-8"))
    [function] = [
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "load_model"
    ]
    body = ast.unparse(function)
    assert body.index("require_torch_floor()") < body.index("from_pretrained(")


# --- with the real library -----------------------------------------------------------------------


class Payload:
    """What an attacker puts in a trainer.pt: a pickle that runs a command when it is read."""

    def __init__(self, marker):
        self.marker = str(marker)

    def __reduce__(self):
        return (os.system, (f"touch {self.marker}",))


def test_real_torch_refuses_a_trainer_pt_with_a_payload_and_runs_nothing(train_lora, tmp_path):
    torch = pytest.importorskip("torch", reason="needs torch 2.6+: the training environment")
    marker = tmp_path / "ran"
    path = tmp_path / "trainer.pt"
    torch.save({"step": 200, "history": Payload(marker)}, path)
    with pytest.raises(train_lora.TrainerStateRefused) as raised:
        train_lora.load_trainer_state(path)
    assert not marker.exists()
    assert not [word for word in ADVICE if word in str(raised.value)]
    with pytest.raises(RuntimeError, match="was not written") as refused:
        train_lora.save_trainer_state(
            {"step": 200, "history": Payload(marker)}, tmp_path / "next.pt"
        )
    assert not marker.exists()
    assert not [word for word in ADVICE if word in str(refused.value)]
    assert list(tmp_path.iterdir()) == [path]  # no next.pt and no next.pt.part


def test_real_torch_reads_back_the_state_that_train_lora_saves(train_lora, tmp_path):
    """The shape of what train_lora.py puts in trainer.pt at each checkpoint."""
    torch = pytest.importorskip("torch", reason="needs torch 2.6+: the training environment")
    weight = torch.nn.Parameter(torch.randn(4, 3))
    optimizer = torch.optim.AdamW([weight], lr=1e-3)
    weight.grad = torch.randn(4, 3)
    optimizer.step()  # fills in exp_avg, exp_avg_sq and the step counter
    rng = random.Random(7)  # noqa: S311  (a fixed seed in a test, not a secret)
    rng.random()
    state = {
        "step": 200,
        "optimizer": optimizer.state_dict(),
        "rng": rng.getstate(),  # (3, (625 integers), None)
        "plan": [[3, 1, 2], [0, 4]],
        "cursor": 7,
        "history": {
            "args": {"r": 16, "lr": 5e-5, "quant": "bf16", "resume": None, "flag": True},
            "log": [{"step": 5, "loss": 1.25, "lr": 1e-5, "elapsed": 12.5}],
            "eval": [{"step": 0, "loss": 2.0, "accuracy": 0.5}],
        },
        "torch_rng": torch.get_rng_state(),
        "cuda_rng": torch.get_rng_state(),  # stands in for the CUDA state: no GPU is needed here
    }
    path = tmp_path / "step-200" / "trainer.pt"
    path.parent.mkdir()
    train_lora.save_trainer_state(state, path)
    assert [item.name for item in path.parent.iterdir()] == ["trainer.pt"]
    back = train_lora.load_trainer_state(path, map_location="cpu")
    assert back["step"] == 200
    assert back["cursor"] == 7
    assert back["plan"] == state["plan"]
    assert back["history"] == state["history"]
    assert back["rng"] == state["rng"]
    resumed = random.Random()  # noqa: S311  (it only takes the saved state)
    resumed.setstate(back["rng"])  # what --resume does with it
    assert resumed.random() == rng.random()
    assert torch.equal(back["torch_rng"], state["torch_rng"])
    assert torch.equal(back["cuda_rng"], state["cuda_rng"])
    moments = back["optimizer"]["state"][0]
    original = optimizer.state_dict()["state"][0]
    assert torch.equal(moments["exp_avg"], original["exp_avg"])
    assert torch.equal(moments["exp_avg_sq"], original["exp_avg_sq"])
    assert back["optimizer"]["param_groups"] == original_groups(optimizer)


def original_groups(optimizer):
    return optimizer.state_dict()["param_groups"]
