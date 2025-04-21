# Smart Queue Management System

A comprehensive Flask-based web application that enables businesses to create, manage, and monitor customer queues efficiently.

## Features

- Supports business-specific queue creation
- Admin login and queue management
- Position tracking and notifications via SMS
- Flexible queue handling across multiple businesses
- Built with Flask, Replit DB, and PostgreSQL integration

## Deployment to Vercel

This application is ready to be deployed to Vercel. Follow these steps:

1. **Push to GitHub**: First, push this project to a GitHub repository.

2. **Connect to Vercel**: 
   - Go to [vercel.com](https://vercel.com) and sign up or log in.
   - Create a new project and import your GitHub repository.

3. **Configure Environment Variables**:
   In the Vercel dashboard, add the following environment variables:
   
   - `DATABASE_URL`: Your PostgreSQL database connection string
   - `SESSION_SECRET`: A strong secret key for session management
   - `TWILIO_ACCOUNT_SID`: Your Twilio account SID (for SMS notifications)
   - `TWILIO_AUTH_TOKEN`: Your Twilio auth token
   - `TWILIO_PHONE_NUMBER`: Your Twilio phone number

4. **Deploy**:
   - Click "Deploy" in the Vercel dashboard.
   - Vercel will automatically detect the Python project and use the vercel.json configuration.

## Local Development

1. Install dependencies:
   ```
   pip install -r vercel_requirements.txt
   ```

2. Set up environment variables.

3. Run the Flask application:
   ```
   python main.py
   ```

## Admin Access

The default admin credentials are:
- Username: `admin`
- Password: `admin123`

For security, change these credentials in production.