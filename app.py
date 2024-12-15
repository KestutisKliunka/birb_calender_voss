import pandas as pd
import streamlit as st
import calendar

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

# Streamlit app
st.title("BIRB Voss kalender")

# Search bar
search_query = st.text_input("Search by EtikettID, Name, Address, or Kunde:")

if search_query and len(search_query) >= 3:
    results = data[
        data['EtikettID'].astype(str).str.contains(search_query, case=False, na=False) |
        data['Eiendomsnavn'].astype(str).str.contains(search_query, case=False, na=False) |
        data['Gatenavn'].astype(str).str.contains(search_query, case=False, na=False) |
        data['Bemerkning'].astype(str).str.contains(search_query, case=False, na=False)
    ]

    if not results.empty:
        st.write("Search Results:")
        results['EtikettID'] = results['EtikettID'].astype(str).str.replace(',', '')
        results['Rutenummer'] = results['Rutenummer'].astype(str).str.replace(',', '')
        st.dataframe(results[['EtikettID', 'Eiendomsnavn', 'Gatenavn', 'Bemerkning', 'Rutenummer']])

        # Highlight calendar days based on routes
        calendar_data = {}
        for _, row in results.iterrows():
            route = str(row['Rutenummer'])
            week_day = int(route[3])
            cycle_week = int(route[4])
            waste_type = route[0]

            color = COLORS.get(waste_type, 'white')
            weeks = CYCLE_WEEKS.get(cycle_week, [])

            for week in weeks:
                if week not in calendar_data:
                    calendar_data[week] = {}
                calendar_data[week][week_day] = color

        # Display calendar
        st.write("Calendar for 2025:")
        for month in range(1, 13):
            st.subheader(calendar.month_name[month])
            cal = calendar.monthcalendar(2025, month)
            for week in cal:
                formatted_week = []
                for day in week:
                    if day == 0:
                        formatted_week.append("   ")  # Empty space for non-day cells
                    else:
                        # Highlight day if it matches pickup days
                        week_number = (day - 1) // 7 + 1
                        color = calendar_data.get(week_number, {}).get(week.index(day), 'white')
                        formatted_week.append(f":{color}_circle: {day}")
                st.write(" | ".join(formatted_week))
    else:
        st.write("No results found.")
else:
    st.write("Enter at least 3 characters to search.")
