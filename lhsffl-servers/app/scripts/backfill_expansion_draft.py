"""
Backfill the 2020 Expansion Draft as draft selections.

When the league expanded 8 -> 10 teams for 2020, Tyler (roster 10) and Jacob (roster 9) stocked
their rosters via an expansion draft. In Sleeper this was executed as `commissioner` transactions
dated 2020-05-25, which the normal transaction ingestion skips (commissioner is not an allowed
type). As a result those players have no acquiring event and trade-tree branches dead-end.

This script records each of the 48 selections as BOTH:
  * a DraftPicks(type='expansion') row  -> the canonical "selection" (team, round, pick_no), and
  * a Transactions(type='expansion') row -> the dated event the trade tree walks, so a branch
    terminates at the selection.

Sleeper is the source of truth for player id + roster (we read the 2020-05-25 commissioner adds
to rosters 9/10); the PDF board supplies the pick order.

Two structural cases handled:
  * "atomic"      - the commissioner txn carries both the add (->9/10) and the drop (<-original
                    team). That drop is not ingested, so we include it on the expansion txn.
  * "pre-dropped" - the original team dropped the player in a separate `free_agent` txn (already
                    ingested), then a commissioner add-only moved him to 9/10. We DO NOT add a
                    second drop (it would duplicate the existing one); the trade-tree relabel logic
                    terminates the branch at that existing free_agent drop.

The DB connection comes from an env file (SQL_USER / SQL_PASSWORD / SQL_HOST / DB_NAME),
selectable with --env-file (default .flaskenv = local). Point --env-file at a prod env file to
write to prod. Run from the lhsffl-servers directory:

    # dry run (prints the 48-row table, no DB writes, no env needed)
    venv/bin/python -m app.scripts.backfill_expansion_draft

    # write to LOCAL db (uses .flaskenv)
    venv/bin/python -m app.scripts.backfill_expansion_draft --commit

    # write to PROD db (uses a prod env file you provide)
    venv/bin/python -m app.scripts.backfill_expansion_draft --commit --env-file .env.prod
"""
import sys
import os
import re
import json
import time
import logging
from datetime import datetime, timezone

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Repo root (lhsffl-servers/) — used to resolve relative --env-file paths.
SERVERS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# --- Constants -------------------------------------------------------------------------------
SEASON = 2020
LEAGUE_ID = '516385651688570880'           # 2020 Sleeper league
TYLER_ROSTER = 10
JACOB_ROSTER = 9
EXPANSION_DRAFT_DATE = datetime(2020, 5, 25, tzinfo=timezone.utc)
# Sentinel well below Sleeper's 18-digit snowflake ids, so it can never collide with a real id.
# Used as DraftPicks.sleeper_draft_id and as the base for per-pick sleeper_transaction_id.
EXPANSION_DRAFT_SLEEPER_ID = 920200000000

DRAFTER_ROSTER = {'Tyler': TYLER_ROSTER, 'Jacob': JACOB_ROSTER}

PLAYERS_JSON = os.path.join(os.path.dirname(__file__), 'players.json')

# --- The PDF board (EXPANSION DRAFT BOARD.pdf): (pick_no, name, drafter) ---------------------
BOARD = [
    (1, "Chris Carson", "Tyler"), (2, "Melvin Gordon", "Jacob"), (3, "Leonard Fournette", "Jacob"),
    (4, "Hollywood Brown", "Tyler"), (5, "Todd Gurley", "Tyler"), (6, "Mike Williams", "Jacob"),
    (7, "Henry Ruggs", "Jacob"), (8, "Keshaun vaughn", "Tyler"), (9, "Ty hilton", "Tyler"),
    (10, "Marlon Mack", "Jacob"), (11, "Justin jefferson", "Jacob"), (12, "Curtis Samuel", "Tyler"),
    (13, "Marvin Jones", "Tyler"), (14, "Kyler Murray", "Jacob"), (15, "Dallas Goedert", "Jacob"),
    (16, "Phillip Lindsay", "Tyler"), (17, "Tyler Higbee", "Tyler"), (18, "Denzel Mims", "Jacob"),
    (19, "Chase Edmunds", "Jacob"), (20, "Dede Westbrook", "Tyler"), (21, "Damien Williams", "Tyler"),
    (22, "David Johnson", "Jacob"), (23, "Corey Davis", "Jacob"), (24, "Golden tate", "Tyler"),
    (25, "Daniel Jones", "Tyler"), (26, "Irv smith jr.", "Jacob"), (27, "Justin Tucker", "Jacob"),
    (28, "Breshad Perrimen", "Tyler"), (29, "Aaron rodgers", "Tyler"), (30, "Hunter renfrow", "Jacob"),
    (31, "Tevin Coleman", "Jacob"), (32, "Derrius Guice", "Tyler"), (33, "Allen Lazard", "Tyler"),
    (34, "Rashaad penny", "Jacob"), (35, "Boston Scott", "Jacob"), (36, "Will Lutz", "Tyler"),
    (37, "Bryce Love", "Tyler"), (38, "Baker Mayfield", "Jacob"), (39, "Duke Johnson", "Jacob"),
    (40, "Matt Ryan", "Tyler"), (41, "Josh Oliver", "Tyler"), (42, "Jared cook", "Jacob"),
    (43, "Andy Isabella", "Jacob"), (44, "Larry Fitzgerald", "Tyler"), (45, "Randall cobb", "Tyler"),
    (46, "Eno Benjamin", "Jacob"), (47, "Kj Hill", "Jacob"), (48, "Donovan peoples jones", "Tyler"),
]

