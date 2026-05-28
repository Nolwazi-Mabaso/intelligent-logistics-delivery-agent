from models import (
    create_truck,
    assign_delivery_to_truck,
    is_truck_available,
    display_delivery,
    display_truck
)

from itertools import combinations



def calculate_priorities(deliveries):
    return sorted(deliveries, key=lambda d: d["priority_score"], reverse=True)

def generate_states(deliveries, trucks, beam_width=10):
    states = []
    num_trucks = len(trucks)
    num_deliveries = len(deliveries)

    sorted_deliveries = calculate_priorities(deliveries)
    delivery_ids = [d["id"] for d in sorted_deliveries]

    available_trucks = [
    t for t in trucks
    if t["status"] in ["Available", "Full"]
    ]

    capacity_map = {t["id"]: t["capacity"] for t in available_trucks}
    truck_ids = [t["id"] for t in available_trucks]
    
    if not truck_ids:
        return []
    
    generated = set()  

    for first_truck_count in range(0, num_deliveries + 1):

         for first_truck_deliveries in combinations(delivery_ids, first_truck_count):

            remaining = [d for d in delivery_ids
                        if d not in first_truck_deliveries]

            assignment = {}
            unassigned = []
            valid = True


            t0 = truck_ids[0]
            if len(first_truck_deliveries) <= capacity_map[t0]:
                assignment[t0] = list(first_truck_deliveries)
            else:
                valid = False

            if valid:

                other_trucks = truck_ids[1:]
                remaining_copy = remaining.copy()

                for tid in other_trucks:
                    cap = capacity_map[tid]
                    assigned_to_this = remaining_copy[:cap]
                    assignment[tid] = assigned_to_this
                    remaining_copy = remaining_copy[cap:]

                unassigned = remaining_copy

                state_key = str(sorted(
                    [(k, tuple(sorted(v)))
                     for k, v in assignment.items()]
                ))

                if state_key not in generated:
                    generated.add(state_key)
                    states.append({
                        "assignment": assignment,
                        "unassigned": unassigned
                    })

            if len(states) >= beam_width * 3:
                break

    return states[:beam_width] if len(states) > beam_width else states

def evaluate_utility(state, deliveries, trucks):
    utility = 0.0

    priority_map = {d["id"]: d["priority_score"] for d in deliveries}

    capacity_map = {t["id"]: t["capacity"] for t in trucks}

    assignment = state["assignment"]
    unassigned = state["unassigned"]

    for truck_id, delivery_ids in assignment.items():
        assigned_priorities = [priority_map.get(d, 0) for d in delivery_ids]
        utility += sum(assigned_priorities)

        if len(delivery_ids) > capacity_map.get(truck_id, 0):
            utility -= 10

        for i in range(len(assigned_priorities) - 1):
            if assigned_priorities[i] >= assigned_priorities[i + 1]:
                utility += 1  
            else:
                utility -= 1  

    utility -= 5 * len(unassigned)

    return round(utility, 4)

def select_best_state(states, deliveries, trucks):
    scored_states = []

    for state in states:
        score = evaluate_utility(state, deliveries, trucks)
        scored_states.append({
            "state"  : state,
            "utility": score
        })

    scored_states.sort(key=lambda x: x["utility"], reverse=True)

    best = scored_states[0]
    return best, scored_states


def generate_reasoning(best, deliveries, trucks):
    state = best["state"]
    assignment = state["assignment"]
    unassigned = state["unassigned"]
    utility = best["utility"]

    priority_map = {d["id"]: d["priority_score"] for d in deliveries}
    sorted_deliveries = calculate_priorities(deliveries)

    reasons = []

    total_assigned = sum(len(v) for v in assignment.values())
    total_deliveries = len(deliveries)

    if len(unassigned) == 0:
        reasons.append(
            f"All {total_deliveries} deliveries successfully assigned "
            f"— no penalties incurred"
        )
    else:
        reasons.append(
            f"{total_assigned} of {total_deliveries} deliveries assigned "
            f"— {len(unassigned)} flagged as Delayed "
            f"(no available truck capacity)"
        )

    capacity_map = {t["id"]: t["capacity"] for t in trucks}
    overloaded = [
        tid for tid, dids in assignment.items()
        if len(dids) > capacity_map.get(tid, 0)
    ]

    if not overloaded:
        reasons.append("No trucks are overloaded — all capacity constraints respected")
    else:
        reasons.append(
            f"Warning: {len(overloaded)} truck(s) overloaded — "
            f"capacity constraints violated"
        )

    if sorted_deliveries:
        top = sorted_deliveries[0]
        reasons.append(
            f"Highest priority delivery {top['id']} "
            f"(score: {top['priority_score']}) "
            f"was assigned first"
        )

    reasons.append(
        f"Utility score {utility} — highest of all "
        f"schedule combinations evaluated"
    )

    return reasons


