# Cronjobs

Automated tasks for the clothing rental system.

## Available Cronjobs

### 1. check_late_bookings.py
**Purpose**: Check and mark bookings as LATE if past rental_end date

**Schedule**: Every hour
```bash
# Crontab
0 * * * * cd /path/to/project && /path/to/venv/bin/python cronjobs/check_late_bookings.py
```

**What it does**:
- Finds all bookings with status=RENTING and rental_end < now
- Changes status to LATE
- Sends late notification email to customers

---

### 2. send_reminders.py
**Purpose**: Send reminder emails 1 day before pickup/return

**Schedule**: Daily at 18:00
```bash
# Crontab
0 18 * * * cd /path/to/project && /path/to/venv/bin/python cronjobs/send_reminders.py
```

**What it does**:
- Finds bookings with rental_start = tomorrow (status=APPROVED)
  → Sends pickup reminder
- Finds bookings with rental_end = tomorrow (status=RENTING)
  → Sends return reminder

---

### 3. auto_complete_cleaning.py
**Purpose**: Auto-complete bookings stuck in RETURNED_CLEANING

**Schedule**: Daily at 00:00
```bash
# Crontab
0 0 * * * cd /path/to/project && /path/to/venv/bin/python cronjobs/auto_complete_cleaning.py
```

**What it does**:
- Finds bookings with status=RETURNED_CLEANING for > 3 days
- Changes status to COMPLETED
- Marks inventory items as available
- Sends completion email

---

## Setup

### 1. Make scripts executable
```bash
chmod +x cronjobs/*.py
```

### 2. Test manually
```bash
# Activate venv
source venv/bin/activate

# Run each script
python cronjobs/check_late_bookings.py
python cronjobs/send_reminders.py
python cronjobs/auto_complete_cleaning.py
```

### 3. Add to crontab
```bash
crontab -e
```

Add these lines:
```
# Clothing Rental Cronjobs
0 * * * * cd /var/www/clothing-rental && /var/www/clothing-rental/venv/bin/python cronjobs/check_late_bookings.py >> /var/log/clothing-rental/cronjobs.log 2>&1
0 18 * * * cd /var/www/clothing-rental && /var/www/clothing-rental/venv/bin/python cronjobs/send_reminders.py >> /var/log/clothing-rental/cronjobs.log 2>&1
0 0 * * * cd /var/www/clothing-rental && /var/www/clothing-rental/venv/bin/python cronjobs/auto_complete_cleaning.py >> /var/log/clothing-rental/cronjobs.log 2>&1
```

### 4. Create log directory
```bash
sudo mkdir -p /var/log/clothing-rental
sudo chown www-data:www-data /var/log/clothing-rental
```

---

## Alternative: Using Celery Beat

Instead of cron, you can use Celery Beat for more advanced scheduling:

```python
# celery_app.py
from celery import Celery
from celery.schedules import crontab

celery = Celery('clothing_rental')

@celery.task
def check_late_bookings_task():
    # Import and run
    pass

celery.conf.beat_schedule = {
    'check-late-bookings': {
        'task': 'check_late_bookings_task',
        'schedule': crontab(minute=0),  # Every hour
    },
    # ...
}
```

Run:
```bash
celery -A celery_app worker --beat
```

---

## Monitoring

View logs:
```bash
tail -f /var/log/clothing-rental/cronjobs.log
```

Check last run:
```bash
grep "Auto-completed" /var/log/clothing-rental/cronjobs.log | tail -5
```
