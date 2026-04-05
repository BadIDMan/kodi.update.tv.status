import pymysql
import requests
import os
import time
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
DB_HOST = "127.0.0.1" # if you run this script directly on DB backend server; use other IP if running script externally to the DB backend server
DB_PORT = 3306 # or your custom port
DB_USER = "db_kodi_user"
DB_PASS = "db_kodi_password"

TMDB_API_KEY = "YOUR_TMDB_API_KEY" # must provide here your tmdb API key. Create an account on https://www.themoviedb.org and request free API key in your account's profile

LOG_DIR = "/volume1/homes/administrator/logs" # provide location for the logs
LOG_FILE = "kodi_tv_status_update"

DRY_RUN = True   # True = no DB updates; False = update c02 (status) in tvshows table
LOG_ALL = True  # True = log unchanged shows; False = log only shows for which status is changed
SLEEP = 0.05
LOG_RETENTION_DAYS = 7


# =========================
# SETUP
# =========================
def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)

def cleanup_old_logs():
    now = datetime.now()
    cutoff = now - timedelta(days=LOG_RETENTION_DAYS)

    for fname in os.listdir(LOG_DIR):
        if not fname.startswith(LOG_FILE):
            continue

        fpath = os.path.join(LOG_DIR, fname)

        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if mtime < cutoff:
                os.remove(fpath)
        except Exception as e:
            print(f"Log cleanup error: {fname} -> {e}")

def create_logs():
    ts = datetime.now().strftime("%Y%m%d%H%M")
    main_log = open(f"{LOG_DIR}/{ts}_{LOG_FILE}.log", "w", encoding="utf-8")
    error_log = open(f"{LOG_DIR}/{ts}_{LOG_FILE}_errors.log", "w", encoding="utf-8")
    return main_log, error_log

def get_latest_db(conn):
    with conn.cursor() as c:
        c.execute("SHOW DATABASES LIKE 'MyVideos%'")
        dbs = [list(r.values())[0] for r in c.fetchall()]
    return max(dbs, key=lambda x: int(x.replace("MyVideos", "")))

# =========================
# TMDB
# =========================
def get_tmdb_status(tmdb_id):
    url = f"https://api.themoviedb.org/3/tv/{tmdb_id}"
    params = {"api_key": TMDB_API_KEY}

    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return None
        return r.json().get("status")
    except:
        return None

def normalize_status(status):
    if status == "Returning Series":
        return "Continuing"
    return status

def parse_tmdb_id(raw):
    try:
        return int(str(raw).split("-")[0])
    except:
        return None

# =========================
# DB
# =========================
conn = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASS,
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor
)

DB_NAME = get_latest_db(conn)
conn.select_db(DB_NAME)

print(f"Using database: {DB_NAME}")

# =========================
# MAIN
# =========================
def main():
    ensure_log_dir()
    cleanup_old_logs()   # <-- NEW

    log, error_log = create_logs()

    updated = 0
    unchanged = 0
    errors = 0

    with conn.cursor() as cursor:

        cursor.execute("""
        SELECT 
            t.idShow,
            t.c00 AS name,
            t.c02 AS current_status,
            u.value AS tmdb_raw
        FROM tvshow t
        JOIN uniqueid u 
            ON u.media_id = t.idShow
        WHERE u.type='tmdb'
          AND u.media_type='tvshow'
        """)

        shows = cursor.fetchall()
        total = len(shows)

        start = time.time()

        for i, show in enumerate(shows, 1):

            idShow = show["idShow"]
            name = show["name"]
            old_status = show["current_status"]
            raw_tmdb = show["tmdb_raw"]

            tmdb_id = parse_tmdb_id(raw_tmdb)
            if not tmdb_id:
                continue

            new_status_raw = get_tmdb_status(tmdb_id)

            if not new_status_raw:
                errors += 1
                error_log.write(f"{name};{tmdb_id};ERROR\n")
                log.write(f"{name};{old_status};ERROR\n")
                continue

            new_status = normalize_status(new_status_raw)

            if old_status == new_status:
                unchanged += 1
                if LOG_ALL:
                    log.write(f"{name};{old_status};UNCHANGED\n")
                continue

            updated += 1
            log.write(f"{name};{old_status};{new_status}\n")

            if not DRY_RUN:
                cursor.execute("""
                UPDATE tvshow
                SET c02=%s
                WHERE idShow=%s
                """, (new_status, idShow))

            # Progress
            if i % 20 == 0 or i == total:
                percent = (i / total) * 100
                elapsed = time.time() - start
                speed = i / elapsed if elapsed > 0 else 0
                eta = (total - i) / speed if speed > 0 else 0

                print(f"[{i}/{total}] {percent:.1f}% | "
                      f"{speed:.1f}/s | ETA {int(eta)}s")

            time.sleep(SLEEP)

        if not DRY_RUN:
            conn.commit()

    # =====================
    # SUMMARY
    # =====================
    log.write("\n=== SUMMARY ===\n")
    log.write(f"Total: {total}\n")
    log.write(f"Updated: {updated}\n")
    log.write(f"Unchanged: {unchanged}\n")
    log.write(f"Errors: {errors}\n")

    log.close()
    error_log.close()

    print("Done.")

# =========================
if __name__ == "__main__":
    main()