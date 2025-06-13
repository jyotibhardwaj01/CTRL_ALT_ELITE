# generate_world_cities.py
import json
import os
# Ensure you are in the root directory of your project when running this,
# or adjust sys.path if llm_access is not found.
try:
    from llm_access.llm_api import get_llm_response
except ImportError:
    print("Error: Could not import get_llm_response from llm_access.llm_api.")
    print("Please ensure you are running this script from the project root directory,")
    print("and that llm_access/__init__.py exists and llm_api.py is correctly placed.")
    exit(1)

OUTPUT_FILE_PATH = os.path.join("input", "world_cities.json")

def generate_and_save_world_cities():
    """
    Generates a comprehensive list of world tourist cities using an LLM
    and saves it to input/world_cities.json.
    """
    print(f"Attempting to generate a comprehensive list of world tourist cities and save to {OUTPUT_FILE_PATH}...")
    
    prompt = (
        "Generate a comprehensive list of at least 500 globally famous tourist cities. "
        "The list should include a diverse range of cities from all continents. "
        "Format the response as a single JSON object with one key: 'cities'. "
        "The value of 'cities' should be a JSON list of strings. "
        "Each string in the list must be in the format 'City Name, Country Name'. "
        "Example: {\"cities\": [\"Paris, France\", \"Tokyo, Japan\", \"Rome, Italy\", ..., \"Cairo, Egypt\"]}"
    )
    
    try:
        response_data = get_llm_response(prompt) # Expects a dictionary
        
        if response_data and isinstance(response_data, dict) and "cities" in response_data and isinstance(response_data["cities"], list):
            cities_list = [str(city) for city in response_data["cities"] if isinstance(city, str)]
            
            if cities_list:
                # Ensure uniqueness and sort
                unique_sorted_cities = sorted(list(set(cities_list)))
                
                # Create the input directory if it doesn't exist (though it should)
                os.makedirs(os.path.dirname(OUTPUT_FILE_PATH), exist_ok=True)
                
                with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
                    json.dump({"cities": unique_sorted_cities}, f, indent=4, ensure_ascii=False)
                
                print(f"Successfully generated and saved {len(unique_sorted_cities)} cities to {OUTPUT_FILE_PATH}")
                print("The application will now attempt to use this file for destination suggestions.")
            else:
                print("Error: LLM returned a 'cities' list, but it was empty or contained no valid city strings.")
        else:
            print("Error: Could not parse city list from LLM response or response format was incorrect.")
            print(f"LLM Response (partial for debugging): {str(response_data)[:500]}")
            
    except Exception as e:
        print(f"An error occurred during LLM call or file processing: {e}")

if __name__ == "__main__":
    # Ensure llm_access/__init__.py exists for package recognition if running as script
    # This is a good practice for modules.
    llm_access_dir = "llm_access"
    llm_access_init_path = os.path.join(llm_access_dir, "__init__.py")
    if not os.path.exists(llm_access_init_path):
        if not os.path.exists(llm_access_dir):
            os.makedirs(llm_access_dir, exist_ok=True)
        try:
            with open(llm_access_init_path, 'w') as f:
                pass # Create an empty __init__.py
            print(f"Ensured {llm_access_init_path} exists for package recognition.")
        except IOError as e:
            print(f"Warning: Could not create {llm_access_init_path}: {e}. Imports might fail.")
            
    generate_and_save_world_cities()
