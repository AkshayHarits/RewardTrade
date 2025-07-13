import math
from datetime import datetime,timezone

def calculate_bpv(merchant_redemption_value, msf, sdbf):
    # Clamp the factors to prevent extreme values
    msf = max(0.8, min(1.2, msf))
    sdbf = max(0.8, min(1.2, sdbf))
    
    # Calculate BPV with proper scaling
    bpv = merchant_redemption_value * msf * sdbf
    
    # Prevent extreme values
    return max(0.1, min(2.0, bpv))

def update_msf(current_msf, trade_volume, time_period):
    sensitivity = 0.01
    msf_change = math.log(trade_volume + 1) * sensitivity
    return max(0.5, min(1.5, current_msf + msf_change))

def update_sdbf(current_sdbf, supply, demand):
    sensitivity = 0.1
    ratio = demand / supply if supply > 0 else 1
    sdbf_change = (ratio - 1) * sensitivity
    return max(0.5, min(1.5, current_sdbf + sdbf_change))

class MerchantBPV:
    def __init__(self, name, redemption_value):
        self.name = name
        self.redemption_value = redemption_value
        self.msf = 1.0
        self.sdbf = 1.0
        self.last_update = datetime.now(timezone.utc)  
        self.trade_volume = 0
        self.supply = 1000
        self.demand = 1000

    def update_factors(self, new_trades, new_supply, new_demand):
        time_since_update = (datetime.now() - self.last_update).total_seconds() / 3600
        self.trade_volume += new_trades
        self.supply += new_supply
        self.demand += new_demand

        if time_since_update >= 24:
            self.msf = update_msf(self.msf, self.trade_volume, time_since_update)
            self.sdbf = update_sdbf(self.sdbf, self.supply, self.demand)
            self.trade_volume = 0
            self.last_update = datetime.now()

    def get_bpv(self):
        return calculate_bpv(self.redemption_value, self.msf, self.sdbf)
