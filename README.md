# 🚗 Automotive Service AI Call System

A FastAPI-based voice assistant system for automotive service centers. It automatically calls customers for service reminders and schedules appointments. It uses **Plivo** for telephony, **Azure OpenAI** for conversational AI, and **MongoDB** for data storage. The system supports bilingual interaction (English and Hindi).

---

## 🌟 Key Features

- 🔁 **Automated Service Reminders**: Calls customers based on due dates for first or regular service.
- 🧠 **AI-Powered Conversations**: Uses Azure OpenAI to engage users naturally in Hindi or English.
- 📅 **Appointment Booking**: Detects appointment confirmations and saves them to Excel.
- 📊 **Real-Time Dashboard**: Monitor live calls, transcripts, and customer details.
- 📁 **Excel Customer Records**: Reads customer info from Excel to assess service eligibility.
- 🗃 **MongoDB Storage**: Stores call sessions and transcripts.
- 🎯 **Service Type Detection**: Distinguishes between first service and regular maintenance.
- 🌐 **Bilingual Support**: Switches language dynamically during calls.

---

## ⚙️ Requirements

- Python 3.8+
- MongoDB
- Plivo Account
- Azure OpenAI Account
- Excel files (`Customer_Records.xlsx`, `Service_Appointments.xlsx`)
- `requirements.txt` dependencies

---

## 🛠 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/automotive-service-ai.git
cd automotive-service-ai
````

### 2. Create a Virtual Environment (Optional)

```bash
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up `.env`

Create a `.env` file in the root directory:

```
PLIVO_AUTH_ID=your_plivo_auth_id
PLIVO_AUTH_TOKEN=your_plivo_auth_token
PLIVO_FROM_NUMBER=your_plivo_number
PLIVO_TO_NUMBER=destination_number
PLIVO_ANSWER_XML=https://your-server.com/webhook

AZURE_OPENAI_API_KEY_P=your_azure_openai_key
AZURE_OPENAI_API_ENDPOINT_P=wss://your-endpoint.openai.azure.com/openai/realtime?api-version=2024-10-01-preview&deployment=your-deployment

HOST_URL=wss://your-server.com
PORT=8090

MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=automotive_service_db

SERVICE_CENTER_NAME=Patni Toyota Nagpur
SERVICE_REMINDER_DAYS=30
REGULAR_SERVICE_MONTHS=9

CUSTOMER_RECORDS_FILE=Customer_Records.xlsx
SERVICE_APPOINTMENTS_FILE=Service_Appointments.xlsx

AI_VOICE_NAME=Priya
DEFAULT_VOICE=sage
PRIMARY_LANGUAGE=hi
SECONDARY_LANGUAGE=en-US
```

### 5. Generate Sample Data

```bash
python generate_sample_data.py
```

### 6. Start MongoDB

Ensure MongoDB is running locally or update the `MONGODB_URL`.

---

## 🚀 Usage

### Start the Server

```bash
python main.py
```

Access the app at: `http://localhost:8090`

### Dashboard

Visit: `http://localhost:8090/dashboard` for live monitoring.

### Key Endpoints

| Endpoint                    | Description             |
| --------------------------- | ----------------------- |
| `GET /`                     | Health check            |
| `GET /dashboard`            | Live dashboard          |
| `POST /webhook`             | Plivo call webhook      |
| `POST /incoming-call`       | Incoming call handler   |
| `POST /voice`               | Language switch handler |
| `WebSocket /media-stream`   | Audio streaming         |
| `WebSocket /ws/transcripts` | Transcript updates      |

---

## 📞 Call Flow Overview

1. System reads customer records from Excel.
2. Checks eligibility based on service due dates.
3. Initiates Plivo calls to eligible customers.
4. AI assistant interacts (primarily in Hindi).
5. On confirmation (e.g., “**बुक कर दी है**”), appointment is logged.
6. MongoDB stores call and transcript data.
7. Appointment is added to `Service_Appointments.xlsx`.

---

## 📂 File Structure

```
automotive-service-ai/
├── main.py
├── settings.py
├── requirements.txt
├── generate_sample_data.py
├── automotive_dashboard.html
├── .env.template
├── Customer_Records.xlsx
├── Service_Appointments.xlsx
└── database/
    ├── models.py
    ├── db_service.py
    └── websocket_manager.py
```

---

## 📊 Customer Data Format

The `Customer_Records.xlsx` should contain:

| Column              | Description                  |
| ------------------- | ---------------------------- |
| Name                | Customer name                |
| Phone Number        | With country code            |
| Address             | Residential address          |
| Car Model           | e.g., Toyota Glanza          |
| Car Delivery Date   | Format: YYYY-MM-DD           |
| Last Servicing Date | Optional, format: YYYY-MM-DD |

---

## 📅 Appointment Detection

Extracts:

* Appointment Date
* Appointment Time
* Service Type (first/regular)
* Customer Info

Details are saved in `Service_Appointments.xlsx`.

---

## 🧩 Customization

* 🔄 **Prompts**: Edit `initialize_session()` for custom AI flow.
* ⚙️ **Service Rules**: Modify `determine_service_type()` logic.
* 🌐 **Languages**: Add more language options in `/voice` endpoint.
* 💻 **Dashboard**: Customize `automotive_dashboard.html`.
* 📌 **Appointment Parsing**: Improve in `extract_appointment_details_from_response()`.

---

## 📘 API Documentation

Visit: `http://localhost:8090/docs` after server is running.

---

## 🗄 Database Schema

### `CallSessions`

| Field           | Type      |
| --------------- | --------- |
| call\_id        | UUID      |
| customer\_name  | String    |
| customer\_phone | String    |
| car\_model      | String    |
| service\_type   | String    |
| started\_at     | Timestamp |

### `Transcripts`

| Field     | Type       |
| --------- | ---------- |
| entry\_id | UUID       |
| call\_id  | ForeignKey |
| speaker   | user/ai    |
| message   | Text       |
| timestamp | Timestamp  |

---
