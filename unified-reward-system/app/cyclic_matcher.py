from collections import defaultdict
from app import db
from app.models import UserPoints, Merchant

def find_exchange_cycles(pending_exchanges):
    """Finds cycles in Smart Exchange requests and optimizes trade execution."""
    graph = defaultdict(list)
    merchant_bpvs = {m.id: m.bpv for m in Merchant.query.all()}  # ✅ Fetch BPV once

    for exchange in pending_exchanges:
        graph[exchange.from_merchant_id].append((exchange.to_merchant_id, exchange, merchant_bpvs[exchange.from_merchant_id]))

    cycles = []
    for start in graph:
        stack = [(start, [])]
        while stack:
            node, path = stack.pop()
            for neighbor, exchange, bpv in graph[node]:
                if neighbor == start and len(path) > 1:
                    cycles.append(path + [(exchange, bpv)])
                elif neighbor not in path:
                    stack.append((neighbor, path + [(exchange, bpv)]))
    return cycles

def execute_cycle(cycle):
    """Executes a matched exchange cycle based on the minimum trade amount."""
    min_amount = min(exchange.amount for exchange, _ in cycle)
    
    for exchange, bpv in cycle:
        exchange.amount -= min_amount
        if exchange.amount == 0:
            exchange.status = 'completed'

        # ✅ Update user balances based on BPV
        user_points_from = UserPoints.query.filter_by(user_id=exchange.user_id, merchant_id=exchange.from_merchant_id).first()
        user_points_to = UserPoints.query.filter_by(user_id=exchange.user_id, merchant_id=exchange.to_merchant_id).first()

        if user_points_from and user_points_from.points >= min_amount:
            user_points_from.points -= min_amount
            if user_points_to:
                user_points_to.points += int(min_amount * bpv)  # ✅ Convert based on BPV
            else:
                db.session.add(UserPoints(user_id=exchange.user_id, merchant_id=exchange.to_merchant_id, points=int(min_amount * bpv)))

    db.session.commit()
