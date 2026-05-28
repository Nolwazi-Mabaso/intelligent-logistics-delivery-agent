from models import (
    create_delivery,
    create_truck,
    update_delivery_status,
    recalculate_priority,
    free_truck_slot,
    display_delivery,
    display_truck
)

from agent import (
    calculate_priorities,
    generate_states,
    select_best_state,
    display_priority_report,
    display_search_results
)

def get_weight_settings():

    print("\n" "-------------------------------------------------")
    print("   SCHEDULING AGENT v2.0")
    print("\n  CONTROL PARAMETERS")
    print("  Priority = (w1 x 1/deadline) + (w2 x importance)")
    print("  Press Enter to use defaults (w1=1.0, w2=1.0)\n")

    while True:
        w1_input = input("  Enter w1 (urgency weight)   : ").strip()
        if w1_input == "":
            w1 = 1.0
            break
        try:
            w1 = float(w1_input)
            if w1 > 0:
                break
            print("  Must be greater than 0.")
        except ValueError:
            print("  Invalid input.")

    while True:
        w2_input = input("  Enter w2 (importance weight): ").strip()
        if w2_input == "":
            w2 = 1.0
            break
        try:
            w2 = float(w2_input)
            if w2 > 0:
                break
            print("  Must be greater than 0.")
        except ValueError:
            print("  Invalid input.")

    print(f"\n   Weights set — w1: {w1}  |  w2: {w2}")
    return w1, w2

def get_deliveries(w1, w2):

    deliveries = []

    print("\n" "-------------------------------------------------")
    print("  ADD DELIVERIES")
    print("  Type 'done' when finished.")
    print("-------------------------------------------------------")

    number = 1

    while True:
        print(f"\n  --- Delivery D{number} ---")

        hours_input = input("  Hours until deadline : ").strip()
        if hours_input.lower() == "done":
            break
        try:
            hours = float(hours_input)
            if hours <= 0:
                print("  Must be greater than 0.")
                continue
        except ValueError:
            print("  Invalid input.")
            continue

        print("  Importance — 1: Low  |  2: Medium  |  3: High")
        imp_input = input("  Importance           : ").strip()
        if imp_input.lower() == "done":
            break
        try:
            importance = int(imp_input)
            if importance not in [1, 2, 3]:
                print("  Please enter 1, 2, or 3.")
                continue
        except ValueError:
            print("  Invalid input.")
            continue

        delivery = create_delivery(
            f"D{number}", hours, importance, w1, w2
        )
        deliveries.append(delivery)

        print(f"\n   D{number} added — "
              f"Priority Score: {delivery['priority_score']}")
        number += 1

    return deliveries

def get_trucks():

    trucks = []

    print("\n" "-------------------------------------------------")
    print("  ADD TRUCKS")
    print("  Type 'done' when finished.")
    print("---------------------------------------------------------")

    number = 1

    while True:
        print(f"\n  --- Truck T{number} ---")

        cap_input = input("  Maximum capacity : ").strip()
        if cap_input.lower() == "done":
            break
        try:
            capacity = int(cap_input)
            if capacity <= 0:
                print("  Must be greater than 0.")
                continue
        except ValueError:
            print("  Invalid input.")
            continue

        truck = create_truck(f"T{number}", capacity)
        trucks.append(truck)

        print(f"   T{number} added — Capacity: {capacity}")
        number += 1

    return trucks

def run_agent_cycle(deliveries, trucks, w1, w2):
    active_deliveries = [
        d for d in deliveries
        if d["status"] in ["Pending", "Delayed"]
    ]

    active_trucks = [
        t for t in trucks
        if t["status"] in ["Available", "Full"]
    ]

    if not active_deliveries:
        print("\n   All deliveries have been handled.")
        print("  No rescheduling required.")
        return None, None

    display_priority_report(active_deliveries, w1, w2)

    print("\n  Agent searching schedule combinations...")
    states = generate_states(active_deliveries, active_trucks)
    print(f"  {len(states)} valid states generated.")

    if not states:
        print("\n  !!ALERT!! No valid schedules found.")
        print("  All trucks may be full or unavailable.")
        return None, None

    best, scored_states = select_best_state(
        states, active_deliveries, active_trucks
    )

    display_search_results(
        scored_states, best, active_deliveries, active_trucks
    )

    if best:
        from agent import commit_best_state
        commit_best_state(best, active_deliveries, active_trucks)
        print("\n   Schedule committed. Drivers notified.")

    return best, scored_states

