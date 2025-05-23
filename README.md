# Language Tutoring API

Admin user information (use this account to generate new token or run protected function()):

username: admin <br/>
password: admin  <br/>
userid: 0  <br/>

You can add new admin user using create_admin.py under scripts
## Features

- User authentication and management
- Language learning resources and exercises
- Progress tracking
- MongoDB database integration with both sync and async support
- Integrated frontend and backend deployment

## Setup

1. Clone the repository
2. Install backend dependencies:
   ```
   pip install -r backend/requirements.txt
   ```
3. Install frontend dependencies:
   ```
   npm install
   ```
4. Set up environment variables:
   - Create a `.env` file in the root directory or use the existing one in the backend directory
   - Make sure MongoDB connection details are configured

### Backend Only

To run just the backend API:

```
cd backend
python -m uvicorn app.main:app --reload
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 //for local network host
```

### Frontend Only

To run just the frontend:

```
npm run web
```

## API Endpoints

The API will be available at `http://localhost:8000` with the following endpoints:
- API will be available at `http://{IPAddress}:8000` if host to local network
- `/` - Welcome message
- `/docs` - Interactive API documentation (Swagger UI)
- `/redoc` - Alternative API documentation
- `/test-db` - Test the MongoDB connection
- Authentication endpoints:
  - `/login` - User login
  - `/register` - User registration
  - `/refresh-token` - Token refresh
  - `/logout` - User logout

## Frontend Access

The frontend application will be available at:
- Web: `http://localhost:8081`


## Development

- Frontend: React Native (in `src/` directory)
- Backend: FastAPI (in `backend/` directory)
- Database: MongoDB Atlas

## MongoDB Integration

The application uses a custom MongoDB client that supports both synchronous and asynchronous operations.

## Database

Under `database/` directory, mongodb_utils is library for updating MongoDB database.

sqlite is used for local storage under frontend.
