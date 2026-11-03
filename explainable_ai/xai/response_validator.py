import json

class XAIResponseValidationError(Exception):
    """Raised when an XAI provider response does not conform to the required schema."""
    pass

def validate_xai_response(response):
    """Validate that a response dictionary follows the strict XAI schema.

    Args:
        response (dict): The parsed JSON response from an LLM provider.

    Raises:
        XAIResponseValidationError: If any validation rule is violated.
    """
    # Rule A: Must be a dict
    if not isinstance(response, dict):
        raise XAIResponseValidationError("Response must be a Python dictionary.")

    required_keys = [
        "overall_condition",
        "summary",
        "why_degraded",
        "key_evidence",
        "affected_regions_explanation",
        "severity_explanation",
        "technical_interpretation",
        "limitations",
    ]

    # Rule B: All required keys exist
    for key in required_keys:
        if key not in response:
            raise XAIResponseValidationError(f"Missing required XAI response field: {key}")

    # Rule C: No unexpected keys
    extra_keys = set(response.keys()) - set(required_keys)
    if extra_keys:
        raise XAIResponseValidationError(
            f"Unexpected XAI response field(s): {', '.join(sorted(extra_keys))}"
        )

    # Rule D: All string fields are strings
    string_fields = [
        "overall_condition",
        "summary",
        "why_degraded",
        "affected_regions_explanation",
        "severity_explanation",
        "technical_interpretation",
        "limitations",
    ]
    for field in string_fields:
        if not isinstance(response[field], str):
            raise XAIResponseValidationError(
                f"XAI field '{field}' must be a string."
            )

    # Rule E: key_evidence must be a list
    if not isinstance(response["key_evidence"], list):
        raise XAIResponseValidationError("XAI field 'key_evidence' must be a list.")

    # Rule F & G: each item in key_evidence must be a string
    for idx, item in enumerate(response["key_evidence"]):
        if not isinstance(item, str):
            raise XAIResponseValidationError(
                f"Item {idx} in 'key_evidence' must be a string."
            )

    # All checks passed
    return True
