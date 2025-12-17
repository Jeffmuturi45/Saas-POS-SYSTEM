# SaaS POS SYSTEM

[![Python Version](https://img.shields.io/badge/python-3.11-blue)]()
[![Django Version](https://img.shields.io/badge/django-6.0-green)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

## Overview

**SaaS POS SYSTEM** is a multi-tenant Point of Sale platform built with **Django**, designed to serve multiple businesses like retail shops, shoe stores, and hardware outlets.  
The system supports **demo/trial usage**, **license-based activation**, **role-based access control**, and **customizable POS branding per business**.

It’s fully **responsive**, **timezone-aware**, and designed for **scalability**, allowing super admins to manage multiple businesses centrally.

---

## Features

### Super Admin
- Manage businesses and licenses
- Control feature availability per business
- View analytics, audit logs, and global search
- Backup and restore business data

### Business Admin
- Configure POS branding (logo, colors, receipt footer)
- Manage products, inventory, and staff
- Track sales and generate reports
- Request license upgrades from Super Admin

### Cashier
- Process sales using cash, MPESA, or bank
- Print branded receipts
- Limited access to system settings

### System
- Demo/trial accounts with automatic expiration
- License key generation and validation
- Feature gating and usage analytics
- Mobile responsive UI
- Role-based permissions and security

---

## Tech Stack

- **Backend:** Django 6.0
- **Frontend:** HTML, CSS, JavaScript, Bootstrap, Font Awesome
- **Database:** MySQL (development), PostgreSQL (production)
- **Other:** Python-dotenv for environment variables

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Jeffmuturi45/Saas-POS-SYSTEM.git
cd Saas-POS-SYSTEM


Create a virtual environment:

python -m venv venv


Activate the virtual environment:

Windows (Git Bash):

source venv/Scripts/activate


macOS / Linux:

source venv/bin/activate


Install dependencies:

pip install -r requirements.txt


Configure .env file (example):

SECRET_KEY=your-django-secret-key
DEBUG=True
DB_NAME=saas_pos_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=127.0.0.1
DB_PORT=3306


Apply migrations:

python manage.py migrate


Run the development server:

python manage.py runserver


Open http://127.0.0.1:8000
 in your browser.

Contributing

Contributions are welcome! Please follow these steps:

Fork the repository

Create a feature branch (git checkout -b feature/your-feature)

Commit your changes (git commit -m "Add your feature")

Push to the branch (git push origin feature/your-feature)

Open a Pull Request

License

This project is licensed under the MIT License. See the LICENSE
 file for details.

Contact

Author: Jeff Muturi
GitHub: https://github.com/Jeffmuturi45
