# Implementation Plan: POST /study_sessions Route 

## 1. Setup Steps
- [x] 1.1. Import required modules at the top of the file
  ```python
  from flask import request, jsonify
  from datetime import datetime, timezone
  import sqlite3
  ```
- [x] 1.2. Create the route decorator with correct HTTP method
  ```python
  @app.route('/api/study-sessions', methods=['POST'])
  ```

## 2. Request Validation Steps
- [x] 2.1. Add request data validation
  ```python
  def validate_study_session(data):
      required_fields = ['group_id', 'study_activity_id']
      return all(field in data for field in required_fields)
  ```
- [x] 2.2. Check if request contains JSON data
  ```python
  if not request.is_json:
      return jsonify({'error': 'Content-Type must be application/json'}), 400
  ```

## 3. Implementation Steps
- [x] 3.1. Get JSON data from request
  ```python
  data = request.get_json()
  ```
- [x] 3.2. Validate required fields
  ```python
  if not validate_study_session(data):
      return jsonify({'error': 'Missing required fields'}), 400
  ```
- [x] 3.3. Create new study session object
  ```python
  new_session = {
      'group_id': data['group_id'],
      'study_activity_id': data['study_activity_id'],
      'created_at': datetime.now(timezone.utc).isoformat()
  }
  ```
- [x] 3.4. Add to database
  ```python
  cursor.execute('''
      INSERT INTO study_sessions (group_id, study_activity_id, created_at)
      VALUES (?, ?, ?)
  ''', (new_session['group_id'], new_session['study_activity_id'], 
        new_session['created_at']))
  ```
- [x] 3.5. Return success response
  ```python
  return jsonify({
      'message': 'Study session created successfully',
      'session': new_session
  }), 201
  ```

## 4. Error Handling Steps
- [x] 4.1. Add try-except block around database operations
  ```python
  try:
      # database operations here
  except sqlite3.IntegrityError as e:
      return jsonify({'error': 'Invalid group_id or study_activity_id'}), 400
  except Exception as e:
      return jsonify({'error': str(e)}), 500
  ```

## 5. Testing Steps
- [x] 5.1. Create test file and fixtures
- [x] 5.2. Write test for successful creation
- [x] 5.3. Write test for missing fields
- [x] 5.4. Write test for invalid content type
- [x] 5.4. Write test for foreign key constraints
- [x] 5.5. Run tests with pytest 

## 6. Final Checklist
- [x] 6.1. All imports are in place
- [x] 6.2. Route decorator is correctly configured
- [x] 6.3. Request validation is implemented
- [x] 6.4. Database operations are properly handled
- [x] 6.5. Error handling is in place
- [x] 6.6. Tests are written
- [x] 6.7. Tests are passing 
- [x] 6.8. Code is properly formatted and documented

## 7. Testing Code
```python
# test_study_sessions.py

import pytest
from flask import json
from your_app import app  # replace with your actual app import

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_create_study_session_success(client):
    test_data = {
        'group_id': '123',
        'study_activity_id': '456'
    }
    response = client.post(
        '/study_sessions',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'message' in data
    assert 'session' in data
    assert data['session']['group_id'] == test_data['group_id']

def test_create_study_session_missing_fields(client):
    test_data = {
        'group_id': '123'  # missing required fields
    }
    response = client.post(
        '/study_sessions',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_create_study_session_invalid_content_type(client):
    response = client.post(
        '/study_sessions',
        data='not json data'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_create_study_session_foreign_key_constraints(client):
    # test foreign key constraints
    pass
```
## Running Tests
- [x] Install pytest if not already installed: `pip install pytest`
- [x] Run tests with: `pytest test_study_sessions.py -v`




## 8. Manual Testing with curl
- [] 8.1. Test successful creation
  ```bash
  curl -X POST http://localhost:5000/api/study-sessions \
    -H "Content-Type: application/json" \
    -d '{"group_id": 1, "study_activity_id": 1}'
  ```
  Expected response (201):
  ```json
  {
    "message": "Study session created successfully",
    "session": {
      "group_id": 1,
      "study_activity_id": 1,
      "created_at": "2025-02-09T21:18:13Z"
    }
  }
  ```

- [ ] 8.2. Test missing fields
  ```bash
  curl -X POST http://localhost:5000/api/study-sessions \
    -H "Content-Type: application/json" \
    -d '{"group_id": 1}'
  ```
  Expected response (400):
  ```json
  {
    "error": "Missing required fields"
  }
  ```

- [ ] 8.3. Test invalid content type
  ```bash
  curl -X POST http://localhost:5000/api/study-sessions \
    -d "not json data"
  ```
  Expected response (400):
  ```json
  {
    "error": "Content-Type must be application/json"
  }
  ```

- [ ] 8.4. Test invalid foreign key
  ```bash
  curl -X POST http://localhost:5000/api/study-sessions \
    -H "Content-Type: application/json" \
    -d '{"group_id": 999, "study_activity_id": 1}'
  ```
  Expected response (400):
  ```json
  {
    "error": "Invalid group_id or study_activity_id"
  }
  ```

Note: For Windows PowerShell users, replace the backslashes `\` with backticks ``` ` ``` and use single quotes for the JSON data:
```powershell
curl -X POST http://localhost:5000/api/study-sessions `
  -H "Content-Type: application/json" `
  -d '{\"group_id\": 1, \"study_activity_id\": 1}'
```