# Waste Calendar 2025

This project provides a 2025 calendar tool for waste collection based on routes and waste types. It supports flexible search options and visualizes collection days on the calendar.

## Features
- Search by `EtikettID`, name, address, or customer.
- Highlight days on the calendar based on waste type and route logic.
- Supports Norwegian characters.

## Dataset Rules
1. **Route Number Interpretation**:
   - First digit:
     - `2` or `3`: Paper/Plastic (Blue)
     - `6`: Glass/Metal (Gray)
     - `7`: Restavfall/Matavfall (Green)
   - Fourth digit: Weekday (1=Monday, 2=Tuesday, etc.).
   - Fifth digit: Cycle week (1–4).

2. **Cycle Weeks**:
   - Cycle 1: Calendar weeks [2, 6, 10, 14, ...].
   - Cycle 2: Calendar weeks [3, 7, 11, 15, ...].
   - Cycle 3: Calendar weeks [4, 8, 12, 16, ...].
   - Cycle 4: Calendar weeks [1, 5, 9, 13, ...].

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/waste-calendar-2025.git
   cd waste-calendar-2025
