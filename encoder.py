import json
from uuid import UUID

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # Convert UUID to a string
            return str(obj)
        return super().default(obj)
    
    