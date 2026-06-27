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

Repository:

- URL: `https://github.com/eddiemac1993/swiftfind.git`
- Branch: `schoolprocure`

1. Create or log into your PythonAnywhere account.
2. Open a Bash console and run:

   ```bash
   git clone --branch schoolprocure https://github.com/eddiemac1993/swiftfind.git ~/SchoolProcure
   cd ~/SchoolProcure
   bash pythonanywhere_setup.sh
   ```

3. In the PythonAnywhere Web tab, create a manual web app.
4. Set the virtualenv path:

   ```text
   /home/YOUR_USERNAME/SchoolProcure/.venv
   ```

5. Replace the WSGI file contents with the contents of:

   ```text
   /home/YOUR_USERNAME/SchoolProcure/pythonanywhere_wsgi.py
   ```

6. Add static files mapping:

   ```text
   URL: /static/
   Directory: /home/YOUR_USERNAME/SchoolProcure/staticfiles
   ```

7. Add media files mapping:

   ```text
   URL: /media/
   Directory: /home/YOUR_USERNAME/SchoolProcure/media
   ```

8. Reload the web app.

Manual commands, if you do not use the setup script:

   ```bash
   cd /home/YOUR_USERNAME/SchoolProcure
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py seed_demo
   python manage.py collectstatic
   ```

## Email

The development app uses Django's console email backend. For production, configure SMTP credentials through environment variables or add provider-specific SMTP settings in `schoolprocure/settings.py`.
