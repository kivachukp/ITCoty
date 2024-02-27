from pathlib import Path

_this_file = Path(__file__).resolve()

DIR_ROOT = _this_file.parent.parent.resolve()
DIR_EXCEL = (DIR_ROOT / "excel").resolve()
DIR_LOGS = (DIR_ROOT / "logs").resolve()
DIR_OTHERS = (DIR_ROOT / "other_operations").resolve()
DIR_PATTERNS = (DIR_ROOT / "patterns").resolve()
DIR_REPORT = (DIR_ROOT / "report").resolve()
DIR_UTILS = (DIR_ROOT / "utils").resolve()