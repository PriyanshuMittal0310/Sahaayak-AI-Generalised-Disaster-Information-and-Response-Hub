# 🌍 Sahaayak AI: Generalised Disaster Information and Response Hub

A comprehensive real-time disaster monitoring platform with a React frontend and FastAPI backend that visualizes disaster data from multiple sources including USGS, citizen reports, and social media feeds. The application provides an interactive map with real-time disaster updates, intelligent disaster classification, and location-based incident reporting.

## 📌 Latest Updates

- **Enhanced Language Processing**: Improved disaster detection with multi-language support
- **Streamlined API**: Simplified endpoints for better integration
- **Robust Error Handling**: Better error messages and validation
- **Performance Optimizations**: Faster response times and reduced resource usage
- **Simplified Deployment**: Easier setup with Docker Compose

## 🎯 Project Goals

1. **Real-time Disaster Monitoring**: Aggregate and analyze disaster data from multiple sources
2. **Citizen Engagement**: Enable public reporting of disaster incidents
3. **Data Visualization**: Provide intuitive visualizations of disaster data
4. **Automated Analysis**: Use AI to classify and prioritize disaster reports
5. **Open Source**: Community-driven development for global impact

## 🌟 Features

### Backend (FastAPI)
- 🌍 **Real-time disaster data** from multiple sources (USGS, GDACS, ReliefWeb, RSS feeds)
- 🗄️ **PostgreSQL with PostGIS** for spatial data processing and storage
- 🔄 **Alembic** for database migrations
- 🤖 **AI-Powered NLP Processing** with language detection and disaster type classification
- 📍 **Intelligent Geocoding** with automatic location extraction and coordinate mapping
- 📊 **Comprehensive data** including location, magnitude, severity, and time
- 🏥 **Health monitoring** with built-in health check endpoint
- 🐳 **Docker support** for easy deployment
- ⚡ **Redis caching** for improved performance

### Frontend (React)
- 🗺️ **Interactive map** using React Leaflet with real-time updates
- 📱 **Responsive design** for all device sizes
- ⚡ **Real-time updates** every minute
- 📍 **Color-coded markers** for different data sources and disaster types
- 📝 **Incident reporting** with photo uploads and GPS location
- 🔄 **Manual refresh** capability
- 💬 **Rich popups** with detailed disaster information
- 🔍 **Advanced filtering** by disaster type, date, and severity
- 🕒 **Auto-refreshing** data without page reload
- 🌐 **Responsive layout** for all screen sizes
- 🎯 **Smart disaster classification** with visual indicators

### AI & NLP Features
- 🔤 **Language Detection** - Supports 55+ languages using langdetect
- 🏷️ **Disaster Type Classification** - Rule-based + LLM-powered classification
- 📍 **Named Entity Recognition** - Location extraction using spaCy + OpenAI fallback
- 🗺️ **Intelligent Geocoding** - OpenStreetMap Nominatim integration with rate limiting
- 📊 **PostGIS Integration** - Spatial queries and geometry processing

## 🏗 System Architecture

### Backend Architecture
```
├── backend/
│   ├── api/                  # API endpoints and routes
│   ├── migrations/           # Database migrations
│   ├── models/              # Database models
│   ├── services/            # Core business logic
│   │   ├── nlp_service.py   # NLP processing
│   │   ├── geocoding_service.py  # Location services
│   │   └── credibility_service.py # Credibility scoring
│   ├── main.py             # FastAPI application entry
│   └── requirements.txt    # Python dependencies
```

### Frontend Architecture
```
├── frontend/
│   ├── public/            # Static files
│   └── src/
│       ├── components/    # Reusable UI components
│       ├── pages/         # Page components
│       ├── services/      # API service layer
│       └── App.jsx        # Main application component
```

## 🌐 API Endpoints

### Disaster Detection
- `POST /api/disasters/detect` - Analyze text for disaster information
  ```json
  {
    "text": "Heavy rainfall caused flooding in Mumbai",
    "detect_language": true,
    "use_openai": false
  }
  ```

