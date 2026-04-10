# AgendaCero Backend

Production-ready Django backend for the AgendaCero SaaS appointment management platform.

## Overview

AgendaCero is a multi-tenant SaaS application designed for small businesses (barbershops, beauty salons, medical offices) to manage appointments, clients, and services.

## Technology Stack

- **Python 3.12** - Programming language
- **Django 5.0** - Web framework
- **Django Rest Framework 3.15** - API framework
- **PostgreSQL 15** - Database
- **Redis 7** - In-memory store and message broker
- **SimpleJWT** - JWT authentication
- **Docker & Docker Compose** - Containerization
- **Gunicorn** - WSGI server
- **Celery 5.4** - Asynchronous task queue
- **drf-spectacular** - API documentation (Swagger/OpenAPI)
- **django-filter** - Filtering support
- **django-cors-headers** - CORS handling

## Features

- Multi-tenant architecture (each user manages their own business data)
- JWT-based authentication
- UUID primary keys for all models
- Soft delete capability
- Appointment overlap prevention with atomic DB locks (select_for_update)
- Dynamic business working hours (Business Schedules)
- Asynchronous background tasks (Celery + Redis) for emails and limits
- API versioning (`/api/v1/`)
- Automatic API documentation
- Comprehensive unit tests
- Docker-ready deployment

## Project Structure

```
agendacero-backend/
├── config/                 # Django project configuration
│   ├── __init__.py
│   ├── settings.py         # Main settings
│   ├── urls.py             # URL configuration
│   ├── wsgi.py             # WSGI entry point
│   └── asgi.py             # ASGI entry point
├── apps/
│   ├── users/              # User management & authentication
│   ├── businesses/         # Business entities
│   ├── clients/            # Client/customer management
│   ├── services/           # Service catalog
│   └── appointments/       # Appointment scheduling
├── common/                 # Shared utilities
│   ├── models.py           # Base model with common fields
│   ├── permissions.py      # Custom permissions
│   ├── pagination.py       # Custom pagination classes
│   └── serializers.py      # Base serializers
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Docker Compose configuration
├── .env.example            # Environment variables template
└── manage.py               # Django management script
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Or Python 3.12+ for local development

### Using Docker (Recommended)

1. **Clone the repository**

```bash
git clone <repository-url>
cd agendacero-backend
```

2. **Create environment file**

```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Build and start containers**

```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

### Local Development

1. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Run migrations**

```bash
python manage.py migrate
```

5. **Create superuser**

```bash
python manage.py createsuperuser
```

6. **Run development server**

```bash
python manage.py runserver
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register/` | Register new user |
| POST | `/api/v1/auth/login/` | Login (get JWT tokens) |
| POST | `/api/v1/auth/refresh/` | Refresh access token |
| GET | `/api/v1/auth/me/` | Get current user info |

### Businesses

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/businesses/` | List businesses |
| POST | `/api/v1/businesses/` | Create business |
| GET | `/api/v1/businesses/{id}/` | Get business details |
| PUT/PATCH | `/api/v1/businesses/{id}/` | Update business |
| DELETE | `/api/v1/businesses/{id}/` | Delete business |

### Clients

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/clients/` | List clients |
| POST | `/api/v1/clients/` | Create client |
| GET | `/api/v1/clients/{id}/` | Get client details |
| PUT/PATCH | `/api/v1/clients/{id}/` | Update client |
| DELETE | `/api/v1/clients/{id}/` | Delete client (soft) |

### Services

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/services/` | List services |
| POST | `/api/v1/services/` | Create service |
| GET | `/api/v1/services/{id}/` | Get service details |
| PUT/PATCH | `/api/v1/services/{id}/` | Update service |
| DELETE | `/api/v1/services/{id}/` | Delete service (soft) |

### Appointments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/appointments/` | List appointments |
| POST | `/api/v1/appointments/` | Create appointment |
| GET | `/api/v1/appointments/{id}/` | Get appointment details |
| PUT/PATCH | `/api/v1/appointments/{id}/` | Update appointment |
| DELETE | `/api/v1/appointments/{id}/` | Delete appointment (soft) |
| PATCH | `/api/v1/appointments/{id}/status/` | Update status |
| PATCH | `/api/v1/appointments/{id}/confirm/` | Confirm appointment |
| PATCH | `/api/v1/appointments/{id}/complete/` | Complete appointment |
| PATCH | `/api/v1/appointments/{id}/cancel/` | Cancel appointment |
| PATCH | `/api/v1/appointments/{id}/mark_no_show/` | Mark as no-show |

