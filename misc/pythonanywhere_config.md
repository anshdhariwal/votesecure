# 🐍 PythonAnywhere Deployment Guide (Free Tier)

This guide will help you deploy **VoteSecure** to PythonAnywhere. This platform is ideal because it keeps your `db.sqlite3` file persistent.

---

### **Step 1: Upload Your Code**
1.  Log in to [PythonAnywhere](https://www.pythonanywhere.com/).
2.  Go to the **"Files"** tab.
3.  Create a folder named `voting_system`.
4.  Upload your files into that folder (or use a Bash console to `git clone` your repo).

### **Step 2: Create a Virtual Environment**
1.  Open a **Bash Console** from the PythonAnywhere dashboard.
2.  Run the following command (replace `myenv` with your preferred name):
    ```bash
    mkvirtualenv --python=/usr/bin/python3.10 myenv
    pip install -r requirements.txt
    ```

### **Step 3: Configure the Web App**
1.  Go to the **"Web"** tab on the PythonAnywhere dashboard.
2.  Click **"Add a new web app"**.
3.  Choose **Manual Configuration** (do NOT choose the Django default option, it creates a dummy project).
4.  Select **Python 3.10**.
5.  In the Web tab settings:
    *   **Source code**: `/home/YOUR_USERNAME/voting_system`
    *   **Working directory**: `/home/YOUR_USERNAME/voting_system`
    *   **Virtualenv**: `/home/YOUR_USERNAME/.virtualenvs/myenv`

### **Step 4: Edit the WSGI Configuration**
1.  In the **"Web"** tab, find the **"WSGI configuration file"** link and click it.
2.  Delete everything in that file and paste the following:

```python
import os
import sys

# Add your project directory to the sys.path
path = '/home/YOUR_USERNAME/voting_system'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'voting_system.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```
*(Replace `YOUR_USERNAME` with your actual PythonAnywhere username).*

### **Step 5: Static & Media Files**
In the **"Web"** tab, scroll down to the **"Static files"** section and add these two entries:
*   **URL**: `/static/` | **Path**: `/home/YOUR_USERNAME/voting_system/static`
*   **URL**: `/media/` | **Path**: `/home/YOUR_USERNAME/voting_system/media`

### **Step 6: Finalize**
1.  Run migrations in the Bash console:
    ```bash
    python manage.py collectstatic --noinput
    ```
2.  Go back to the **Web** tab and click **"Reload YOUR_USERNAME.pythonanywhere.com"**.

---

### **✅ Deployment Check**
Your site should now be live at `https://YOUR_USERNAME.pythonanywhere.com/`. 

**Note**: Remember to log in to PythonAnywhere once a day/week and click the **"Run until tomorrow"** button on the Web tab to keep the free site active!
