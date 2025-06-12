# pipeline.py
import json
import os
import re
import datetime
from llm_access.llm_api import get_llm_response # Assuming this is the function to call the LLM

INPUT_DIR = "input"
OUTPUT_DIR = "output" # Base output directory

def sanitize_foldername(name):
    """Sanitizes a string to be used as a folder or file name."""
    name = str(name).strip().replace(' ', '_').replace(',', '')
    name = re.sub(r'(?u)[^-\w.]', '', name) # Keep alphanumeric, underscore, hyphen, dot
    return name if name else "unknown_item"

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
        " CRITICAL INSTRUCTIONS FOR ITINERARY FORMATTING: Please provide a detailed day-by-day plan. "
        "Each day MUST be structured into 'Morning', 'Afternoon', and 'Evening' segments.\n"
        "For EACH suggested Point of Interest (POI) or activity within these segments, you ABSOLUTELY MUST provide ALL of the following details. "
        "Format these details exactly as shown using Markdown, with each piece of information on a new line:\n"
        "**Name:** [Full Name of POI/Activity]\n"
        "**Description:** [A brief, concise description (1-2 sentences).]\n"
        "**Estimated Duration:** [e.g., 2 hours, 30 minutes, Half Day]\n"
        "**Cost Level:** [e.g., Free, $, $$, $$$ (provide a rough estimate if possible)]\n"
        "**Popularity Score:** [e.g., 90/100, High, Medium, Low - based on general perception]\n"
        "**Best Time to Visit:** [e.g., Early Morning, Late Afternoon, Evening, Any Time, Specific Season if applicable]\n"
        "**Family-Friendly:** [Yes/No/Depends (with brief explanation if 'Depends')]\n"
        "**Requires Pre-booking:** [Yes/No/Recommended]\n"
        "**Why this POI/Activity?:** [Briefly explain why this fits the user's interests/destination type, e.g., 'Great for history lovers', 'Offers stunning beach views'.]\n\n"
        "If a segment (Morning, Afternoon, Evening) includes multiple POIs or activities, list each one sequentially. "
        "Each POI/activity MUST have its own complete set of the details listed above. "
        "Separate distinct POIs/activities within the same segment using a Markdown horizontal rule (e.g., '---').\n\n"
        "At the end of EACH DAY'S plan (after listing all segments and their activities), please include:\n"
        "**Daily Meal Suggestions:** [Suggest 2-3 types of cuisine or specific restaurant recommendations suitable for the day's location/activities. Mention breakfast, lunch, and dinner if appropriate.]\n"
        "**Daily Logistical Tips:** [Include any relevant transportation advice, dress code notes, or other practical tips for the day.]\n"
        "Ensure the entire itinerary is coherent and flows logically from one activity/day to the next."
    )
    
    # 2. Call the LLM
    llm_response = get_llm_response(final_prompt)
    if not llm_response: # Basic check if LLM failed
        print("Error: Failed to get itinerary from LLM.")
        return None, None # Indicate failure

    # 3. Adapt LLM response (logic moved from app.py)
    adapted_itinerary = {
        "destination": llm_response.get("destination", destination_name), # Use LLM destination, fallback to input
        "from_date": from_date.strftime('%Y-%m-%d') if from_date and hasattr(from_date, 'strftime') else None,
        "to_date": to_date.strftime('%Y-%m-%d') if to_date and hasattr(to_date, 'strftime') else None,
        "duration": duration_days,
        "num_travellers": num_travellers,
        "details": llm_response.get("itinerary", []),
        "estimated_cost": llm_response.get("estimated_cost")
    }

    # 4. Save the generated itinerary with dynamic pathing
    try:
        # Use LLM-confirmed destination for folder structure
        llm_confirmed_destination_sanitized = sanitize_foldername(adapted_itinerary.get('destination', 'generated_trip'))
        
        from_date_str_path = from_date.strftime('%Y-%m-%d') if from_date and hasattr(from_date, 'strftime') else "nodate"
        to_date_str_path = to_date.strftime('%Y-%m-%d') if to_date and hasattr(to_date, 'strftime') else "nodate"
        date_folder_name = f"{from_date_str_path}_to_{to_date_str_path}"

        output_directory_path = os.path.join(OUTPUT_DIR, llm_confirmed_destination_sanitized, date_folder_name)
        os.makedirs(output_directory_path, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename_leaf = f"itinerary_{llm_confirmed_destination_sanitized}_{timestamp}.json"
        output_filepath = os.path.join(output_directory_path, output_filename_leaf)
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(adapted_itinerary, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved itinerary to {output_filepath}")
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
