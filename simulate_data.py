import os
import pandas as pd
import random
from faker import Faker

# Initialize Faker
fake = Faker()


def generate_text(word_count=100):
        words = fake.words(nb=word_count)
        return ' '.join(words).capitalize() + '.'

def simulate_data():
    # Generate simulated data
    num_entries = 100  # Number of rows
    data = {
        "output": [generate_text() for _ in range(num_entries)],
        "ground_truth": [generate_text() for _ in range(num_entries)],
    }

    # Create DataFrame
    df = pd.DataFrame(data)

    # Ensure the "data" directory exists
    os.makedirs("data", exist_ok=True)

    # Save to CSV
    file_path = "data/00-simulated_data.csv"
    df.to_csv(file_path, index=False)

    print(f"Data saved to {file_path}")