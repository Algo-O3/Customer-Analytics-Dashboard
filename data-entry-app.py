"""
Customer Data Entry Application
File: customer_data_entry.py
This application allows users to input customer data and store it in MySQL database
"""

import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import datetime
import re


from db_config import DB_CONFIG


st.set_page_config(
    page_title="Customer Data Entry",
    page_icon="📝",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
    }
    .success-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        color: #155724;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        color: #721c24;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def create_connection():
    """Create a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone format"""
    pattern = r'^[\d\-\+\(\)\s]{10,20}$'
    return re.match(pattern, phone) is not None

def insert_customer(customer_data):
    """Insert customer data into database"""
    connection = create_connection()
    if connection is None:
        return False, "Failed to connect to database"
    
    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO customers (name, email, phone, purchase_amount, 
                             product_category, region, purchase_date, customer_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, customer_data)
        connection.commit()
        cursor.close()
        connection.close()
        return True, "Customer data inserted successfully!"
    except Error as e:
        return False, f"Error inserting data: {e}"

def update_customer(customer_id, customer_data):
    """Update existing customer data"""
    connection = create_connection()
    if connection is None:
        return False, "Failed to connect to database"
    
    try:
        cursor = connection.cursor()
        query = """
        UPDATE customers 
        SET name=%s, email=%s, phone=%s, purchase_amount=%s, 
            product_category=%s, region=%s, purchase_date=%s, customer_type=%s
        WHERE customer_id=%s
        """
        cursor.execute(query, customer_data + (customer_id,))
        connection.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        connection.close()
        
        if rows_affected > 0:
            return True, "Customer data updated successfully!"
        else:
            return False, "No customer found with that ID"
    except Error as e:
        return False, f"Error updating data: {e}"

def get_recent_entries(limit=10):
    """Fetch recent customer entries"""
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        query = f"""
        SELECT customer_id, name, email, purchase_amount, 
               product_category, region, purchase_date, customer_type
        FROM customers
        ORDER BY created_at DESC
        LIMIT {limit}
        """
        df = pd.read_sql(query, connection)
        connection.close()
        return df
    except Error as e:
        st.error(f"Error fetching data: {e}")
        return None

# Main App
def main():
    st.title("📝 Customer Data Entry System")
    st.markdown("---")
    
    # Sidebar for operation selection
    operation = st.sidebar.radio(
        "Select Operation",
        ["Add New Customer", "Update Customer", "View Recent Entries"]
    )
    
    if operation == "Add New Customer":
        st.header("Add New Customer")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Customer Name*", placeholder="John Doe")
            email = st.text_input("Email*", placeholder="john.doe@example.com")
            phone = st.text_input("Phone", placeholder="555-0123")
            purchase_amount = st.number_input("Purchase Amount*", min_value=0.0, step=0.01, format="%.2f")
        
        with col2:
            product_category = st.selectbox(
                "Product Category*",
                ["Electronics", "Clothing", "Home & Garden", "Books", "Sports", "Toys", "Food & Beverage", "Other"]
            )
            region = st.selectbox(
                "Region*",
                ["North", "South", "East", "West", "Central"]
            )
            purchase_date = st.date_input("Purchase Date*", value=datetime.now())
            customer_type = st.selectbox("Customer Type*", ["New", "Existing"])
        
        st.markdown("---")
        
        if st.button("💾 Submit Customer Data"):
            # Validation
            errors = []
            
            if not name:
                errors.append("Name is required")
            if not email:
                errors.append("Email is required")
            elif not validate_email(email):
                errors.append("Invalid email format")
            if phone and not validate_phone(phone):
                errors.append("Invalid phone format")
            if purchase_amount <= 0:
                errors.append("Purchase amount must be greater than 0")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                customer_data = (
                    name, email, phone, purchase_amount,
                    product_category, region, purchase_date, customer_type
                )
                
                success, message = insert_customer(customer_data)
                
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")
    
    elif operation == "Update Customer":
        st.header("Update Customer Information")
        
        customer_id = st.number_input("Customer ID*", min_value=1, step=1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Customer Name*", placeholder="John Doe")
            email = st.text_input("Email*", placeholder="john.doe@example.com")
            phone = st.text_input("Phone", placeholder="555-0123")
            purchase_amount = st.number_input("Purchase Amount*", min_value=0.0, step=0.01, format="%.2f")
        
        with col2:
            product_category = st.selectbox(
                "Product Category*",
                ["Electronics", "Clothing", "Home & Garden", "Books", "Sports", "Toys", "Food & Beverage", "Other"]
            )
            region = st.selectbox(
                "Region*",
                ["North", "South", "East", "West", "Central"]
            )
            purchase_date = st.date_input("Purchase Date*", value=datetime.now())
            customer_type = st.selectbox("Customer Type*", ["New", "Existing"])
        
        st.markdown("---")
        
        if st.button("🔄 Update Customer Data"):
            # Validation
            errors = []
            
            if not name:
                errors.append("Name is required")
            if not email:
                errors.append("Email is required")
            elif not validate_email(email):
                errors.append("Invalid email format")
            if phone and not validate_phone(phone):
                errors.append("Invalid phone format")
            if purchase_amount <= 0:
                errors.append("Purchase amount must be greater than 0")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                customer_data = (
                    name, email, phone, purchase_amount,
                    product_category, region, purchase_date, customer_type
                )
                
                success, message = update_customer(customer_id, customer_data)
                
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
    
    else:  # View Recent Entries
        st.header("📊 Recent Customer Entries")
        
        limit = st.slider("Number of records to display", 5, 50, 10)
        
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        df = get_recent_entries(limit)
        
        if df is not None and not df.empty:
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            # Summary statistics
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                st.metric("Total Revenue", f"${df['purchase_amount'].sum():,.2f}")
            with col3:
                st.metric("Avg Purchase", f"${df['purchase_amount'].mean():,.2f}")
            with col4:
                st.metric("New Customers", len(df[df['customer_type'] == 'New']))
        else:
            st.info("No customer data available")

if __name__ == "__main__":
    main()
