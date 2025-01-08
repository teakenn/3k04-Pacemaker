def defaultParams():
    global params
    params = {
        "mode": 0,
        "rate_adapt": 0,
        "lrl": 60,
        "url": 60,
        "vent_amp": 1.0,
        "atr_amp": 1.0,
        "vent_pw": 20,
        "atr_pw": 20,
        "vent_sens": 4,
        "atr_sens": 4,
        "vrp": 20,
        "arp": 20,
        "pvarp": 1,
        "act_thresh": 0.5,
        "reaction_time": 30,
        "response_fact": 10,
        "recovery_time": 30,
        "msr": 120
    }
    return params