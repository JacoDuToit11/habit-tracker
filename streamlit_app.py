from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

import streamlit as st
import pandas as pd
import os
from datetime import date

# Configuration
HABITS_FILE = 'habits.csv'
# Load password from environment variable
PASSWORD = os.getenv("HABIT_TRACKER_PASSWORD")

# Check if password environment variable is set
if not PASSWORD:
    st.error("Password environment variable (HABIT_TRACKER_PASSWORD) not set.")
    st.stop() # Stop the app if password is not configured

# --- Authentication ---
def check_password():
    """Returns `True` if the user had the correct password."""

    if "password_entered" not in st.session_state:
        # First run, show input for password.
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        return False
    elif not st.session_state["password_entered"]:
        # Password not correct, show input + error.
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

def password_entered():
    """Checks whether a password entered by the user is correct."""
    if st.session_state["password"] == PASSWORD:
        st.session_state["password_entered"] = True
        del st.session_state["password"]  # Don't store password.
    else:
        st.session_state["password_entered"] = False

# --- Data Handling ---
def load_habit_data():
    """Loads habit data from CSV, creates file if it doesn't exist."""
    if not os.path.exists(HABITS_FILE):
        # Create empty DataFrame with just a Date column if file is new
        df = pd.DataFrame(columns=['Date'])
        df.to_csv(HABITS_FILE, index=False)
        return df
    else:
        try:
            return pd.read_csv(HABITS_FILE, parse_dates=['Date'])
        except pd.errors.EmptyDataError:
             # Handle case where file exists but is empty
            df = pd.DataFrame(columns=['Date'])
            df.to_csv(HABITS_FILE, index=False)
            return df
        except Exception as e:
            st.error(f"Error loading habit data: {e}")
            # Return an empty DataFrame on error to prevent app crash
            return pd.DataFrame(columns=['Date'])


def save_habit_data(df):
    """Saves habit data to CSV."""
    try:
        df.to_csv(HABITS_FILE, index=False)
    except Exception as e:
        st.error(f"Error saving habit data: {e}")

def add_habit(habit_name, df):
    """Adds a new habit column to the DataFrame."""
    if habit_name and habit_name not in df.columns:
        df[habit_name] = False # Default new habit to False for existing dates
        st.success(f"Habit '{habit_name}' added!")
        return df
    elif habit_name in df.columns:
        st.warning(f"Habit '{habit_name}' already exists.")
        return df
    else:
        st.error("Habit name cannot be empty.")
        return df

def ensure_today_exists(df):
    """Checks if today's date exists, adds a row if not."""
    today_str = date.today().strftime('%Y-%m-%d')
    # Convert 'Date' column to string for comparison if it's datetime objects
    if pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

    if today_str not in df['Date'].values:
        new_row = {'Date': today_str}
        # Initialize habit columns to False for the new day
        for col in df.columns:
            if col != 'Date':
                new_row[col] = False
        # Use pandas.concat instead of append
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    # Convert Date column back to datetime if needed, or keep as string
    # df['Date'] = pd.to_datetime(df['Date']) # Optional: convert back
    return df


# --- App Logic ---
st.set_page_config(page_title="Habit Tracker", layout="wide")

if check_password():
    st.title("✅ Habit Tracker")

    # Load data
    habits_df = load_habit_data()

    # Ensure today's date row exists
    habits_df = ensure_today_exists(habits_df)

    # Add new habit section
    st.sidebar.header("Manage Habits")
    new_habit_name = st.sidebar.text_input("Add New Habit")
    if st.sidebar.button("Add Habit"):
        habits_df = add_habit(new_habit_name, habits_df)
        save_habit_data(habits_df) # Save immediately after adding

    # Display Habits for Today
    st.header(f"Today's Habits ({date.today().strftime('%Y-%m-%d')})")

    today_str = date.today().strftime('%Y-%m-%d')
    today_index = habits_df[habits_df['Date'] == today_str].index

    if not today_index.empty:
        today_index = today_index[0] # Get the first index if multiple (shouldn't happen)
        habit_cols = [col for col in habits_df.columns if col != 'Date']

        if not habit_cols:
            st.info("No habits added yet. Add some using the sidebar!")
        else:
            cols = st.columns(len(habit_cols))
            updated = False
            for i, habit in enumerate(habit_cols):
                with cols[i]:
                    # Ensure the value fetched is explicitly boolean for checkbox
                    current_value = bool(habits_df.loc[today_index, habit])
                    checked = st.checkbox(habit, value=current_value, key=f"{habit}_{today_str}")
                    if checked != current_value:
                        habits_df.loc[today_index, habit] = checked
                        updated = True

            if updated:
                save_habit_data(habits_df)
                # Optional: Rerun to reflect immediate save feedback, though usually not necessary
                # st.rerun()
    else:
        st.error("Could not find or create today's row. Please check "+ HABITS_FILE)


    # Display Raw Data (Optional)
    st.subheader("All Habit Data")
    st.dataframe(habits_df)
