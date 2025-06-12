import streamlit as st
import json
import datetime
import os # Keep for potential path joining if needed for dataset
# import re # No longer needed in app.py
# from llm_access.llm_api import get_llm_response # Now handled by pipeline
from pipeline import create_travel_itinerary # Import the main pipeline function

def main():
    st.set_page_config(page_title="AI Travel Planner", layout="wide")

    st.title("🌍 AI Powered Travel Itinerary Planner")
    
    st.image("https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=1200&h=400&fit=crop", use_container_width=True)

    st.markdown("---") 

    st.subheader("Get Inspired!")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image("https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?q=80&w=600&h=400&fit=crop", caption="Charming Streets", use_container_width=True)
    with col2:
        st.image("https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?q=80&w=600&h=400&fit=crop", caption="Scenic Lakes", use_container_width=True)
    with col3:
        st.image("https://images.unsplash.com/photo-1503220317375-aaad61436b1b?q=80&w=600&h=400&fit=crop", caption="Adventure Awaits", use_container_width=True)
    
    st.markdown("---")

    st.markdown("Let's plan your next adventure! Fill in your preferences below.")

    try:
        dataset_file_path = "input/Dataset.json" # Ensure this path is correct
        with open(dataset_file_path, 'r', encoding='utf-8') as f:
            poi_data = json.load(f)
        
        popular_destinations_from_json = sorted(list(set([
            f"{poi.get('name', 'Unknown POI')}, {poi.get('destination_city', 'Unknown City')}" 
            for poi in poi_data 
            if poi.get('name') and poi.get('destination_city')
        ])))
        POPULAR_DESTINATIONS = popular_destinations_from_json + ["Other - type your own"]
        if not popular_destinations_from_json:
            POPULAR_DESTINATIONS = [
                "Paris, France", "Rome, Italy", "Tokyo, Japan", "Kyoto, Japan",
                "New York, USA", "London, UK", "Barcelona, Spain", "Amsterdam, Netherlands",
                "Berlin, Germany", "Sydney, Australia", "Melbourne, Australia",
                "Bali, Indonesia", "Phuket, Thailand", "Bangkok, Thailand", "Singapore",
                "Dubai, UAE", "Cancun, Mexico", "Honolulu, Hawaii, USA",
                "Vancouver, Canada", "Toronto, Canada",
                "Other - type your own"
            ]
            st.sidebar.warning(f"Could not load or parse destinations from {dataset_file_path}. Using default list.")

        all_categories = set()
        for poi in poi_data:
            categories_str = poi.get('category')
            if categories_str and isinstance(categories_str, str):
                all_categories.update([cat.strip() for cat in categories_str.split('|') if cat.strip()])
        
        INTEREST_OPTIONS = sorted(list(all_categories))
        if not INTEREST_OPTIONS:
            INTEREST_OPTIONS = ["History", "Adventure", "Relaxation", "Food", "Culture", "Nature", "Nightlife", "Shopping"]
            st.sidebar.warning(f"Could not load categories from {dataset_file_path}. Using default list.")

    except FileNotFoundError:
        st.sidebar.error(f"Error: {dataset_file_path} not found. Using default destinations and interests.")
        POPULAR_DESTINATIONS = [
            "Paris, France", "Rome, Italy", "Tokyo, Japan", "Kyoto, Japan", 
            "New York, USA", "London, UK", "Barcelona, Spain", "Amsterdam, Netherlands", 
            "Berlin, Germany", "Sydney, Australia", "Melbourne, Australia", 
            "Bali, Indonesia", "Phuket, Thailand", "Bangkok, Thailand", "Singapore", 
            "Dubai, UAE", "Cancun, Mexico", "Honolulu, Hawaii, USA", 
            "Vancouver, Canada", "Toronto, Canada", 
            "Other - type your own"
        ]
        INTEREST_OPTIONS = ["History", "Adventure", "Relaxation", "Food", "Culture", "Nature", "Nightlife", "Shopping"]
    except json.JSONDecodeError:
        st.sidebar.error(f"Error: Could not decode {dataset_file_path}. Using default destinations and interests.")
        POPULAR_DESTINATIONS = [
            "Paris, France", "Rome, Italy", "Tokyo, Japan", "Kyoto, Japan",
            "New York, USA", "London, UK", "Barcelona, Spain", "Amsterdam, Netherlands",
            "Berlin, Germany", "Sydney, Australia", "Melbourne, Australia",
            "Bali, Indonesia", "Phuket, Thailand", "Bangkok, Thailand", "Singapore",
            "Dubai, UAE", "Cancun, Mexico", "Honolulu, Hawaii, USA",
            "Vancouver, Canada", "Toronto, Canada",
            "Other - type your own"
        ]
        INTEREST_OPTIONS = ["History", "Adventure", "Relaxation", "Food", "Culture", "Nature", "Nightlife", "Shopping"]

    with st.sidebar:
        st.header("Travel Preferences")
        
        selected_option = st.selectbox(
            "Destination (select, type to search, or choose 'Other')", 
            options=POPULAR_DESTINATIONS,
            index=0 
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

            with st.spinner("🤖 Generating your personalized itinerary..."):
                itinerary_data, saved_filepath = create_travel_itinerary(preferences)

            if itinerary_data and saved_filepath:
                st.sidebar.success(f"Itinerary saved to {saved_filepath}")
            elif itinerary_data: # Itinerary generated but not saved
                st.sidebar.warning("Itinerary generated, but there was an issue saving it.")
            else: # Failed to generate itinerary
                st.sidebar.error("Failed to generate itinerary. Please check logs or try again.")
                st.stop() # Stop further execution in app if generation failed

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
                    st.markdown(f"---")
                    st.markdown(f"### 📅 Day {day_plan.get('day', 'N/A')}")
                    st.markdown(f"**Activities:** {day_plan.get('activity', 'No activities planned.')}") # This might need adjustment based on pipeline's output structure
            else:
                st.warning("Could not generate detailed itinerary. Please try adjusting your preferences.")

            if itinerary_data.get("estimated_cost"):
                st.markdown(f"**Estimated Cost:** {itinerary_data['estimated_cost']}")
            
            # with st.expander("View Raw Itinerary Data (JSON)"):
            #     st.json(itinerary_data)
    else:
        st.info("Fill in your preferences in the sidebar and click 'Generate Itinerary'.")

if __name__ == "__main__":
    main()
