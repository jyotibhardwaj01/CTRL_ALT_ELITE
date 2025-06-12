# llm_access/llm_api.py

def get_llm_response(prompt):
    """
    Placeholder function to simulate LLM API call.
    In a real application, this would interact with an actual LLM.
    """
    print(f"Simulating LLM call with prompt: {prompt}")
    # Simulate a response based on a simple keyword in the prompt
    if "beach" in prompt.lower() and "7 days" in prompt.lower():
        return {
            "destination": "Phuket, Thailand",
            "itinerary": [
                {"day": 1, "activity": "Arrive in Phuket, check into hotel, relax by the pool."},
                {"day": 2, "activity": "Patong Beach exploration and water sports."},
                {"day": 3, "activity": "Phi Phi Islands day trip (snorkeling, Maya Bay)."},
                {"day": 4, "activity": "Visit Big Buddha and Wat Chalong."},
                {"day": 5, "activity": "Relaxing day at Kata Noi Beach, sunset dinner."},
                {"day": 6, "activity": "Explore Old Phuket Town, local markets."},
                {"day": 7, "activity": "Depart from Phuket."}
            ],
            "estimated_cost": "$1000 - $1500 (excluding flights)"
        }
    elif "mountain" in prompt.lower():
         return {
            "destination": "Swiss Alps, Switzerland",
            "itinerary": [
                {"day": 1, "activity": "Arrive in Zurich, train to Interlaken."},
                {"day": 2, "activity": "Explore Interlaken, Harder Kulm viewpoint."},
                {"day": 3, "activity": "Jungfraujoch - Top of Europe excursion."},
                {"day": 4, "activity": "Hiking near Grindelwald."},
                {"day": 5, "activity": "Relax by Lake Thun or Lake Brienz."},
                {"day": 6, "activity": "Visit a local cheese factory or chocolate shop."},
                {"day": 7, "activity": "Depart from Zurich."}
            ],
            "estimated_cost": "$2000 - $3000 (excluding flights)"
        }
    else:
        return {
            "destination": "Generic City Break",
            "itinerary": [
                {"day": 1, "activity": "Arrive and check in."},
                {"day": 2, "activity": "City tour."},
                {"day": 3, "activity": "Museum visit."},
                {"day": 4, "activity": "Shopping and local cuisine."},
                {"day": 5, "activity": "Day trip to nearby attraction."},
                {"day": 6, "activity": "Relax or explore further."},
                {"day": 7, "activity": "Depart."}
            ],
            "estimated_cost": "$800 - $1200 (excluding flights)"
        }

def generate_itinerary_prompt(preferences):
    """
    Generates a prompt for the LLM based on user preferences.
    """
    prompt = f"Generate a {preferences.get('duration_days', 'few')} days travel itinerary "
    prompt += f"for a {preferences.get('destination_type', 'general')} destination. "
    if preferences.get('activities'):
        prompt += f"Include activities like {', '.join(preferences['activities'])}. "
    if preferences.get('budget'):
        prompt += f"The budget is {preferences['budget']}. "
    if preferences.get('travel_style'):
        prompt += f"The travel style is {preferences['travel_style']}. "
    return prompt.strip()

if __name__ == '__main__':
    # Example usage (for testing this module directly)
    sample_prefs = {
        "destination_type": "beach",
        "duration_days": 7,
        "activities": ["swimming", "snorkeling", "relaxing"],
        "budget": "moderate",
        "travel_style": "adventure"
    }
    prompt = generate_itinerary_prompt(sample_prefs)
    print(f"Generated Prompt:\n{prompt}\n")
    
    response = get_llm_response(prompt)
    print(f"LLM Response:\n{response}")

    sample_prefs_mountain = {
        "destination_type": "mountain",
        "duration_days": 5,
        "activities": ["hiking", "sightseeing"],
        "budget": "luxury",
        "travel_style": "relaxing"
    }
    prompt_mountain = generate_itinerary_prompt(sample_prefs_mountain)
    print(f"\nGenerated Prompt (Mountain):\n{prompt_mountain}\n")
    response_mountain = get_llm_response(prompt_mountain)
    print(f"LLM Response (Mountain):\n{response_mountain}")
