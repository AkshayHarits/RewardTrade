# NPCI_Ecell-Lunatics

**Project Overview: Unified Points System**

The **Unified Points System (UPS)** is an innovative platform designed to address inefficiencies in traditional loyalty programs. It enables seamless conversion, accumulation, and utilization of points across multiple merchants. By integrating a **Liquidity Pool** for instant exchanges and a **P2P Trading System** for market-driven rates, the UPS offers flexibility and value to customers while providing merchants with critical data insights and cost savings. 

Key features include:  
1. **Hybrid Exchange Mechanism**: Combines instant execution and dynamic rate trading via Smart Routing.  
2. **Scalable Architecture**: Includes secure APIs, real-time databases, and AI-driven fraud prevention.  
3. **Enhanced User Experience**: A unified interface for managing points, offering convenience and better returns.  

The UPS revolutionizes loyalty programs by fostering engagement, reducing fragmentation, and unlocking untapped value for all stakeholders.

**Please go through 'Unified Points System.pdf' for detailed overview of the project.**

**Credits:-**
Sashim Suryawanshi,
Akshay Harits,
Dhruv Goyal,
Ramuni Lalith Vishnu

# RewardTrade - Unified Points System

RewardTrade is a platform that allows users to manage and convert loyalty points across multiple merchants.

## Setup Instructions

1. Clone the repository:

git clone https://github.com/yourusername/rewardtrade.git
cd rewardtrade


2. Create a virtual environment and activate it:

python -m venv venv
source venv/bin/activate # On Windows, use venv\Scripts\activate


3. Install the required packages:

pip install -r requirements.txt


4. Set up the database:

 flask db init
 flask db migrate
 flask db upgrade


5. Start the Redis server (required for Celery):

  redis-server


6. In a new terminal, start the Celery worker:

celery -A app.celery worker --loglevel=info


7. In another terminal, start the Flask development server:

python run.py


8. Open a web browser and navigate to `http://127.0.0.1:5000` to access the application.

## Features

- User registration and authentication
- View and manage loyalty points across multiple merchants
- Convert points between merchants using instant or smart exchange
- Automatic liquidity pool rebalancing

## API Endpoints

- `/api/<merchant>/rewards/<phone>`: Get user points for a specific merchant
- `/api/<merchant>/rewards/update`: Update user points for a specific merchant
- `/api/<merchant>/rewards/reset`: Reset user points for testing purposes
- `/api/health`: Check API status

## Known Issues and Future Improvements

- Implement proper error handling and logging
- Enhance security features (e.g., rate limiting, input validation)
- Improve calculation accuracy for point conversions
- Add unit tests and integration tests
- Implement a more sophisticated matching algorithm for smart exchanges

## Contributors

- Sashim Suryawanshi
- Akshay Harits
- Dhruv Goyal
- Ramuni Lalith Vishnu

## License

This project is licensed under the MIT License.
