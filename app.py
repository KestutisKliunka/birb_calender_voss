import pandas as pd
import calendar
from flask import Flask, request, jsonify, render_template

# Load the dataset
data = pd.read_csv('BIRB_Voss_alleruter.csv', sep=None, engine='python', encoding='latin1')

# Initialize Flask app
app = Flask(__name__)

# Function to process dataset and get calendar highlighting
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

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').lower()
    search_type = request.args.get('type', 'etikettid').lower()
    
    if len(query) < 3:
        return jsonify([])

    if search_type == 'etikettid':
        results = data[data['EtikettID'].astype(str).str.contains(query, case=False)]
    elif search_type == 'name':
        results = data[data['Eiendomsnavn'].str.contains(query, case=False, na=False)]
    elif search_type == 'address':
        results = data[data['Gatenavn'].str.contains(query, case=False, na=False)]
    elif search_type == 'kunde':
        results = data[data['Bemerkning'].str.contains(query, case=False, na=False)]
    else:
        results = pd.DataFrame()

    return jsonify(results[['EtikettID', 'Eiendomsnavn', 'Gatenavn', 'Bemerkning']].to_dict(orient='records'))

@app.route('/calendar', methods=['POST'])
def generate_calendar():
    selected_route = request.json.get('route')
    
    if not selected_route:
        return jsonify({'error': 'No route selected'}), 400

    route_data = data[data['Rutenummer'] == int(selected_route)]

    calendar_data = {}
    for _, row in route_data.iterrows():
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

    return jsonify(calendar_data)

@app.route('/view', methods=['GET'])
def view_calendar():
    return render_template('calendar.html')

if __name__ == '__main__':
    app.run(debug=True)
