# Language Tutoring API

## Sprint 1 Progress (March 14-28)

- Completed FastAPI setup and project structure
- Implemented MongoDB Atlas integration
- Developed JWT authentication with user registration and login
- Created token refresh and logout functionality
- Added user profile endpoint and information retrieval

## API Endpoints

### Authentication

- `POST /register`: Register a new user
- `POST /login`: Log in and get auth token
- `POST /logout`: Log out (invalidate token)
- `POST /refresh-token`: Refresh an expired token

### Users

- `GET /users/me`: Get current user profile

## Setup Instructions for Teammates

### Prerequisites
- Python 3.9 or newer
- pip (Python package manager)
- Git

### Step 1: Clone the repository
```bash
git clone https://github.com/CSCI3100GroupProjectTutorApp/language-tutoring-api.git
cd language-tutoring-api
```

### Step 2: Set up Python environment
Choose **one** of these options:

**Option A: With Conda**
```bash
conda create -n language-tutoring python=3.10
conda activate language-tutoring
```

**Option B: With venv**
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set up environment variables
Create a `.env` file in the project root with the following content:
```
# These thing are just for me to test the mongoDB connection.
# MongoDB Atlas
MONGODB_URL=mongodb+srv://CSCI3100_TEST:CSCI3100@test.1hjcm.mongodb.net/?retryWrites=true&w=majority&appName=LanguageTutoringApp

# JWT 
SECRET_KEY=6eb4fd9de4a2ee35f804a5f1225572648735f15d7eab7d6290b55fc626bf139b
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Step 5: Run the application
```bash
uvicorn app.main:app --reload --access-log
```

### Step 6: Verify the setup
- Open your browser and go to `http://127.0.0.1:8000/`
- You should see: `{"message":"Welcome to the Language Tutoring API"}`
- Access the API documentation at `http://127.0.0.1:8000/docs`
- Try the `/test-db` endpoint to verify MongoDB connection
