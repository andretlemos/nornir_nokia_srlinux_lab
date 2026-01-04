#!/bin/bash
# Script to dump NetBox database and prepare for sharing

# Set variables
POSTGRES_CONTAINER="netbox-docker-postgres-1"
DB_NAME="netbox"
DB_USER="netbox"
DUMP_FILE="netbox_backup.sql"
COMPRESSED_FILE="${DUMP_FILE}.gz"

# Export the database from the PostgreSQL container
docker exec -t "$POSTGRES_CONTAINER" pg_dump --username "$DB_USER" --host localhost --no-owner --no-privileges --exclude-table-data=extras_objectchange "$DB_NAME" > "$DUMP_FILE"

# Check if dump was successful
if [ $? -eq 0 ]; then
    echo "Database dump created: $DUMP_FILE"
else
    echo "Error: Database dump failed"
    exit 1
fi

# Compress the database dump
gzip "$DUMP_FILE"
if [ $? -eq 0 ]; then
    echo "Compressed dump to: $COMPRESSED_FILE"
else
    echo "Error: Compression failed"
    exit 1
fi



# Instructions for sharing
echo "Share the following files securely (e.g., via SFTP, Dropbox, or Google Drive):"
echo "- Database dump: $COMPRESSED_FILE"
echo "Ensure the recipient uses the same NetBox version and SECRET_KEY as your instance."