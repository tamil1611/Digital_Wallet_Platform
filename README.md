# Digital Wallet Platform

## 1. Project Overview

The Digital Wallet Platform is a secure REST API application developed using FastAPI and PostgreSQL. It enables users to manage digital wallets and perform financial transactions such as deposits, transfers, withdrawals, and refunds.

The application focuses on secure authentication, transaction integrity, wallet balance management, idempotency, and concurrent transaction handling.

## 2. Key Features

* User registration and authentication
* JWT-based access control
* Role-based authorization
* Digital wallet creation and management
* Wallet freeze and unfreeze functionality
* Deposit management
* Wallet-to-wallet transfers
* Transaction ledger
* Idempotent transaction processing
* Transaction limits
* Suspicious transaction detection
* Daily transaction reports
* Audit logging
* PostgreSQL database integration
* Database schema migrations using Alembic
* Automated testing using Pytest
* Interactive API documentation using Swagger UI

> Features should be considered complete only when they are implemented and tested in the application.

## 3. Technology Stack

| Technology     | Purpose                                 |
| -------------- | --------------------------------------- |
| Python         | Backend programming language            |
| FastAPI        | REST API development                    |
| PostgreSQL     | Relational database                     |
| SQLAlchemy     | ORM and database operations             |
| Alembic        | Database migrations                     |
| Pydantic       | Request validation and serialization    |
| JWT            | Authentication                          |
| Pytest         | Automated testing                       |
| Postman        | API testing                             |
| Git and GitHub | Version control and source code hosting |

## 4. Project Structure

```text
digital_wallet_platform/
├── app/
│   ├── main.py
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   ├── services/
│   ├── repositories/
│   └── utils/
├── alembic/
│   └── versions/
├── tests/
├── docs/
├── postman/
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

The directory structure above represents the intended organization. Adjust it to match the actual repository.

## 5. Prerequisites

Install the following before running the application:

* Python
* PostgreSQL
* Git
* Postman (optional, for API testing)

## 6. Installation

### Step 1: Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd digital_wallet_platform
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with the actual repository URL.

### Step 2: Create a Virtual Environment

On Windows:

```powershell
py -m venv venv
```

Activate the environment:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

## 7. Environment Configuration

Create a `.env` file in the project root directory.

Example:

```dotenv
DATABASE_URL=postgresql://username:password@localhost:5432/wallet_management_db
SECRET_KEY=replace_with_a_secure_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Update the database credentials and configuration values for your local environment.

**Security notes:**

* Never commit the actual `.env` file to GitHub.
* Use a strong, randomly generated secret key.
* Keep production credentials outside the source code.
* Configure separate credentials for development and production.

## 8. Database Setup

### Step 1: Create the PostgreSQL Database

Open PostgreSQL or use `psql`:

```sql
CREATE DATABASE wallet_management_db;
```

### Step 2: Configure the Database URL

Update the `DATABASE_URL` value in your `.env` file.

Example:

```dotenv
DATABASE_URL=postgresql://username:password@localhost:5432/wallet_management_db
```

Replace `username` and the password with your PostgreSQL credentials.

### Step 3: Apply Database Migrations

Check the current migration:

```powershell
alembic current
```

Check available migration heads:

```powershell
alembic heads
```

Apply migrations:

```powershell
alembic upgrade head
```

Ensure that the migrations complete successfully before starting the application.

## 9. Run the Application

Start the FastAPI development server:

```powershell
uvicorn app.main:app --reload
```

The local server should be available at:

`http://127.0.0.1:8000`

### Interactive API Documentation

Swagger UI:

`http://127.0.0.1:8000/docs`

ReDoc:

`http://127.0.0.1:8000/redoc`

OpenAPI schema:

`http://127.0.0.1:8000/openapi.json`

These are the default FastAPI documentation paths unless they have been customized in the application.

## 10. API Modules

The application may expose the following API modules, depending on the implemented routers.

| Module             | Description                                  |
| ------------------ | -------------------------------------------- |
| Authentication     | Registration, login, and user authentication |
| Wallets            | Wallet creation and management               |
| Deposits           | Adding funds to wallets                      |
| Transfers          | Transferring funds between wallets           |
| Withdrawals        | Withdrawing funds                            |
| Refunds            | Processing eligible refunds                  |
| Transactions       | Transaction history and details              |
| Administration     | User and wallet administration               |
| Transaction Limits | Enforcing transaction limits                 |
| Audit Logs         | Tracking important application actions       |
| Reports            | Daily transaction summaries                  |

