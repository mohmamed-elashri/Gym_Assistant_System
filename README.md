# Gym Assistant System

A comprehensive Django-based fitness management platform with AI-powered workout planning, nutrition tracking, and personalized fitness recommendations.

## Features

- **User Authentication**: Secure signup/login with profile management
- **Fitness Profile**: Manage fitness levels, activity tracking, and health metrics
- **AI-Powered Workout Plans**: Generate personalized workout routines using Google Generative AI
- **Nutrition Calculator**: Calculate daily calorie needs and nutritional recommendations
- **Activity Tracking**: Track workouts and monitor progress over time
- **Responsive Dashboard**: Modern web interface for easy access and management
- **REST API**: Complete API for mobile and third-party integrations
- **ML Models**: Trained models for fitness level classification and calorie prediction

## Tech Stack

- **Backend**: Django 5.1 + Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI/ML**: Google Generative AI, scikit-learn, joblib
- **Frontend**: HTML5, CSS3, JavaScript (Django templates)
- **DevOps**: GitHub Actions CI/CD
- **Code Quality**: Ruff, Black, MyPy, Pre-commit hooks

## Prerequisites

- Python 3.14+
- pip or poetry
- Virtual environment (venv/conda)
- Google Generative AI API key (for AI features)

## Installation

### 1. Clone the repository
```bash
git clone git@github.com:mohmamed-elashri/Gym_Assistant_System.git
cd FINAL\ Gym_Assistant_System
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
# Required: DJANGO_SECRET_KEY, Google Generative AI key
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
# Or use the provided script
./run_local.bat  # Windows
./run_local.sh   # macOS/Linux
```

The application will be available at `http://localhost:8000`

## Running Tests

```bash
# Run all tests
python manage.py test

# Or use the provided scripts
./run_tests.ps1  # Windows (PowerShell)
./run_tests.bat  # Windows (Command Prompt)
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

- `GET /api/users/` - List all users
- `POST /api/users/` - Create new user
- `GET/PUT /api/users/<id>/` - Retrieve/update user
- `POST /api/workout-plans/` - Generate workout plan
- `GET /api/fitness-data/` - Get user fitness metrics
- `POST /api/nutrition/` - Calculate nutrition info

See full API documentation by running the server and visiting `/api/docs/`

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
GOOGLE_GENERATIVE_AI_API_KEY=your_api_key_here
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in settings
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Use a production database (PostgreSQL recommended)
- [ ] Set up proper static/media file serving
- [ ] Configure email for password reset
- [ ] Enable HTTPS
- [ ] Set secure cookie flags in settings
- [ ] Use environment variables for sensitive data

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