def display_priority_report(deliveries, w1, w2):
    sorted_deliveries = calculate_priorities(deliveries)
    print("\n" + "-------------------------------------------------------------" )
    print("   AGENT PRIORITY REPORT")
    print(f"   Weights — w1 (urgency): {w1}  |  w2 (importance): {w2}")
    print("="*65)
    print(f"  {'Rank':<6} {'ID':<6} {'Deadline':<12} "
          f"{'Importance':<12} {'Priority':<10} {'Status'}")
    print("-"*65)

    for rank, delivery in enumerate(sorted_deliveries, start=1):
        print(f"  {rank:<6} "
              f"{delivery['id']:<6} "
              f"{delivery['hours_until_deadline']:<12} "
              f"{delivery['importance_label']:<12} "
              f"{delivery['priority_score']:<10} "
              f"{delivery['status']}")

    print("-------------------------------------------------------------")
    print(f"  Total deliveries : {len(deliveries)}")
    print(f"  Highest priority : {sorted_deliveries[0]['id']} "
          f"(score: {sorted_deliveries[0]['priority_score']})")
    print("--------------------------------------------------------------")

def display_search_results(scored_states, best, deliveries, trucks):
    
    priority_map = {d["id"]: d["priority_score"] for d in deliveries}

    print("\n" + "-------------------------------------------------------------")
    print("   STATE SPACE SEARCH RESULTS")
    print(f"   Total states evaluated: {len(scored_states)}")
    print("-------------------------------------------------------------")

    for i, item in enumerate(scored_states, start=1):
        state = item["state"]
        utility = item["utility"]
        is_best = "  <- SELECTED" if item == best else ""

        print(f"\n  State {i}  |  Utility Score: {utility}{is_best}")
        for truck_id, delivery_ids in state["assignment"].items():
            if delivery_ids:
                details = ", ".join(
                    f"{did}(p:{priority_map.get(did, '?')})"
                    for did in delivery_ids
                )
            else:
                details = "No deliveries assigned"

            cap = next(
                (t["capacity"] for t in trucks if t["id"] == truck_id), "?"
            )
            load = len(delivery_ids)
            print(f"    {truck_id} (cap:{cap}, load:{load}) -> {details}")

        if state["unassigned"]:
            print(f"    !!ALERT!!  Delayed (no capacity): "
                  f"{', '.join(state['unassigned'])}")

    print("\n" + "-------------------------------------------------------------")
    print("   AGENT DECISION")
    print("-------------------------------------------------------------")
    print(f"  Selected: State {scored_states.index(best) + 1}")
    print(f"  Utility Score: {best['utility']}")
    print("\n  Reasoning:")
    reasons = generate_reasoning(best, deliveries, trucks)
    for reason in reasons:
        print(f"  -> {reason}")

    print("-------------------------------------------------------------")

    
def commit_best_state(best, deliveries, trucks):
    state = best["state"]
    assignment = state["assignment"]

    for truck in trucks:
        truck["deliveries"] = []
        truck["load"] = 0
        truck["status"] = "Available"

    for delivery in deliveries:
        if delivery["status"] == "Pending":
            delivery["assigned_truck"] = None

    delivery_map = {d["id"]: d for d in deliveries}

    for truck_id, delivery_ids in assignment.items():
        truck = next((t for t in trucks if t["id"] == truck_id), None)
        if not truck:
            continue

        for delivery_id in delivery_ids:
            delivery = delivery_map.get(delivery_id)
            if delivery:
                assign_delivery_to_truck(delivery, truck)


    for delivery_id in state["unassigned"]:
        delivery = delivery_map.get(delivery_id)
        if delivery:
            delivery["status"] = "Delayed"
            delivery["assigned_truck"] = None