from bson import ObjectId


def serialize_mongo_doc(data: dict | list) -> dict | list:
    """
    Recursively convert MongoDB documents containing ObjectIds to JSON serializable format.
    Handles both dictionaries and lists of dictionaries.

    Args:
        data: MongoDB document or list of documents

    Returns:
        The same structure with ObjectIds converted to strings
    """
    if isinstance(data, list):
        return [serialize_mongo_doc(item) for item in data]

    if not isinstance(data, dict):
        return str(data) if isinstance(data, ObjectId) else data

    result = {}
    for key, value in data.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, (dict, list)):
            result[key] = serialize_mongo_doc(value)
        else:
            result[key] = value
    return result
