import streamlit as st
import json
import datetime
import os
import shutil # Added for directory operations
# import re # No longer needed in app.py
from llm_access.llm_api import get_llm_response # Import for fetching city list
from pipeline import create_travel_itinerary # Import the main pipeline function

# --- Helper function to get famous cities from LLM ---
def get_famous_cities_from_llm():
    """
    Fetches a list of famous cities from the LLM.
    Returns a list of city strings or None if an error occurs.
    """
    prompt = (
        "Generate a list of approximately 75-100 globally famous cities suitable for tourism. "
        "Format the response as a single JSON object with one key: 'cities'. "
        "The value of 'cities' should be a JSON list of strings. "
        "Each string should be in the format 'City Name, Country Name'. "
        "Example: {\"cities\": [\"Paris, France\", \"Tokyo, Japan\", \"Rome, Italy\"]}"
    )
    try:
        response_data = get_llm_response(prompt) # Expects a dictionary
        if response_data and isinstance(response_data, dict) and "cities" in response_data and isinstance(response_data["cities"], list):
            cities = [str(city) for city in response_data["cities"] if isinstance(city, str)]
            if cities:
                return sorted(list(set(cities))) # Ensure uniqueness and sort
            else:
                # st.sidebar.warning("LLM returned an empty or invalid list of cities.")
                return None
        else:
            # st.sidebar.warning(f"Could not parse city list from LLM response. Response: {str(response_data)[:200]}") # Log part of response
            return None
    except Exception as e:
        # st.sidebar.error(f"Error fetching cities from LLM: {e}")
        return None

# DEFAULT_DESTINATIONS list has been removed as per user request.

