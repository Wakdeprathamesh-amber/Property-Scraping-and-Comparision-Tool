"""
Parsers for converting text, markdown, and JSON into PropertyData structure
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.property_data import PropertyData, ExtractedContent, ImageData, LinkData, MetaData


def parse_json_to_property_data(data: Dict[str, Any]) -> PropertyData:
    """
    Parse JSON data to PropertyData, handling various JSON structures.
    Supports nested structures, API response formats, and field name variations.
    """
    # Handle nested data structures (e.g., {"message": "success", "data": {...}})
    if "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    
    # Handle array responses (take first item)
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    
    # Extract property name with various field name possibilities
    property_name = (
        data.get("property_name") or
        data.get("name") or
        data.get("title") or
        data.get("property") or
        data.get("propertyName") or
        "Unknown Property"
    )
    
    # Extract URL with various field name possibilities
    url = (
        data.get("url") or
        data.get("source_link") or
        data.get("link") or
        data.get("property_url") or
        data.get("website") or
        data.get("sourceUrl") or
        "https://example.com"
    )
    
    # Extract location (handle both string and dict)
    location = None
    location_data = (
        data.get("location") or
        data.get("address") or
        data.get("city") or
        data.get("area") or
        data.get("address_line_1")
    )
    
    if location_data:
        if isinstance(location_data, str):
            location = location_data
        elif isinstance(location_data, dict):
            # If location is a dict, build a formatted address string
            location_parts = []
            
            # Try common address fields in order of preference
            if location_data.get("name"):
                location_parts.append(str(location_data["name"]))
            if location_data.get("address"):
                location_parts.append(str(location_data["address"]))
            if location_data.get("street"):
                location_parts.append(str(location_data["street"]))
            if location_data.get("city"):
                location_parts.append(str(location_data["city"]))
            if location_data.get("state") or location_data.get("region"):
                location_parts.append(str(location_data.get("state") or location_data.get("region")))
            if location_data.get("country"):
                location_parts.append(str(location_data["country"]))
            if location_data.get("postal_code") or location_data.get("zip_code"):
                location_parts.append(str(location_data.get("postal_code") or location_data.get("zip_code")))
            
            # If we have parts, join them
            if location_parts:
                location = ", ".join(location_parts)
            elif location_data.get("formatted_address"):
                location = str(location_data["formatted_address"])
            elif location_data.get("display_name"):
                location = str(location_data["display_name"])
            elif location_data.get("label"):
                location = str(location_data["label"])
            # Last resort: use coordinates if available
            elif location_data.get("lat") and location_data.get("lng"):
                location = f"{location_data['lat']}, {location_data['lng']}"
            else:
                # If nothing works, try to stringify the dict (but this shouldn't happen)
                location = str(location_data)
        else:
            # For any other type, convert to string
            location = str(location_data) if location_data else None
    
    # Extract provider/source
    provider = (
        data.get("provider") or
        data.get("source") or
        data.get("host") or
        data.get("owner_name") or
        None
    )
    
    # Build text content from available fields
    text_parts = []
    
    # Add property name
    if property_name and property_name != "Unknown Property":
        text_parts.append(f"Property: {property_name}")
    
    # Add location
    if location:
        text_parts.append(f"Location: {location}")
    
    # Add description if available
    if data.get("description"):
        text_parts.append(f"\nDescription:\n{data['description']}")
    
    # Add about/overview
    if data.get("about"):
        text_parts.append(f"\nAbout:\n{data['about']}")
    if data.get("overview"):
        text_parts.append(f"\nOverview:\n{data['overview']}")
    
    # Add pricing information
    if data.get("pricing"):
        pricing = data["pricing"]
        if isinstance(pricing, dict):
            currency = pricing.get("currency", "")
            duration = pricing.get("duration", "")
            min_price = pricing.get("min_price") or pricing.get("minPrice")
            max_price = pricing.get("max_price") or pricing.get("maxPrice")
            if min_price or max_price:
                price_text = f"\nPricing:\n"
                if min_price:
                    price_text += f"From {currency} {min_price} {duration}\n"
                if max_price and max_price != min_price:
                    price_text += f"To {currency} {max_price} {duration}\n"
                text_parts.append(price_text)
    
    # Add amenities/features
    if data.get("amenities"):
        amenities = data["amenities"]
        if isinstance(amenities, list):
            text_parts.append(f"\nAmenities:\n" + "\n".join(f"- {a}" if isinstance(a, str) else f"- {a.get('name', a)}" for a in amenities))
    if data.get("features"):
        features = data["features"]
        if isinstance(features, list):
            text_parts.append(f"\nFeatures:\n" + "\n".join(f"- {f}" if isinstance(f, str) else f"- {f.get('name', f)}" for f in features))
    
    # Add room types
    if data.get("types"):
        types = data["types"]
        if isinstance(types, list):
            text_parts.append(f"\nRoom Types:\n" + "\n".join(f"- {t}" for t in types))
    if data.get("room_types"):
        room_types = data["room_types"]
        if isinstance(room_types, list):
            text_parts.append(f"\nRoom Types:\n" + "\n".join(f"- {rt.get('name', rt) if isinstance(rt, dict) else rt}" for rt in room_types))
    
    # Add meta/facts information
    if data.get("meta") and isinstance(data["meta"], dict):
        meta = data["meta"]
        if meta.get("facts") and isinstance(meta["facts"], list):
            text_parts.append("\nFacts:")
            for fact in meta["facts"]:
                if isinstance(fact, dict):
                    text_parts.append(f"- {fact.get('value', fact.get('name', fact))}")
        
        # Add other meta fields
        if meta.get("floor"):
            text_parts.append(f"\nFloor: {meta['floor']}")
        if meta.get("ranking"):
            text_parts.append(f"Ranking: {meta['ranking']}")
    
    # Add owner/contact information
    if data.get("owner") and isinstance(data["owner"], dict):
        owner = data["owner"]
        if owner.get("emails"):
            text_parts.append(f"\nContact Email: {', '.join(owner['emails'])}")
        if owner.get("phones"):
            text_parts.append(f"Contact Phone: {', '.join(owner['phones'])}")
    
    # Add policies/terms
    if data.get("policies"):
        policies = data["policies"]
        if isinstance(policies, list):
            text_parts.append("\nPolicies:")
            for policy in policies:
                text_parts.append(f"- {policy if isinstance(policy, str) else policy.get('name', policy)}")
    
    # Add all other string fields that might contain useful info
    for key, value in data.items():
        if key not in ["property_name", "name", "url", "source_link", "location", "address", 
                       "provider", "source", "description", "about", "overview", "pricing",
                       "amenities", "features", "types", "room_types", "meta", "owner", 
                       "policies", "images", "links", "videos", "extracted_content"]:
            if isinstance(value, str) and value and len(value) < 500:
                text_parts.append(f"\n{key.replace('_', ' ').title()}: {value}")
    
    # Combine all text
    full_text = "\n".join(text_parts) if text_parts else json.dumps(data, indent=2)
    
    # Extract images
    images = []
    if data.get("images"):
        img_list = data["images"] if isinstance(data["images"], list) else []
        for img in img_list:
            if isinstance(img, str):
                images.append(ImageData(url=img))
            elif isinstance(img, dict):
                images.append(ImageData(
                    url=img.get("url") or img.get("src") or img.get("image_url", ""),
                    alt=img.get("alt") or img.get("title"),
                    title=img.get("title")
                ))
    
    # Extract links
    links = []
    if data.get("links"):
        link_list = data["links"] if isinstance(data["links"], list) else []
        for link in link_list:
            if isinstance(link, str):
                links.append(LinkData(url=link))
            elif isinstance(link, dict):
                links.append(LinkData(
                    url=link.get("url") or link.get("href", ""),
                    text=link.get("text") or link.get("title"),
                    type=link.get("type")
                ))
    
    # Extract meta tags
    meta_tags = None
    if data.get("meta_tags") or data.get("meta"):
        meta_data = data.get("meta_tags") or data.get("meta", {})
        if isinstance(meta_data, dict):
            meta_tags = MetaData(
                title=meta_data.get("title") or property_name,
                description=meta_data.get("description") or (full_text[:200] + "..." if len(full_text) > 200 else full_text),
                keywords=meta_data.get("keywords") if isinstance(meta_data.get("keywords"), list) else None,
                og_tags=meta_data.get("og_tags") if isinstance(meta_data.get("og_tags"), dict) else None
            )
    
    # Create ExtractedContent
    extracted_content = ExtractedContent(
        text=full_text,
        images=images[:20],
        links=links[:50],
        meta_tags=meta_tags or MetaData(
            title=property_name,
            description=full_text[:200] + "..." if len(full_text) > 200 else full_text
        )
    )
    
    # Final safety check: ensure location is a string (not dict or other type)
    if location is not None and not isinstance(location, str):
        if isinstance(location, dict):
            # Convert dict to string (shouldn't happen if above logic worked, but safety check)
            location_parts = []
            if location.get("name"):
                location_parts.append(str(location["name"]))
            if location.get("address"):
                location_parts.append(str(location["address"]))
            if location.get("city"):
                location_parts.append(str(location["city"]))
            if location.get("country"):
                location_parts.append(str(location["country"]))
            location = ", ".join(location_parts) if location_parts else None
        else:
            location = str(location) if location else None
    
    # Build PropertyData
    property_data = PropertyData(
        property_name=property_name,
        provider=provider,
        url=url,
        location=location,  # Guaranteed to be str or None
        extracted_content=extracted_content,
        additional_metadata={
            k: v for k, v in data.items() 
            if k not in ["property_name", "name", "url", "source_link", "location", 
                        "provider", "source", "extracted_content"]
        }
    )
    
    return property_data


def parse_text_to_property_data(text: str, default_url: str = "https://example.com") -> PropertyData:
    """
    Parse plain text into PropertyData structure.
    VERY PERMISSIVE - accepts any text and extracts what it can.
    """
    lines = text.split('\n')
    
    # Extract property name (try multiple strategies)
    property_name = "Unknown Property"
    
    # Strategy 1: Look for explicit patterns
    for line in lines[:20]:  # Check first 20 lines
        # Look for patterns like "Property Name: X" or "Name: X"
        match = re.search(r'(?:property\s*name|name|title)[\s:]+([^\n]+)', line, re.IGNORECASE)
        if match:
            name_candidate = match.group(1).strip()
            if len(name_candidate) > 3 and len(name_candidate) < 100:
                property_name = name_candidate
                break
    
    # Strategy 2: Use first non-empty line if still unknown
    if property_name == "Unknown Property":
        for line in lines[:5]:
            clean_line = line.strip()
            if clean_line and len(clean_line) > 3 and len(clean_line) < 100:
                # Skip lines that look like URLs, dates, or generic words
                if not clean_line.startswith(('http', 'www', 'Location', 'URL', 'Description')):
                    property_name = clean_line
                    break
    
    # Strategy 3: Try to find property names from common patterns
    if property_name == "Unknown Property":
        # Look for property-like names (capitals, specific words)
        for line in lines[:30]:
            match = re.search(r'([A-Z][a-zA-Z\s&]+(?:Court|House|Hall|Residence|Accommodation|Property|Living|Student|Apartments?))', line)
            if match:
                property_name = match.group(1).strip()
                break
    
    # Extract URL
    url = default_url
    url_pattern = r'https?://[^\s\n]+|www\.[^\s\n]+'
    for line in lines:
        match = re.search(url_pattern, line, re.IGNORECASE)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            break
    
    # Extract location
    location = None
    for line in lines:
        match = re.search(r'(?:location|address|city)[\s:]+([^\n]+)', line, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            break
    
    # Extract provider if mentioned
    provider = None
    for line in lines:
        match = re.search(r'(?:provider|by|hosted by)[\s:]+([^\n]+)', line, re.IGNORECASE)
        if match:
            provider = match.group(1).strip()
            break
    
    # Clean up text (remove empty lines, normalize whitespace)
    clean_text = '\n'.join(line.strip() for line in lines if line.strip())
    
    # Extract images (look for image URLs or image references)
    images = []
    image_pattern = r'(?:image|photo|img)[\s:]+([^\s\n]+\.(?:jpg|jpeg|png|gif|webp))'
    for match in re.finditer(image_pattern, clean_text, re.IGNORECASE):
        images.append(ImageData(url=match.group(1)))
    
    # Extract links (look for URLs)
    links = []
    link_pattern = r'(https?://[^\s\n\)]+)'
    for match in re.finditer(link_pattern, clean_text):
        url_found = match.group(0)
        if url_found != url:  # Don't include the main property URL
            links.append(LinkData(url=url_found))
    
    # Create ExtractedContent
    extracted_content = ExtractedContent(
        text=clean_text,
        images=images[:20],  # Limit to 20 images
        links=links[:50],    # Limit to 50 links
        meta_tags=MetaData(
            title=f"{property_name} | Property Details",
            description=clean_text[:200] + "..." if len(clean_text) > 200 else clean_text
        )
    )
    
    return PropertyData(
        property_name=property_name,
        provider=provider,
        url=url,
        location=location,
        extracted_content=extracted_content
    )


def parse_markdown_to_property_data(markdown: str, default_url: str = "https://example.com") -> PropertyData:
    """
    Parse Markdown into PropertyData structure.
    Extracts headings, links, images, and structured content.
    Handles HTML content, Markdown syntax, and mixed formats.
    """
    lines = markdown.split('\n')
    
    # Extract property name from first H1 or H2, or from bold text, or from image alt text
    property_name = "Unknown Property"
    
    # Try H1 first
    for line in lines[:50]:
        h1_match = re.match(r'^#\s+(.+?)(?:\s*\{|$)', line)
        if h1_match:
            property_name = h1_match.group(1).strip()
            # Clean up any markdown formatting
            property_name = re.sub(r'\*\*([^*]+)\*\*', r'\1', property_name)
            property_name = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', property_name)
            break
    
    # If not found, try H2
    if property_name == "Unknown Property":
        for line in lines[:50]:
            h2_match = re.match(r'^##\s+(.+?)(?:\s*\{|$)', line)
            if h2_match:
                property_name = h2_match.group(1).strip()
                property_name = re.sub(r'\*\*([^*]+)\*\*', r'\1', property_name)
                property_name = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', property_name)
                break
    
    # If still not found, try to find from image alt text (common in scraped content)
    if property_name == "Unknown Property":
        img_alt_match = re.search(r'!\[([^\]]+)\]', markdown)
        if img_alt_match:
            alt_text = img_alt_match.group(1).strip()
            # Use alt text if it looks like a property name
            if len(alt_text) > 5 and len(alt_text) < 100:
                property_name = alt_text
    
    # Try to find property name from common patterns
    if property_name == "Unknown Property":
        # Look for patterns like "iQ Sterling Court" or similar
        name_patterns = [
            r'([A-Z][a-zA-Z\s]+(?:Court|House|Hall|Residence|Accommodation|Property))',
            r'([A-Z][a-zA-Z\s]+\s+(?:Court|House|Hall|Residence))',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, markdown[:1000])
            if match:
                property_name = match.group(1).strip()
                break
    
    # Extract URL from markdown links, HTML links, or plain URLs
    url = default_url
    url_candidates = []
    
    # First pass: collect all URLs with priority scores
    url_patterns = [
        (r'href=["\']([^"\']+)["\']', 3),              # HTML href (highest priority)
        (r'\[([^\]]+)\]\(([^\)]+)\)', 2),              # Markdown link
        (r'https?://[^\s\n\)"\'<>]+', 1),              # Plain URL
        (r'www\.[^\s\n\)"\'<>]+', 0),                  # www. URL
    ]
    
    skip_keywords = ['logo', 'icon', 'cdn', 'facebook', 'twitter', 'instagram', 'linkedin', 
                     'youtube', 'pinterest', 'svg', 'png', 'jpg', 'jpeg', 'webp', 'gif',
                     'favicon', 'apple-touch', 'stylesheet', 'script', 'font', 'assets', 'files']
    
    prefer_keywords = ['property', 'accommodation', 'student', 'booking', 'sterling', 'iq',
                       'universityliving.com', 'amberstudent.com', 'unilodgers.com', 
                       'student.com', 'casita.com']
    
    for line in lines:
        for pattern, base_priority in url_patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                if match.lastindex:
                    potential_url = match.group(match.lastindex)
                else:
                    potential_url = match.group(0)
                
                # Clean URL
                potential_url = potential_url.strip('()[]"\'').split('?')[0].split('#')[0]
                if not potential_url.startswith('http'):
                    if potential_url.startswith('www.'):
                        potential_url = 'https://' + potential_url
                    elif '://' not in potential_url:
                        continue  # Skip relative URLs
                
                # Skip obviously non-property URLs
                url_lower = potential_url.lower()
                if any(skip in url_lower for skip in skip_keywords):
                    continue
                
                # Calculate priority score
                priority = base_priority
                if any(pref in url_lower for pref in prefer_keywords):
                    priority += 10
                if '/property' in url_lower or '/accommodation' in url_lower:
                    priority += 5
                if any(ext in url_lower for ext in ['.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico']):
                    priority -= 10  # Heavy penalty for image URLs
                if 'cdn' in url_lower or 'assets' in url_lower or 'files' in url_lower:
                    priority -= 8  # Penalty for CDN/assets
                
                url_candidates.append((potential_url, priority))
    
    # Sort by priority and take the best one
    if url_candidates:
        url_candidates.sort(key=lambda x: x[1], reverse=True)
        url = url_candidates[0][0]
    
    # Fallback: try to find any property-related URL in the main domain
    if url == default_url or any(skip in url.lower() for skip in ['svg', 'png', 'jpg', 'jpeg', 'gif', 'cdn', 'files']):
        for line in lines[:200]:
            # Look for URLs in breadcrumbs or navigation that are actual pages
            breadcrumb_match = re.search(r'(https?://[^\s\n\)"\'<>]+(?:property|accommodation|student|booking|universityliving|amberstudent)[^\s\n\)"\'<>]*)', line, re.IGNORECASE)
            if breadcrumb_match:
                candidate = breadcrumb_match.group(1)
                if not any(ext in candidate.lower() for ext in ['.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    url = candidate
                    break
    
    # Extract location from markdown structure
    location = None
    for i, line in enumerate(lines):
        if re.search(r'^###?\s+(?:location|address|city)', line, re.IGNORECASE):
            if i + 1 < len(lines):
                location = lines[i + 1].strip()
                break
    
    # Extract provider
    provider = None
    for i, line in enumerate(lines):
        if re.search(r'^###?\s+(?:provider|by)', line, re.IGNORECASE):
            if i + 1 < len(lines):
                provider = lines[i + 1].strip()
                break
    
    # Extract images from markdown
    images = []
    image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    for match in re.finditer(image_pattern, markdown):
        alt_text = match.group(1)
        image_url = match.group(2)
        images.append(ImageData(url=image_url, alt=alt_text if alt_text else None))
    
    # Extract links from markdown
    links = []
    link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    for match in re.finditer(link_pattern, markdown):
        link_text = match.group(1)
        link_url = match.group(2)
        if not link_url.startswith('#'):  # Skip anchor links
            links.append(LinkData(url=link_url, text=link_text))
    
    # Extract meta information
    title = property_name
    description = None
    
    # Look for description section
    for i, line in enumerate(lines):
        if re.search(r'^###?\s+(?:description|about|overview)', line, re.IGNORECASE):
            desc_lines = []
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip() and not lines[j].startswith('#'):
                    desc_lines.append(lines[j].strip())
            if desc_lines:
                description = ' '.join(desc_lines)
            break
    
    # Clean markdown text (remove markdown syntax for plain text version)
    clean_text = markdown
    # Remove image syntax
    clean_text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', clean_text)
    # Remove link syntax, keep text
    clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_text)
    # Remove headers
    clean_text = re.sub(r'^#+\s+', '', clean_text, flags=re.MULTILINE)
    # Remove bold/italic
    clean_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean_text)
    clean_text = re.sub(r'\*([^\*]+)\*', r'\1', clean_text)
    
    # Create ExtractedContent
    extracted_content = ExtractedContent(
        text=clean_text,
        images=images[:20],
        links=links[:50],
        meta_tags=MetaData(
            title=title,
            description=description or (clean_text[:200] + "..." if len(clean_text) > 200 else clean_text)
        )
    )
    
    return PropertyData(
        property_name=property_name,
        provider=provider,
        url=url,
        location=location,
        extracted_content=extracted_content
    )


def parse_input_to_property_data(
    data: Any,
    input_format: str = 'auto',
    default_url: str = "https://example.com"
) -> PropertyData:
    """
    Main parser function that handles different input formats.
    
    Args:
        data: Can be a dict (JSON), str (text/markdown), or already PropertyData
        input_format: 'json', 'text', 'markdown', or 'auto'
        default_url: Default URL if not found in input
    
    Returns:
        PropertyData object
    """
    # If already PropertyData, return as is
    if isinstance(data, PropertyData):
        return data
    
    # If dict, assume JSON
    if isinstance(data, dict):
        return parse_json_to_property_data(data)
    
    # If string, parse based on format
    if isinstance(data, str):
        text = data.strip()
        
        # Auto-detect format if needed
        if input_format == 'auto':
            # Try JSON first
            if text.startswith('{') or text.startswith('['):
                try:
                    json_data = json.loads(text)
                    return parse_json_to_property_data(json_data)
                except json.JSONDecodeError as e:
                    # If JSON parsing fails, try to handle partial JSON
                    # Look for JSON-like structure even if not perfect
                    pass
            
            # Check for markdown patterns
            if re.search(r'^#+\s+', text, re.MULTILINE) or re.search(r'\[([^\]]+)\]\(', text):
                return parse_markdown_to_property_data(text, default_url)
            
            # Default to text
            return parse_text_to_property_data(text, default_url)
        
        # Explicit format specified
        if input_format == 'json':
            try:
                json_data = json.loads(text)
                return parse_json_to_property_data(json_data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")
        elif input_format == 'markdown':
            return parse_markdown_to_property_data(text, default_url)
        else:  # text
            return parse_text_to_property_data(text, default_url)
    
    raise ValueError(f"Unsupported input type: {type(data)}")

