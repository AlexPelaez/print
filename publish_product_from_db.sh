#!/bin/bash

# Navigate to the directory if needed (optional)
cd src/

# Call your Python script. 
# - Use full paths to python3 and your script for reliability.
# - Optionally redirect output to a log file.
#
python3 main_push_product_from_db.py >> cron.log 2>&1