# 🌍 Sahaayak AI: Earthquake Monitoring System

A real-time earthquake monitoring platform with a React frontend and FastAPI backend that visualizes seismic data from USGS. The application provides an interactive map with real-time earthquake updates and allows users to submit incident reports.

## 🌟 Features

### Backend (FastAPI)
- 🌍 **Real-time earthquake data** from USGS
- 📍 **Location-based incident reporting**
- 🏥 **Health monitoring** with built-in health check endpoint
- 🐳 **Docker support** for easy deployment
- 📊 **Comprehensive data** including location, magnitude, and time
- 🔄 **Auto-reload** development server

### Frontend (React)
- 🗺️ **Interactive map** using React Leaflet
- 📱 **Responsive design** for all device sizes
- ⚡ **Real-time updates** every minute
- 📍 **Color-coded markers** for different data sources
- 📝 **Incident reporting** with photo uploads
- 🔄 **Manual refresh** capability
- 💬 **Rich popups** with detailed disaster information
- 🔍 **Advanced filtering** by disaster type, date, and severity
- 🕒 **Auto-refreshing** data without page reload
- 🌐 **Responsive layout** for all screen sizes

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Node.js 16+ (for frontend development)
- Python 3.9+ (for backend development)

### Using Docker (Recommended)

1. **Clone and navigate to the project**
   ```bash
   git clone https://github.com/yourusername/sahaayak-ai.git
   cd sahaayak-ai
   ```

2. **Start all services**
   ```bash
   docker-compose up -d --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## 🔧 Development

### Backend Development

1. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the development server**
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
- `POST /ingest/citizen-report` - Submit a new incident report (multipart form)
  - Parameters: `text`, `lat`, `lon`, `file` (optional)

### Data Retrieval
- `GET /api/items` - Get all items (earthquakes and reports)
- `GET /ingest/load-sample` - Load sample data (development only)

### Health Check
- `GET /health` - Service health status

### Static Files
- `GET /uploads/{filename}` - Access uploaded files

## 🏗️ Project Structure

```
sahaayak-ai/
├── backend/               # FastAPI application
│   ├── main.py           # Main application file
│   ├── models.py         # Database models
│   ├── db.py             # Database configuration
│   ├── fetch_usgs.py     # USGS data fetcher
│   ├── seeds/            # Sample data
│   └── requirements.txt  # Python dependencies
├── frontend/             # React application
│   ├── public/           # Static files
│   ├── src/              # React components
│   │   ├── app.jsx       # Main application component
│   │   └── ...
│   └── package.json      # Frontend dependencies
├── docker-compose.yml    # Multi-container setup
└── README.md            # This file
```

## 📝 Data Source
- **USGS**: Real-time earthquake data from the United States Geological Survey
- **Citizen Reports**: User-submitted incident reports with location and details

## 📝 Usage Examples

### Get live earthquake events
```bash
curl http://localhost:8000/realtime/earthquakes
```

### Filter by magnitude (example response)
```json
[
  {
    "id": "us7000m123",
    "magnitude": 4.2,
    "place": "10 km NE of Los Angeles, CA",
    "time": "2025-08-29T17:45:30.000Z",
    "longitude": -118.1234,
    "latitude": 34.0522,
    "depth": 8.5,
    "alert": null,
    "tsunami": 0,
    "title": "M 4.2 - 10 km NE of Los Angeles, CA"
  }
]
```

## 🔄 Environment Variables

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `DOCKER_ENV`: Set to 'true' when running in Docker
- `USGS_API_URL`: USGS API endpoint (default: https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson)

### Frontend
- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8000)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- USGS for providing the earthquake data
- FastAPI and React communities for amazing tools
- All contributors who helped improve this project

## Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f sahaayak-backend

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

## Development

### Adding New Features

1. **Modify the FastAPI app** in `backend/main.py`
2. **Add data processing logic** in `backend/fetch_usgs.py`
3. **Update dependencies** in `backend/requirements.txt`
4. **Test locally** with `python main.py`

### Environment Variables

The application supports the following environment variables:

- `PYTHONPATH`: Python module search path (default: `/app`)
- `PYTHONUNBUFFERED`: Disable Python output buffering (default: `1`)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For issues and questions:
- Check the [API documentation](http://localhost:8000/docs) when running
- Review the logs: `docker-compose logs sahaayak-backend`
- Verify USGS feed status: https://earthquake.usgs.gov/earthquakes/feed/

---

**Sahaayak AI** - Real-time earthquake monitoring made simple 🌍
