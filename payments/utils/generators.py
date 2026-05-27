import uuid


def generate_reference():
    return f"PAY-{uuid.uuid4().hex[:12].upper()}"