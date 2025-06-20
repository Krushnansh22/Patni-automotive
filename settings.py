from pydantic_settings import BaseSettings
from pydantic import Extra
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Plivo Settings
    PLIVO_AUTH_ID: str
    PLIVO_AUTH_TOKEN: str
    PLIVO_FROM_NUMBER: str
    PLIVO_TO_NUMBER: str
    PLIVO_ANSWER_XML: str

    # Azure OpenAI Settings
    AZURE_OPENAI_API_KEY_P: str
    AZURE_OPENAI_API_ENDPOINT_P: str

    # Server Settings
    HOST_URL: str
    PORT: int = 8090

    # MongoDB Settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "automotive_service_db"

    # Automotive Service Specific Settings
    SERVICE_CENTER_NAME: str = "Patni Toyota Nagpur"
    SERVICE_REMINDER_DAYS: int = 30  # Days after delivery for first service
    REGULAR_SERVICE_MONTHS: int = 9  # Months for regular service reminder

    # Excel File Settings
    CUSTOMER_RECORDS_FILE: str = "Customer_Records.xlsx"
    SERVICE_APPOINTMENTS_FILE: str = "Service_Appointments.xlsx"

    # AI Voice Settings
    AI_VOICE_NAME: str = "Priya"  # Name of the AI assistant
    DEFAULT_VOICE: str = "sage"  # OpenAI voice model

    # Language Settings
    PRIMARY_LANGUAGE: str = "hi"  # Hindi
    SECONDARY_LANGUAGE: str = "en-US"  # English

    class Config:
        env_file = ".env"
        extra = Extra.allow


settings = Settings()
