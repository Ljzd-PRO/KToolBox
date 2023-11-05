import json
import random
from pathlib import Path
from typing import Dict, Any, List

openapi_schema_path = "openapi.json"
openapi_schema_path = Path(openapi_schema_path)

output_path = "."
output_path = Path(output_path)

schema_definition = "http://json-schema.org/draft-07/schema#"

encoding = "utf-8"

if __name__ == "__main__":
    object_names: List[str] = []

    with open(openapi_schema_path, encoding=encoding) as f:
        openapi_schema_dict: Dict[str, Any] = json.load(f)
    paths: Dict[str, Dict[str, Any]] = openapi_schema_dict["paths"]

    for path_name, path in paths.items():
        method: Dict[str, Any] = path.get("get") or path.get("post")
        if method and (response := method.get("responses")):
            if response_200 := response.get("200"):
                if response_json := response_200["content"].get("application/json"):
                    if schema := response_json.get("schema"):
                        if "title" not in schema:
                            if summary := method.get("summary"):
                                obj_name = summary.replace(" ", "_")
                                new_obj_name = obj_name
                                while new_obj_name in object_names:
                                    new_obj_name = f"{obj_name}_{random.randint(1000, 9999)}"
                            else:
                                while True:
                                    obj_name = f"Obj_{random.randint(1000, 9999)}"
                                    if obj_name not in object_names:
                                        break
                            object_names.append(obj_name)
                            schema["title"] = obj_name
                            schema["$schema"] = schema_definition
                            with open(output_path / f"{obj_name}.json", "w", encoding=encoding) as f:
                                json.dump(schema, f, indent=4, ensure_ascii=False)
