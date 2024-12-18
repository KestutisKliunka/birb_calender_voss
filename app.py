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

CYCLE_TO_CALENDAR_WEEKS = {
    1: [2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50],
    2: [3, 7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 47, 51],
    3: [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52],
    4: [1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49]
}

# Helper function to calculate pickup dates
def calculate_pickup_dates(cycle_week, weekday, year=2025):
    """
    Calculate all pickup dates in a year for a specific cycle week and weekday.

    Args:
        cycle_week (int): Cycle week (1, 2, 3, or 4).
        weekday (int): Day of the week (1=Monday, ..., 7=Sunday).
        year (int): Year to calculate for.

    Returns:
        list: List of all pickup dates for the year.
    """
    calendar_weeks = CYCLE_TO_CALENDAR_WEEKS.get(cycle_week, [])
    pickup_dates = []

    for calendar_week in calendar_weeks:
        # Calculate the first day of the calendar week
        first_day_of_week = date.fromisocalendar(year, calendar_week, 1)
        
        # Adjust to the correct weekday
        pickup_date = first_day_of_week + timedelta(days=(weekday - 1))
        pickup_dates.append(pickup_date)

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

                # Special case: If the first digit is 8, mark the day as combined Paper/Glass (blue+gray)
                if route[0] == '8':
                    weekday = int(route[3])  # Weekday: 1=Monday, ..., 7=Sunday
                    cycle_week = int(route[4])  # Cycle week
                    pickup_dates = calculate_pickup_dates(cycle_week, weekday)
                    for day in pickup_dates:
                        calendar_data[day].extend(['blue', 'gray'])
                    continue

                weekday = int(route[3])  # Weekday: 1=Monday, ..., 7=Sunday
                cycle_week = int(route[4])  # Cycle week
                waste_type = route[0]  # Waste type: 2/3=Paper, 6=Glass, 7=Restavfall/Matavfall

                # Calculate all pickup dates for the route
                pickup_dates = calculate_pickup_dates(cycle_week, weekday)

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
