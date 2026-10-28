# Digital Wallet Platform — API Documentation

## 1. Overview

The Digital Wallet Platform is a REST API application built using FastAPI and PostgreSQL. It supports digital wallet management, deposits, transfers, transaction tracking, transaction limits, and administrative operations.

### Base URL

```text
http://127.0.0.1:8000
```

### API Documentation Interfaces

* Swagger UI: `/docs`
* ReDoc: `/redoc`
* OpenAPI JSON: `/openapi.json`

## 2. Authentication

Protected endpoints require a valid access token.

### Authorization Header

```http
Authorization: Bearer <access_token>
```

### Common Authentication Errors

**401 Unauthorized**

```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden**

```json
{
  "detail": "Not enough permissions"
}
```

The exact error response depends on the authentication and authorization implementation.

## 3. Authentication APIs

Consult Swagger UI for the registered authentication routes.

| Method | Endpoint         | Description                               |
| ------ | ---------------- | ----------------------------------------- |
| POST   | `/auth/register` | Register a user                           |
| POST   | `/auth/login`    | Authenticate a user                       |
| GET    | `/auth/me`       | Retrieve the authenticated user's details |

### Example: Login

**Request**

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded
```

Example form fields:

```text
username=user@example.com
password=your_password
```

The actual login fields depend on the configured authentication schema.

## 4. Wallet APIs

| Method | Endpoint                            | Description                     |
| ------ | ----------------------------------- | ------------------------------- |
| POST   | `/api/wallets`                      | Create a wallet                 |
| GET    | `/api/wallets`                      | Retrieve wallets                |
| GET    | `/api/wallets/{wallet_id}`          | Retrieve a wallet by ID         |
| PATCH  | `/api/wallets/{wallet_id}`          | Update supported wallet details |
| PATCH  | `/api/wallets/{wallet_id}/freeze`   | Freeze a wallet                 |
| PATCH  | `/api/wallets/{wallet_id}/unfreeze` | Unfreeze a wallet               |

### Example: Create Wallet

**Request**

```http
POST /api/wallets
Authorization: Bearer <access_token>
Content-Type: application/json
```

Example request body:

```json
{
  "currency": "USD"
}
```

The request fields must match the actual wallet creation schema.

### Example: Wallet Response

```json
{
  "id": 2,
  "user_id": 2,
  "available_balance": "1000.00",
  "pending_balance": "0.00",
  "currency": "USD",
  "status": "ACTIVE"
}
```

This is an illustrative response. Actual fields depend on the implemented response schema.

## 5. Deposit API

### Create Deposit

**Endpoint**

```http
POST /deposits/wallets/{wallet_id}/deposits
```

**Headers**

```http
Authorization: Bearer <access_token>
Idempotency-Key: deposit-unique-001
Content-Type: application/json
```

Example request body:

```json
{
  "amount": "100.00",
  "currency": "USD"
}
```

Use the actual deposit request schema if the implementation accepts different fields.

### Example Response

```json
{
  "id": 3,
  "wallet_id": 2,
  "amount": "100.00",
  "currency": "USD",
  "status": "COMPLETED"
}
```

The response is illustrative and must be checked against the actual API.

## 6. Transfer APIs

| Method | Endpoint                              | Description                   |
| ------ | ------------------------------------- | ----------------------------- |
| POST   | `/api/transfers`                      | Create a wallet transfer      |
| GET    | `/api/transfers/{transfer_id}`        | Retrieve transfer details     |
| POST   | `/api/transfers/{transfer_id}/cancel` | Request transfer cancellation |

### Create Transfer

**Request**

```http
POST /api/transfers
Authorization: Bearer <access_token>
Idempotency-Key: transfer-unique-001
Content-Type: application/json
```

**Request Body**

```json
{
  "sender_wallet_id": 2,
  "receiver_wallet_id": 4,
  "amount": "100.00",
  "currency": "USD"
}
```

### Example Successful Response

```json
{
  "id": 3,
  "sender_wallet_id": 2,
  "receiver_wallet_id": 4,
  "amount": "100.00",
  "currency": "USD",
  "status": "COMPLETED"
}
```

### Transfer Validation

The application should validate:

