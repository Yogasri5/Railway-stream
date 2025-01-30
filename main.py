import sqlite3
import streamlit as st

# Establish connection to the SQLite database
conn = sqlite3.connect('railway.db')
c = conn.cursor()

# Function to create necessary tables in the database
def create_db():
    # Creating users, employees, and trains table if not exists
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT , password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS employees (employee_id TEXT , password TEXT , designation TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_number TEXT , train_name TEXT, departure_date TEXT, start_destination TEXT , end_destination TEXT)")

# Function to add a new train and seat table for it
def add_train(train_number, train_name, departure_date, start_destination, end_destination):
    # Insert the new train details into the trains table
    c.execute("""
        INSERT INTO trains (train_number, train_name, departure_date, start_destination, end_destination)
        VALUES (?, ?, ?, ?, ?)
    """, (train_number, train_name, departure_date, start_destination, end_destination))
    
    # Commit the transaction to save the new train
    conn.commit()
    
    # Create the seat table for the new train
    create_seat_table(train_number)
    st.success(f"Train {train_name} added successfully!")

# Function to create the seat table for a given train
def create_seat_table(train_number):
    c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_number} "
              "(seat_number INTEGER PRIMARY KEY, "
              "seat_type TEXT, "
              "booked INTEGER, "
              "passenger_name TEXT, "
              "passenger_age INTEGER, "
              "passenger_gender TEXT)")
    
    # Adding 50 seats for the new train
    for i in range(1, 51):
        seat_type = categorize_seat(i)
        c.execute(f"INSERT INTO seats_{train_number} (seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) "
                  "VALUES (?, ?, 0, '', '', '')", (i, seat_type))

    conn.commit()

# Function to categorize seats based on seat number
def categorize_seat(seat_number):
    if seat_number % 10 in [0, 4, 5, 9]:
        return "Window"
    elif seat_number % 10 in [2, 3, 6, 7]:
        return "Aisle"
    else:
        return "Middle"

# Function to allocate the next available seat for booking
def allocate_next_available_seat(train_number, seat_type):
    # Check if the seat table exists for the given train
    c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='seats_{train_number}'")
    table_exists = c.fetchone()
    
    if not table_exists:
        create_seat_table(train_number)  # Create seat table if it doesn't exist

    # Proceed with seat allocation
    seat_query = c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 AND seat_type=? ORDER BY seat_number ASC", (seat_type,))
    result = seat_query.fetchall()
    
    if result:
        return result[0][0]
    return None

# Function to book tickets for a train
def book_tickets(train_number, passenger_name, passenger_gender, passenger_age, seat_type):
    train_query = c.execute("SELECT * FROM trains WHERE train_number=?", (train_number,))
    train_data = train_query.fetchone()

    if train_data:
        seat_number = allocate_next_available_seat(train_number, seat_type)

        if seat_number:
            c.execute(f"UPDATE seats_{train_number} SET booked=1, seat_type=?, passenger_name=?, passenger_age=?, passenger_gender=? WHERE seat_number=?",
                      (seat_type, passenger_name, passenger_age, passenger_gender, seat_number))
            conn.commit()

            st.success(f"Ticket booked successfully for seat {seat_number}!")
        else:
            st.warning("No available seats of the selected type.")

# Function to cancel booked tickets
def cancel_tickets(train_number, seat_number):
    train_query = c.execute("SELECT * FROM trains WHERE train_number=?", (train_number,))
    train_data = train_query.fetchone()

    if train_data:
        c.execute(f"UPDATE seats_{train_number} SET booked=0, passenger_name='', passenger_age='', passenger_gender='' WHERE seat_number=?",
                  (seat_number,))
        conn.commit()
        
        st.success(f"Ticket for seat {seat_number} canceled successfully!")

# Function to delete a train from the system
def delete_train(train_number):
    train_query = c.execute("SELECT * FROM trains WHERE train_number=?", (train_number,))
    train_data = train_query.fetchone()

    if train_data:
        c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
        c.execute("DELETE FROM trains WHERE train_number=?", (train_number,))
        conn.commit()

        st.success(f"Train {train_number} and its seat information deleted successfully!")

# Function to view all the seats of a specific train
def view_seats(train_number):
    train_query = c.execute("SELECT * FROM trains WHERE train_number=?", (train_number,))
    train_data = train_query.fetchone()

    if train_data:
        seat_query = c.execute(f"SELECT seat_number, seat_type, passenger_name, passenger_age, passenger_gender, booked FROM seats_{train_number} ORDER BY seat_number ASC")
        result = seat_query.fetchall()

        if result:
            st.dataframe(result)
        else:
            st.warning(f"No seats data found for train {train_number}.")
    else:
        st.warning(f"Train {train_number} not found.")

# Streamlit UI for train management
def train_functions():
    st.title("Train Management System")

    functions = st.sidebar.selectbox("Select a function", ["Add train", "View trains", "Search train", "Delete train", "Book ticket", "Cancel ticket", "View seats"])

    if functions == "Add train":
        st.header("Add New Train")
        with st.form(key='new_train_form'):
            train_number = st.text_input("Train number")
            train_name = st.text_input("Train name")
            departure_date = st.text_input("Departure date")
            start_destination = st.text_input("Start destination")
            end_destination = st.text_input("End destination")
            submit_button = st.form_submit_button("Add train")

        if submit_button and train_number and train_name and start_destination and end_destination:
            add_train(train_number, train_name, departure_date, start_destination, end_destination)

    elif functions == "View trains":
        st.title("View All Trains")
        train_query = c.execute("SELECT * FROM trains")
        trains = train_query.fetchall()
        st.dataframe(trains)

    elif functions == "Book ticket":
        st.title("Book Ticket")
        train_number = st.text_input("Train number to book ticket")
        seat_type = st.selectbox("Select seat type", ["Aisle", "Middle", "Window"])
        passenger_name = st.text_input("Passenger Name")
        passenger_age = st.number_input("Passenger Age", min_value=1)
        passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female"])

        if st.button("Book Ticket"):
            if train_number and passenger_name and passenger_gender and passenger_age:
                book_tickets(train_number, passenger_name, passenger_gender, passenger_age, seat_type)

    elif functions == "Cancel ticket":
        st.title("Cancel Ticket")
        train_number = st.text_input("Train number to cancel ticket")
        seat_number = st.number_input("Seat number to cancel", min_value=1)

        if st.button("Cancel Ticket"):
            if train_number and seat_number:
                cancel_tickets(train_number, seat_number)

    elif functions == "View seats":
        st.title("View Seats")
        train_number = st.text_input("Enter train number to view seats")

        if st.button("View Seats"):
            if train_number:
                view_seats(train_number)

    elif functions == "Delete train":
        st.title("Delete Train")
        train_number = st.text_input("Enter train number to delete")

        if st.button("Delete Train"):
            if train_number:
                delete_train(train_number)

# Call the train management functions to run the app
train_functions()