### Batch Processing
- `POST /api/disasters/batch-detect` - Process multiple texts at once
  ```json
  [
    {"text": "Earthquake in California"},
    {"text": "Forest fire in Australia"}
  ]
  ```

### Data Access
- `GET /api/items` - List all disaster reports
- `GET /api/items/{id}` - Get specific report details
- `POST /api/ingest` - Submit new citizen report

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Node.js 16+ (for frontend development)
- Python 3.9+ (for backend development)

### Using Docker (Recommended)

1. **Clone and navigate to the project**
   ```bash
   git clone https://github.com/PriyanshuMittal0310/Sahaayak-AI-Generalised-Disaster-Information-and-Response-Hub.git
   cd Sahaayak-AI-Generalised-Disaster-Information-and-Response-Hub
   ```

2. **Start all services**
   ```bash
   docker-compose up -d --build
   ```

3. **Initialize the database**
   ```bash
   # Apply database migrations
   docker-compose exec sahaayak-backend alembic upgrade head
   
   # Verify the database state
   docker-compose exec sahaayak-backend alembic current
   ```
   You should see output indicating the latest migration is applied.

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## 🛠 Development Setup

### Backend Development

1. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   # On Windows: .\venv\Scripts\activate
   # On Unix/Mac: source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   Create a `.env` file in the backend directory:
   ```env
   DATABASE_URL=postgresql://dev:dev@localhost:5432/crisis
   REDIS_URL=redis://localhost:6379/0
   OPENAI_API_KEY=your-api-key-here  # Optional for enhanced features
   ```

3. **Database setup**
   ```bash
   # Run migrations
   alembic upgrade head
   
   # Seed initial data
   python -m seeds.seed_initial_data
   ```

4. **Run the development server**
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Development

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**
   Create a `.env` file in the frontend directory:
   ```env
   REACT_APP_API_URL=http://localhost:8000
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_nlp.py -v
```

### Frontend Tests
```bash
# Run unit tests
npm test

# Run end-to-end tests
npm run test:e2e
```

## 🚀 Deployment

### Production Deployment

1. **Build the Docker images**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

2. **Start the services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Monitor the services**
   ```bash
   docker-compose logs -f
   ```

### Environment Variables

#### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection URL
- `OPENAI_API_KEY`: For enhanced NLP features
- `DEBUG`: Set to `False` in production

#### Frontend
- `REACT_APP_API_URL`: Backend API URL
- `NODE_ENV`: Set to `production` for production builds

5. **Run the development server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Development

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**
   ```bash
   npm start
   ```

## 📝 API Endpoints

### Data Ingestion
- `GET /ingest/usgs` - Fetch latest earthquake data from USGS
- `GET /ingest/seed/reddit` - Load Reddit seed data
- `GET /ingest/seed/x` - Load X (Twitter) seed data
- `POST /api/ingest` - Submit a new incident report (multipart form)
  - Parameters: `text`, `lat`, `lon`, `file` (optional)

### Data Retrieval
- `GET /api/items` - Get all items (disasters and reports) with NLP data
- `GET /ingest/sample` - Load sample data (development only)

### AI & NLP Processing
- `POST /api/process-nlp-geocoding` - Process existing items with NLP and geocoding

### Health Check
- `GET /health` - Service health status
- `GET /status` - Alternative health check

### Static Files
- `GET /uploads/{filename}` - Access uploaded files

## 🏗️ Project Structure

