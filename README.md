# Kodi TV Show Status Updater


## Overview
This Python 3 script updates TV show status in the Kodi database using data from The Movie Database (TMDb).<br>
Kodi does not automatically refresh TV show status after scraping, which leads to outdated metadata over time.<br>
This script ensures your library stays accurate.<br>


##  Problem
Kodi stores TV show status in *tvshow.c02*
but:
- Status is only set during scraping  
- No automatic updates  
- Many shows remain incorrectly marked (e.g. *Continuing* instead of *Ended*)  


## Solution
This script:
- Determines the active Kodi database MyVideosXXX
- Reads TMDb IDs from Kodi database  
- Fetches current status from TMDb API  
- Normalizes values (e.g. 'Returning Series' -> 'Continuing')  
- Updates tvshow.c02 (when DRY_RUN is set to False)
- Logs all changes and errors  


## Environment
Designed to run on backend systems such as:
- Synology NAS (MariaDB/MySQL)
- Linux server hosting Kodi database


## Prerequisites
Requirements are Python 3, pip, and Python packages pymysql and requests.


## Installation (via SSH)
### Check Python<br>
To verify Python run:<br>
> python3 --version<br>

If missing, install Python3 using your system package manager or Synology Package Center.<br>

### Check pip<br>
To verify pip run:<br>
> python3 -m pip --version<br>

If missing, install it using:<br>
> python3 -m ensurepip --upgrade<br>

Then update pip:<br>
> python3 -m pip install --upgrade pip<br>

### Install required modules<br>
Install required modules using:<br>
> python3 -m pip install pymysql requests<br>


## Usage
1. Copy the script to your NAS or server

2. Make it executable:
> chmod +x kodi_update_tv_status.py

3. Before running, edit the CONFIG section in the script and set:
- database credentials
- TMDb API key
- log directory
- DRY_RUN flag
- log rotation flag

4. Run the script:
> python3 kodi_update_tv_status.py


## Notes
Script operates only on media_type = 'tvshow'<br>
It does not modify episodes or movies.<br>
Designed for safe, repeatable execution (can be scheduled)<br>


## Disclaimer
Use at your own risk<br>
Always backup your Kodi database before running with DRY_RUN = False<br>
The author takes no responsibility for any data loss or corruption<br>
