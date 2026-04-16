import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from skill.scripts.extract import extract_data


def load_config(args: argparse.Namespace) -> dict:
    if args.config:
        return json.loads(Path(args.config).read_text(encoding="utf-8"))
    if args.payload:
        return json.loads(args.payload)
    raise ValueError("请通过 --config 或直接传入 JSON 配置")


def main() -> int:
    parser = argparse.ArgumentParser(description="Excel 数据提取工具")
    parser.add_argument("payload", nargs="?", help="JSON 配置字符串")
    parser.add_argument("--config", help="JSON 配置文件路径")
    args = parser.parse_args()

    try:
        config = load_config(args)
        result = extract_data(
            file_path=config["file_path"],
            conditions=config.get("conditions", []),
            columns=config.get("columns"),
            sort_by=config.get("sort_by"),
            sort_ascending=config.get("sort_ascending", True),
            output_format=config.get("output_format", "json"),
        )
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
