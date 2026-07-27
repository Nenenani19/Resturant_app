# Restaurant App

A modern Flask-based restaurant ordering web application that lets users browse the menu, add items to a cart, place orders, register/login, and manage their profile.

## Features

- Browse a restaurant menu organized by categories
- Add, update, and remove items from the cart
- Place orders with customer details
- View and update order status
- Register and log in securely
- Manage user profile information
- Persist data using SQLite

## Tech Stack

- Python 3.10+
- Flask
- SQLite
- Jinja2
- Werkzeug

## Getting Started

### 1. Clone or open the project

```powershell
cd C:\Resturant_app
```

### 2. Activate the virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install Flask
```

### 4. Run the application

```powershell
python app.py
```

Then open your browser at:

```text
http://127.0.0.1:5000/
```

## Project Structure

- `app.py` - Main Flask application and route handlers
- `database.py` - Database initialization, schema, and sample data
- `templates/` - HTML templates for the home page, menu, cart, orders, login, signup, and profile
- `static/` - CSS, JavaScript, and menu images
- `restaurant.db` - SQLite database file

## Environment Variables

You can optionally set a custom secret key:

```powershell
$env:SECRET_KEY="your-secret-key"
```

## Notes

- The app uses SQLite, so no external database server is required.
- Menu images are stored in `static/images/`.
- The database is initialized automatically when the app starts.

## License

This project is open-source and available under the MIT License.
