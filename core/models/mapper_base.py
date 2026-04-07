"""
Helper functions for handling version fields in mappers.
"""


def versioned_fields_to_dict(django_model):
    """
    Extract version fields from Django model to dictionary.

    Args:
        django_model: Django model instance with version fields

    Returns:
        dict: Dictionary with version fields
    """
    return {
        "version": getattr(django_model, "version", 1),
        "last_modified_node": getattr(django_model, "last_modified_node", ""),
        "last_modified_at": getattr(django_model, "last_modified_at", None),
    }


def versioned_fields_from_dict(domain_dict, django_model):
    """
    Apply version fields from domain model dict to Django model.

    Args:
        domain_dict: Dictionary containing version fields
        django_model: Django model instance to update

    Returns:
        Django model instance with version fields applied
    """
    if "version" in domain_dict:
        django_model.version = domain_dict["version"]
    if "last_modified_node" in domain_dict:
        django_model.last_modified_node = domain_dict["last_modified_node"]
    if "last_modified_at" in domain_dict:
        django_model.last_modified_at = domain_dict["last_modified_at"]
    return django_model