* Sender and receiver wallets exist.
* The sender has permission to initiate the transfer.
* The wallets are eligible for transactions.
* Sender and receiver are different wallets.
* Both wallets use the same currency.
* The transfer amount is valid.
* The sender has sufficient available balance.
* Transaction limits are respected.
* Duplicate requests are handled safely.

The exact validation behavior depends on the implemented business rules.

## 7. Withdrawal APIs

Withdrawal endpoints must be documented using the actual registered routes.

A withdrawal request generally includes the wallet identifier, amount, and any required idempotency header.

Example error:

```json
{
  "detail": "Insufficient balance"
}
```

Use the actual withdrawal endpoint, request schema, and error response from Swagger UI.

## 8. Refund APIs

Refund endpoints should document:

* The original transaction or transfer reference
* Refund amount, if supplied by the request
* Refund eligibility rules
* Duplicate refund prevention
* Refund status transitions
* Successful response and error responses

Only document the refund routes that are implemented in the application.

## 9. Transaction History

Transaction history endpoints should describe how clients retrieve ledger entries or transaction records.

Document the supported filters, pagination parameters, ownership rules, and response schema.

Example ledger entry:

```json
{
  "id": 4,
  "transaction_type": "TRANSFER_DEBIT",
  "amount": "100.00",
  "balance_before": "1100.00",
  "balance_after": "1000.00"
}
```

This example illustrates a debit ledger entry and is not a guarantee of the actual API response structure.

## 10. Transaction Limits

The application may enforce daily or per-transaction limits.

Example error:

```json
{
  "detail": "Daily withdrawal limit exceeded"
}
```

Document the configured limits, relevant endpoints, and actual status codes used by the application.

## 11. Suspicious Transaction Detection

Where implemented, document:

* Suspicious transaction detection rules
* The transaction attributes evaluated
* How suspicious activity is recorded
* Whether the transaction is blocked, flagged, or reviewed
* Permissions required to access detection results

Do not expose sensitive detection rules to unauthorized users.

## 12. Daily Transaction Reports

Document the report endpoints that are actually registered.

Report responses may include:

* Report period
* Transaction status
* Transaction count
* Total transaction amount

Example:

```json
{
  "status": "COMPLETED",
  "count": 4,
  "total_amount": "1300.00"
}
```

The actual report response may contain additional fields.

## 13. Idempotency

Financial operations may use the `Idempotency-Key` header.

Example:

```http
Idempotency-Key: transfer-unique-001
```

Expected behavior:

* Repeating the same request with the same key must not execute the operation twice.
* Reusing the same key with a different request should be rejected.
* Concurrent requests using the same key must not create duplicate financial operations.

### Example Conflict Response

```json
{
  "detail": "This Idempotency-Key was already used with a different request."
}
```

The actual response status and replay behavior depend on the implementation.

## 14. Common HTTP Status Codes

| Status Code | Meaning                                      |
| ----------- | -------------------------------------------- |
| 200         | Request successful                           |
| 201         | Resource created                             |
| 400         | Invalid operation or business rule violation |
| 401         | Authentication required or invalid           |
| 403         | Permission denied                            |
| 404         | Resource not found                           |
| 409         | Conflict, such as an idempotency conflict    |
| 422         | Request validation failed                    |
| 500         | Unexpected server error                      |

These are common HTTP status codes. Each endpoint should document the codes it actually returns.

## 15. Validation Error Example

FastAPI may return a `422 Unprocessable Entity` response when request validation fails.

```json
{
  "detail": [
    {
      "loc": [
        "body",
        "amount"
      ],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

The exact error structure depends on the validation failure.

## 16. Testing APIs

Start the application:

```powershell
uvicorn app.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Use Swagger UI or the Postman Collection to test the registered endpoints.

For every endpoint, verify:

1. Successful request.
2. Invalid request body.
3. Missing or invalid authentication.
4. Insufficient permissions.
5. Resource not found.
6. Relevant business rule violations.
7. Duplicate request handling where idempotency applies.

## 17. Security Notes

* Use HTTPS in production.
* Store passwords securely using an appropriate password-hashing algorithm.
* Protect access tokens and secrets.
* Enforce ownership and role permissions.
* Validate financial amounts.
* Use database transactions for balance updates.
* Apply appropriate database locking and constraints.
* Avoid logging passwords, access tokens, or sensitive payment information.

---

**Documentation status:** Draft. Verify all endpoint paths, request fields, response schemas, and status codes against the running application before final submission.
