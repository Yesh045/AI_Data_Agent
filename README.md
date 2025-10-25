# AI Analyst Dashboard

A complete single-page web application that provides AI-powered analysis of SQL databases with real-time chat interface and dynamic visualizations.

## 🎯 Features

- **Auto Dashboard**: Automatically generates 4 pre-built charts on startup
- **AI Chat Interface**: Natural language queries powered by Google Gemini API
- **SQL Generation**: AI automatically generates SQL queries from natural language
- **Dynamic Visualizations**: On-demand chart creation with Chart.js
- **Responsive Design**: Clean, modern UI that works on all devices
- **Real-time Analysis**: Instant responses and data exploration

## 🚀 Quick Start

1. **Activate Virtual Environment**:
   ```bash
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate    # Windows
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**:
   Create a `.env` file with your Google API key:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

4. **Run the Application**:
   ```bash
   python app.py
   ```

5. **Open in Browser**:
   Navigate to `http://localhost:5000`

## 🧩 Architecture

### Backend (Flask)
- **Database Connection**: SQLite with automatic schema detection
- **AI Integration**: Google Gemini API for SQL generation and analysis
- **REST API**: Clean endpoints for dashboard and chat functionality
- **Security**: Read-only SQL queries with injection protection

### Frontend (HTML/CSS/JS)
- **Responsive Layout**: Two-panel design (40% chat, 60% dashboard)
- **Chart.js Integration**: Dynamic visualizations
- **Real-time Chat**: Instant AI responses with typing indicators
- **Modern UI**: Clean design with smooth animations

## 📊 Database Schema

The application connects to `college.db` with the following tables:
- **students**: Student information (ID, name, major, GPA, enrollment year)
- **courses**: Course catalog (ID, title, department, credits)
- **enrollment**: Student-course relationships (enrollment ID, student ID, course ID, semester, grade)
- **faculty**: Faculty information (ID, name, department, hire date)

## 🔗 API Endpoints

- `GET /` - Main dashboard page
- `GET /init_dashboard` - Initialize dashboard with pre-built charts
- `POST /chat` - Handle AI chat queries

## 💬 Example Queries

Try these natural language queries:
- "Show me all students in Computer Science"
- "What are the top 5 courses by enrollment?"
- "Plot average GPA by major"
- "How many students are enrolled in each department?"
- "Show me students with GPA above 3.5"

## 🎨 Features

### Auto Dashboard
- Total student count
- Students by major (bar chart)
- Average GPA by major (line chart)
- Course enrollment distribution (pie chart)

### AI Chat
- Natural language processing
- Automatic SQL generation
- Data table display
- On-demand chart creation
- Conversation history

### Visualizations
- Bar charts
- Line charts
- Pie charts
- Metric cards
- Responsive design

## 🛠️ Technical Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js
- **AI**: Google Gemini API
- **Database**: SQLite
- **Styling**: Modern CSS with Inter font

## 🔒 Security

- Read-only database access
- SQL injection protection
- Input validation
- Safe query execution

## 📱 Responsive Design

- Desktop: Two-panel layout
- Tablet: Stacked panels
- Mobile: Optimized single-column layout

## 🎯 Demo Ready

The application is fully functional and demo-ready with:
- Instant dashboard loading
- Working AI chat interface
- Dynamic chart generation
- Professional UI/UX
- Error handling and fallbacks

Perfect for presentations and demonstrations!