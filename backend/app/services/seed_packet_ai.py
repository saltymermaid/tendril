"""Seed packet photo AI extraction using Claude API."""

import base64
import json
import logging
from dataclasses import dataclass

import anthropic

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are analyzing a photo of a seed packet for a gardening application. 
Extract as much planting information as possible from the image.

Return a JSON object with ONLY the following fields (use null for any field you cannot determine):

{
  "name": "variety name (e.g., 'Cherokee Purple', 'Sugar Snap')",
  "days_to_germination_min": integer or null,
  "days_to_germination_max": integer or null,
  "days_to_harvest_min": integer or null,
  "days_to_harvest_max": integer or null,
  "planting_depth": "string like '1/4 inch' or '1/2 inch' or null",
  "spacing": "one of '1x1', '1x2', '2x2' based on plant spacing needs, or null",
  "sunlight": "one of 'full_sun', 'partial_shade', 'full_shade', or null",
  "is_climbing": true/false or null,
  "planting_method": "one of 'direct_sow', 'transplant', 'both', or null",
  "notes": "any additional useful info from the packet (growing tips, soil preferences, etc.)"
}

Rules for spacing interpretation:
- Plants needing 6" or less spacing → "1x1" (fits in one square foot)
- Plants needing 12-18" spacing → "1x2" (needs 2 square feet)
- Plants needing 24"+ spacing → "2x2" (needs 4 square feet)

If the packet shows a range for days (e.g., "65-80 days"), use the lower number for min and higher for max.
If only one number is given for days, use it for both min and max.

Return ONLY valid JSON, no markdown formatting or explanation."""


@dataclass
class ExtractionResult:
    """Result from seed packet AI extraction."""

    success: bool
    data: dict | None = None
    error: str | None = None


async def extract_seed_packet_data(
    image_base64: str,
    media_type: str,
    api_key: str,
) -> ExtractionResult:
    """Extract planting data from a seed packet photo using Claude API.

    Args:
        image_base64: Base64-encoded image data (no data: prefix)
        media_type: MIME type (e.g., 'image/jpeg', 'image/png')
        api_key: User's Claude API key

    Returns:
        ExtractionResult with extracted data or error message
    """
    try:
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
        )

        # Parse the response
        response_text = message.content[0].text.strip()

        # Try to extract JSON from the response (handle markdown code blocks)
        if response_text.startswith("```"):
            # Remove markdown code block
            lines = response_text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)

        data = json.loads(response_text)

        # Validate and clean the data
        cleaned = _clean_extraction(data)

        return ExtractionResult(success=True, data=cleaned)

    except anthropic.AuthenticationError:
        return ExtractionResult(
            success=False,
            error="Invalid Claude API key. Please check your API key in Settings.",
        )
    except anthropic.RateLimitError:
        return ExtractionResult(
            success=False,
            error="Claude API rate limit reached. Please try again in a moment.",
        )
    except anthropic.APIError as e:
        logger.error("Claude API error: %s", e)
        return ExtractionResult(
            success=False,
            error=f"Claude API error: {e.message}",
        )
    except json.JSONDecodeError:
        logger.error("Failed to parse Claude response as JSON: %s", response_text[:200])
        return ExtractionResult(
            success=False,
            error="Could not parse AI response. The photo may be unclear — try a clearer image.",
        )
    except Exception as e:
        logger.error("Unexpected error in seed packet extraction: %s", e)
        return ExtractionResult(
            success=False,
            error="An unexpected error occurred. Please try again.",
        )


def _clean_extraction(data: dict) -> dict:
    """Validate and clean extracted data to match our schema."""
    cleaned: dict = {}

    # String fields
    if data.get("name"):
        cleaned["name"] = str(data["name"]).strip()

    # Integer fields
    for field in [
        "days_to_germination_min",
        "days_to_germination_max",
        "days_to_harvest_min",
        "days_to_harvest_max",
    ]:
        val = data.get(field)
        if val is not None:
            try:
                cleaned[field] = int(val)
            except (ValueError, TypeError):
                pass

    # Planting depth
    if data.get("planting_depth"):
        cleaned["planting_depth"] = str(data["planting_depth"]).strip()

    # Spacing — validate against allowed values
    spacing = data.get("spacing")
    if spacing in ("1x1", "1x2", "2x2"):
        cleaned["spacing"] = spacing

    # Sunlight — validate
    sunlight = data.get("sunlight")
    if sunlight in ("full_sun", "partial_shade", "full_shade"):
        cleaned["sunlight"] = sunlight

    # Boolean
    if data.get("is_climbing") is not None:
        cleaned["is_climbing"] = bool(data["is_climbing"])

    # Planting method — validate
    method = data.get("planting_method")
    if method in ("direct_sow", "transplant", "both"):
        cleaned["planting_method"] = method

    # Notes
    if data.get("notes"):
        cleaned["notes"] = str(data["notes"]).strip()

    return cleaned
