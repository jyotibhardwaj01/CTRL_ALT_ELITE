# llm_access/llm_api.py
import openai
from openai import AzureOpenAI
import requests
import json
import os # For potential future use with environment variables

# --- Azure OpenAI Configuration ---
# User inputs (as provided in the example)
# For production, these should ideally be environment variables or come from a secure config
WORKSPACE_ID = "RittikaPlaygneUd"
MODEL_NAME = "gpt-4o"
ASSET_ID = "204383"

# URLs
TOKEN_URL = "https://aiplatform.gcs.int.thomsonreuters.com/v1/openai/token"
OPENAI_BASE_URL = "https://eais2-use.int.thomsonreuters.com"

# Global variable to store the client, initialized once
_azure_openai_client = None
_client_error = None

def _initialize_azure_openai_client():
    global _azure_openai_client, _client_error
    if _azure_openai_client:
        return _azure_openai_client, None # Already initialized

    payload = {
        "workspace_id": WORKSPACE_ID,
        "model_name": MODEL_NAME
    }

    try:
        print(f"Attempting to fetch OpenAI credentials from {TOKEN_URL}...")
        resp = requests.post(TOKEN_URL, json=payload, timeout=10) # Added timeout
        resp.raise_for_status()  # Raise an exception for HTTP errors
        credentials = resp.json()
        print("Successfully fetched credentials.")
    except requests.exceptions.RequestException as e:
        _client_error = f"Failed to retrieve OpenAI credentials from token URL: {e}"
        print(f"Error: {_client_error}")
        return None, _client_error
    except json.JSONDecodeError as e:
        _client_error = f"Failed to decode JSON response from token URL: {e}. Response content: {resp.text[:500]}" # Log part of response
        print(f"Error: {_client_error}")
        return None, _client_error

    if "openai_key" in credentials and "openai_endpoint" in credentials and "azure_deployment" in credentials:
        openai_api_key = credentials["openai_key"]
        openai_deployment_id = credentials["azure_deployment"]
        openai_api_version = credentials["openai_api_version"]
        # token = credentials["token"] # This token is for the TR API, not directly for Azure OpenAI client
        llm_profile_key = openai_deployment_id.split("/")[0]

        headers = {
            "Authorization": f"Bearer {credentials['token']}",
            "api-key": openai_api_key, # This is the key AzureOpenAI client will use
            "Content-Type": "application/json",
            "x-tr-chat-profile-name": "ai-platforms-chatprofile-prod",
            "x-tr-userid": WORKSPACE_ID,
            "x-tr-llm-profile-key": llm_profile_key,
            "x-tr-user-sensitivity": "true",
            "x-tr-sessionid": openai_deployment_id,
            "x-tr-asset-id": ASSET_ID,
            "x-tr-authorization": OPENAI_BASE_URL # This seems to be the base URL itself
        }
        
        try:
            print(f"Initializing AzureOpenAI client with endpoint: {OPENAI_BASE_URL} and deployment: {openai_deployment_id}")
            _azure_openai_client = AzureOpenAI(
                azure_endpoint=OPENAI_BASE_URL, # The base URL for the Azure service
                api_key=openai_api_key,         # The key obtained from credentials
                api_version=openai_api_version,
                azure_deployment=openai_deployment_id, # The specific deployment ID
                default_headers=headers # Pass all required headers
            )
            print("AzureOpenAI client initialized successfully.")
            return _azure_openai_client, None
        except Exception as e:
            _client_error = f"Failed to initialize AzureOpenAI client: {e}"
            print(f"Error: {_client_error}")
            return None, _client_error
    else:
        _client_error = "Failed to retrieve necessary OpenAI credentials. Check response structure."
        print(f"Error: {_client_error}. Credentials received: {credentials}")
        return None, _client_error

def get_llm_response(prompt_content):
    """
    Gets a response from the configured Azure OpenAI LLM.
    The prompt_content should be the user's message to the LLM.
    Returns a Python dictionary parsed from the LLM's JSON response, or None on failure.
    """
    global _azure_openai_client, _client_error
    
    if not _azure_openai_client and not _client_error:
        _initialize_azure_openai_client()

    if _client_error:
        print(f"Cannot call LLM due to client initialization error: {_client_error}")
        return None
    
    if not _azure_openai_client:
        print("Error: AzureOpenAI client is not initialized and no previous error recorded.")
        return None

    try:
        print(f"Sending prompt to LLM (model: {MODEL_NAME}): '{prompt_content[:200]}...'") # Log a snippet of the prompt
        
        response = _azure_openai_client.chat.completions.create(
            model=MODEL_NAME, # This should align with the model for which credentials were fetched
            messages=[
                {"role": "system", "content": "You are an AI travel planner. Respond ONLY with a valid JSON object as per the user's instructions. Do not add any explanatory text before or after the JSON."},
                {"role": "user", "content": prompt_content},
            ],
            temperature=0.7, # Adjust for creativity vs. predictability
            max_tokens=4096, # Adjust based on expected output size
            response_format={"type": "json_object"} # Request JSON output if supported by model/API version
        )

        llm_output_content = response.choices[0].message.content
        print(f"Raw LLM response content: {llm_output_content[:500]}...") # Log a snippet of the raw response

        # The LLM should return a string that is a valid JSON object.
        parsed_response = json.loads(llm_output_content)
        print("Successfully parsed LLM JSON response.")
        return parsed_response

    except openai.APIError as e:
        print(f"OpenAI API Error: {e}")
    except requests.exceptions.RequestException as e: # Catch potential network errors during the API call itself
        print(f"Network error during LLM call: {e}")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON from LLM response: {e}. Response was: {llm_output_content}")
    except Exception as e:
        print(f"An unexpected error occurred while getting LLM response: {e}")
    
    return None # Return None if any error occurs

