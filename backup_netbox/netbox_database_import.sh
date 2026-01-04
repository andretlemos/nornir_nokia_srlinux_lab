#!/bin/bash
# Script to import NetBox database and media into a Docker instance

# Set variables
POSTGRES_CONTAINER="netbox-docker-postgres-1"  # Replace with your PostgreSQL container name
NETBOX_CONTAINER="netbox-docker-netbox-1"      # Replace with your NetBox container name
DB_USER="netbox"
DB_NAME="netbox"
DUMP_FILE="netbox_backup.sql"         # Replace with your dump file

# Stop NetBox services
docker compose stop netbox-docker-netbox-1 netbox-docker-netbox-worker-1 netbox-docker-netbox-housekeeping-1

# Drop and recreate the database
echo "Dropping and recreating database..."
docker exec -it "$POSTGRES_CONTAINER" psql -U netbox -d postgres -c "DROP DATABASE IF EXISTS netbox;"
docker exec -it "$POSTGRES_CONTAINER" psql -U netbox -d postgres -c "CREATE DATABASE netbox;"
docker exec -it "$POSTGRES_CONTAINER" psql -U netbox -d netbox -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker exec -it "$POSTGRES_CONTAINER" psql -U netbox -d netbox -c "GRANT ALL ON SCHEMA public TO netbox;"

docker exec -it "$POSTGRES_CONTAINER" psql -U netbox -c 'GRANT ALL PRIVILEGES ON DATABASE netbox TO netbox;'
docker exec -it "$POSTGRES_CONTAINER" psql -U netbox -c "ALTER DATABASE netbox OWNER TO netbox;"
docker exec -it "$POSTGRES_CONTAINER" psql -U netbox -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO netbox;"
docker exec -it "$POSTGRES_CONTAINER" psql -U netbox -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO netbox;"
docker exec -it "$POSTGRES_CONTAINER" psql -U netbox -c "GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO netbox;"

# Check if dump file exists
if [ ! -f "$DUMP_FILE" ]; then
    if [ -f "$DUMP_FILE.gz" ]; then
        echo "Decompressing $DUMP_FILE.gz..."
        gunzip -k "$DUMP_FILE.gz"
    else
        echo "Error: $DUMP_FILE not found"
        exit 1
    fi
fi
docker exec -i "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$DUMP_FILE"
if [ $? -eq 0 ]; then
    echo "Database imported successfully"
else
    echo "Error: Database import failed"
    exit 1
fi

# Run migrations
docker exec "$NETBOX_CONTAINER" /opt/netbox/netbox/manage.py migrate
if [ $? -eq 0 ]; then
    echo "Migrations completed"
else
    echo "Error: Migrations failed"
    exit 1
fi

# Start NetBox services
echo "Starting all NetBox services..."
docker compose up -d
echo "NetBox services restarted. Access at http://<host>:8000"

# Clean up decompressed file if it was gzipped
if [ -f "$DUMP_FILE.gz" ]; then
    rm -f "$DUMP_FILE"
fi