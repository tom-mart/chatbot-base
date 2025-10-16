#!/bin/bash

# Script to add VAPID keys to .env file

ENV_FILE="../.env"
VAPID_FILE=".env.vapid"

if [ ! -f "$VAPID_FILE" ]; then
    echo "Error: $VAPID_FILE not found!"
    echo "Please run: python generate_vapid_keys.py first"
    exit 1
fi

echo "Adding VAPID keys to $ENV_FILE..."

# Read the VAPID keys
VAPID_PRIVATE_KEY=$(grep VAPID_PRIVATE_KEY $VAPID_FILE | cut -d '=' -f2)
VAPID_PUBLIC_KEY=$(grep VAPID_PUBLIC_KEY $VAPID_FILE | cut -d '=' -f2)
VAPID_SUBJECT=$(grep VAPID_SUBJECT $VAPID_FILE | cut -d '=' -f2)

# Check if keys already exist in .env
if grep -q "VAPID_PRIVATE_KEY" "$ENV_FILE" 2>/dev/null; then
    echo "VAPID keys already exist in $ENV_FILE"
    echo "Do you want to replace them? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        echo "Aborted."
        exit 0
    fi
    # Remove old keys
    sed -i '/VAPID_PRIVATE_KEY/d' "$ENV_FILE"
    sed -i '/VAPID_PUBLIC_KEY/d' "$ENV_FILE"
    sed -i '/VAPID_SUBJECT/d' "$ENV_FILE"
fi

# Append new keys
echo "" >> "$ENV_FILE"
echo "# VAPID Keys for Push Notifications" >> "$ENV_FILE"
echo "VAPID_PRIVATE_KEY=$VAPID_PRIVATE_KEY" >> "$ENV_FILE"
echo "VAPID_PUBLIC_KEY=$VAPID_PUBLIC_KEY" >> "$ENV_FILE"
echo "VAPID_SUBJECT=$VAPID_SUBJECT" >> "$ENV_FILE"

echo "✅ VAPID keys added to $ENV_FILE successfully!"
echo ""
echo "Keys added:"
echo "  VAPID_PRIVATE_KEY=$VAPID_PRIVATE_KEY"
echo "  VAPID_PUBLIC_KEY=$VAPID_PUBLIC_KEY"
echo "  VAPID_SUBJECT=$VAPID_SUBJECT"