def generate_and_save_world_cities_list(output_directory="input", filename="world_cities.json"):
    """
    Prompts the LLM for a list of world cities and saves it to a JSON file.
    """
    cities_prompt = (
        "Generate a comprehensive list of at least 300-500 major and famous cities from around the world, "
        "suitable for use as tourism destinations. Include a diverse range of cities from various continents and countries. "
        "Format the response as a single JSON object with one key: 'cities'. "
        "The value of 'cities' should be a JSON list of strings. "
        "Each string must be in the format 'City Name, Country Name'. "
        "Example: {\"cities\": [\"Paris, France\", \"Tokyo, Japan\", \"New York, USA\", \"Cairo, Egypt\", \"Rio de Janeiro, Brazil\"]}"
    )
    
    print(f"Attempting to generate a list of world cities using LLM...")
    response_data = get_llm_response(cities_prompt) # Expects a dictionary
    
    if response_data and isinstance(response_data, dict) and "cities" in response_data and isinstance(response_data["cities"], list):
        cities_list = [str(city) for city in response_data["cities"] if isinstance(city, str)]
        if cities_list:
            # Ensure the output directory exists
            # Since this script is in llm_access, and we want to save to 'input' at the project root:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ../
            target_output_directory = os.path.join(project_root, output_directory)
            os.makedirs(target_output_directory, exist_ok=True)
            
            output_filepath = os.path.join(target_output_directory, filename)
            
            try:
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    json.dump({"cities": sorted(list(set(cities_list)))}, f, indent=4, ensure_ascii=False)
                print(f"Successfully generated and saved {len(cities_list)} cities to {output_filepath}")
                return True
            except IOError as e:
                print(f"Error saving cities list to {output_filepath}: {e}")
                return False
        else:
            print("LLM returned an empty or invalid list of cities.")
            return False
    else:
        print(f"Could not parse city list from LLM response for world cities. Response: {str(response_data)[:200]}")
        return False