Refer to Swagger UI for the actual registered endpoints and request schemas.

## 11. Transaction Integrity and Concurrency

Financial transactions must maintain consistent wallet balances and ledger records.

The application uses or should implement the following safeguards where appropriate:

* Database transactions for related financial updates
* Row-level locking when processing concurrent transfers
* Consistent wallet-locking order to reduce deadlocks
* Database constraints to protect data integrity
* Idempotency keys to prevent duplicate transaction processing
* Balance validation before debiting a wallet
* Ledger records for financial transaction tracking
* Atomic commits or rollbacks when a transaction fails

For a transfer, the sender debit, receiver credit, transfer status, and associated ledger entries must be handled consistently within the database transaction.

A failed operation must not leave only one wallet updated.

## 12. Idempotency

Idempotency helps prevent the same financial operation from being processed more than once when a client retries a request.

For example, a transfer request may include:

```http
Idempotency-Key: transfer-unique-001
```

The server should ensure that:

* Repeating the same key with the same request does not execute the financial operation twice.
* Reusing a key with a different request is rejected.
* Concurrent requests using the same key cannot create duplicate transactions.

The exact response behavior depends on the implemented idempotency logic.

## 13. Automated Testing

Run the test suite using:

```powershell
pytest -v
```

For detailed output:

```powershell
pytest -v -s
```

Important test scenarios include:

* User registration and authentication
* Wallet creation and retrieval
* Successful deposits
* Successful transfers
* Insufficient balance
* Frozen wallet restrictions
* Invalid transfer requests
* Duplicate idempotency keys
* Transaction limits
* Authorization failures
* Ledger consistency
* Concurrent transfer processing

Record the actual test results before reporting the project as fully tested.

## 14. Postman Collection

The Postman Collection can be used to test API endpoints manually.

Recommended collection folders:

* Authentication
* Wallets
* Deposits
* Transfers
* Withdrawals
* Refunds
* Transactions
* Administration
* Reports

Export the collection as JSON and save it in the `postman/` directory.

Example filename:

`Digital_Wallet_Platform.postman_collection.json`

Only include endpoints that exist in the application.

## 15. Database Models and Migrations

The application may contain database models for:

* Users
* Wallets
* Transfers
* Deposits
* Withdrawals
* Transactions or ledger entries
* Idempotency records
* Transaction limits
* Audit logs
* Notifications

The actual models and relationships should be documented according to the current SQLAlchemy models and Alembic migrations.

To create a new migration after modifying models:

```powershell
alembic revision --autogenerate -m "describe_schema_change"
```

Review the generated migration before applying it.

Apply migrations:

```powershell
alembic upgrade head
```

## 16. API Documentation

API documentation is available through FastAPI's automatically generated OpenAPI documentation.

It provides:

* Endpoint paths and HTTP methods
* Request parameters
* Request body schemas
* Response schemas
* Authentication requirements
* Available HTTP status codes

Additional examples and error scenarios should be documented in `docs/API_DOCUMENTATION.md`.

## 17. Architecture

The application follows a layered backend architecture:

```text
Client / Postman
       |
       v
FastAPI Application
       |
       v
Authentication and Authorization
       |
       v
API Routers
       |
       v
Service Layer
       |
       v
Repository / SQLAlchemy
       |
       v
PostgreSQL Database
```

The router layer handles HTTP requests, the service layer contains business logic, and the database layer manages persistence.

Adapt this diagram to match the actual dependencies and modules in the project.

## 18. Security Considerations

* Hash passwords before storing them.
* Authenticate protected endpoints.
* Enforce role-based permissions.
* Validate request data.
* Protect sensitive configuration values.
* Use database transactions for financial operations.
* Enforce wallet ownership and status checks.
* Validate transaction amounts and available balances.
* Prevent duplicate processing through idempotency.
* Avoid exposing sensitive information in error messages and logs.

## 19. Future Improvements

Potential improvements include:

* Docker-based deployment
* Redis-based caching and distributed coordination
* Background notification processing
* Rate limiting
* Enhanced monitoring and alerting
* CI/CD automation
* Additional integration and concurrency tests

These items are future improvements unless already implemented.

## 20. License

Add the appropriate license information if the project is distributed under an open-source license.

---

**Project:** Digital Wallet Platform
**Backend Framework:** FastAPI
**Database:** PostgreSQL
**ORM:** SQLAlchemy
**Migration Tool:** Alembic
**Testing Framework:** Pytest
