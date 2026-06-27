# Deployment Notes

## GitHub

```bash
git init
git add .
git commit -m "Build SchoolProcure procurement system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/SchoolProcure.git
git push -u origin main
```

## PythonAnywhere

1. Upload or clone the GitHub repository into `/home/YOUR_USERNAME/SchoolProcure`.
2. Create a virtual environment and install dependencies:

   ```bash
   cd /home/YOUR_USERNAME/SchoolProcure
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py seed_demo
   python manage.py collectstatic
   ```

3. Set the WSGI file using `pythonanywhere_wsgi.py` and replace `YOUR_PYTHONANYWHERE_USERNAME`.
4. Add static mapping `/static/` to `/home/YOUR_USERNAME/SchoolProcure/staticfiles`.
5. Add media mapping `/media/` to `/home/YOUR_USERNAME/SchoolProcure/media`.
6. Reload the web app.

## Email

The development app uses Django's console email backend. For production, configure SMTP credentials through environment variables or add provider-specific SMTP settings in `schoolprocure/settings.py`.