def add_urgent_delivery(deliveries, w1, w2):
    print("\n" "-------------------------------------------------")
    print("  !!ALERT!! : NEW DELIVERY RECEIVED")
    print("  Agent will re-evaluate the full schedule.")
    print("-------------------------------------------------------")

    number = len(deliveries) + 1

    while True:
        hours_input = input(
            f"\n  Hours until deadline (D{number}): "
        ).strip()
        try:
            hours = float(hours_input)
            if hours <= 0:
                print("  Must be greater than 0.")
                continue
            break
        except ValueError:
            print("  Invalid input.")

    print("  Importance — 1: Low  |  2: Medium  |  3: High")
    while True:
        imp_input = input("  Importance           : ").strip()
        try:
            importance = int(imp_input)
            if importance not in [1, 2, 3]:
                print("  Please enter 1, 2, or 3.")
                continue
            break
        except ValueError:
            print("  Invalid input.")

    delivery = create_delivery(
        f"D{number}", hours, importance, w1, w2
    )
    deliveries.append(delivery)

    print(f"\n   D{number} added — "
          f"Priority Score: {delivery['priority_score']}")
    print("  Agent is re-evaluating all schedules...\n")

    return deliveries


def update_status(deliveries, trucks):
    print("\n" "-------------------------------------------------")
    print("  UPDATE DELIVERY STATUS")
    print("-------------------------------------------------")

    # Show current deliveries
    print("\n  Current deliveries:")
    for delivery in deliveries:
        display_delivery(delivery)

    delivery_id = input(
        "\n  Enter delivery ID to update (e.g. D1): "
    ).strip().upper()

    # Find the delivery
    target = next(
        (d for d in deliveries if d["id"] == delivery_id), None
    )

    if not target:
        print(f"  Delivery {delivery_id} not found.")
        return deliveries, trucks

    print("  New status:")
    print("  1. In Transit")
    print("  2. Delivered")

    choice = input("  Select (1 or 2): ").strip()

    if choice == "1":
        update_delivery_status(target, "In Transit", trucks, deliveries)
        print(f"\n   {delivery_id} marked as In Transit.")

    elif choice == "2":
        update_delivery_status(target, "Delivered", trucks)
        print(f"\n   {delivery_id} marked as Delivered.")

    elif choice == "2":
        update_delivery_status(target, "Delivered", trucks, deliveries)
        print(f"\n   {delivery_id} marked as Delivered.")
        print(f"   Truck slot freed.")
        print("  Agent will re-evaluate pending deliveries.")
    else:
        print("  Invalid choice.")

    return deliveries, trucks



def main():

    # --- SENSE: Get inputs ---
    w1, w2 = get_weight_settings()
    deliveries = get_deliveries(w1, w2)
    trucks = get_trucks()

    if not deliveries:
        print("\n  No deliveries entered. Exiting.")
        return

    if not trucks:
        print("\n  No trucks entered. Exiting.")
        return

    run_agent_cycle(deliveries, trucks, w1, w2)
    

    while True:
        print("\n" "-------------------------------------------------")
        print("  AGENT MONITORING — Awaiting Changes")
        print("-------------------------------------------------------")
        print("  1. Add urgent delivery")
        print("  2. Update delivery status")
        print("  3. Adjust weights and reschedule")
        print("  4. View current deliveries")
        print("  5. View current trucks")
        print("  6. Exit")
        print("\n" "-------------------------------------------------")

        choice = input("  Select option: ").strip()

        if choice == "1":
            deliveries = add_urgent_delivery(deliveries, w1, w2)
            run_agent_cycle(deliveries, trucks, w1, w2)

        elif choice == "2":
            deliveries, trucks = update_status(deliveries, trucks)
            print("\n  Agent re-evaluating schedule...")
            run_agent_cycle(deliveries, trucks, w1, w2)

        elif choice == "3":
            print("\n  Adjusting control parameters...")
            w1, w2 = get_weight_settings()

            for delivery in deliveries:
                delivery["w1"] = w1
                delivery["w2"] = w2
                recalculate_priority(delivery)

            print("  All priorities recalculated.")
            run_agent_cycle(deliveries, trucks, w1, w2)

        elif choice == "4":
            print("\n  Current Deliveries:")
            print("\n" "--------------------------------------------------------")
            for i, d in enumerate(
                calculate_priorities(deliveries), start=1
            ):
                display_delivery(d, rank=i)

        elif choice == "5":
            print("\n  Current Trucks:")
            print("-"*65)
            for truck in trucks:
                display_truck(truck)

        elif choice == "6":
            print("\n  Agent shutting down. Goodbye.\n")
            break

        else:
            print("\n  Invalid option.")


if __name__ == "__main__":
    main()