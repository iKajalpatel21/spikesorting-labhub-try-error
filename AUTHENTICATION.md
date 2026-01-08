# Authentication System Documentation

## Current Users

### Admin User
- **Username:** `admin`
- **Password:** Set during Django setup (initially `admin`)
- **Role:** Superuser (full access)
- **Access:** Django Admin + API

## Where Credentials Are Stored

### 1. **Django Database (SQLite)**
**Location:** `/Users/kajalpatel/spikesorting-labhub-try-error/db.sqlite3`

- User credentials are stored in the `auth_user` table
- Passwords are hashed using Django's default PBKDF2 algorithm
- **Never stored in plain text!**

```sql
Table: auth_user
Columns:
  - id (Primary Key)
  - username (Unique)
  - password (Hashed with PBKDF2)
  - email
  - first_name
  - last_name
  - is_staff (Boolean)
  - is_superuser (Boolean)
  - date_joined
```

### 2. **Authentication Tokens**
**Table:** `authtoken_token` (Django REST Framework)

- When a user logs in, a token is generated
- Token is stored securely in the database
- Client stores token in localStorage for session persistence

```sql
Table: authtoken_token
Columns:
  - key (Token string)
  - user_id (Foreign key to auth_user)
  - created (Timestamp)
```

### 3. **Client-Side Storage (Browser)**
**Location:** Browser's localStorage

```javascript
// Stored during login
localStorage.setItem('token', 'abc123def456...');
localStorage.setItem('user', JSON.stringify({ username: 'admin', id: 1 }));
```

- **Token:** Used for API authentication (sent in Authorization header)
- **User:** Display user info in the UI

## Authentication Flow

### Login Process
```
1. User enters username & password on Login Page
2. React sends POST to /qmodel/auth/login/
   {
     "username": "admin",
     "password": "admin"
   }
3. Django authenticates credentials against db.sqlite3
4. If valid:
   - Creates/gets authentication token
   - Returns token + user_id
   - React stores in localStorage
5. React redirects to Dashboard
6. All subsequent API calls include token:
   Authorization: Token abc123def456...
```

### Logout Process
```
1. User clicks Logout button
2. React clears localStorage (token & user)
3. Token remains in database (can be reused if user logs in again)
```

## How to Manage Users

### View All Users
```bash
cd /Users/kajalpatel/spikesorting-labhub-try-error
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.all().values('username', 'email', 'is_superuser')
```

### Create New User
```bash
python manage.py createsuperuser
# Follow prompts for username, email, password
```

### Create Regular User (Non-Admin)
```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.create_user(username='john', password='secure123')
```

### Change User Password
```bash
python manage.py changepassword admin
```

### Delete User
```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='admin')
>>> user.delete()
```

## Security Notes

### ✅ What's Secure
- Passwords are hashed with PBKDF2 (not stored in plain text)
- Tokens are generated server-side and validated
- HTTPS recommended in production (currently using HTTP for development)
- Token can be revoked by deleting from authtoken_token table

### ⚠️ What to Improve for Production
1. **Use environment variables for secrets**
   - Store Django SECRET_KEY in .env file
   - Never commit sensitive data to git

2. **Enable HTTPS**
   - Required for production
   - Use Django's SECURE_SSL_REDIRECT setting

3. **Use strong passwords**
   - Django validates password strength
   - Enforce password complexity in production

4. **Set token expiration**
   - Currently tokens never expire
   - Add token refresh mechanism for security

5. **CORS configuration**
   - Currently allows all origins in development
   - Restrict in production to your domain

## Database Location

```
Project Root
└── db.sqlite3  ← All credentials stored here
```

### Backing up credentials
```bash
# Backup database
cp db.sqlite3 db.sqlite3.backup

# Restore database
cp db.sqlite3.backup db.sqlite3
```

## Testing Authentication

### Test login endpoint directly
```bash
curl -X POST http://localhost:8000/qmodel/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Response:
# {
#   "token": "abc123def456...",
#   "user_id": 1,
#   "username": "admin"
# }
```

### Test protected endpoint with token
```bash
curl -H "Authorization: Token abc123def456..." \
  http://localhost:8000/qmodel/jobs/
```

## Default Credentials

- **Username:** admin
- **Password:** admin (initially set, can be changed with `python manage.py changepassword admin`)

⚠️ **Change this password immediately in production!**
