#!/bin/bash
BACKUP_DIR=~/swiftfind/backups
mkdir -p $BACKUP_DIR

# Database backup
cp db.sqlite3 $BACKUP_DIR/db_$(date +%Y-%m-%d_%H-%M).sqlite3

# Data export
python manage.py dumpdata --indent 2 > $BACKUP_DIR/data_$(date +%Y-%m-%d_%H-%M).json

# Keep only last 7 backups
ls -t $BACKUP_DIR/db_*.sqlite3 | tail -n +8 | xargs rm -f
ls -t $BACKUP_DIR/data_*.json | tail -n +8 | xargs rm -f

echo "Backup completed at $(date)"
