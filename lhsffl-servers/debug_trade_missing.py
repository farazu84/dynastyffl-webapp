from app import create_app, db
from app.models.transactions import Transactions
from app.models.transaction_players import TransactionPlayers
from app.models.transaction_rosters import TransactionRosters

app = create_app()

with app.app_context():
    transaction_id = 1343
    roster_id = 7
    player_id = 3164 # Zeke

    origin = Transactions.query.get(transaction_id)
    print(f"Origin: {origin.transaction_id} | {origin.created_at} | {origin.status}")

    # 1. Check if there are ANY transactions for this roster after origin
    future_txns = Transactions.query \
        .join(TransactionRosters) \
        .filter(TransactionRosters.sleeper_roster_id == roster_id) \
        .filter(Transactions.created_at > origin.created_at) \
        .order_by(Transactions.created_at.asc()) \
        .all()

    print(f"\nFound {len(future_txns)} future transactions for Roster {roster_id}")
    
    found_zeke = False
    for txn in future_txns:
        # Check if Zeke is involved
        moves = TransactionPlayers.query.filter_by(transaction_id=txn.transaction_id).all()
        zeke_move = next((m for m in moves if m.player_sleeper_id == player_id), None)
        
        if zeke_move:
            print(f"\n[FOUND ZEKE] Txn {txn.transaction_id} | Type: {txn.type} | Status: {txn.status} | Date: {txn.created_at}")
            print(f"  - Action: {zeke_move.action} | Roster: {zeke_move.sleeper_roster_id}")
            found_zeke = True
            
            # Check if this transaction would be filtered out
            if txn.status != 'complete':
                print("  ! SKIPPED: Status is not complete")
            
    if not found_zeke:
        print("\n[!] Zeke (3164) not found in any future transactions for this roster.")
