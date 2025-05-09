# Language Tutoring API

This branch is used for testing the authorization function e.g. register, login. I didn't merge it cause the ai change front end code 
and I am afraid that it affects the design.

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

## Database

Under `database/` directory, mongodb_utils is library for updating MongoDB database.

sqlite is the implementation of local sqlite storage where the data can be accessed under the data folder in the root directory.

There are 2 tables in the database.
1. words: table to store the words offline
2. sync_queue: a queue storing the operations record with words waiting to be updated to cloud database

To check the content of the data :

```
cd data
sqlite3 word_data.db #filename is word_data.db in this example

# Once in the SQLite shell:
.tables  # Should show 'words' and 'sync_queue' tables
SELECT * FROM words;
SELECT * FROM sync_queue;
.exit
```
How to install sqlite:

Refer to this link: https://www.tutorialspoint.com/sqlite/sqlite_installation.htm

or this video (for windows): https://www.youtube.com/watch?v=ZiJb7EIaRCE

## PDF Processing Support

The application supports text extraction from PDF files in addition to standard image formats (JPEG/PNG).

PDF text extraction is handled by pdfplumber and PyPDF2, which are pure Python packages that don't require any additional installation or external dependencies. All necessary packages are included in the requirements.txt file.

For PDFs that contain native text (not scanned images), the application will extract text directly from the PDF. For scanned PDFs, users can save individual pages as images and use the OCR functionality for text recognition.
