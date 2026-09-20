# MAXDEL Hotel Management System

A Django-based hotel management and booking system developed for **MAXDEL Hospitality Services**.

## Overview

The MAXDEL Hotel Management System is a web-based platform designed to streamline hotel operations, guest bookings, room management, payments, check-in/check-out processes, reporting, and administrative activities.

The system provides different functionality for hotel management and reception staff while also providing guests with an online booking experience.

## Features

* Guest room booking
* Room availability management
* Room and room-type management
* Guest information management
* Booking management
* Check-in and check-out management
* Online payment integration
* Deposit and balance payment tracking
* Booking payment verification
* Guest history
* Reception dashboard
* Management dashboard
* Monthly and yearly reporting
* Invoice generation
* Administrative controls
* Responsive hotel website
* Django-based backend
* Database-driven room and booking management

## Technologies Used

* **Python**
* **Django**
* **HTML5**
* **CSS3**
* **JavaScript**
* **Bootstrap**
* **SQLite / Django ORM**
* **Paystack API**

## Project Structure

```text
MAXDEL-Hotel-Management-System/
│
├── Apk/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── website/
│   ├── migrations/
│   ├── static/
│   ├── templates/
│   ├── admin.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── manage.py
├── populate_rooms.py
├── .env.example
└── .gitignore
```

## Security

Sensitive credentials and environment variables are not included in this repository.

The application uses environment variables for sensitive configuration such as payment API credentials and secret keys.

**Never commit your `.env` file or API credentials to the repository.**

## Project Status

The system is an ongoing software project and may continue to receive improvements, additional features, bug fixes, and security enhancements.

## Copyright & Usage

**© 2026 Elorm Dzikunu. All Rights Reserved.**

This repository is made publicly available for **viewing and portfolio purposes only**.

No permission is granted to copy, reproduce, modify, distribute, publish, sublicense, sell, commercially exploit, or create derivative works from this software or any substantial portion of its source code without prior written permission from the copyright holder.

By accessing this repository, you acknowledge that the source code remains the intellectual property of its copyright holder.

For licensing, commercial use, collaboration, or other permissions, please contact the copyright holder.

## Disclaimer

This repository is intended to demonstrate the development and technical implementation of the MAXDEL Hotel Management System.

Production deployment should include appropriate security configuration, environment management, database security, payment security, access controls, backups, and other operational safeguards.
