from __future__ import annotations

from datetime import date, datetime
from typing import Any

def default_json_serializer(obj: Any) -> Any:
    """
    Default JSON serializer for objects not serializable by default json code.
    Serializes datetime and date objects to standard ISO strings.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} is not JSON serializable")