```
sahaayak-ai/
├── backend/                    # FastAPI application
│   ├── main.py                # Main application file
│   ├── models.py              # Database models with NLP fields
│   ├── db.py                  # Database configuration
│   ├── config.py              # Configuration settings
│   ├── fetch_usgs.py          # USGS data fetcher
│   ├── ingest.py              # Data ingestion utilities
│   ├── scheduler.py           # Background task scheduler
│   ├── tasks.py               # Celery task definitions
│   ├── services/              # AI and NLP services
│   │   ├── __init__.py
│   │   ├── nlp_service.py     # Language detection & disaster classification
│   │   └── geocoding_service.py # Location geocoding service
│   ├── utils/                 # Utility functions
│   │   └── rate_limiter.py    # API rate limiting
│   ├── migrations/            # Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── add_nlp_geocoding_fields.py
│   │       └── f428361a56b6_fix_items_table_schema.py
│   ├── seeds/                 # Sample data
│   │   ├── reddit_seed.json
│   │   └── x_seed.json
│   ├── uploads/               # File upload directory
│   ├── test_nlp_geocoding.py  # NLP testing script
│   ├── alembic.ini           # Alembic configuration
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Backend Docker configuration
├── frontend/                  # React application
│   ├── public/                # Static files
│   │   └── index.html
│   ├── src/                   # React components
│   │   ├── app.jsx           # Main application component
│   │   └── index.js          # Entry point
│   ├── package.json          # Frontend dependencies
│   ├── package-lock.json     # Dependency lock file
│   └── Dockerfile            # Frontend Docker configuration
├── docker-compose.yml         # Multi-container setup
├── start-servers.ps1         # Windows startup script
├── LICENSE                   # MIT License
└── README.md                 # This comprehensive documentation
```

## 🤖 AI & NLP Features

### Language Detection
- Uses `langdetect` library for automatic language detection
- Supports 55+ languages
- Fallback handling for short or unclear text

### Disaster Type Classification
- **Rule-based classification**: Uses keyword matching for common disaster types
- **LLM fallback**: Uses OpenAI GPT-3.5-turbo for complex cases
- Supported disaster types: earthquake, flood, fire, storm, drought, landslide, volcano, tsunami, pandemic, conflict

### Named Entity Recognition (NER)
- Uses spaCy for location extraction from text
- Extracts cities, countries, regions, states, provinces
- **LLM fallback**: Uses OpenAI for better location extraction when spaCy confidence is low

### Geocoding
- Uses Nominatim (OpenStreetMap) for geocoding
- Converts location names to coordinates (lat/lon)
- Creates PostGIS geometry points for spatial queries
- Rate limiting to respect Nominatim usage policies

## 📊 Database Schema

### Items Table
```sql
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    ext_id VARCHAR,                    -- External ID from source
    source VARCHAR,                    -- 'USGS' | 'GDACS' | 'REDDIT' | 'X' | 'CITIZEN'
    source_handle VARCHAR,             -- Handle or subreddit
    text TEXT,                         -- Main content
    magnitude FLOAT,                   -- Disaster magnitude/severity
    place VARCHAR,                     -- Location name
    lat FLOAT,                         -- Latitude
    lon FLOAT,                         -- Longitude
    media_url VARCHAR,                 -- Uploaded file URL
    raw_json JSONB,                    -- Raw source data
    
    -- AI & NLP Fields
    language VARCHAR,                  -- Detected language code
    disaster_type VARCHAR,             -- Classified disaster type
    geom GEOMETRY(POINT, 4326),       -- PostGIS geometry point
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ext_id, source)
);
```

## 🔄 Environment Variables

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `DOCKER_ENV`: Set to 'true' when running in Docker
- `USGS_API_URL`: USGS API endpoint
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key for enhanced NLP features (optional)
- `RATE_LIMIT`: API rate limiting configuration
- `CORS_ORIGINS`: CORS allowed origins

### Frontend
- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8000)
- `NODE_ENV`: Environment mode
- `CHOKIDAR_USEPOLLING`: File watching configuration

## 👥 Contributing

We welcome contributions from the community! Here's how you can help:

1. **Report Bugs**
   - Check existing issues to avoid duplicates
   - Provide detailed reproduction steps
   - Include error messages and screenshots if applicable

2. **Suggest Enhancements**
   - Describe the feature or improvement
   - Explain why it would be valuable
   - Include any relevant references or examples

