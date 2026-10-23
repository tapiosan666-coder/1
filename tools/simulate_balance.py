#!/usr/bin/env python3
"""Design-level Monte Carlo model, NOT engine gameplay measurements.

Each run samples a fixed uniformly distributed discovery rank in [1, 5000].
No rerolls, minimum duration, or delayed true-identity placement exist.
Simulated 50-person work batches approximate concurrent searching/scanning.
The assumptions describe the proposed full game, not the 120-NPC sector build.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


ASSUMPTIONS = {
    "model": "aggregate-v1; hypothetical 15-floor finished game; not measured gameplay",
    "population": 5000,
    "batch_size": 50,
    "true_selection": "fixed uniform discovery rank 1..5000; no minimum duration or re-selection",
    "identity_order": "exchangeable encounter order, no revisits; spatial NPC routes are NOT simulated",
    "accuracy": "per-run Beta(12, 6), clipped to 0.30..0.95; ADS included in this abstraction",
    "fire_rate": "6.25 shots/s; 5 down to 1 hits; 30 shots, 1 s reload; infinite reserve",
    "skill_orders": {
        "scanner_first": ["focus", "focus", "sonar", "cat", "focus", "sprint", "pulse", "focus", "cat_speed", "sonar", "pulse", "sprint", "sonar"],
        "cat_first": ["cat", "cat_speed", "sonar", "focus", "cat_speed", "focus", "sprint", "pulse", "focus", "sonar", "focus", "pulse", "sonar"],
        "explorer": ["sonar", "sprint", "focus", "sonar", "cat", "focus", "pulse", "focus", "sprint", "cat_speed", "focus", "pulse", "sonar"],
        "specialist": ["focus", "pulse", "sonar", "pulse", "cat", "focus", "sprint", "cat_speed", "focus", "sonar", "focus", "pulse", "sonar"],
    },
    "ap": "10 per fake; escalating skill costs copied from IdentityRun; no free initial AP",
    "movement": "search 3.8 s per person + 5.5 s store-search overhead; per-batch Gamma noise; NPC mobility multiplier Uniform(0.85,1.35) per run",
    "density": "remaining-density multiplier (5000 / max(80, remaining))**0.40; no individual world-space agents",
    "sonar": "search-time reduction 1/(1+0.35*level), up to level 3 in these purchase orders",
    "sprint": "search-time reduction 1/(1+0.25*level), up to level 2",
    "cat": "1 cat, 20 / 12 / 6 s per scan; 65% productive uptime; one in simulation and game",
    "special": "radius 8 / 12 / 16 m; 25 s cooldown; Poisson local occupancy from mean density 0.035/m2; 55% productive uptime",
    "floor_travel": "15 floors approximated as 333-identity sectors; 65 s first-visit transition, not skippable",
    "fast_travel": "after 2 visited sectors, reduces simulated revisit routing by 15%; never skips first visits",
    "chests": "10 reachable chests in rank-space; discovery probabilities 0.55 normal (6), 0.65 rare (3), 0.80 legendary (1); uniform first discovery rank; no 3D reachability simulation",
    "item_timing": "discovered items saved until next work batch; offensive variants remove 100..200 at density 1, capped by remaining rank/density; utility variants multiply search by 0.65 for 180 s",
    "items": "uniform choice among the eight specified items; magnet/chain/black hole/ceiling laser/disco represented as crowd clearing, watch/sonar/cart as utility; proposed effects, not implemented gameplay",
    "special_original": "cat, pulse, offensive item mark original; player then travels 15..90 m at 5 m/s and completes required normal hits + reload allowance",
    "limitations": "perfect identification bookkeeping; no missed rooms, navigation errors, combat stress, pauses, save/load, real collision or multi-floor NPC motion; cannot establish a 3-hour commercial playtime",
}

COST = {"focus": 60, "sonar": 40, "sprint": 60, "cat": 100, "cat_speed": 80, "pulse": 120}


def simulate(trials: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    rank = rng.integers(1, 5001, trials)
    strategy = rng.integers(0, 4, trials)
    order = list(ASSUMPTIONS["skill_orders"].values())
    accuracy = np.clip(rng.beta(12, 6, trials), 0.30, 0.95)
    mobility = rng.uniform(0.85, 1.35, trials)
    levels = {key: np.zeros(trials, dtype=np.int32) for key in COST}
    ap = np.zeros(trials)
    next_purchase = np.zeros(trials, dtype=np.int32)
    done = np.zeros(trials, dtype=np.int32)
    seconds = np.zeros(trials)
    chest_rank = rng.integers(1, 5001, (trials, 10))
    chest_seen = np.zeros((trials, 10), dtype=bool)
    chest_probability = np.array([0.55] * 6 + [0.65] * 3 + [0.80])
    chest_found = rng.random((trials, 10)) < chest_probability
    item_type = rng.integers(0, 8, (trials, 10))
    utility_left = np.zeros(trials)
    special_finish = np.zeros(trials, dtype=bool)
    items_used = np.zeros(trials, dtype=np.int32)
    # A maximum 5000 ranks with at least one identity processed each step.
    for _ in range(101):
        active = done < rank
        if not active.any():
            break
        # Purchase priorities are fixed at run start; prices use actual AP.
        for _purchase in range(13):
            purchased = np.zeros(trials, dtype=bool)
            for strategy_id, skills in enumerate(order):
                for slot, key in enumerate(skills):
                    price = COST[key] * (levels[key] + 1)
                    eligible = active & ~purchased & (strategy == strategy_id) & (next_purchase == slot) & (ap >= price)
                    ap[eligible] -= price[eligible]
                    levels[key][eligible] += 1
                    next_purchase[eligible] += 1
                    purchased |= eligible
            if not purchased.any():
                break
        remaining = rank - done
        batch = np.minimum(50, remaining)
        density = np.maximum(0.016, (5000 - done) / 5000)
        found_now = (~chest_seen) & chest_found & (chest_rank <= done[:, None]) & active[:, None]
        chest_seen |= found_now
        offensive = found_now & np.isin(item_type, [0, 1, 3, 6, 7])
        utility = found_now & np.isin(item_type, [2, 4, 5])
        item_capacity = (offensive * rng.integers(100, 201, (trials, 10))).sum(axis=1)
        item_capacity = np.floor(item_capacity * density).astype(np.int32)
        item_scanned = np.minimum(remaining, item_capacity)
        finished_by_item = active & (item_scanned >= remaining)
        utility_left = np.where(utility.any(axis=1), 180.0, utility_left)
        items_used += found_now.sum(axis=1).astype(np.int32)
        # Items count as encounters, not a re-roll of the original.
        batch = np.minimum(remaining, np.maximum(batch, item_scanned))
        ordinary_batch = np.maximum(0, batch - item_scanned)
        search_per_person = (3.8 + 5.5) * mobility / np.power(density, 0.40)
        search_per_person /= (1 + 0.35 * levels["sonar"]) * (1 + 0.25 * levels["sprint"])
        search_per_person *= np.where(utility_left > 0, 0.65, 1.0)
        visited = done // 333 + 1
        search_per_person *= np.where(visited >= 2, 0.85, 1.0)
        search = ordinary_batch * search_per_person * rng.gamma(8.0, 1 / 8, trials)
        hits = 5 - levels["focus"]
        gun_per_person = hits / (6.25 * accuracy) + hits / accuracy / 30.0
        gun_rate = 1.0 / gun_per_person
        cat_period = np.choose(np.minimum(2, levels["cat_speed"]), [20.0, 12.0, 6.0])
        cat_rate = levels["cat"] * 0.65 / cat_period
        pulse_radius = 4 + 4 * levels["pulse"]
        local_occupancy = rng.poisson(np.pi * pulse_radius**2 * 0.035 * density)
        pulse_rate = np.where(levels["pulse"] > 0, local_occupancy / 25.0 * 0.55, 0.0)
        # Cat/pulse work during search, reducing manual discovery workload.
        passive_rate = cat_rate + pulse_rate
        dt = (search + ordinary_batch / gun_rate) / (1 + passive_rate * search_per_person + passive_rate / gun_rate)
        crossed_floor = ((done + batch) // 333) > (done // 333)
        dt += crossed_floor * 65.0
        dt += (item_scanned > 0) * 2.0
        utility_left = np.maximum(0, utility_left - dt)
        finished = active & ((done + batch) >= rank)
        passive_share = passive_rate * dt / np.maximum(1, ordinary_batch)
        special = finished & ((rng.random(trials) < np.minimum(0.95, passive_share)) | finished_by_item)
        special_finish |= special
        # A special detection still requires approach and the ordinary gun.
        dt += special * (rng.uniform(15, 90, trials) / 5.0 + gun_per_person + 1.0)
        seconds += np.where(active, dt, 0)
        ap += np.where(active, np.maximum(0, batch - finished.astype(int)) * 10, 0)
        done += np.where(active, batch, 0)
    if np.any(done < rank):
        raise RuntimeError("Simulation did not finish every trial")
    minutes = seconds / 60

    def summarize(values: np.ndarray) -> dict:
        return {"mean_minutes": round(float(values.mean()), 3),
                "median_minutes": round(float(np.median(values)), 3),
                **{f"p{p}_minutes": round(float(np.percentile(values, p)), 3) for p in [1, 5, 10, 90, 95, 99]},
                "min_minutes": round(float(values.min()), 3), "max_minutes": round(float(values.max()), 3),
                "over_3h_percent": round(float((values > 180).mean() * 100), 3),
                "over_6h_percent": round(float((values > 360).mean() * 100), 3)}

    return {"seed": seed, "trials": trials, "numpy_version": np.__version__, "assumptions": ASSUMPTIONS,
            "summary": summarize(minutes),
            "mean_discovery_rank": round(float(rank.mean()), 3),
            "median_discovery_rank": float(np.median(rank)),
            "first_identity_trials": int((rank == 1).sum()),
            "special_detection_percent": round(float(special_finish.mean() * 100), 3),
            "mean_items_discovered": round(float(items_used.mean()), 3),
            "strategies": {name: summarize(minutes[strategy == i]) for i, name in enumerate(ASSUMPTIONS["skill_orders"])},
            "conclusion": "Predictive model only. Compare with 180-minute target; do not enforce a minimum or move the original. Validate with instrumented full-map playtests."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--output", type=Path, default=Path("docs/balance-results.json"))
    args = parser.parse_args()
    if args.trials < 100_000:
        parser.error("Full design report requires at least 100,000 trials")
    result = simulate(args.trials, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"trials": result["trials"], "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