### Documentation

- **Swagger UI**: `http://localhost:8000/api/docs/swagger/`
- **ReDoc**: `http://localhost:8000/api/docs/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### Health Check

- `GET /api/health/` - Returns `{"status": "healthy", "version": "1.0.0"}`

## API Usage Examples

### Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "password_confirm": "securepass123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

### Create an Appointment

```bash
curl -X POST http://localhost:8000/api/v1/appointments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "client": "<client-uuid>",
    "service": "<service-uuid>",
    "start_time": "2024-01-15T10:00:00Z",
    "notes": "First appointment"
  }'
```

## Running Tests

```bash
# Run all tests
python manage.py test

# Run with verbosity
python manage.py test -v 2

# Run specific app tests
python manage.py test apps.users
python manage.py test apps.appointments

# Run with coverage (requires coverage)
coverage run --source='.' manage.py test
coverage report
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | (required in production) |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `POSTGRES_DB` | Database name | `agendacero_db` |
| `POSTGRES_USER` | Database user | `agendacero_user` |
| `POSTGRES_PASSWORD` | Database password | `agendacero_password` |
| `POSTGRES_HOST` | Database host | `db` |
| `POSTGRES_PORT` | Database port | `5432` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Access token lifetime | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Refresh token lifetime | `7` |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | `http://localhost:4200,http://127.0.0.1:4200` |
| `CELERY_BROKER_URL` | Redis URL for Celery | `redis://redis:6379/0` |

## Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

## Docker Commands

```bash
# Build and start
docker-compose up --build

# Start in background
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f celery

# Run migrations manually
docker-compose run web python manage.py migrate

# Create superuser
docker-compose run web python manage.py createsuperuser

# Run tests
docker-compose run web python manage.py test

# Access Django shell
docker-compose run web python manage.py shell

# Access database shell
docker-compose exec db psql -U agendacero_user -d agendacero_db
```

## Security Considerations

1. **Change `SECRET_KEY`** in production - never use the default
2. **Set `DEBUG=False`** in production
3. **Configure `ALLOWED_HOSTS`** with your production domains
4. **Use strong passwords** for database and JWT secrets
5. **Enable HTTPS** in production
6. **Regularly update dependencies** for security patches

## Architecture Decisions

### Multi-Tenant Design
- Each user owns a business
- All data (clients, services, appointments) is scoped to a business
- Custom permissions ensure data isolation

### UUID Primary Keys
- All models use UUID instead of auto-increment integers
- Prevents ID enumeration attacks
- Better for distributed systems

### Soft Delete
- Models include `is_deleted`, `deleted_at` fields
- Deleted records are filtered by default
- Data retention for audit purposes

### Appointment Overlap Prevention
- Database constraint ensures `end_time > start_time`
- Application-level check prevents overlapping time slots
- Strict Database Atomic Locks (`select_for_update`) to prevent concurrent race conditions
- Only applies to scheduled/confirmed appointments

### Dynamic Business Schedules
- Businesses can set exact working hours via `BusinessSchedule` per day of the week
- `/api/v1/appointments/available-slots/` logic crosses service duration with open hours automatically

### Asynchronous Task Execution (Celery)
- Uses Celery and Redis to offload heavy processes from the main HTTP thread
- Example: Email delivery for Appointment Confirmations runs in the background

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
Copyright (c) 2026 Jorge Eduardo Gallo Zuluaga. All rights reserved.

This project is proprietary software. Unauthorized copying, modification,
distribution, or use of this software, via any medium, is strictly prohibited
without the prior written permission of the author.

## Support

For issues and questions, please contact the development team.

## Author
Jorge Eduardo Gallo Zuluaga 
Full Stack Developer  

- GitHub: https://github.com/JorgeEGZ
- Email: jorgegz1998@gmail.com
