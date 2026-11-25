# Gym Assistant System

[![CI](https://github.com/mohmamed-elashri/Gym_Assistant_System/actions/workflows/python-tests.yml/badge.svg)](https://github.com/mohmamed-elashri/Gym_Assistant_System/actions)
[![License](https://img.shields.io/github/license/mohmamed-elashri/Gym_Assistant_System)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Issues](https://img.shields.io/github/issues/mohmamed-elashri/Gym_Assistant_System)](https://github.com/mohmamed-elashri/Gym_Assistant_System/issues)

A comprehensive Django-based fitness management platform with AI-powered workout planning, nutrition tracking, and personalized fitness recommendations.

## Features

- **User Authentication**: Secure signup/login with profile management
- **Fitness Profile**: Manage fitness levels, activity tracking, and health metrics
- **AI-Powered Workout Plans**: Generate personalized workout routines using Google Generative AI
- **Nutrition Calculator**: Calculate daily calorie needs and nutritional recommendations
- **Activity Tracking**: Track workouts and monitor progress over time
- **Responsive Dashboard**: Modern web interface for easy access and management
- **REST API**: Complete API for mobile and third-party integrations
- **ML Models**: Demonstration models for fitness level classification and calorie estimation, trained on synthetic data (see [Machine learning models](#machine-learning-models))

## Tech Stack

- **Backend**: Django 5.1 + Django REST Framework
- **Database**: SQLite (default). PostgreSQL is used when `POSTGRES_DB` is set (see Docker below)
- **AI/ML**: Google Generative AI, scikit-learn, joblib
- **Frontend**: HTML5, CSS3, JavaScript (Django templates)
- **DevOps**: GitHub Actions CI/CD
- **Code Quality**: Ruff, Black, MyPy, Pre-commit hooks

## Prerequisites

- Python 3.12+
- pip or poetry
- Virtual environment (venv/conda)
- Google Generative AI API key (for AI features)

## Installation

### 1. Clone the repository
```bash
git clone git@github.com:mohmamed-elashri/Gym_Assistant_System.git
cd Gym_Assistant_System
```

### 2. Create and activate virtual environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
# Or for development with extra tools:
pip install -r requirements-dev.txt
```

### 4. Configure environment variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your settings
# Required: DJANGO_SECRET_KEY, and at least one GEMINI_KEY_1 or OPENROUTER_KEY_1
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Create superuser (admin)
```bash
python manage.py createsuperuser
```

### 7. Start the development server
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## Machine learning models

The models are **demonstration models trained on synthetic data**. They are not validated on real people and must not be used for health or training decisions.

- The original training data and models could not be recovered, so no original dataset is credited (details: [docs/MODEL_PROVENANCE.md](docs/MODEL_PROVENANCE.md)).
- `tools/train_synthetic_models.py` generates seeded synthetic data (calories from the published Keytel et al. 2005 heart-rate equation; fitness level from a documented heuristic) and writes the model files.
- Reported metrics are on held-out synthetic rows only. They show that the models recover the generating rule, not accuracy on real users.
- A real, properly licensed dataset is planned to replace the synthetic one.

## Running Tests

```bash
# Run all tests
python -m pytest -q

# Or use the provided scripts
./run_tests.ps1  # Windows (PowerShell)
```

## Project Structure

```
Gym_Assistant_System/
├── fitness_api/              # Main Django app
│   ├── models.py            # Database models
│   ├── views.py             # API views
│   ├── urls.py              # URL routing
│   ├── ai_service.py        # Google Generative AI integration
│   ├── ml_exceptions.py     # ML-related exceptions
│   ├── calorie_predictor.py # ML calorie prediction model
│   ├── nutrition_calculator.py
│   ├── templates/           # HTML templates
│   └── migrations/          # Database migrations
├── gym_config/              # Django settings & config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── models/                  # Trained ML models (joblib)
├── tools/                   # ML training & evaluation scripts
├── data/                    # Datasets
├── requirements.txt         # Python dependencies
├── manage.py               # Django management script
└── db.sqlite3              # SQLite database (dev)
```

## API Endpoints

All routes are mounted under `/api/` (see `fitness_api/urls.py`).

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/predict/` | none | Predict fitness level from age, gender, weight, height |
| POST | `/api/chat/` | none (throttled) | AI fitness assistant chat |
| POST | `/api/workout-calories/` | none | Estimate calories burned for a workout |
| POST | `/api/workout-plan/` | session login | Generate a 4-week plan from the user's saved fitness data |
| GET | `/api/dashboard/` | session login | User dashboard page |
| GET | `/api/health/live/`, `/api/health/ready/` | none | Liveness and database readiness |
| GET | `/api/docs/`, `/api/schema/` | none | Swagger UI and OpenAPI schema |

Model files (`models/*.pkl`) are not committed. Generate them with `python tools/train_synthetic_models.py` (see below).

## Configuration

### Django Settings
Edit `gym_config/settings.py` to customize:
- Database configuration
- Allowed hosts
- Static files serving
- CORS settings

### Environment Variables (.env)
```
DJANGO_SECRET_KEY=your_secret_key_here
DJANGO_DEBUG=False  # Set to True only in development
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
GEMINI_KEY_1=your_api_key_here
```

## Deployment

Readiness status, known gaps and a checklist: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). The project is not deployed anywhere.

### Production Checklist
- [ ] Set `DEBUG=False` in settings
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Use a production database (PostgreSQL recommended)
- [ ] Set up proper static/media file serving
- [ ] Configure email for password reset
- [ ] Enable HTTPS
- [ ] Set secure cookie flags in settings
- [ ] Use environment variables for sensitive data

### Docker Compose (web + PostgreSQL)

```bash
cp .env.example .env   # set DJANGO_SECRET_KEY, POSTGRES_PASSWORD, and an AI key
docker compose up --build
docker compose exec web python manage.py migrate
```

The Docker files were added in this PR and have not been built in CI yet.

### Deploying to Heroku, AWS, or other platforms
Refer to Django deployment documentation and platform-specific guides.

## Development Workflow

### Code Quality Tools
```bash
# Format code with Black
black fitness_api/

# Lint with Ruff
ruff check fitness_api/

# Type checking with MyPy
mypy fitness_api/

# Run pre-commit hooks
pre-commit run --all-files
```

### Making Changes
1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `./run_tests.ps1`
4. Commit: `git commit -m "feat: add your feature"`
5. Push: `git push origin feature/your-feature`
6. Create Pull Request on GitHub

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and linters before submitting PR
6. Create a pull request with a clear description

## Troubleshooting

### Virtual Environment Issues
```bash
# Deactivate current env
deactivate

# Remove and recreate
rmdir /s .venv  # Windows
rm -rf .venv    # macOS/Linux
python -m venv .venv
```

### Database Issues
```bash
# Reset database (development only)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Missing Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Support & Contact

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing issues for solutions
- See documentation in `/docs` folder

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](docs/CHANGELOG.md) for version history and updates.

---

**Last Updated**: 2026-06-16  
**Version**: 1.0.0  
**Status**: Active Development
