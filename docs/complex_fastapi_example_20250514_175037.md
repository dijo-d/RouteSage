# Complex FastAPI Example

Demonstrating advanced FastAPI features

**Version:** 1.0.0

**Generated:** 2025-05-14 17:50:37

## Table of Contents

### authentication
- [POST /token](#token)

### users
- [POST /users/](#users-)
- [GET /users/me/](#users-me-)
- [GET /users/](#users-)

### items
- [POST /items/](#items-)
- [GET /items/](#items-)
- [GET /items/{item_id}](#items-{item_id})
- [PUT /items/{item_id}](#items-{item_id})
- [DELETE /items/{item_id}](#items-{item_id})

### health
- [GET /health](#health)


---

## authentication

### POST /token {#token}

**Summary:** Login to obtain an access token

Authenticates a user and returns an access token upon successful authentication. Uses OAuth2 password flow.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| form_data | body | ✓ | OAuth2 password request form containing username and password. |

---

## users

### POST /users/ {#users-}

**Summary:** Create a new user

Registers a new user in the system. Requires username, email, full name, password, and role. Username must be unique.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| user | body | ✓ | User data for registration. |

---

### GET /users/me/ {#users-me-}

**Summary:** Get current user's information

Retrieves the information of the currently authenticated user.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| current_user | dependency | ✓ | The currently authenticated user, injected as a dependency. Requires a valid access token. |

---

### GET /users/ {#users-}

**Summary:** Read users

Retrieves a list of users. Requires admin privileges. Supports pagination with skip and limit parameters.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| current_user | dependency | ✓ | The currently authenticated user, injected as a dependency. Requires admin privileges. |
| skip | query | ✗ | Number of users to skip for pagination. |
| limit | query | ✗ | Maximum number of users to return. |

---

## items

### POST /items/ {#items-}

**Summary:** Create a new item

Creates a new item in the system. Requires item details (name, description, price, tax). The item is associated with the currently authenticated user.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| item | body | ✓ | Item data for creation. |
| current_user | dependency | ✓ | The currently authenticated user, injected as a dependency. Requires a valid access token. |

---

### GET /items/ {#items-}

**Summary:** Read items

Retrieves a list of items. Supports pagination with skip and limit parameters. Allows filtering by minimum and maximum price. Requires a valid access token.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| current_user | dependency | ✓ | The currently authenticated user, injected as a dependency. Requires a valid access token. |
| skip | query | ✗ | Number of items to skip for pagination. |
| limit | query | ✗ | Maximum number of items to return. |
| min_price | query | ✗ | Minimum price of the items to return. |
| max_price | query | ✗ | Maximum price of the items to return. |

---

### GET /items/{item_id} {#items-{item_id}}

**Summary:** Read a specific item

Retrieves a specific item by its ID. Requires a valid access token. Users can only access items they own, unless they are an admin.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| item_id | path | ✓ | ID of the item to retrieve. |
| current_user | dependency | ✓ | The currently authenticated user, injected as a dependency. Requires a valid access token. |

---

### PUT /items/{item_id} {#items-{item_id}}

**Summary:** Update a specific item

Updates a specific item by its ID. Requires a valid access token. Users can only update items they own, unless they are an admin.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| item_id | path | ✓ | ID of the item to update. |
| item_update | body | ✓ | Updated item data. |
| current_user | dependency | ✓ | The currently authenticated user, injected as a dependency. Requires a valid access token. |

---

### DELETE /items/{item_id} {#items-{item_id}}

**Summary:** Delete a specific item

Deletes a specific item by its ID. Requires a valid access token. Users can only delete items they own, unless they are an admin.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| item_id | path | ✓ | ID of the item to delete. |
| current_user | dependency | ✓ | The currently authenticated user, injected as a dependency. Requires a valid access token. |

---

## health

### GET /health {#health}

**Summary:** Health check endpoint

{
  "endpoints": [
    {
      "path": "/health",
      "methods": [
        "GET"
      ],
      "description": "This endpoint performs a health check on the API. It verifies that the API is running and responsive. It can be used by monitoring systems or other services to determine the availability and operational status of the application.",
      "parameters": [],
      "response": {
        "200": {
          "description": "Indicates that the API is healthy and operational. The response body typically contains a simple message confirming the API's status (e.g., 'OK' or a JSON object with a status field).",
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "status": {
                    "type": "string",
                    "description": "A status message indicating the health of the service. Usually 'OK'."
                  }
                },
                "example": {
                  "status": "OK"
                }
              }
            }
          }
        },
        "500": {
          "description": "Indicates that the API is not healthy. This could be due to database connection issues, internal errors, or other critical problems. The response body may contain error details.",
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "error": {
                    "type": "string",
                    "description": "A detailed error message explaining the cause of the health check failure."
                  }
                },
                "example": {
                  "error": "Database connection failed"
                }
              }
            }
          }
        }
      },
      "tags": [
        "health"
      ]
    }
  ]
}

---

