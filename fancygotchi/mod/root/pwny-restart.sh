#!/bin/bash

# Define the search string
SEARCH_STRING="fatal error: concurrent map iteration and map write"

# Continuously monitor syslog for the search string
tail -f /var/log/syslog | while read line
do
  if echo "$line" | grep -q "$SEARCH_STRING"; then
    # If the string is found, execute a command
    echo "Found the search string in syslog, executing command..."
    # Insert your command here:
  sleep 10 && sudo systemctl restart bettercap pwngrid-peer && touch /root/.pwnagotchi-auto && systemctl restart pwnagotchi
fi
done