import pandas as pd
import streamlit as st
import calendar
from collections import defaultdict

# Load the dataset
data = pd.read_csv('BIRB_Voss_alleruter.csv', sep=None, engine='python', encoding='latin1')

# Define constants
CYCLE_WEEKS = {
    1: [2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50],
    2: [3, 7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 47, 51],
    3: [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52],
    4: [1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49]
}

COLORS = {
    '2': 'blue',  # Paper/plastic
    '3': 'blue',
    '6': 'gray',  # Glass/metal
    '7': 'green'  # Restavfall/matavfall
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

        # Remove duplicates from selection list but keep all routes for calendar highlighting
        results['Selection'] = (
            results['FullAddress'] + " - " + results['Eiendomsnavn'] + " (" + results['Fraksjon'] + ")"
        )
        unique_results = results.drop_duplicates(subset=['FullAddress', 'Eiendomsnavn', 'Fraksjon'])

        selected_rows = st.multiselect(
            "Select one or more to view calendar:",
            unique_results.index,
            format_func=lambda x: unique_results.loc[x, 'Selection']
        )

        if selected_rows:
            selected_entries = results[results.index.isin(selected_rows)]

            # Highlight calendar days based on the selected routes
            calendar_data = defaultdict(lambda: defaultdict(list))

            for _, row in selected_entries.iterrows():
                route = str(row['Rutenummer'])
                week_day = int(route[3])  # Weekday: 1=Mon, 2=Tue, ..., 7=Sun
                cycle_week = int(route[4])  # Cycle week
                waste_type = route[0]  # Waste type: 2/3=Paper, 6=Glass, 7=Restavfall

                # Skip weekends
                if week_day not in [6, 7]:
                    color = COLORS.get(waste_type, 'white')
                    weeks = CYCLE_WEEKS.get(cycle_week, [])

                    for week in weeks:
                        calendar_data[week][week_day].append(color)

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
                    for i, day in enumerate(week):
                        if day == 0:
                            # Empty day
                            month_grid += "<td style='padding: 5px;'></td>"
                        else:
                            # Determine colors for the day
                            colors = calendar_data.get(day, {}).get(i + 1, [])
                            if colors:
                                # Divide the highlight for overlapping colors
                                gradient = "linear-gradient("
                                gradient += ", ".join(f"{color} {50 * idx}%, {color} {50 * (idx + 1)}%" for idx, color in enumerate(colors))
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
