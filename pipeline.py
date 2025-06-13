# pipeline.py
import json
import os
import re
import datetime
import requests # For downloading images
import uuid # For unique filenames
from urllib.parse import urlparse # To get file extension
from llm_access.llm_api import get_llm_response # Assuming this is the function to call the LLM

INPUT_DIR = "input"
OUTPUT_DIR = "Output" # Base output directory, changed to capital 'O'
IMAGES_SUBDIR = "images" # Subdirectory for storing downloaded images

def sanitize_foldername(name):
    """Sanitizes a string to be used as a folder or file name."""
    name = str(name).strip().replace(' ', '_').replace(',', '')
    name = re.sub(r'(?u)[^-\w.]', '', name) # Keep alphanumeric, underscore, hyphen, dot
    return name[:100] if name else "unknown_item" # Limit length

def get_llm_placeholder_image_url(description_for_image):
    """
    Asks the LLM for a generic, royalty-free, publicly accessible image URL
    based on the provided description.
    Returns a URL string or None.
    """
    prompt = (
        f"Please provide a single, publicly accessible, royalty-free image URL that best represents the following: '{description_for_image}'. "
        "The image should be suitable as a general placeholder. "
        "Respond with ONLY the URL itself, no other text or explanation. "
        "Example: https://images.unsplash.com/photo-12345. If no suitable royalty-free image can be found, respond with an empty string."
    )
    try:
        response = get_llm_response(prompt) # Assuming get_llm_response can handle direct string if LLM returns just URL
        if isinstance(response, str) and response.strip().startswith(('http://', 'https://')):
            print(f"LLM provided placeholder image URL: {response.strip()}")
            return response.strip()
        # If LLM response is a dict (as it was for other calls)
        elif isinstance(response, dict) and "image_url" in response and isinstance(response["image_url"], str) and response["image_url"].strip().startswith(('http://', 'https://')):
            print(f"LLM provided placeholder image URL: {response['image_url'].strip()}")
            return response["image_url"].strip()
        elif isinstance(response, dict) and "url" in response and isinstance(response["url"], str) and response["url"].strip().startswith(('http://', 'https://')): # another common key
            print(f"LLM provided placeholder image URL: {response['url'].strip()}")
            return response["url"].strip()
        else:
            print(f"LLM did not provide a valid placeholder URL for '{description_for_image}'. Response: {str(response)[:200]}")
            return None
    except Exception as e:
        print(f"Error fetching placeholder image URL from LLM for '{description_for_image}': {e}")
        return None

