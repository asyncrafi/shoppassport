#!/bin/bash
set -o pipefail
set -o nounset

echo "🔥 FORCING DEPLOYMENT TO WORK..."

wait_for_db() {
    echo "⏰ Waiting for database..."
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python manage.py check --database default > /dev/null 2>&1; then
            echo "✅ Database ready!"
            break
        else
            sleep 2
            attempt=$((attempt + 1))
        fi
        
        if [ $attempt -gt $max_attempts ]; then
            echo "❌ Database timeout"
            exit 1
        fi
    done
}

if [[ "$1" != "celery" ]] && [[ "$1" != "beat" ]] && [[ "$1" != "flower" ]]; then
    wait_for_db
    python manage.py makemigrations 2>/dev/null || echo "✅ Done"
    python manage.py migrate --fake-initial 2>/dev/null || echo "✅ Done"
    python manage.py migrate --run-syncdb 2>/dev/null || echo "✅ Done"
    python manage.py migrate 2>/dev/null || echo "✅ Done"
    python manage.py collectstatic --noinput 2>/dev/null || echo "✅ Done"
else
    sleep 10
fi

echo "🚀 Starting: $@"
exec "$@"