def main():
    st.set_page_config(page_title="WanderLust - AI Travel Planner", layout="wide") # Changed page_title

    # Custom CSS for overall aesthetics
    st.markdown("""
    <style>
    /* --- General Body and Font --- */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f8eadd; /* TR Light Amber */
        color: #333; /* Keeping text dark for readability */
    }
    /* --- Main App Container (Streamlit's default might be targeted differently, this is a general idea) --- */
    .main .block-container { /* Attempt to target Streamlit's main content block */
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* --- Custom Container for our content --- */
    .content-container {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-top: 1rem;
    }

    /* --- Title Styling --- */
    /* Custom title if we use markdown h1 */
    h1.custom-main-title {
        color: #d4792a; /* TR Dark Amber */
        font-size: 2.8em;
        font-weight: 700;
        text-align: center; /* Center the main title */
        margin-bottom: 0.5em;
    }
    .title-icon {
        width: 60px; /* Slightly smaller than before for balance */
        height: 60px;
        margin-right: 15px;
        vertical-align: middle;
    }


    /* --- Sidebar Styling --- */
    .stSidebar { /* Targets Streamlit's sidebar */
        background-color: #f8eadd; /* TR Light Amber */
        padding: 15px;
    }
    .stSidebar .stHeader, .stSidebar h1, .stSidebar h2, .stSidebar h3 { /* Target sidebar headers */
        color: #d4792a !important; /* TR Dark Amber */
    }


    /* --- Button Styling --- */
    .stButton>button {
        background-color: #d4792a; /* TR Dark Amber */
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        font-weight: bold;
        transition: background-color 0.3s ease;
        width: 100%; /* Make sidebar button full width */
    }
    .stButton>button:hover {
        background-color: #b46724; /* Darker Amber on hover */
    }
    
    /* --- Day Header (existing, slightly refined) --- */
    .day-header {
        background-color: #f8eadd; /* TR Light Amber */
        padding: 12px 18px;
        border-radius: 8px;
        margin-top: 15px; /* Space above the header */
        margin-bottom: 10px; /* Space below the header */
        display: flex;
        align-items: center;
        border: 1px solid #d4792a; /* TR Dark Amber border */
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .day-header img {
        width: 30px; /* Icon size */
        height: 30px;
        margin-right: 12px; /* Space between icon and text */
    }
    .day-header h3 {
        margin: 0;
        color: #d4792a; /* TR Dark Amber */
        font-size: 1.6em; /* Slightly larger font for Day X */
        font-weight: 600;
    }
    .activity-card {
        background-color: #ffffff;
        border: 1px solid #e8e8e8;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .activity-card h4 {
        color: #d4792a; /* TR Dark Amber */
        margin-top: 0;
        margin-bottom: 8px;
    }
    .activity-card p {
        margin-bottom: 5px;
        font-size: 0.95em;
    }
    .activity-card img {
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .section-title {
        font-weight: bold;
        color: #d4792a; /* TR Dark Amber */
        margin-top:15px; /* Increased margin */
        margin-bottom: 8px;
        font-size: 1.1em;
        border-bottom: 2px solid #f8eadd; /* TR Light Amber */
        padding-bottom: 5px;
    }

    /* --- Input Field Styling (General) --- */
    .stTextInput input, .stDateInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 5px !important;
        border: 1px solid #ced4da !important;
    }
    .stTextArea textarea {
        border-radius: 5px !important;
        border: 1px solid #ced4da !important;
        min-height: 100px;
    }

    /* --- Horizontal Rule --- */
    hr {
        border-top: 1px solid #dee2e6;
    }

    /* --- Estimated Cost Styling --- */
    .estimated-cost-display {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 1.1em;
        font-weight: bold;
        color: #28a745; /* Green color for cost - keeping for financial indication */
        text-align: right;
        padding: 10px 15px;
        margin-top: 20px;
        background-color: #f8eadd; /* TR Light Amber */
        border-radius: 5px;
        border: 1px solid #e9ecef; /* Keeping a light border or could change to a light amber variant */
    }

    /* --- Meal Cost Estimation Styling (Enhanced) --- */
    .meal-cost-estimation {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: right;
        padding: 10px 15px;
        margin-top: 8px; 
        background-color: #e8f5e9; /* Light green background */
        border-radius: 8px; /* Slightly more rounded */
        border: 1px solid #c8e6c9; /* Softer green border */
        border-left: 5px solid #4CAF50; /* Prominent green accent on the left */
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); /* Subtle shadow */
    }
    .meal-cost-estimation .cost-label { /* Class for the "Total Estimated Meal Cost:" part */
        font-weight: bold;
        color: #388E3C; /* Darker green for the label */
        font-size: 1.0em;
        margin-right: 8px; /* Space between label and value */
    }
    .meal-cost-estimation .cost-value { /* Class for the actual cost value */
        font-weight: bold;
        color: #4CAF50; /* Bright green for the value */
        font-size: 1.05em; /* Slightly larger value */
    }

    /* --- Meal Suggestions Styling --- */
    .meal-suggestions-container {
        margin-top: 15px;
        padding: 15px;
        background-color: #fdfdfd; /* Very light grey, almost white */
        border-radius: 8px;
        border: 1px solid #f0f0f0;
    }
    .meal-item {
        margin-bottom: 8px;
    }
    .meal-item strong { /* For Breakfast:, Lunch:, Dinner: labels */
        color: #d4792a; /* TR Dark Amber */
        display: inline-block;
        width: 90px; /* Fixed width for alignment */
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Custom HTML for Main Title ---
    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://i.postimg.cc/N0kBq1yX/2150846903.jpg" class="title-icon" alt="App Icon">
            <h1 class="custom-main-title">WanderLust</h1>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Hero Image
    st.image("https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=1200&h=350&fit=crop", use_container_width=True) # Slightly reduced height

    st.markdown("---") 

    # "Get Inspired!" Section - can be wrapped in a content-container if desired, or kept separate
    st.subheader("Get Inspired!") # Standard subheader, or could be custom HTML
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image("https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?q=80&w=600&h=400&fit=crop", caption="Charming Streets", use_container_width=True)
    with col2:
        st.image("https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?q=80&w=600&h=400&fit=crop", caption="Scenic Lakes", use_container_width=True)
    with col3:
        st.image("https://images.unsplash.com/photo-1503220317375-aaad61436b1b?q=80&w=600&h=400&fit=crop", caption="Adventure Awaits", use_container_width=True)
    
    st.markdown("---")

    st.markdown("Let's plan your next adventure! Fill in your preferences below.")

    # --- Initialize POPULAR_DESTINATIONS and INTEREST_OPTIONS ---
    POPULAR_DESTINATIONS = []
    INTEREST_OPTIONS = []

    # 1. Prioritize loading from input/world_cities.json
    world_cities_file_path = os.path.join("input", "world_cities.json") # Ensure correct path
    loaded_from_file = False
    if os.path.exists(world_cities_file_path):
        try:
            with open(world_cities_file_path, 'r', encoding='utf-8') as f:
                world_cities_data = json.load(f)
            if world_cities_data and isinstance(world_cities_data, dict) and \
               "cities" in world_cities_data and isinstance(world_cities_data["cities"], list):
                cities_from_file = [str(city) for city in world_cities_data["cities"] if isinstance(city, str)]
                if cities_from_file:
                    POPULAR_DESTINATIONS.extend(cities_from_file)
                    loaded_from_file = True
                    # st.sidebar.info(f"Loaded {len(cities_from_file)} destinations from {world_cities_file_path}.") # User-facing message removed
                else:
                    # st.sidebar.warning(f"{world_cities_file_path} was found but contained no valid cities. Will try LLM fallback.") # User-facing message removed
                    pass
            else:
                # st.sidebar.warning(f"Invalid format in {world_cities_file_path}. Will try LLM fallback.") # User-facing message removed
                pass
        except json.JSONDecodeError:
            # st.sidebar.warning(f"Could not decode {world_cities_file_path}. Will try LLM fallback.") # User-facing message removed
            pass
        except Exception as e:
            # st.sidebar.warning(f"Error reading {world_cities_file_path}: {e}. Will try LLM fallback.") # User-facing message removed
            pass
    else:
        # st.sidebar.info(f"{world_cities_file_path} not found. Will try LLM for destinations.") # User-facing message removed
        pass

    # 2. If loading from file failed or yielded no destinations, try LLM as a fallback
    if not loaded_from_file or not POPULAR_DESTINATIONS:
        # st.sidebar.info(f"Primary city list ({world_cities_file_path}) empty, not found, or failed to load. Attempting to fetch a dynamic list from AI as a fallback...") # User-facing message removed
        llm_cities = get_famous_cities_from_llm() # This fetches a smaller, dynamic list
        if llm_cities:
            POPULAR_DESTINATIONS.extend(llm_cities)
            # st.sidebar.info(f"Loaded {len(llm_cities)} destinations from LLM as fallback.") # User-facing message removed
    
    # 3. If still no destinations after file and LLM, the list will be empty (before adding "Other")
    if not POPULAR_DESTINATIONS:
        # st.sidebar.error("CRITICAL: Failed to load destinations. The destination list will be initially empty (except for 'Other').") # Simplified error
        pass 
    
    # Ensure "Other - type your own" is present and list is unique and sorted
    POPULAR_DESTINATIONS = sorted(list(set(POPULAR_DESTINATIONS))) # Deduplicate and sort
    if not POPULAR_DESTINATIONS: # Ensure there's at least 'Other' if all loads fail
        POPULAR_DESTINATIONS.append("Other - type your own")
    elif "Other - type your own" not in POPULAR_DESTINATIONS: # Add if not present
        POPULAR_DESTINATIONS.append("Other - type your own")


    # --- Load INTEREST_OPTIONS from Dataset.json ---
    # This part remains for interest categories
    dataset_file_path = "input/Dataset.json"
    try:
        with open(dataset_file_path, 'r', encoding='utf-8') as f:
            poi_data = json.load(f) # poi_data is now locally scoped here
        
        if poi_data and isinstance(poi_data, list):
            all_categories = set()
            for poi in poi_data:
                categories_str = poi.get('category')
                if categories_str and isinstance(categories_str, str):
                    all_categories.update([cat.strip() for cat in categories_str.split('|') if cat.strip()])
            if all_categories:
                INTEREST_OPTIONS.extend(sorted(list(all_categories)))
                # st.sidebar.info(f"Loaded {len(INTEREST_OPTIONS)} interest categories from {dataset_file_path}.")
    except FileNotFoundError:
        # st.sidebar.warning(f"Interest categories file {dataset_file_path} not found. Using defaults.")
        pass
    except json.JSONDecodeError:
        # st.sidebar.warning(f"Could not decode interest categories from {dataset_file_path}. Using defaults.")
        pass
    except Exception as e:
        # st.sidebar.warning(f"Error reading interest categories from {dataset_file_path}: {e}. Using defaults.")
        pass

    if not INTEREST_OPTIONS: # Fallback for INTEREST_OPTIONS
        INTEREST_OPTIONS = ["History", "Adventure", "Relaxation", "Food", "Culture", "Nature", "Nightlife", "Shopping"]
        # st.sidebar.warning(f"Using default interest categories.")
    INTEREST_OPTIONS = sorted(list(set(INTEREST_OPTIONS))) # Deduplicate and sort

    with st.sidebar:
        st.header("🌍 Your Travel Preferences") # Added icon
        
        # Determine a safe index for the selectbox
        s_options = POPULAR_DESTINATIONS
        s_index = 0
        if not s_options or (len(s_options) == 1 and s_options[0] == "Other - type your own"):
            # If only "Other" is there, or list is empty before "Other" is forced, make "Other" selected
            if "Other - type your own" not in s_options: s_options.append("Other - type your own") # Should be redundant
            s_index = s_options.index("Other - type your own") if "Other - type your own" in s_options else 0
        elif "Paris, France" in s_options: # Default to Paris if available
             s_index = s_options.index("Paris, France")


        selected_option = st.selectbox(
            "Destination (select, type to search, or choose 'Other')", 
            options=s_options,
            index=s_index 
        )

        if selected_option == "Other - type your own":
            destination = st.text_input("Enter your custom destination:", placeholder="e.g., Mykonos, Greece", key="custom_destination")
        else:
            destination = selected_option
        
        today = datetime.date.today()
        from_date = st.date_input("From Date", value=today, min_value=today)
        to_date = st.date_input("To Date", value=from_date + datetime.timedelta(days=6), min_value=from_date)
        num_travellers = st.number_input("Number of Travellers", min_value=1, value=1, step=1)

        interests = st.multiselect(
            "Interests/Activities",
            options=INTEREST_OPTIONS
        )
        budget_options = ["Backpacker", "Economy", "Mid-Range", "Comfort", "Luxury", "Ultra-Luxury"]
        budget = st.select_slider(
            "Budget",
            options=budget_options,
            value="Mid-Range"
        )
        additional_prefs = st.text_area("Any other preferences or specific places to visit?")

    if st.sidebar.button("✨ Generate Itinerary"):
        if not destination:
            st.sidebar.error("Please enter a destination.")
        elif from_date and to_date and to_date < from_date:
            st.sidebar.error("'To Date' cannot be before 'From Date'.")
        else:
            duration_calculated = (to_date - from_date).days + 1
            preferences = {
                "destination": destination,
                "from_date": from_date, # Pass datetime.date object
                "to_date": to_date,     # Pass datetime.date object
                "duration": duration_calculated,
                "num_travellers": num_travellers,
                "interests": interests,
                "budget": budget,
                "additional_prefs": additional_prefs
            }

            # --- Clear and recreate the output directory ---
            output_dir = "Output" # Changed to capital 'O'
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            os.makedirs(output_dir)
            # --- End of clearing output directory ---

            itinerary_data, saved_filepath = create_travel_itinerary(preferences)

            if itinerary_data and saved_filepath:
                # st.sidebar.success(f"Itinerary saved to {saved_filepath}")
                pass
            elif itinerary_data: # Itinerary generated but not saved
                # st.sidebar.warning("Itinerary generated, but there was an issue saving it.")
                pass
            else: # Failed to generate itinerary
                # st.sidebar.error("Failed to generate itinerary. Please check logs or try again.")
                st.stop() # Stop further execution in app if generation failed
            
            # --- Wrap itinerary display in a content-container ---
            st.markdown("<div class='content-container'>", unsafe_allow_html=True)


            st.subheader(f"Your Trip to {itinerary_data.get('destination', 'Your Destination')}")
            
            from_date_str_display = itinerary_data.get('from_date') # Already formatted string from pipeline
            to_date_str_display = itinerary_data.get('to_date') # Already formatted string from pipeline
            duration_display = itinerary_data.get('duration', 'N/A')
            num_travellers_display = itinerary_data.get('num_travellers', 1)

            if from_date_str_display and to_date_str_display:
                st.markdown(f"**Dates:** {from_date_str_display} to {to_date_str_display} ({duration_display} days)")
            else:
                st.markdown(f"**Duration:** {duration_display} days")
            
            st.markdown(f"**Travellers:** {num_travellers_display}")

            if "details" in itinerary_data and itinerary_data["details"]:
                for day_plan in itinerary_data["details"]:
                    st.markdown(f"---") # Separator line
                    
                    # Custom HTML for styled day header
                    day_number = day_plan.get('day', 'N/A')
                    day_header_html = f"""
                    <div class="day-header">
                        <img src="https://i.postimg.cc/KcMBSWSY/travel-4988737.png" alt="Day Icon">
                        <h3>Day {day_number}</h3>
                    </div>
                    """
                    st.markdown(day_header_html, unsafe_allow_html=True)
                    
                    # Display day summary
                    day_summary = day_plan.get("day_summary")
                    if day_summary:
                        st.markdown(f"*{day_summary}*")

                    # Display activities for the day
                    activities = day_plan.get("activities", [])
                    if activities:
                        st.markdown("<div class='section-title'>Activities:</div>", unsafe_allow_html=True)
                        for activity in activities:
                            activity_html = "<div class='activity-card'>"
                            activity_html += f"<h4>{activity.get('name', 'N/A')} ({activity.get('time_of_day', 'N/A')})</h4>"
                            
                            poi_image = activity.get("poi_image_url")
                            if poi_image and isinstance(poi_image, str) and poi_image.strip():
                                activity_html += f"<img src='{poi_image}' alt='{activity.get('name', 'Activity Image')}' style='width:100%; max-width:400px;'>" # Basic styling for POI image
                            
                            if activity.get('description'):
                                activity_html += f"<p><strong>Description:</strong> {activity.get('description')}</p>"
                            if activity.get('why_relevant'):
                                activity_html += f"<p><strong>Why this?:</strong> {activity.get('why_relevant')}</p>"
                            if activity.get('estimated_duration'):
                                activity_html += f"<p><strong>Duration:</strong> {activity.get('estimated_duration')}</p>"
                            if activity.get('estimated_cost'):
                                activity_html += f"<p><strong>Cost:</strong> {activity.get('estimated_cost')}</p>"
                            activity_html += "</div>"
                            st.markdown(activity_html, unsafe_allow_html=True)
                    else:
                        st.markdown("<p>No specific activities planned for this day.</p>", unsafe_allow_html=True)

                    # Display Meal Suggestions
                    meal_suggestions_data = day_plan.get("daily_meal_suggestions")
                    if isinstance(meal_suggestions_data, dict) and any(str(v).strip() for v in meal_suggestions_data.values()): # Check if any value is non-empty after stripping
                        meal_html_parts = []
                        breakfast = str(meal_suggestions_data.get("breakfast", "")).strip()
                        lunch = str(meal_suggestions_data.get("lunch", "")).strip()
                        dinner = str(meal_suggestions_data.get("dinner", "")).strip()

                        if breakfast:
                            meal_html_parts.append(f"<div class='meal-item'><strong>Breakfast:</strong> {breakfast}</div>")
                        if lunch:
                            meal_html_parts.append(f"<div class='meal-item'><strong>Lunch:</strong> {lunch}</div>")
                        if dinner:
                            meal_html_parts.append(f"<div class='meal-item'><strong>Dinner:</strong> {dinner}</div>")
                        
                        if meal_html_parts: # Only build the full HTML if there's actual content
                            full_meal_html = "<div class='section-title'>🍽️ Meal Suggestions:</div>" # Added icon
                            full_meal_html += "<div class='meal-suggestions-container'>"
                            full_meal_html += "".join(meal_html_parts)
                            full_meal_html += "</div>"
                            st.markdown(full_meal_html, unsafe_allow_html=True)
                            
                    elif isinstance(meal_suggestions_data, str) and meal_suggestions_data.strip(): # Fallback for old string format
                        st.markdown(f"<div class='section-title'>🍽️ Meal Suggestions:</div><p>{meal_suggestions_data}</p>", unsafe_allow_html=True)


                    # Display Logistical Tips
                    logistical_tips = day_plan.get("daily_logistical_tips")
                    if logistical_tips and str(logistical_tips).strip():
                        st.markdown(f"<div class='section-title'>💡 Logistical Tips:</div><p>{str(logistical_tips).strip()}</p>", unsafe_allow_html=True) # Added icon and strip
            else:
                st.warning("Could not generate detailed itinerary. Please try adjusting your preferences.")

            # Display Estimated Costs
            estimated_cost_main = itinerary_data.get("estimated_cost")
            estimated_total_meal_cost = itinerary_data.get("total_estimated_meal_cost")
            estimated_daily_meal_cost_person = itinerary_data.get("estimated_daily_meal_cost_per_person")

            if estimated_cost_main:
                cost_label = "Estimated Cost (Excl. Meals)" if estimated_total_meal_cost or estimated_daily_meal_cost_person else "Estimated Cost"
                cost_html = f"""
                <div class="estimated-cost-display">
                    {cost_label}: {estimated_cost_main}
                </div>
                """
                st.markdown(cost_html, unsafe_allow_html=True)

            if estimated_total_meal_cost: # This is the calculated total string from pipeline.py
                meal_cost_html = f"""
                <div class="meal-cost-estimation">
                    <span class="cost-label">Total Estimated Meal Cost:</span><span class="cost-value">{estimated_total_meal_cost}</span>
                </div>
                """
                st.markdown(meal_cost_html, unsafe_allow_html=True)
            elif estimated_daily_meal_cost_person: # Fallback if total wasn't calculated but daily per person is there
                 meal_cost_html = f"""
                <div class="meal-cost-estimation">
                    <span class="cost-label">Daily Meal Cost (per person):</span><span class="cost-value">{estimated_daily_meal_cost_person}</span>
                </div>
                """
                 st.markdown(meal_cost_html, unsafe_allow_html=True)
            
            # with st.expander("View Raw Itinerary Data (JSON)"):
            #     st.json(itinerary_data)
            
            st.markdown("</div>", unsafe_allow_html=True) # Close content-container
    else:
        st.info("Fill in your preferences in the sidebar and click 'Generate Itinerary'.")

if __name__ == "__main__":
    main()