def download_image(image_url, destination_folder, base_filename):
    """
    Downloads an image from a URL and saves it locally.
    Returns the local path if successful, else None.
    """
    if not image_url or not isinstance(image_url, str) or not image_url.strip().startswith(('http://', 'https://')):
        return None
    
    try:
        # Attempt with verification first
        try:
            response = requests.get(image_url, stream=True, timeout=10, verify=True)
            response.raise_for_status()
        except requests.exceptions.SSLError as ssl_err:
            print(f"SSL verification failed for {image_url}: {ssl_err}. Attempting with verify=False (SECURITY WARNING).")
            print("WARNING: Disabling SSL verification. This is insecure and should ONLY be used in controlled development environments if you understand the risks.")
            response = requests.get(image_url, stream=True, timeout=10, verify=False)
            response.raise_for_status() # Raise an exception for bad status codes even with verify=False

        # Try to get a file extension
        parsed_url = urlparse(image_url)
        path_parts = os.path.splitext(parsed_url.path)
        ext = path_parts[1] if len(path_parts) > 1 and path_parts[1] else '.jpg' # Default to .jpg
        
        # Sanitize base_filename further if needed, and add UUID to ensure uniqueness
        filename = f"{sanitize_foldername(base_filename)}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(destination_folder, filename)
        
        os.makedirs(destination_folder, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded image to {filepath}")
        return filepath
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {image_url}: {e}")
        return None
    except IOError as e:
        print(f"Failed to save image from {image_url} to {filepath}: {e}")
        return None

def create_travel_itinerary(preferences):
    """
    Generates a travel itinerary based on preferences, calls LLM,
    adapts the response, and saves it to a structured output path.
    Returns the itinerary data and the path where it was saved.
    """
    # 1. Construct the prompt for the LLM (logic moved from app.py)
    prompt_parts = []
    destination_name = preferences.get('destination', 'a nice place')
    from_date = preferences.get('from_date') # Expected to be datetime.date object
    to_date = preferences.get('to_date')     # Expected to be datetime.date object
    num_travellers = preferences.get('num_travellers', 1)
    interests = preferences.get("interests")
    budget = preferences.get("budget")
    additional_prefs = preferences.get("additional_prefs")

    prompt_parts.append("You are an AI travel planner. A user has provided the following details for their trip:")
    prompt_parts.append(f"- Destination: {destination_name}")

    if from_date and to_date:
        duration_days = (to_date - from_date).days + 1
        prompt_parts.append(f"- Dates: From {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')} ({duration_days} days)")
    else:
        duration_days = preferences.get('duration', 7) # Fallback if dates are not proper objects
        prompt_parts.append(f"- Destination: {destination_name}")
        prompt_parts.append(f"- Duration: {duration_days} days (dates not specified or invalid)")
        
    prompt_parts.append(f"- Number of Travellers: {num_travellers}")

    if interests:
        prompt_parts.append(f"- Interests: {', '.join(interests)}")
    if budget:
        prompt_parts.append(f"- Budget: {budget}")
    if additional_prefs:
        prompt_parts.append(f"- Additional Preferences: {additional_prefs}")
    
    prompt_parts.append("Based STRICTLY on these user-provided details, generate a detailed day-by-day travel itinerary.")

    destination_lower = str(destination_name).lower()
    interests_lower = [str(i).lower() for i in interests if isinstance(i, str)] if interests else []

    is_beach_trip = "beach" in destination_lower or \
                    ("beach" in interests_lower) or \
                    ("sea" in interests_lower)
    is_mountain_trip = "mountain" in destination_lower or \
                       ("mountain" in interests_lower) or \
                       ("hiking" in interests_lower)

    if is_beach_trip and duration_days == 7:
        if "beach" not in destination_lower:
             prompt_parts.append("Focus on beach activities.")
    elif is_mountain_trip:
        if "mountain" not in destination_lower:
            prompt_parts.append("Focus on mountain activities.")

    final_prompt = " ".join(prompt_parts)
    final_prompt += (
        " IMPORTANT: Respond *only* with a single, valid JSON object. Do not include any text or explanation before or after the JSON. "
        "The JSON object must have the following top-level keys: "
        "1. 'destination': A string with the name of the destination (e.g., \"Paris, France\"). "
        "2. 'itinerary': A list of objects. Each object represents a single day's plan and *must* have the following keys: "
        "   a. 'day': (integer) The day number (e.g., 1). "
        "   b. 'day_summary': (string) A brief overall summary for the day's theme or main focus. "
        # "   c. 'image_url': (string) A publicly accessible, royalty-free (if possible) direct URL to a general image representing the day. Use an empty string if no suitable image is found. " # REMOVED
        "   c. 'activities': (list of objects) Each object in this list represents a specific POI or activity for the day and *must* include: " # Note: 'c' was 'd'
        "      i. 'name': (string) Name of the POI or activity (e.g., \"Eiffel Tower Visit\"). "
        "      ii. 'time_of_day': (string) Suggested time (e.g., \"Morning\", \"9:00 AM - 12:00 PM\", \"Afternoon\"). "
        "      iii. 'description': (string) A detailed description of the POI/activity. "
        "      iv. 'why_relevant': (string) Reason why this POI/activity is included or interesting. "
        "      v. 'estimated_duration': (string) Estimated time to spend (e.g., \"2-3 hours\"). "
        "      vi. 'estimated_cost': (string) Estimated cost (e.g., \"€25 per person\", \"Free\", \"$$ - Moderate\"). "
        "      vii. 'poi_image_url': (string, optional) A direct URL to an image specific to this POI/activity. Use an empty string if not available. "
        "   e. 'daily_meal_suggestions': (object) An object with keys 'breakfast', 'lunch', and 'dinner'. Each key should have a string value with a suggestion for that meal. If a meal suggestion isn't applicable or available, use an empty string for its value. Example: {\"breakfast\": \"Hotel breakfast or local bakery.\", \"lunch\": \"Cafe near museum.\", \"dinner\": \"Traditional restaurant for pasta.\"} "
        "   f. 'daily_logistical_tips': (string) Any logistical tips for the day (e.g., \"Book museum tickets online. Wear comfortable shoes.\"). "
        "3. 'estimated_cost': A string describing the overall estimated cost for the trip *excluding meals* (e.g., for accommodation, activities, local transport: \"$1000 - $1500 for 2 people\"). "
        "4. 'estimated_daily_meal_cost_per_person': A string representing a typical daily cost for three meals per person (e.g., \"$50-70 USD\", \"€40-60 EUR\"). This should align with the user's budget preference. "
        "Example of a day object within the 'itinerary' list: "
        "{\"day\": 1, \"day_summary\": \"Exploring iconic Parisian landmarks.\", "
        " \"activities\": [{\"name\": \"Eiffel Tower\", \"time_of_day\": \"Morning\", \"description\": \"Visit the iconic tower.\", \"why_relevant\": \"Symbol of Paris.\", \"estimated_duration\": \"2-3 hours\", \"estimated_cost\": \"€25\", \"poi_image_url\": \"https://example.com/eiffel.jpg\"}], "
        " \"daily_meal_suggestions\": {\"breakfast\": \"Croissants and coffee.\", \"lunch\": \"Crepes from a street vendor.\", \"dinner\": \"Romantic bistro meal.\"}, \"daily_logistical_tips\": \"Book Eiffel Tower tickets online to avoid queues.\"} "
        "The number of day objects in the 'itinerary' list should match the trip duration."
    )
    
    # 2. Call the LLM
    llm_response = get_llm_response(final_prompt)
    if not llm_response: # Basic check if LLM failed
        print("Error: Failed to get itinerary from LLM.")
        return None, None # Indicate failure

    # 3. Adapt LLM response (logic moved from app.py)
    # Initialize adapted_itinerary with basic structure
    adapted_itinerary = {
        "destination": llm_response.get("destination", destination_name),
        "from_date": from_date.strftime('%Y-%m-%d') if from_date and hasattr(from_date, 'strftime') else None,
        "to_date": to_date.strftime('%Y-%m-%d') if to_date and hasattr(to_date, 'strftime') else None,
        "duration": duration_days,
        "num_travellers": num_travellers,
        "details": [], # Will be populated after image processing
        "estimated_cost": llm_response.get("estimated_cost"), # This is now ex-meals
        "estimated_daily_meal_cost_per_person": llm_response.get("estimated_daily_meal_cost_per_person") # New field
    }
    
    # Calculate total meal cost if possible
    total_estimated_meal_cost_str = None
    daily_meal_cost_str = adapted_itinerary.get("estimated_daily_meal_cost_per_person")
    if daily_meal_cost_str and isinstance(daily_meal_cost_str, str):
        # Try to extract a numerical average from strings like "$50-70 USD" or "€40"
        cost_numbers = re.findall(r'\d+\.?\d*', daily_meal_cost_str)
        if cost_numbers:
            avg_daily_cost_person = sum(float(c) for c in cost_numbers) / len(cost_numbers)
            total_meal_cost = avg_daily_cost_person * duration_days * num_travellers
            # Try to keep currency symbol if present
            currency_symbol_match = re.search(r'([$€£¥₹])', daily_meal_cost_str) # Add more symbols as needed
            currency_symbol = currency_symbol_match.group(1) if currency_symbol_match else ""
            total_estimated_meal_cost_str = f"{currency_symbol}{total_meal_cost:.2f} for {num_travellers} person(s) over {duration_days} day(s)"
            adapted_itinerary["total_estimated_meal_cost"] = total_estimated_meal_cost_str
            print(f"Calculated total meal cost: {total_estimated_meal_cost_str}")
        else:
            # If no numbers found, but string exists, store it as is for display
            adapted_itinerary["total_estimated_meal_cost"] = f"Approx. {daily_meal_cost_str} per person/day (total for {num_travellers} over {duration_days} days not auto-calculated)"


    # Create images directory
    images_dir_path = os.path.join(OUTPUT_DIR, IMAGES_SUBDIR)
    os.makedirs(images_dir_path, exist_ok=True)

    raw_itinerary_details = llm_response.get("itinerary", [])
    processed_details = []

    for day_plan_raw in raw_itinerary_details:
        day_plan_processed = day_plan_raw.copy() # Start with a copy
        
        # Ensure 'image_url' for the day is not processed or added if it's not in the raw LLM response
        if "image_url" in day_plan_processed:
            del day_plan_processed["image_url"] # Remove it if LLM somehow still provides it

        processed_activities = []
        if "activities" in day_plan_raw and isinstance(day_plan_raw["activities"], list):
            for activity_raw in day_plan_raw["activities"]:
                activity_processed = activity_raw.copy()
                poi_image_url_original = activity_raw.get("poi_image_url")
                local_poi_image_path_activity = None
                activity_name_sanitized = sanitize_foldername(activity_raw.get("name", "poi"))
                poi_image_filename_base_activity = f"{adapted_itinerary['destination']}_day_{day_plan_raw.get('day', 'unknown')}_{activity_name_sanitized}"

                if poi_image_url_original:
                    local_poi_image_path_activity = download_image(poi_image_url_original, images_dir_path, poi_image_filename_base_activity)

                if not local_poi_image_path_activity: # If original POI URL failed or was empty, try placeholder
                    print(f"Attempting to get placeholder for POI image: {activity_raw.get('name', 'Activity')} in {adapted_itinerary['destination']}")
                    placeholder_desc_poi = f"an image representing {activity_raw.get('name', 'an activity')} in {adapted_itinerary['destination']}"
                    placeholder_poi_url = get_llm_placeholder_image_url(placeholder_desc_poi)
                    if placeholder_poi_url:
                        local_poi_image_path_activity = download_image(placeholder_poi_url, images_dir_path, f"{poi_image_filename_base_activity}_placeholder")
                
                activity_processed["poi_image_url"] = local_poi_image_path_activity if local_poi_image_path_activity else ""
                processed_activities.append(activity_processed)
        day_plan_processed["activities"] = processed_activities
        processed_details.append(day_plan_processed)
    
    adapted_itinerary["details"] = processed_details

    # 4. Save the generated itinerary (with local image paths)
    try:
        output_filename_leaf = "Generated_Output.json"
        output_filepath = os.path.join(OUTPUT_DIR, output_filename_leaf)
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(adapted_itinerary, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved itinerary with local image paths to {output_filepath}")
        return adapted_itinerary, output_filepath
        
    except Exception as e:
        print(f"Error saving itinerary: {e}")
        return adapted_itinerary, None # Return data even if save fails, but no path

# Example of how this pipeline might be run from a script (optional, for testing)
def main_cli():
    print("Starting travel itinerary generation pipeline (CLI example)...")
    
    # Example preferences (normally these would come from app.py or a config file)
    sample_preferences = {
        "destination": "Paris, France",
        "from_date": datetime.date(2025, 7, 10),
        "to_date": datetime.date(2025, 7, 16),
        "num_travellers": 2,
        "interests": ["Museums", "Eiffel Tower", "Food"],
        "budget": "Mid-Range",
        "additional_prefs": "Looking for romantic spots."
    }
    
    itinerary_data, saved_path = create_travel_itinerary(sample_preferences)
    
    if itinerary_data and saved_path:
        print(f"\nGenerated Itinerary Data:\n{json.dumps(itinerary_data, indent=2)}\n")
        print(f"Itinerary saved to: {saved_path}")
    elif itinerary_data:
        print("\nGenerated Itinerary Data (but failed to save):\n{json.dumps(itinerary_data, indent=2)}\n")
    else:
        print("Failed to generate itinerary.")
        
    print("\nTravel itinerary generation pipeline (CLI example) finished.")

if __name__ == "__main__":
    # Ensure llm_access/__init__.py exists so it's treated as a package
    # This might be better handled in project setup rather than runtime.
    llm_access_init_path = os.path.join("llm_access", "__init__.py")
    if not os.path.exists(llm_access_init_path):
        try:
            with open(llm_access_init_path, 'w') as f:
                pass 
            print(f"Created {llm_access_init_path} for package recognition.")
        except IOError:
            print(f"Warning: Could not create {llm_access_init_path}")
            
    # main_cli() # Uncomment to run the CLI example
    pass # Keep __main__ block minimal if pipeline.py is mainly a library
