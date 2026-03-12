# Full-Stack Event Management System (Django + DRF)

Production-style event platform with role-based dashboards for Admin, Organizer, and Attendee.

## Features

- Role-based access control: Admin, Organizer, Attendee
- Authentication: register, login, logout, password reset
- Event lifecycle: create, publish, block, search, review, rating
- Booking flow: create booking, Razorpay payment, verify, confirm ticket
- Ticketing: unique ticket ID, QR code generation, validation endpoint
- Notifications: in-app notification APIs and email confirmation
- Reminder command for upcoming events
- Organizer/Admin analytics API with Chart.js-ready trend data
- Calendar API and FullCalendar dashboard view
- REST APIs for mobile app integration
- Location coordinates for Google Maps embedding
- Stream metadata for live event sessions

## Project Structure

- accounts
- events
- bookings
- payments
- dashboard
- analytics_app
- notifications

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables from `.env.example`.

3. Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create superuser:

```bash
python manage.py createsuperuser
```

5. Run server:

```bash
python manage.py runserver
```

## Key Routes

- Home: `/`
- Events UI: `/events/`
- Dashboard UI: `/dashboard/`
- Bookings UI: `/bookings/history/`
- Admin: `/admin/`
- Swagger docs: `/api/docs/`

## Core APIs

- Register: `POST /accounts/register/`
- JWT login: `POST /accounts/api/token/`
- Events: `/events/api/events/`
- Booking create: `POST /bookings/api/bookings/`
- Razorpay create order: `POST /payments/api/create-order/`
- Razorpay verify: `POST /payments/api/verify/`
- Ticket validate (QR): `POST /bookings/api/tickets/validate/`
- Analytics: `GET /analytics/api/dashboard/`
- Notifications: `GET /notifications/api/list/`

## Event Reminder Command

```bash
python manage.py send_event_reminders
```

Schedule this command via cron/Task Scheduler for periodic reminders.

## Notes

- Configure a real SMTP provider for production emails.
- Add Redis + Channels/WebSockets if you need push real-time notifications.
- Replace default DB with PostgreSQL in production.
- Add Celery for async tasks (emails, reminders, recommendations).
