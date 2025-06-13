# Can You Use Uvicorn with SSL/TLS Encryption?


## Option 1: Run Uvicorn Directly with SSL Certs:
If you have .pem or .crt and .key files (e.g., from Let's Encrypt), you can do:
```bash
uvicorn labhub.asgi:application \
  --host 0.0.0.0 \
  --port 443 \
  --ssl-keyfile /path/to/privkey.pem \
  --ssl-certfile /path/to/fullchain.pem
```
Then your app will run over:
https://yourdomain.com

## Option 2: Use Nginx as a Reverse Proxy (Most Common in Production)
Nginx handles SSL


Nginx forwards traffic to your Uvicorn app running on port 8000
```Nginx
Example : server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

This is more secure and flexible, especially when deploying on servers or cloud platforms.
# Encryption & Secure-API Best Practices  
*(Phase 3 – Encryption Research)*

## 1  Why SSL/TLS Is Critical for Django APIs
| Risk with HTTP | How TLS Solves It |
|---------------|-------------------|
| Anyone on the network can **read** or **modify** requests (MITM). | TLS encrypts data in transit, so intercepted traffic is unreadable. |
| Clients can be tricked into talking to a **fake server**. | Certificates prove your server’s identity. |
| API tokens / passwords travel in **plain text**. | Tokens & credentials stay encrypted end-to-end. |

Result: **HTTPS (TLS) is mandatory** for any production API that handles credentials, PII, or research data.

---

## 2  Adding SSL/TLS in Uvicorn

### 2.1  Quick Local Test (Self-Signed Cert)

```bash
# generate a quick self-signed cert (valid for localhost only)
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=localhost"

# run Uvicorn with TLS
uvicorn labhub.asgi:application \
  --host 0.0.0.0 --port 8443 \
  --ssl-keyfile key.pem \
  --ssl-certfile cert.pem


## Resources:

https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/uvicorn/?utm_source=chatgpt.com

https://www.uvicorn.org/deployment/?utm_source=chatgpt.com#running-from-the-command-line

https://medium.com/%40mariovanrooij/adding-https-to-fastapi-ad5e0f9e084e

https://www.valentinog.com/blog/uvicorn-django/?utm_source=chatgpt.com

https://realpython.com/django-nginx-gunicorn/?utm_source=chatgpt.com