3. **Submit Pull Requests**
   - Fork the repository
   - Create a feature branch
   - Add tests for your changes
   - Update documentation as needed
   - Submit a pull request with a clear description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ by the Sahaayak AI team
- Uses data from USGS, GDACS, and other open data sources
- Powered by FastAPI, React, and PostGIS

## 📝 Usage Examples

### Get live disaster events
```bash
curl http://localhost:8000/api/items
```

### Submit incident report
```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "text=Flooding reported in downtown area" \
  -F "lat=37.7749" \
  -F "lon=-122.4194" \
  -F "file=@flood_photo.jpg"
```

### Process existing items with NLP
```bash
curl -X POST http://localhost:8000/api/process-nlp-geocoding
```

### Example API Response
```json
{
  "count": 38,
  "items": [
    {
      "id": 1,
      "ext_id": "us7000qu29",
      "source": "USGS",
      "text": "297 km ENE of Lospalos, Timor Leste",
      "place": "297 km ENE of Lospalos, Timor Leste",
      "magnitude": 4.4,
      "lat": -8.1234,
      "lon": 127.5678,
      "language": "en",
      "disaster_type": "earthquake",
      "created_at": "2025-09-05T16:12:36.550000Z"
    }
  ]
}
```

## 🧪 Testing

### Test NLP and Geocoding Features
```bash
cd backend
python test_nlp_geocoding.py
```

Expected output:
- Language detection results
- Disaster type classification
- Location extraction
- Geocoding results
- Integrated processing examples

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f sahaayak-backend
docker-compose logs -f sahaayak-frontend

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d

# Access database
docker-compose exec db psql -U dev -d crisis

# Run migrations
docker-compose exec sahaayak-backend alembic upgrade head
```

## 🚨 Troubleshooting

### Common Issues

1. **spaCy model not found**
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **Database migration errors**
   ```bash
   # Check if columns exist
   docker-compose exec db psql -U dev -d crisis -c "\d items"
   
   # Add missing columns manually if needed
   docker-compose exec db psql -U dev -d crisis -c "ALTER TABLE items ADD COLUMN IF NOT EXISTS language VARCHAR;"
   ```

3. **Geocoding timeouts**
   - Check internet connection
   - Nominatim may be temporarily unavailable
   - Consider using alternative geocoding services

4. **OpenAI API errors**
   - Verify API key is set correctly
   - Check API quota and billing
   - Rule-based classification will still work without OpenAI

5. **Frontend "Failed to fetch" errors**
   - Ensure backend is running on port 8000
   - Check CORS configuration
   - Verify API endpoints are accessible

### Performance Optimization

- **Rate Limiting**: Nominatim geocoding has 1 second delay between requests
- **Batch Processing**: Use `/api/process-nlp-geocoding` for processing existing items in batches
- **Caching**: Consider implementing Redis caching for frequently geocoded locations
- **Database Indexing**: PostGIS spatial indexes are automatically created

## 🔮 Future Enhancements

1. **Multi-language spaCy models** for better NER in different languages
2. **Alternative geocoding services** (Google Maps, Mapbox) for better accuracy
3. **Advanced caching layer** for improved performance
4. **Confidence scoring** for all classifications
5. **Custom disaster type training** for domain-specific classification
6. **Real-time notifications** for critical disasters
7. **Mobile app** for field reporting
8. **Machine learning models** for disaster prediction

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **USGS** for providing earthquake data
- **OpenStreetMap** for geocoding services
- **spaCy** for natural language processing
- **FastAPI and React** communities for amazing tools
- **All contributors** who helped improve this project

## 📞 Support

For issues and questions:
- Check the [API documentation](http://localhost:8000/docs) when running
- Review the logs: `docker-compose logs sahaayak-backend`
- Verify USGS feed status: https://earthquake.usgs.gov/earthquakes/feed/
- Check application logs for detailed error messages

---

**Sahaayak AI** - Intelligent disaster monitoring and response made simple 🌍🤖