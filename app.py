import pandas as pd
import streamlit as st
import calendar
from collections import defaultdict
from datetime import date, timedelta

# Load the dataset
data = pd.read_csv('BIRB_Voss_alleruter.csv', sep=None, engine='python', encoding='latin1')

# Ensure all relevant fields are strings and handle NaN values
data['EtikettID'] = data['EtikettID'].fillna('').astype(str)
data['Eiendomsnavn'] = data['Eiendomsnavn'].fillna('').astype(str)
data['Gatenavn'] = data['Gatenavn'].fillna('').astype(str)
data['Husnummer'] = data['Husnummer'].fillna('').astype(str)
data['FullAddress'] = (data['Gatenavn'] + ' ' + data['Husnummer']).str.strip()
data['Bemerkning'] = data['Bemerkning'].fillna('').astype(str)
data['Rutenummer'] = data['Rutenummer'].astype(str)

# Define constants
COLORS = {
    '2': 'blue',  # Paper/plastic
    '3': 'blue',
    '6': 'gray',  # Glass/metal
    '7': 'green'  # Combined Restavfall/Matavfall
}

CYCLE_WEEKS = {
    1: 2,  # Start of cycle week 1 in calendar week
    2: 3,  # Start of cycle week 2 in calendar week
    3: 4,  # Start of cycle week 3 in calendar week
    4: 1   # Start of cycle week 4 in calendar week
}

# Helper function to calculate pickup dates
def calculate_yearly_pickup_dates(start_date, weekday, interval=28):
    """
    Calculate all pickup dates in a year starting from a specific date.

    Args:
        start_date (datetime.date): The first pickup date.
        weekday (int): Day of the week (1=Monday, 7=Sunday).
        interval (int): Days between pickups (default=28 for 4-week cycle).

    Returns:
        list: List of all pickup dates for the year.
    """
    current_date = start_date
    pickup_dates = []

    # Adjust start_date to match the specified weekday
    while current_date.weekday() + 1 != weekday:
        current_date += timedelta(days=1)

    # Generate all pickup dates for the year
    while current_date.year == start_date.year:
        pickup_dates.append(current_date)
        current_date += timedelta(days=interval)

    return pickup_dates

# Streamlit app
st.title("BIRB Voss kalender")

# Search bar
search_query = st.text_input("Search by Address, EtikettID, Name, or Kunde:")

if search_query and len(search_query) >= 3:
    results = data[
        data['EtikettID'].str.contains(search_query, case=False, na=False) |
        data['Eiendomsnavn'].str.contains(search_query, case=False, na=False) |
        data['FullAddress'].str.contains(search_query, case=False, na=False) |
        data['Bemerkning'].str.contains(search_query, case=False, na=False)
    ]

    if not results.empty:
        st.write("Search Results:")

        # Consolidate and deduplicate results for display
        consolidated_results = results[['Eiendomsnavn', 'FullAddress', 'Fraksjon']].drop_duplicates()
        consolidated_results['SearchResult'] = (
            consolidated_results['Eiendomsnavn'] + " - " +
            consolidated_results['FullAddress'] + " (" +
            consolidated_results['Fraksjon'] + ")"
        )

        # Show unique results in a multiselect box
        selected_rows = st.multiselect(
            "Select one or more customers to view calendar:",
            consolidated_results.index,
            format_func=lambda x: consolidated_results.loc[x, 'SearchResult']
        )

        if selected_rows:
            # Retrieve selected entries
            selected_entries = consolidated_results.loc[selected_rows]

            # Filter the original dataset to include all routes for the selected entries
            filtered_data = data.merge(
                selected_entries,
                on=['Eiendomsnavn', 'FullAddress', 'Fraksjon'],
                how='inner'
            )

            # Highlight calendar days based on all routes for the selected entries
            calendar_data = defaultdict(list)

            # Process all routes for the selected entries
            for _, row in filtered_data.iterrows():
                route = str(row['Rutenummer'])
                weekday = int(route[3])  # Weekday: 1=Monday, 7=Sunday
                cycle_week = int(route[4])  # Cycle week
                waste_type = route[0]  # Waste type: 2/3=Paper, 6=Glass, 7=Restavfall/Matavfall

                # Map cycle week to its starting calendar week
                first_calendar_week = CYCLE_WEEKS.get(cycle_week, 1)
                first_pickup_date = date(2025, 1, 1) + timedelta(weeks=(first_calendar_week - 1))

                # Calculate all pickup dates for the route
                pickup_dates = calculate_yearly_pickup_dates(first_pickup_date, weekday)

                # Map pickup dates to the calendar
                for day in pickup_dates:
                    calendar_data[day].append(COLORS.get(waste_type, 'white'))

            # Display full year calendar
            st.write("Full Calendar for 2025:")
            for month in range(1, 13):
                st.subheader(calendar.month_name[month])
                cal = calendar.monthcalendar(2025, month)

                # Build a visual representation of the calendar
                month_grid = "<table style='border-collapse: collapse; width: 100%;'>"
                month_grid += "<tr><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th><th>Sun</th></tr>"
                for week in cal:
                    month_grid += "<tr>"
                    for day in week:
                        if day == 0:
                            # Empty day
                            month_grid += "<td style='padding: 5px;'></td>"
                        else:
                            # Determine colors for the day
                            pickup_date = date(2025, month, day)
                            colors = calendar_data.get(pickup_date, [])
                            if colors:
                                # Divide the highlight for overlapping colors
                                gradient = "linear-gradient("
                                gradient += ", ".join(
                                    f"{color} {100 / len(colors) * idx}%, {color} {100 / len(colors) * (idx + 1)}%"
                                    for idx, color in enumerate(colors)
                                )
                                gradient += ")"
                                style = f"background: {gradient}; padding: 5px; text-align: center;"
                                month_grid += f"<td style='{style}'>{day}</td>"
                            else:
                                month_grid += f"<td style='padding: 5px;'>{day}</td>"
                    month_grid += "</tr>"
                month_grid += "</table>"
                st.markdown(month_grid, unsafe_allow_html=True)

    else:
        st.write("No results found.")
else:
    st.write("Enter at least 3 characters to search.")