if __name__ == '__main__':
    # Example usage for testing this module directly
    print("Testing LLM API module...")
    
    # --- This part is for initializing the client, crucial for other tests ---
    client, error = _initialize_azure_openai_client()
    if error:
        print(f"Exiting test due to client initialization error: {error}")
    elif not client:
        print("Exiting test: Client could not be initialized for unknown reasons.")
    # --- End of client initialization ---

    else: # Only proceed if client initialized successfully
        # --- Generate and save world cities list (NEW) ---
        # This will be run when the script is executed directly, e.g., python llm_access/llm_api.py
        # You might want to comment this out after the file is generated once to avoid repeated calls.
        print("\n--- Attempting to generate world_cities.json ---")
        if generate_and_save_world_cities_list():
            print("world_cities.json generation successful.")
        else:
            print("world_cities.json generation failed.")
        print("--- Finished world_cities.json generation attempt ---\n")
        # --- End of generating world cities list ---


        # --- Existing test for itinerary generation prompt ---
        test_prompt = (
            "You are an AI travel planner. A user has provided the following details for their trip: "
            "- Destination: Paris, France "
            "- Dates: From 2025-07-10 to 2025-07-12 (3 days) "
            "- Number of Travellers: 2 "
            "- Interests: Museums, Eiffel Tower, Food "
            "- Budget: Mid-Range "
            "- Additional Preferences: Looking for romantic spots. "
            "Based STRICTLY on these user-provided details, generate a detailed day-by-day travel itinerary. "
            "IMPORTANT: Respond *only* with a single, valid JSON object. Do not include any text or explanation before or after the JSON. "
            "The JSON object must have the following top-level keys: "
            "1. 'destination': A string with the name of the destination (e.g., \"Paris, France\"). "
            "2. 'itinerary': A list of objects. Each object represents a single day's plan and *must* have a 'day' key (integer, e.g., 1) and an 'activity' key (string). The 'activity' string should be a comprehensive description of the day's plan, including morning, afternoon, and evening segments, details for each Point of Interest (POI) or activity (like name, brief description, estimated duration, general cost level e.g., Free, $, $$, $$$), and suggestions for meals or logistical tips for that day. "
            "3. 'estimated_cost': A string describing the overall estimated cost for the trip (e.g., \"$1500 - $2000 for 2 people excluding flights\"). "
            "Example of a day object within the 'itinerary' list: "
            "{\"day\": 1, \"activity\": \"Morning: Visit the Eiffel Tower (iconic landmark, 2-3 hours, $$). Afternoon: Explore the Louvre Museum (world-renowned art, 3-4 hours, $$). Evening: Enjoy a romantic dinner cruise on the Seine River (2 hours, $$$). Meal suggestion: Try crepes from a street vendor for lunch. Tip: Purchase museum tickets online in advance to save time.\"} "
            "Ensure the 'activity' string is detailed and covers the full day. The number of day objects in the 'itinerary' list should match the trip duration."
        )
        
        print(f"\nSending test prompt to LLM:\n{test_prompt}\n")
        llm_response_data = get_llm_response(test_prompt)

        if llm_response_data:
            print("\nSuccessfully received and parsed LLM response:")
            print(json.dumps(llm_response_data, indent=2))
        else:
            print("\nFailed to get a valid response from LLM for the test prompt.")
        # --- End of itinerary generation test ---

        # --- Existing test for simple prompt ---
        simple_prompt = "What is the capital of France? Respond in JSON like {\"capital\": \"answer\"}."
        print(f"\nSending simple test prompt to LLM:\n{simple_prompt}\n")
        simple_response_data = get_llm_response(simple_prompt)
        if simple_response_data:
            print("\nSuccessfully received and parsed simple LLM response:")
            print(json.dumps(simple_response_data, indent=2))
        else:
            print("\nFailed to get a valid response from LLM for the simple test prompt.")
        # --- End of simple prompt test ---
    
    # Initialize client first (normally happens on first call to get_llm_response)
    client, error = _initialize_azure_openai_client()
    if error:
        print(f"Exiting test due to client initialization error: {error}")
    elif not client:
        print("Exiting test: Client could not be initialized for unknown reasons.")
    else:
        # Test prompt similar to what pipeline.py would generate
        test_prompt = (
            "You are an AI travel planner. A user has provided the following details for their trip: "
            "- Destination: Paris, France "
            "- Dates: From 2025-07-10 to 2025-07-12 (3 days) "
            "- Number of Travellers: 2 "
            "- Interests: Museums, Eiffel Tower, Food "
            "- Budget: Mid-Range "
            "- Additional Preferences: Looking for romantic spots. "
            "Based STRICTLY on these user-provided details, generate a detailed day-by-day travel itinerary. "
            "IMPORTANT: Respond *only* with a single, valid JSON object. Do not include any text or explanation before or after the JSON. "
            "The JSON object must have the following top-level keys: "
            "1. 'destination': A string with the name of the destination (e.g., \"Paris, France\"). "
            "2. 'itinerary': A list of objects. Each object represents a single day's plan and *must* have a 'day' key (integer, e.g., 1) and an 'activity' key (string). The 'activity' string should be a comprehensive description of the day's plan, including morning, afternoon, and evening segments, details for each Point of Interest (POI) or activity (like name, brief description, estimated duration, general cost level e.g., Free, $, $$, $$$), and suggestions for meals or logistical tips for that day. "
            "3. 'estimated_cost': A string describing the overall estimated cost for the trip (e.g., \"$1500 - $2000 for 2 people excluding flights\"). "
            "Example of a day object within the 'itinerary' list: "
            "{\"day\": 1, \"activity\": \"Morning: Visit the Eiffel Tower (iconic landmark, 2-3 hours, $$). Afternoon: Explore the Louvre Museum (world-renowned art, 3-4 hours, $$). Evening: Enjoy a romantic dinner cruise on the Seine River (2 hours, $$$). Meal suggestion: Try crepes from a street vendor for lunch. Tip: Purchase museum tickets online in advance to save time.\"} "
            "Ensure the 'activity' string is detailed and covers the full day. The number of day objects in the 'itinerary' list should match the trip duration."
        )
        
        print(f"\nSending test prompt to LLM:\n{test_prompt}\n")
        llm_response_data = get_llm_response(test_prompt)

        if llm_response_data:
            print("\nSuccessfully received and parsed LLM response:")
            print(json.dumps(llm_response_data, indent=2))
        else:
            print("\nFailed to get a valid response from LLM for the test prompt.")

        # Example of a simple prompt
        simple_prompt = "What is the capital of France? Respond in JSON like {\"capital\": \"answer\"}."
        print(f"\nSending simple test prompt to LLM:\n{simple_prompt}\n")
        simple_response_data = get_llm_response(simple_prompt)
        if simple_response_data:
            print("\nSuccessfully received and parsed simple LLM response:")
            print(json.dumps(simple_response_data, indent=2))
        else:
            print("\nFailed to get a valid response from LLM for the simple test prompt.")
