def create_delivery(delivery_id, hours_until_deadline, importance, w1=1.0, w2=1.0):
    priority_score = round(
        (w1 * (1 / hours_until_deadline)) + (w2 * importance), 4
    )

    return {
        "id"                  : delivery_id,
        "hours_until_deadline": hours_until_deadline,
        "importance"          : importance,
        "importance_label"    : get_importance_label(importance),
        "status"              : "Pending",
        "assigned_truck"      : None,
        "priority_score"      : priority_score,
        "w1"                  : w1,
        "w2"                  : w2
    }
def get_importance_label(importance):
    labels = {1: "Low", 2: "Medium", 3: "High"}
    return labels.get(importance, "Unknown")


def update_delivery_status(delivery, new_status, trucks=None, all_deliveries=None):
    valid_statuses = ["Pending", "In Transit", "Delivered", "Delayed"]
    if new_status not in valid_statuses:
        return False

    old_status = delivery["status"]
    delivery["status"] = new_status

    if trucks and delivery["assigned_truck"]:
        truck = next(
            (t for t in trucks
             if t["id"] == delivery["assigned_truck"]),
            None
        )

        if truck:
            if new_status == "In Transit":
                # Free the capacity slot
                if old_status in ["Pending", "Delayed"]:
                    if truck["load"] > 0:
                        truck["load"] -= 1
                    if delivery["id"] in truck["deliveries"]:
                        truck["deliveries"].remove(delivery["id"])

                truck["status"] = "Out for Delivery"

            elif new_status == "Delivered":

                if old_status in ["Pending", "Delayed"]:
                    if truck["load"] > 0:
                        truck["load"] -= 1
                    if delivery["id"] in truck["deliveries"]:
                        truck["deliveries"].remove(delivery["id"])

                if all_deliveries:
                    in_transit_on_truck = [
                        d for d in all_deliveries
                        if d["assigned_truck"] == truck["id"]
                        and d["status"] == "In Transit"
                        and d["id"] != delivery["id"]
                    ]
                    if in_transit_on_truck:

                        truck["status"] = "Out for Delivery"
                    else:

                        if truck["load"] == 0:
                            truck["status"] = "Available"
                        elif truck["load"] < truck["capacity"]:
                            truck["status"] = "Available"
                        else:
                            truck["status"] = "Full"
                else:
                    if truck["load"] == 0:
                        truck["status"] = "Available"
                    elif truck["load"] < truck["capacity"]:
                        truck["status"] = "Available"
                    else:
                        truck["status"] = "Full"

    return True

def recalculate_priority(delivery):
    delivery["priority_score"] = round(
        (delivery["w1"] * (1 / delivery["hours_until_deadline"]))
        + (delivery["w2"] * delivery["importance"]), 4
    )
    return delivery

def create_truck(truck_id, capacity):

    return {
        "id"         : truck_id,
        "capacity"   : capacity,
        "deliveries" : [],        # list of delivery IDs assigned
        "load"       : 0,         # current number of assigned deliveries
        "status"     : "Available"  # Available, Full, Out for Delivery
    }


def is_truck_available(truck):
    return truck["status"] == "Available" and truck["load"] < truck["capacity"]


def assign_delivery_to_truck(delivery, truck):
    if not is_truck_available(truck):
        return False

    delivery["assigned_truck"] = truck["id"]
    truck["deliveries"].append(delivery["id"])
    truck["load"] += 1

    if truck["load"] >= truck["capacity"]:
        truck["status"] = "Full"

    return True


def free_truck_slot(truck):
    if truck["load"] > 0:
        truck["load"] -= 1
        if truck["status"] == "Full":
            truck["status"] = "Available"
        return True
    return False

def display_delivery(delivery, rank=None):
    rank_str = f"  [{rank}] " if rank else "      "
    print(f"{rank_str}"
          f"{delivery['id']:<6} | "
          f"Deadline: {delivery['hours_until_deadline']}hrs | "
          f"Importance: {delivery['importance_label']:<8} | "
          f"Priority: {delivery['priority_score']:<8} | "
          f"Status: {delivery['status']:<12} | "
          f"Truck: {delivery['assigned_truck'] or 'Unassigned'}")


def display_truck(truck):
    assigned = ", ".join(truck["deliveries"]) if truck["deliveries"] else "None"
    print(f"      {truck['id']:<6} | "
          f"Capacity: {truck['capacity']} | "
          f"Load: {truck['load']} | "
          f"Status: {truck['status']:<16} | "
          f"Deliveries: {assigned}")