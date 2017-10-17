from rest_framework.exceptions import ValidationError


def validate_content_type(value, content_types: list):
    if value.content_type not in content_types:
        raise ValidationError("Некорректный тип файла")
