from typing import Any

from core.enums.order_event import OrderEventType
from core.schemas import (
    GameSnapshotSchema,
    OrderEventSchema,
    OrderSchema,
    StationSchema,
    TrainSchema,
)


def _normalize_cargo(raw_cargo: Any) -> list[dict[str, Any]]:
    if isinstance(raw_cargo, dict):
        return [{"name": name, "count": count} for name, count in raw_cargo.items()]

    if isinstance(raw_cargo, list):
        return [
            {
                "name": item.get("type") or item.get("name"),
                "count": item.get("count", 0),
            }
            for item in raw_cargo
            if isinstance(item, dict)
        ]

    return []


def to_snapshot_obj(raw_snapshot: dict) -> GameSnapshotSchema:
    raw_trains = raw_snapshot.get("trains", {}) or {}
    trains: dict[int, TrainSchema] = {}
    
    for train_id, raw_train_data in raw_trains.items():
        if not isinstance(raw_train_data, dict):
            continue

        front_loco, body_wagons, rear_loco = raw_train_data.get("length", "0-0-0").split("-")

        t_id_int = int(train_id)
        trains[t_id_int] = TrainSchema(
            id=t_id_int,
            name=raw_train_data.get("name", "Nameless"),
            front_loco=int(front_loco),
            body_wagons=int(body_wagons),
            rear_loco=int(rear_loco),
            fuel=raw_train_data.get("fuel", []),
            body_composition=raw_train_data.get("composition_summary", {}),
            planet=raw_train_data.get("planet", "Unknown planet"),
        )

    raw_stations = raw_snapshot.get("stations", {}) or {}
    stations: dict[int, StationSchema] = {}
    
    for station_id, raw_station in raw_stations.items():
        if not isinstance(raw_station, dict):
            continue

        raw_position = raw_station.get("position", {})
        s_id_int = int(station_id)

        stations[s_id_int] = StationSchema(
            id=s_id_int,
            name=raw_station.get("name", "Unnamed station"),
            position=(
                raw_position.get("x", 0),
                raw_position.get("y", 0),
            ),
            planet=raw_station.get("planet", "Unknown planet"),
        )

    raw_orders = raw_snapshot.get("active_orders", []) or []
    orders = []

    for raw_order in raw_orders:
        if not isinstance(raw_order, dict):
            continue

        t_id = int(raw_order["train_id"])
        train_data = trains.get(t_id, {"id": t_id})

        cargo_list = _normalize_cargo(raw_order.get("required", []))

        raw_current_content = raw_order.get("current_content", []) 
        current_content = _normalize_cargo(raw_current_content)

        orders.append(
            OrderSchema(
                id=raw_order["id"],
                train_data=train_data,
                created_tick=raw_order["creation_time"],
                network_id=raw_order["network_id"],
                current_cargo=current_content,
                requested_cargo=cargo_list,
            )
        )

    raw_events = raw_snapshot.get("order_events", []) or []
    order_events = []

    for raw_event in raw_events:
        if not isinstance(raw_event, dict):
            continue

        from_id = int(raw_event["from_id"])
        to_id = int(raw_event["to_id"])
        train_id = int(raw_event["train_id"])

        from_station = stations.get(from_id) or {"id": from_id}
        to_station = stations.get(to_id) or {"id": to_id}
        train_data = trains.get(train_id) or {"id": train_id}

        order_events.append(
            OrderEventSchema(
                id=raw_event["id"],
                order_id=raw_event["order_id"],
                type=normalize_type(raw_event["action"]),
                tick=raw_event["tick"],
                from_station=from_station,
                to_station=to_station,
                train_data=train_data,
                is_cargo_empty=raw_event["is_empty"],
            )
        )

    return GameSnapshotSchema(
        protocol_version=raw_snapshot["protocol_version"],
        world_id=raw_snapshot["world_id"],
        sequence_number=raw_snapshot["sequence_number"],
        tick=raw_snapshot["tick"],
        active_orders=orders,
        order_events=order_events,
        trains=trains,
        stations=stations,
    )

def normalize_type(raw_type):
    match raw_type:
        case "create":
            return OrderEventType.CREATED
        case "accept":
            return OrderEventType.LOADED
        case "complete":
            return OrderEventType.COMPLETED
        case "error":
            return OrderEventType.ERROR
        case "reassigned":
            return OrderEventType.REASSIGNED
        case _:
            return raw_type