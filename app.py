import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import joblib
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -----------------------------
# Authentication Setup
# -----------------------------
users = {
    "admin": "admin123",
    "user": "user123"
}

st.set_page_config(layout="wide")

SESSION_TIMEOUT = 1800  # 30 minutes

def login():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if username in users and users[username] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.last_active = time.time()
            st.rerun()
        else:
            st.error("Invalid username or password")

def logout_button():
    st.markdown(
        """
        <style>
        .logout-container {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            margin-bottom: 15px;
        }
        .username-text {
            margin-right: 15px;
            font-size: 18px;
            color: #ddd;
            font-weight: 600;
        }
        .logout-btn {
            font-size: 25px;
            font-weight: bold;
            background-color: #f63366;
            color: white;
            padding: 10px 25px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            width: 120px;
            user-select: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns([10, 1])
    with cols[0]:
        st.markdown(f'<div class="username-text">👤 {st.session_state.get("username", "User")}</div>', unsafe_allow_html=True)
    # with cols[1]:
    #     if st.button("Logout", key="logout_btn"):
    #         st.session_state.authenticated = False
    #         st.session_state.username = ""
    #         st.session_state.last_active = 0
    #         st.rerun()


def check_session_timeout():
    if "last_active" in st.session_state:
        elapsed = time.time() - st.session_state.last_active
        if elapsed > SESSION_TIMEOUT:
            st.warning("Session expired due to inactivity. Please login again.")
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.last_active = 0
            st.rerun()
    st.session_state.last_active = time.time()

# -----------------------------
# Email sending function
# -----------------------------
def send_email_gmail(sender_email, app_password, receiver_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        st.success(f"Email sent successfully to {receiver_email}")
    except Exception as e:
        st.error(f"Failed to send email to {receiver_email}: {e}")

# -----------------------------
# Helper: satisfaction emoji
# -----------------------------
def visualize_multi_punch(df, column, title_prefix="", compact=False):
    from collections import Counter
    import squarify

    series = df[column].dropna().str.split(',')
    flat_list = [item.strip() for sublist in series for item in sublist if item.strip()]
    counts = Counter(flat_list)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"{title_prefix} - Frequency")
        size = (4, 3) if compact else (6, 4)
        fig1, ax1 = plt.subplots(figsize=size)
        fig1.patch.set_facecolor('#0e1117')
        ax1.set_facecolor('#0e1117')
        ax1.bar(counts.keys(), counts.values(), color='#1f77b4')
        ax1.tick_params(colors='white')
        ax1.spines['bottom'].set_color('white')
        ax1.spines['left'].set_color('white')
        plt.xticks(rotation=45, ha='right', fontsize=8)
        st.pyplot(fig1)

    with col2:
        st.subheader(f"{title_prefix} - Share")
        fig2, ax2 = plt.subplots(figsize=(size[0], size[0]))
        ax2.pie(counts.values(), labels=counts.keys(), autopct='%1.1f%%', startangle=140,
                textprops={'color': 'white'})
        fig2.patch.set_facecolor('#0e1117')
        st.pyplot(fig2)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader(f"{title_prefix} - Treemap")
        fig3, ax3 = plt.subplots(figsize=(size[0], size[0]))
        sizes = list(counts.values())
        labels = [f"{k}\n{v}" for k, v in counts.items()]
        squarify.plot(sizes=sizes, label=labels, color=sns.color_palette("pastel"), alpha=.9, text_kwargs={'fontsize': 9})
        plt.axis('off')
        fig3.patch.set_facecolor('#0e1117')
        st.pyplot(fig3)

    with col4:
        st.subheader(f"{title_prefix} - Sorted Bar Chart")
        fig4, ax4 = plt.subplots(figsize=(size[0]+1, size[1]))
        sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
        sns.barplot(x=list(sorted_counts.values()), y=list(sorted_counts.keys()), ax=ax4, palette="Blues_d")
        ax4.set_facecolor('#0e1117')
        fig4.patch.set_facecolor('#0e1117')
        ax4.tick_params(colors='white')
        ax4.set_title(f"{title_prefix} - Sorted Frequencies", color='white')
        st.pyplot(fig4)


def satisfaction_emoji(val):
    return "🟢 😊" if val == 1 else "🔴 😞"

# -----------------------------
# Main Streamlit app
# -----------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.last_active = 0

if not st.session_state.authenticated:
    login()
else:
    check_session_timeout()
    logout_button()

    # 🧠 
    st.title("Customer Satisfaction : Insights & Predictions")
    st.markdown("Fetching live data based on survey responses.")

    # Google Sheet config
    sheet_id = "13J3irHlq1rFd5LDXbSEo1kgDGz-U0rZ-JzYTtexR-0c"
    sheet_name = "SurveyForm"

    def load_google_sheet(sheet_id, sheet_name):
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        return pd.read_csv(url)

    try:
        show_latest_only = st.checkbox("🔄 Show only the latest response", value=False)
        df_all = load_google_sheet(sheet_id, sheet_name)
        df = df_all.tail(1).reset_index(drop=True) if show_latest_only else df_all

        st.success("Live data loaded from Google Sheets!")
        df = df.iloc[:, 1:]  # remove first column if it's an index
        last_column = df.pop(df.columns[-1])
        df.insert(0, last_column.name, last_column)
        st.write(df.tail())

        question_labels = {
                "Q2": "Factors influencing customers decision to shop",
                "Q5": "What would make customers more likely to shop",
                "Q6": "Preferred payment methods",
                "Q7": "Promotional activities customers find appealing"
            }

        multi_cols = [col for col in df.columns if df[col].astype(str).str.contains(',').any()]
        if multi_cols:
            label_to_col = {v: k for k, v in question_labels.items()}
            options = [question_labels.get(col, col) for col in multi_cols]
            selected_label = st.selectbox("Select a multi-punch question to visualize", options)
            col_selected = label_to_col[selected_label]
            if st.button("Visualize"):
                visualize_multi_punch(df, col_selected, title_prefix=selected_label, compact=True)
        else:
            st.info("No multi-select columns detected for visualization.")


        model_file = "customer_classifier_RF.pkl"
        model = joblib.load(model_file)

        # Map categorical for prediction
        q1_map = {'Once a week': 1, '2-3 times a week': 2, 'Once a month': 3, 'Rarely': 4}
        q3_map = {'₹100-₹500': 1, '₹500-₹1000': 2, '₹1000-₹2000': 3, '₹2000+': 4}

        df['Q1'] = df['Q1'].map(q1_map)
        df['Q3'] = df['Q3'].map(q3_map)

        df = df.dropna(subset=['Q1'])

        # Only proceed if Q1 is not 'Never'
        if not df.empty and 'Q1' in df.columns:
            try:
                st.subheader("🔮 Predict Customer Satisfaction")

                df['Q4'] = df['Q4'].astype(int)
                df['Q8'] = df['Q8'].astype(int)
                df['Q9'] = df['Q9'].astype(int)
                df['Q10'] = df['Q10'].astype(int)

                X = df[['Q1', 'Q3', 'Q4', 'Q8', 'Q9', 'Q10']]
                df['Predicted_Cust_Satisfaction'] = model.predict(X)

                st.success("Prediction complete!")

                df['Satisfaction_Emoji'] = df['Predicted_Cust_Satisfaction'].apply(satisfaction_emoji)

                st.write(df[['Email Address','Q1', 'Q3', 'Q4', 'Q8', 'Q9', 'Q10', 'Satisfaction_Emoji']].tail())

                st.download_button(
                    label="📥 Download prediction",
                    data=df.to_csv(index=False),
                    file_name="predictions.csv",
                    mime="text/csv"
                )

                # --- Email Sending UI ---
                st.markdown("---")
                st.subheader("📧 Send Email to Satisfied Customers")
                sender_email = st.text_input("Sender Email", value="andrewgilf9@gmail.com")
                app_password = st.text_input("App Password", type="password", value="hyyglzdypsjqgqph")

                if st.button("Send Email"):
                    if sender_email == "" or app_password == "":
                        st.error("Please enter sender email and app password.")
                    else:
                        count = 0
                        for _, row in df.iterrows():
                            if row['Predicted_Cust_Satisfaction'] == 1 and pd.notna(row['Email Address']):
                                receiver_email = row['Email Address']
                                subject = "Thank you for your positive feedback!"
                                body = (
                                    f"Dear {receiver_email},\n\n"
                                    "We are thrilled to inform you that our prediction model has identified you as a satisfied customer! \n\n"
                                    "Here is the coupon code for your next purchase: COUPON123\n\n"
                                    "Thank you for your positive feedback in the recent survey. "
                                    "We appreciate your satisfaction and hope to continue serving you well.\n\n"
                                    "Best regards,\nCustomer Service Team"
                                )
                                send_email_gmail(sender_email, app_password, receiver_email, subject, body)
                                count += 1
                        if count == 0:
                            st.info("No customers with Predicted_Cust_Satisfaction == 1 found to send emails.")

            except Exception as e:
                st.error(f"Prediction failed: {e}")
        else:
            st.info("No valid survey responses to predict.")
    except Exception as e:
        st.error(f"Failed to load data from Google Sheets: {e}")