# Misspellings / aliases the normalized full-name match can't resolve on its own.
NAME_OVERRIDES = {
    "keshaun vaughn": "6885",     # Ke'Shawn Vaughn
    "will lutz": "3678",          # Wil Lutz
    "breshad perrimen": "2331",   # Breshad Perriman
    "chase edmunds": "5000",      # Chase Edmonds
    "irv smith jr": "6126",       # Irv Smith
}


def _norm(s):
    s = s.lower().replace('.', '').replace("'", '').replace('-', ' ')
    s = re.sub(r'\b(jr|sr|ii|iii)\b', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def _resolve_board_ids():
    """Map each board name to a sleeper_id via players.json + NAME_OVERRIDES."""
    with open(PLAYERS_JSON) as f:
        players = json.load(f)
    idx = {}
    for pid, p in players.items():
        if not isinstance(p, dict):
            continue
        full = p.get('full_name') or f"{p.get('first_name', '')} {p.get('last_name', '')}"
        idx.setdefault(_norm(full), []).append(pid)

    resolved = {}
    unresolved = []
    for pick_no, name, drafter in BOARD:
        key = _norm(name)
        pid = NAME_OVERRIDES.get(key) or (idx.get(key, [None])[0])
        if pid is None:
            unresolved.append((pick_no, name))
        else:
            resolved[pick_no] = str(pid)
    if unresolved:
        raise SystemExit(f"Could not resolve players (add to NAME_OVERRIDES): {unresolved}")
    return resolved


def _fetch_expansion_moves():
    """
    Return {player_sleeper_id(str): {'add_roster': int, 'drop_roster': int|None}} for the
    2020-05-25 commissioner adds to rosters 9/10. drop_roster is set only when the same
    commissioner txn also drops that player (the "atomic" case).
    """
    moves = {}
    for week in range(0, 19):
        resp = requests.get(f'https://api.sleeper.app/v1/league/{LEAGUE_ID}/transactions/{week}')
        resp.raise_for_status()
        for txn in (resp.json() or []):
            if txn.get('type') != 'commissioner':
                continue
            ts = txn.get('status_updated') or txn.get('created')
            if not ts:
                continue
            day = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date()
            if day != EXPANSION_DRAFT_DATE.date():
                continue
            adds = txn.get('adds') or {}
            drops = txn.get('drops') or {}
            for pid, rid in adds.items():
                if rid in (TYLER_ROSTER, JACOB_ROSTER):
                    moves[str(pid)] = {
                        'add_roster': rid,
                        'drop_roster': drops.get(pid),  # None when add-only (pre-dropped)
                    }
        time.sleep(0.2)
    return moves


def build_selections():
    """Join the PDF board with the Sleeper commissioner moves and validate all 48."""
    resolved = _resolve_board_ids()
    moves = _fetch_expansion_moves()

    selections = []
    errors = []
    for pick_no, name, drafter in BOARD:
        pid = resolved[pick_no]
        expected_roster = DRAFTER_ROSTER[drafter]
        move = moves.get(pid)
        if not move:
            errors.append(f"pick {pick_no} {name} ({pid}): no 2020-05-25 commissioner add found")
            continue
        if move['add_roster'] != expected_roster:
            errors.append(
                f"pick {pick_no} {name} ({pid}): board says {drafter} (r{expected_roster}) "
                f"but Sleeper added to r{move['add_roster']}")
            continue
        selections.append({
            'pick_no': pick_no,
            'name': name,
            'drafter': drafter,
            'player_sleeper_id': int(pid),
            'add_roster': expected_roster,
            'drop_roster': move['drop_roster'],
            'atomic': move['drop_roster'] is not None,
        })

    if errors:
        for e in errors:
            logger.error(e)
        raise SystemExit(f"Validation failed for {len(errors)} of {len(BOARD)} picks; aborting.")
    return selections


def _print_table(selections):
    logger.info("Resolved 2020 Expansion Draft selections (%d):", len(selections))
    print(f"\n{'#':>3}  {'PLAYER':24} {'ID':>6}  {'DRAFTER':7} ADD  DROP  CASE")
    for s in selections:
        drop = s['drop_roster'] if s['drop_roster'] is not None else '-'
        case = 'atomic' if s['atomic'] else 'pre-dropped'
        print(f"{s['pick_no']:>3}  {s['name']:24} {s['player_sleeper_id']:>6}  "
              f"{s['drafter']:7} r{s['add_roster']:<3} {str(drop):>4}  {case}")
    n_atomic = sum(1 for s in selections if s['atomic'])
    print(f"\n  atomic (expansion txn carries drop): {n_atomic}")
    print(f"  pre-dropped (free_agent drop already ingested, expansion txn add-only): "
          f"{len(selections) - n_atomic}\n")


def _insert(selections):
    from sqlalchemy import text
    from app import db
    from app.models.draft_picks import DraftPicks
    from app.models.transactions import Transactions
    from app.models.transaction_players import TransactionPlayers
    from app.models.transaction_rosters import TransactionRosters

    # Ensure the Transactions.type enum allows 'expansion' (idempotent; MySQL only — SQLite has no
    # enforced enums). Mirrors migrations/expansion_draft.sql so the --commit run is self-contained.
    if db.engine.dialect.name == 'mysql':
        db.session.execute(text(
            "ALTER TABLE Transactions "
            "MODIFY COLUMN type ENUM('trade','waiver','free_agent','expansion') NOT NULL"
        ))
        db.session.commit()
        logger.info("Ensured Transactions.type enum includes 'expansion'.")

    if DraftPicks.query.filter_by(sleeper_draft_id=EXPANSION_DRAFT_SLEEPER_ID).first():
        logger.info("Expansion DraftPicks already present (sleeper_draft_id=%s); nothing to do.",
                    EXPANSION_DRAFT_SLEEPER_ID)
        return {'success': True, 'inserted': 0}

    inserted = 0
    for s in selections:
        pick_no = s['pick_no']
        roster = s['add_roster']
        player_id = s['player_sleeper_id']

        db.session.add(DraftPicks(
            season=SEASON,
            round=(pick_no - 1) // 2 + 1,  # 2 picks (Tyler + Jacob) per round -> 24 rounds
            pick_no=pick_no,
            draft_slot=roster,
            drafting_roster_id=roster,
            original_roster_id=roster,
            player_sleeper_id=player_id,
            sleeper_draft_id=EXPANSION_DRAFT_SLEEPER_ID,
            type='expansion',
        ))

        txn = Transactions(
            sleeper_transaction_id=EXPANSION_DRAFT_SLEEPER_ID + pick_no,
            year=SEASON,
            week=0,
            type='expansion',
            status='complete',
            creator_sleeper_user_id=None,
            sleeper_league_id=int(LEAGUE_ID),
            waiver_priority=None,
            created_at=EXPANSION_DRAFT_DATE,
            status_updated_at=EXPANSION_DRAFT_DATE,
        )
        db.session.add(txn)
        db.session.flush()  # get transaction_id

        # Rosters involved: the selecting team always; the original team only when we record a drop.
        rosters = {roster}
        db.session.add(TransactionPlayers(
            transaction_id=txn.transaction_id,
            player_sleeper_id=player_id,
            sleeper_roster_id=roster,
            action='add',
        ))
        if s['atomic']:
            drop_roster = s['drop_roster']
            rosters.add(drop_roster)
            db.session.add(TransactionPlayers(
                transaction_id=txn.transaction_id,
                player_sleeper_id=player_id,
                sleeper_roster_id=drop_roster,
                action='drop',
            ))
        for rid in rosters:
            db.session.add(TransactionRosters(
                transaction_id=txn.transaction_id,
                sleeper_roster_id=rid,
                is_consenter=False,
            ))
        inserted += 1

    db.session.commit()
    logger.info("Inserted %d expansion DraftPicks + %d expansion Transactions.", inserted, inserted)
    return {'success': True, 'inserted': inserted}


def _parse_env_file(argv):
    if '--env-file' in argv:
        return argv[argv.index('--env-file') + 1]
    return '.flaskenv'


def main():
    argv = sys.argv[1:]
    commit = '--commit' in argv
    selections = build_selections()
    _print_table(selections)

    if not commit:
        logger.info("Dry run — no DB writes. Re-run with --commit to insert.")
        return

    # Load DB connection (SQL_USER/SQL_PASSWORD/SQL_HOST/DB_NAME + LEAGUE_ID) from the chosen env
    # file; override=True so the selected file wins over anything already in the environment.
    env_file = _parse_env_file(argv)
    env_path = env_file if os.path.isabs(env_file) else os.path.join(SERVERS_ROOT, env_file)
    if not os.path.exists(env_path):
        raise SystemExit(f"Env file not found: {env_path}")
    load_dotenv(env_path, override=True)
    logger.info("Loaded env from %s — target DB: %s / %s",
                env_path, os.environ.get('SQL_HOST'), os.environ.get('DB_NAME'))

    from app import create_app
    from config import DevConfig
    app = create_app(DevConfig)
    with app.app_context():
        result = _insert(selections)
        logger.info("Result: %s", result)


if __name__ == '__main__':
    main()
