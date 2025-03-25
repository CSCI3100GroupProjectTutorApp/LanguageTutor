# Language Tutoring API

This branch is used for testing the authorization function e.g. register, login. I didn't merge it cause the ai change front end code 
and I am afraid it affects the design

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
uvicorn app.main:app --reload
```

### Frontend Only

To run just the frontend:

```
npm run web
```

## API Endpoints

The API will be available at `http://localhost:8000` with the following endpoints:

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
