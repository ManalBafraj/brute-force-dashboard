

# %% to doing run for this file 
#streamlit run app.py


# %%
# Brute Force Attack Dashboard using Streamlit

# %% Imports and Setup
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import ast

# Page config
st.set_page_config(page_title="Brute Force Dashboard", layout="wide")
st.title("🔐 Brute Force Attack Dashboard")
st.markdown("Welcome! This project analyzes brute force login attempts and displays interactive statistics and smart alerts.")

# %% 1. Upload or Load Default Data
uploaded_file = st.sidebar.file_uploader("📤 Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.sidebar.success("✅ File uploaded successfully!")
else:
    df = pd.read_excel("cleaned_login_data.xlsx")
    st.sidebar.info("📁 Using default data")

# Timestamp processing
if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
df["date_only"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["date"] = df["timestamp"].dt.date

# %% 2. Sidebar Filters
st.sidebar.header("🔽 Filter Data")
users = df['username'].dropna().unique().tolist()
selected_user = st.sidebar.selectbox("👤 Select User", options=["All"] + sorted(users))
dates = df['date_only'].dropna().unique()
selected_date = st.sidebar.selectbox("📅 Select Date", options=["All"] + sorted(dates))

filtered_df = df.copy()
if selected_user != "All":
    filtered_df = filtered_df[filtered_df["username"] == selected_user]
if selected_date != "All":
    filtered_df = filtered_df[filtered_df["date_only"] == selected_date]

# %% 3. Charts
st.header("📊 Basic Charts")
col1, col2 = st.columns(2)

# Top IPs
with col1:
    st.subheader("Top IP Addresses")
    top_ips = filtered_df['foreign_ip'].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x=top_ips.index, y=top_ips.values, ax=ax, palette="rocket")
    ax.set_xlabel("IP Address")
    ax.set_ylabel("Attempts")
    ax.set_title("Top 10 IP Addresses")
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig)
    st.markdown("**Most Frequent IP Addresses**")

# Top Passwords
with col2:
    st.subheader("Top Passwords Used")
    try:
        exploded_passwords = []
        for pw in filtered_df['passwords'].dropna():
            if isinstance(pw, str) and pw.startswith("[") and pw.endswith("]"):
                try:
                    exploded_passwords.extend(ast.literal_eval(pw))
                except:
                    exploded_passwords.append(pw)
            else:
                exploded_passwords.append(pw)

        top_passwords = pd.Series(exploded_passwords).value_counts().head(10)
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        sns.barplot(x=top_passwords.index, y=top_passwords.values, ax=ax2, palette="flare")
        ax2.set_xlabel("Password")
        ax2.set_ylabel("Count")
        ax2.set_title("Top 10 Most Frequent Passwords")
        ax2.tick_params(axis='x', rotation=45)
        st.pyplot(fig2)
        st.markdown("**Most Commonly Used Passwords**")

    except Exception as e:
        st.warning(f"⚠️ Couldn't plot passwords: {e}")

# %% 4. Data Preview and Export
st.header("📄 Login Attempts Data")
st.subheader("📋 Preview of the Data")
st.dataframe(filtered_df.head(10))

# Download
excel_buffer = BytesIO()
filtered_df.to_excel(excel_buffer, index=False)
excel_buffer.seek(0)

st.download_button(
    label="⬇️ Download Filtered Data as Excel",
    data=excel_buffer,
    file_name="filtered_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# %% 5. Quick Stats
st.subheader("📈 Quick Statistics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🔢 Total Attempts", len(filtered_df))

with col2:
    if not filtered_df.empty:
        top_user = filtered_df['username'].value_counts().idxmax()
        st.metric("👤 Most Targeted User", top_user)

with col3:
    if 'country' in filtered_df.columns and not filtered_df['country'].isnull().all():
        top_country = filtered_df['country'].value_counts().idxmax()
        st.metric("🌍 Top Country", top_country)
    else:
        st.warning("⚠️ 'country' column is not available in the data.")

# %% 6. Suspicious IPs
st.header("🚨 Suspicious Activity Detection")
threshold = st.slider("Set attempt threshold", min_value=10, max_value=200, value=50, step=10)

ip_counts = filtered_df['foreign_ip'].value_counts()
suspicious_ips = ip_counts[ip_counts > threshold]

st.subheader("🔥 IPs with high number of login attempts")
st.write(f"Found {len(suspicious_ips)} suspicious IPs (>{threshold} attempts)")
st.dataframe(suspicious_ips)

# Failed attempts
if 'status' in filtered_df.columns:
    failed_attempts = filtered_df[filtered_df['status'].str.lower() == 'failed']
    st.subheader("❌ Failed Login Attempts")
    st.write(f"Total failed attempts: {len(failed_attempts)}")
    st.dataframe(failed_attempts.head(10))
else:
    st.warning("⚠️ 'status' column not found in the dataset.")

# %% 7. Weak Passwords
st.header("🔐 Weak Password Usage")
try:
    total_attempts = len(filtered_df)
    weak_attempts = filtered_df[filtered_df['used_weak_password'] == True]
    weak_count = len(weak_attempts)
    weak_percentage = (weak_count / total_attempts) * 100 if total_attempts > 0 else 0

    st.metric("🔓 Weak Password Attempts", weak_count)
    st.metric("📊 Percentage", f"{weak_percentage:.2f}%")

    st.subheader("🧾 Sample of Weak Password Attempts")
    st.dataframe(weak_attempts[['username', 'passwords', 'foreign_ip', 'timestamp']].head(10))
except Exception as e:
    st.error(f"Error analyzing weak passwords: {e}")

# %% 8. Time-based Activity
st.header("⏰ Time-based Activity Analysis")
try:
    # Hourly
    st.subheader("🕒 Login Attempts by Hour")
    hour_counts = filtered_df['hour'].value_counts().sort_index()
    fig, ax = plt.subplots()
    sns.barplot(x=hour_counts.index, y=hour_counts.values, palette="magma", ax=ax)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Number of Attempts")
    ax.set_title("Login Attempts per Hour")
    st.pyplot(fig)

    # Daily
    if 'date' in filtered_df.columns:
        st.subheader("📅 Login Attempts by Day")
        filtered_df['day_of_week'] = pd.to_datetime(filtered_df['date']).dt.day_name()
        day_counts = filtered_df['day_of_week'].value_counts()
        fig2, ax2 = plt.subplots()
        sns.barplot(x=day_counts.index, y=day_counts.values, palette="cool", ax=ax2)
        ax2.set_xlabel("Day of the Week")
        ax2.set_ylabel("Number of Attempts")
        ax2.set_title("Login Attempts per Day")
        st.pyplot(fig2)

except Exception as e:
    st.error(f"Error in time-based analysis: {e}")
