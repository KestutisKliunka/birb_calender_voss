import pandas as pd
import streamlit as st
import calendar
from collections import defaultdict
from datetime import timedelta, date

# Load the dataset
data = pd.read_csv('BIRB_Voss_alleruter.csv', sep=None, engine='python', encoding='latin1')

# Define constants
COLORS = {
    '2': 'blue',  # Paper/plastic
    '3': 'blue',
    '6': 'gray',  # Glass/metal
    '7': 'green'  # Combined Restavfall/Matavfall
}

# Ensure all relevant fields are strings and handle NaN values
data['Gatenavn'] = data['Gatenavn'].fillna('').astype(str)
data['Husnummer'] = data['Husnummer'].fillna('').astype(str)
data['FullAddress'] = (data['Gatenavn'] + ' ' + data['Husnummer']).str.strip()
data['EtikettID'] = data['EtikettID'].astype(str).str.replace(',', '')
data['Rutenummer'] = data['Rutenummer'].astype(str).str.replace(',', '')
data['Eiendomsnavn'] = data['Eiendomsnavn'].fillna('').astype(str)
data['Fraksjon'] = data['Fraksjon'].fillna('').astype(str)
data['Bemerkning'] = data['Bemerkning'].fillna('').astype(str)
data['Frekvens'] = data['Frekvens'].fillna(4)  # Default to 4 weeks if missing

# Helper function to calculate pickup days
def calculate_pickup_days(start_date, weekday, frequency, year=2025):
    """
    Calculate all pickup dates in a year based on the start date, weekday, and frequency.

    Args:
        start_date (datetime.date): The first date to start calculations from.
        weekday (int): Day of the week (1=Mon, 2=Tue, ..., 7=Sun).
        frequency (float): Pickup frequency (1=weekly, 2=every 2 weeks, etc.).
        year (int): Year to calculate for.

    Returns:
        list: List of all pickup dates in the given year.
    """
    current_date = start_date
    days = []
    delta = timedelta(days=int(7 / frequency))  # Frequency determines the gap in days

    # Ensure we start on the correct weekday
    while current_date.weekday() + 1 != weekday:
        current_date += timedelta(days=1)

    # Generate all dates for the year
    while current_date.year == year:
        days.append(current_date)
        current_date += delta

    return days

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
                weekday = int(route[3])  # Weekday: 1=Mon, 2=Tue, ..., 7=Sun
                frequency = float(row['Frekvens'])  # Pickup frequency
                waste_type = route[0]  # Waste type: 2/3=Paper, 6=Glass, 7=Restavfall/Matavfall

                # Combine Restavfall and Matavfall for routes starting with 7
                color = COLORS.get(waste_type, 'white')

                # Calculate all pickup days for the route
                pickup_days = calculate_pickup_days(date(2025, 1, 1), weekday, frequency)

                # Map pickup days to the calendar
                for day in pickup_days:
                    calendar_data[day].append(color)

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
