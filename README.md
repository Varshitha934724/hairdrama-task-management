# Hairdrama Task Management

A simple task management web application built for the Hairdrama Tech internship assignment.

## Features

- Google OAuth login
- Create tasks
- Assign tasks to other users
- Add task description
- Add due date and due time
- View task status
- Mark tasks as completed
- Gmail email notifications

## Tech Stack

### Frontend
- Next.js
- TypeScript
- React
- Supabase Authentication

### Backend
- Python
- Flask
- Flask-CORS

### Database
- Supabase PostgreSQL

### Integrations
- Google OAuth 2.0
- Gmail API

## Architecture

```text
User
  |
  v
Next.js Frontend
  |
  v
Supabase Authentication
  |
  v
Flask Backend
  |
  +----> Supabase PostgreSQL
  |
  +----> Gmail API


hairdrama-task-management/
├── backend/
│   ├── app.py
│   ├── .env.example
│   ├── .gitignore
│   └── gmail_token.json
├── frontend/
│   ├── app/
│   │   ├── auth/
│   │   │   └── callback/
│   │   │       └── route.ts
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── public/
│   ├── .env.local
│   ├── .gitignore
│   ├── package.json
│   └── tsconfig.json
├── migrations/
│   └── 001_initial_schema.sql
└── README.md



## Environment Variables

Create the required environment files using the example files provided in the repository.

Never commit real API keys, OAuth credentials, Gmail tokens, or other secrets to GitHub.

## Running Locally

### Backend

```bash
cd backend
python app.py

http://127.0.0.1:5000

cd frontend
npm install
npm run dev

http://localhost:3000

migrations/001_initial_schema.sql

Varshitha934724
