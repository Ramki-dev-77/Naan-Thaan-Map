"""
Campus Navigation System — Seed Tooling
Seeds realistic campus spatial dataset with verified buildings, rooms, facilities,
and a fully connected pedestrian graph with stairs and accessible paths.
"""
import os
import json
import click
from flask import current_app
from app.extensions import db
from app.models.campus import Campus
from app.models.building import Building
from app.models.room import Room
from app.models.facility import Facility
from app.models.category import Category
from app.models.navigation import NavigationNode, NavigationEdge
from app.models.admin import AdminUser
from app.services.routing_service import haversine_distance
from app.utils.security import hash_password


def create_demo_data():
    """Generates realistic demo campus data."""
    # 1. Create Default Categories
    categories = [
        {"name": "Academic", "slug": "academic", "icon": "book", "color": "#2563eb"},
        {"name": "Dining", "slug": "dining", "icon": "coffee", "color": "#f97316"},
        {"name": "Parking", "slug": "parking", "icon": "car", "color": "#64748b"},
        {"name": "Medical", "slug": "medical", "icon": "plus-circle", "color": "#ef4444"},
        {"name": "Restroom", "slug": "restroom", "icon": "restroom", "color": "#06b6d4"},
        {"name": "Administration", "slug": "admin", "icon": "briefcase", "color": "#8b5cf6"},
        {"name": "Auditorium", "slug": "auditorium", "icon": "users", "color": "#ec4899"},
        {"name": "Library", "slug": "library", "icon": "bookmark", "color": "#10b981"},
    ]
    cat_map = {}
    for c in categories:
        existing = Category.query.filter_by(slug=c["slug"]).first()
        if not existing:
            cat_obj = Category(**c)
            db.session.add(cat_obj)
            db.session.flush()
            cat_map[c["slug"]] = cat_obj
        else:
            cat_map[c["slug"]] = existing

    # 2. Create Default Admin User
    admin = AdminUser.query.filter_by(username="admin").first()
    if not admin:
        admin = AdminUser(
            username="admin",
            email="admin@campus.edu",
            password_hash=hash_password("CampusAdmin2026!"),
            role="superadmin",
            is_active=True
        )
        db.session.add(admin)

    # 3. Create Campus
    campus_name = "Demo Engineering Campus"
    campus = Campus.query.filter_by(slug="demo-engineering-campus").first()
    if not campus:
        # Campus boundary roughly 450m x 450m
        boundary_coords = [
            [77.5920, 12.9700],
            [77.5975, 12.9700],
            [77.5975, 12.9745],
            [77.5920, 12.9745],
            [77.5920, 12.9700]
        ]
        campus = Campus(
            name=campus_name,
            slug="demo-engineering-campus",
            description="Realistic benchmark engineering campus model featuring academic blocks, research labs, student amenities, and verified accessible walkway graphs.",
            latitude=12.9722,
            longitude=12.9722,
            boundary={"type": "Polygon", "coordinates": [boundary_coords]},
            is_active=True
        )
        # Fix coordinates center
        campus.latitude = 12.9722
        campus.longitude = 77.5947
        db.session.add(campus)
        db.session.flush()

    # Clear existing campus children to allow clean re-seed
    Building.query.filter_by(campus_id=campus.id).delete()
    Facility.query.filter_by(campus_id=campus.id).delete()
    NavigationNode.query.filter_by(campus_id=campus.id).delete()
    db.session.commit()

    # 4. Create Buildings
    # Footprint helper: creates a small rectangular polygon around centroid
    def make_box(lat, lng, dlat=0.0003, dlng=0.0004):
        return {
            "type": "Polygon",
            "coordinates": [[
                [lng - dlng, lat - dlat],
                [lng + dlng, lat - dlat],
                [lng + dlng, lat + dlat],
                [lng - dlng, lat + dlat],
                [lng - dlng, lat - dlat]
            ]]
        }

    buildings_data = [
        {
            "name": "Administration Block",
            "code": "ADM",
            "description": "Central Administrative Offices, Dean of Academics, Registrar, and Admissions.",
            "latitude": 12.9708,
            "longitude": 77.5935,
            "entrance_lat": 12.9708,
            "entrance_lng": 77.5939,
            "floors": 3,
            "accessible": True,
            "footprint": make_box(12.9708, 12.9708)
        },
        {
            "name": "Computer Science Block",
            "code": "CSB",
            "description": "Department of Computer Science & Engineering, AI Lab, Systems Lab, and Cloud Infrastructure Hub.",
            "latitude": 12.9732,
            "longitude": 77.5940,
            "entrance_lat": 12.9732,
            "entrance_lng": 77.5944,
            "floors": 4,
            "accessible": True,
            "footprint": make_box(12.9732, 12.9732)
        },
        {
            "name": "Electronics Block",
            "code": "EEB",
            "description": "Electronics, Robotics, VLSI Design Labs, and Microcontroller Workshops.",
            "latitude": 12.9735,
            "longitude": 77.5960,
            "entrance_lat": 12.9735,
            "entrance_lng": 77.5956,
            "floors": 3,
            "accessible": True,
            "footprint": make_box(12.9735, 12.9735)
        },
        {
            "name": "Central Library",
            "code": "LIB",
            "description": "Multilevel Digital Archive, Quiet Study Zones, Journal Collections, and Collaborative Study Rooms.",
            "latitude": 12.9720,
            "longitude": 77.5952,
            "entrance_lat": 12.9720,
            "entrance_lng": 77.5948,
            "floors": 3,
            "accessible": True,
            "footprint": make_box(12.9720, 12.9720)
        },
        {
            "name": "Student Center",
            "code": "SAC",
            "description": "Student Dining Hall, Cafeteria, Cultural Activity Rooms, and Campus Bookstore.",
            "latitude": 12.9715,
            "longitude": 77.5962,
            "entrance_lat": 12.9715,
            "entrance_lng": 77.5958,
            "floors": 2,
            "accessible": True,
            "footprint": make_box(12.9715, 12.9715)
        },
        {
            "name": "Main Auditorium",
            "code": "AUD",
            "description": "1,500-seat Plenary Hall for Graduation, Conferences, Guest Lectures, and Cultural Events.",
            "latitude": 12.9707,
            "longitude": 77.5955,
            "entrance_lat": 12.9707,
            "entrance_lng": 77.5951,
            "floors": 2,
            "accessible": True,
            "footprint": make_box(12.9707, 12.9707)
        }
    ]

    # Fix footprints coordinates correctly with proper lat & lng
    for b in buildings_data:
        b["footprint"] = make_box(b["latitude"], b["longitude"])

    building_map = {}
    for b_data in buildings_data:
        b_obj = Building(
            campus_id=campus.id,
            name=b_data["name"],
            code=b_data["code"],
            description=b_data["description"],
            latitude=b_data["latitude"],
            longitude=b_data["longitude"],
            entrance_latitude=b_data["entrance_lat"],
            entrance_longitude=b_data["entrance_lng"],
            footprint=b_data["footprint"],
            floors=b_data["floors"],
            accessible=b_data["accessible"]
        )
        db.session.add(b_obj)
        db.session.flush()
        building_map[b_data["code"]] = b_obj

    # 5. Create Navigation Nodes (Walkway junctions, entrances, stairs, ramps)
    nodes_data = [
        # Gate & Perimeter Junctions
        {"id_key": "GATE_MAIN", "lat": 12.9701, "lng": 77.5945, "type": "ENTRANCE", "label": "Main Campus Gate", "floor": 0},
        {"id_key": "JUNC_SOUTH", "lat": 12.9705, "lng": 77.5945, "type": "JUNCTION", "label": "South Central Plaza Junction", "floor": 0},
        {"id_key": "JUNC_CENTRAL", "lat": 12.9718, "lng": 77.5946, "type": "JUNCTION", "label": "Campus Central Fountain Plaza", "floor": 0},
        {"id_key": "JUNC_NORTH", "lat": 12.9728, "lng": 77.5946, "type": "JUNCTION", "label": "North Quad Junction", "floor": 0},
        {"id_key": "JUNC_EAST", "lat": 12.9720, "lng": 77.5958, "type": "JUNCTION", "label": "East Courtyard Junction", "floor": 0},
        {"id_key": "JUNC_WEST", "lat": 12.9718, "lng": 77.5938, "type": "JUNCTION", "label": "West Academic Walkway", "floor": 0},

        # Building Entrances (Ground level)
        {"id_key": "ENT_ADM", "lat": 12.9708, "lng": 77.5939, "type": "ENTRANCE", "label": "Administration Block Entrance", "building": "ADM", "floor": 0},
        {"id_key": "ENT_CSB", "lat": 12.9732, "lng": 77.5944, "type": "ENTRANCE", "label": "Computer Science Block Entrance", "building": "CSB", "floor": 0},
        {"id_key": "ENT_EEB", "lat": 12.9735, "lng": 77.5956, "type": "ENTRANCE", "label": "Electronics Block Entrance", "building": "EEB", "floor": 0},
        {"id_key": "ENT_LIB", "lat": 12.9720, "lng": 77.5948, "type": "ENTRANCE", "label": "Central Library Entrance", "building": "LIB", "floor": 0},
        {"id_key": "ENT_SAC", "lat": 12.9715, "lng": 77.5958, "type": "ENTRANCE", "label": "Student Center Entrance", "building": "SAC", "floor": 0},
        {"id_key": "ENT_AUD", "lat": 12.9707, "lng": 77.5951, "type": "ENTRANCE", "label": "Auditorium Main Portico", "building": "AUD", "floor": 0},

        # Specialized Nodes: Stairs vs Accessible Ramp at Central Terrace
        {"id_key": "TERRACE_LOWER", "lat": 12.9722, "lng": 77.5942, "type": "JUNCTION", "label": "Lower Terrace Plaza", "floor": 0},
        {"id_key": "TERRACE_STAIRS", "lat": 12.9724, "lng": 77.5942, "type": "STAIRS", "label": "Terrace Stone Steps (Stairs)", "floor": 0},
        {"id_key": "TERRACE_RAMP", "lat": 12.9723, "lng": 77.5940, "type": "RAMP", "label": "Terrace Accessible Ramp", "floor": 0},
        {"id_key": "TERRACE_UPPER", "lat": 12.9726, "lng": 77.5942, "type": "JUNCTION", "label": "Upper CS Quad", "floor": 0},

        # Indoor CS Block Nodes (Floor 1 and 2)
        {"id_key": "CS_LOBBY", "lat": 12.9732, "lng": 77.5942, "type": "CORRIDOR", "label": "CS Ground Floor Lobby", "building": "CSB", "floor": 0},
        {"id_key": "CS_ELEVATOR_G", "lat": 12.9733, "lng": 77.5941, "type": "ELEVATOR", "label": "CS Block Elevator (Ground)", "building": "CSB", "floor": 0},
        {"id_key": "CS_ELEVATOR_1", "lat": 12.9733, "lng": 77.5941, "type": "ELEVATOR", "label": "CS Block Elevator (Floor 1)", "building": "CSB", "floor": 1},
        {"id_key": "CS_ELEVATOR_2", "lat": 12.9733, "lng": 77.5941, "type": "ELEVATOR", "label": "CS Block Elevator (Floor 2)", "building": "CSB", "floor": 2},
        {"id_key": "CS_DOOR_101", "lat": 12.9731, "lng": 77.5940, "type": "DOOR", "label": "Door CS-101", "building": "CSB", "floor": 0},
        {"id_key": "CS_DOOR_102", "lat": 12.9731, "lng": 77.5938, "type": "DOOR", "label": "Door CS-102", "building": "CSB", "floor": 0},
        {"id_key": "CS_DOOR_LAB1", "lat": 12.9734, "lng": 77.5940, "type": "DOOR", "label": "Door CS-LAB-1", "building": "CSB", "floor": 1},
        {"id_key": "CS_DOOR_LAB2", "lat": 12.9734, "lng": 77.5938, "type": "DOOR", "label": "Door CS-LAB-2", "building": "CSB", "floor": 2},
    ]

    node_obj_map = {}
    for nd in nodes_data:
        b_id = building_map[nd["building"]].id if "building" in nd else None
        node = NavigationNode(
            campus_id=campus.id,
            building_id=b_id,
            node_type=nd["type"],
            label=nd["label"],
            floor=nd["floor"],
            latitude=nd["lat"],
            longitude=nd["lng"],
            is_active=True
        )
        db.session.add(node)
        db.session.flush()
        node_obj_map[nd["id_key"]] = node

    # 6. Create Navigation Edges with true Haversine distance
    edges_spec = [
        # Main spine (South to North)
        ("GATE_MAIN", "JUNC_SOUTH", True, False, "PAVED_WALKWAY"),
        ("JUNC_SOUTH", "ENT_ADM", True, False, "PAVED_WALKWAY"),
        ("JUNC_SOUTH", "ENT_AUD", True, False, "PAVED_WALKWAY"),
        ("JUNC_SOUTH", "JUNC_CENTRAL", True, False, "PAVED_WALKWAY"),
        
        # Central Hub Connections
        ("JUNC_CENTRAL", "ENT_LIB", True, False, "PAVED_WALKWAY"),
        ("JUNC_CENTRAL", "JUNC_EAST", True, False, "PAVED_WALKWAY"),
        ("JUNC_CENTRAL", "JUNC_WEST", True, False, "PAVED_WALKWAY"),
        ("JUNC_CENTRAL", "TERRACE_LOWER", True, False, "PAVED_WALKWAY"),

        # Terrace Paths: STAIRS vs ACCESSIBLE RAMP
        ("TERRACE_LOWER", "TERRACE_STAIRS", False, True, "STAIRWAY"),     # Stairs (accessible=False)
        ("TERRACE_STAIRS", "TERRACE_UPPER", False, True, "STAIRWAY"),     # Stairs (accessible=False)
        ("TERRACE_LOWER", "TERRACE_RAMP", True, False, "RAMP"),           # Ramp (accessible=True)
        ("TERRACE_RAMP", "TERRACE_UPPER", True, False, "RAMP"),           # Ramp (accessible=True)

        # North Quad Connections
        ("TERRACE_UPPER", "JUNC_NORTH", True, False, "PAVED_WALKWAY"),
        ("JUNC_NORTH", "ENT_CSB", True, False, "PAVED_WALKWAY"),
        ("JUNC_NORTH", "ENT_EEB", True, False, "PAVED_WALKWAY"),

        # East Quad & Student Center
        ("JUNC_EAST", "ENT_SAC", True, False, "PAVED_WALKWAY"),
        ("ENT_SAC", "ENT_EEB", True, False, "PAVED_WALKWAY"),

        # CS Block Internal Connectivity
        ("ENT_CSB", "CS_LOBBY", True, False, "CORRIDOR"),
        ("CS_LOBBY", "CS_DOOR_101", True, False, "CORRIDOR"),
        ("CS_DOOR_101", "CS_DOOR_102", True, False, "CORRIDOR"),
        ("CS_LOBBY", "CS_ELEVATOR_G", True, False, "CORRIDOR"),
        ("CS_ELEVATOR_G", "CS_ELEVATOR_1", True, False, "ELEVATOR"),
        ("CS_ELEVATOR_1", "CS_DOOR_LAB1", True, False, "CORRIDOR"),
        ("CS_ELEVATOR_1", "CS_ELEVATOR_2", True, False, "ELEVATOR"),
        ("CS_ELEVATOR_2", "CS_DOOR_LAB2", True, False, "CORRIDOR"),
    ]

    for src_k, dst_k, is_acc, has_stairs, ptype in edges_spec:
        src_node = node_obj_map[src_k]
        dst_node = node_obj_map[dst_k]
        dist = haversine_distance(src_node.latitude, src_node.longitude, dst_node.latitude, dst_node.longitude)
        if dist < 1.0:
            dist = 4.0  # Vertical elevator height

        edge = NavigationEdge(
            source_node_id=src_node.id,
            destination_node_id=dst_node.id,
            distance=dist,
            accessible=is_acc,
            stairs=has_stairs,
            path_type=ptype,
            is_bidirectional=True
        )
        db.session.add(edge)

    # 7. Create Rooms
    rooms_data = [
        # CS Block
        {"building": "CSB", "num": "CS-101", "name": "Foundations of Computing", "floor": 0, "dept": "Computer Science", "node": "CS_DOOR_101"},
        {"building": "CSB", "num": "CS-102", "name": "Algorithms Lecture Theatre", "floor": 0, "dept": "Computer Science", "node": "CS_DOOR_102"},
        {"building": "CSB", "num": "CS-201", "name": "Software Engineering Seminar Room", "floor": 1, "dept": "Computer Science", "node": "CS_DOOR_LAB1"},
        {"building": "CSB", "num": "CS-LAB-1", "name": "Artificial Intelligence & Robotics Lab", "floor": 1, "dept": "Computer Science", "node": "CS_DOOR_LAB1"},
        {"building": "CSB", "num": "CS-LAB-2", "name": "Cloud Computing & Systems Lab", "floor": 2, "dept": "Computer Science", "node": "CS_DOOR_LAB2"},
        
        # Administration Block
        {"building": "ADM", "num": "ADM-101", "name": "Registrar & Admissions Desk", "floor": 0, "dept": "Administration", "node": "ENT_ADM"},
        {"building": "ADM", "num": "ADM-204", "name": "Office of the Dean of Academic Affairs", "floor": 1, "dept": "Academic Administration", "node": "ENT_ADM"},

        # Electronics Block
        {"building": "EEB", "num": "EE-101", "name": "Circuits & Signal Processing Lab", "floor": 0, "dept": "Electronics Engineering", "node": "ENT_EEB"},
        {"building": "EEB", "num": "EE-205", "name": "VLSI Design & Embedded Systems Workshop", "floor": 1, "dept": "Electronics Engineering", "node": "ENT_EEB"},

        # Library
        {"building": "LIB", "num": "LIB-01", "name": "Digital Reference & Journal Section", "floor": 0, "dept": "Library Services", "node": "ENT_LIB"},
        {"building": "LIB", "num": "LIB-02", "name": "Silent Graduate Study Hall", "floor": 1, "dept": "Library Services", "node": "ENT_LIB"},
    ]

    for r in rooms_data:
        b_obj = building_map[r["building"]]
        door_node = node_obj_map.get(r.get("node"))
        room = Room(
            building_id=b_obj.id,
            room_number=r["num"],
            name=r["name"],
            floor=r["floor"],
            department=r["dept"],
            latitude=door_node.latitude if door_node else b_obj.latitude,
            longitude=door_node.longitude if door_node else b_obj.longitude,
            node_id=door_node.id if door_node else None,
            description=f"{r['name']} situated in {b_obj.name}, Floor {r['floor']}."
        )
        db.session.add(room)

    # 8. Create Campus Facilities & Points of Interest
    facilities_data = [
        {"name": "Main Entrance Security Checkpoint", "cat": "admin", "lat": 12.9701, "lng": 77.5945, "bld": None, "desc": "24/7 Security Gate, Visitor Passes, and Campus Information Counter.", "hours": "24 Hours"},
        {"name": "South Campus Parking Lot", "cat": "parking", "lat": 12.9703, "lng": 77.5932, "bld": None, "desc": "Visitor and Faculty two-wheeler and four-wheeler parking zone with EV charging.", "hours": "06:00 - 22:00"},
        {"name": "Campus Health & Urgent Medical Center", "cat": "medical", "lat": 12.9712, "lng": 77.5933, "bld": None, "desc": "First aid, licensed campus physician on duty, and ambulance dispatch.", "hours": "08:00 - 20:00"},
        {"name": "Central Cafeteria & Food Court", "cat": "dining", "lat": 12.9715, "lng": 77.5960, "bld": "SAC", "desc": "Hot meals, bakery, coffee bar, and grab-and-go refreshments.", "hours": "07:30 - 21:00"},
        {"name": "Ground Floor Restroom (Accessible)", "cat": "restroom", "lat": 12.9721, "lng": 77.5947, "bld": "LIB", "desc": "Gender-neutral, ADA compliant wheelchair accessible restroom.", "hours": "All Building Hours"},
        {"name": "Central Library Helpdesk & Reserves", "cat": "library", "lat": 12.9720, "lng": 77.5950, "bld": "LIB", "desc": "Book circulation, inter-library loans, and research assistance.", "hours": "08:00 - 23:00"},
        {"name": "Main Auditorium Foyer", "cat": "auditorium", "lat": 12.9707, "lng": 77.5951, "bld": "AUD", "desc": "Ticketing and reception foyer for college symposia and cultural events.", "hours": "Event Days"},
    ]

    for f in facilities_data:
        cat_obj = cat_map.get(f["cat"])
        b_obj = building_map.get(f["bld"]) if f["bld"] else None
        facility = Facility(
            campus_id=campus.id,
            building_id=b_obj.id if b_obj else None,
            category_id=cat_obj.id,
            name=f["name"],
            description=f["desc"],
            latitude=f["lat"],
            longitude=f["lng"],
            accessible=True,
            opening_hours=f["hours"]
        )
        db.session.add(facility)

    db.session.commit()
    return campus


def create_svce_data():
    """Generates authentic Sri Venkateswara College of Engineering (SVCE) campus data."""
    # Ensure Categories
    cat_map = {c.slug: c for c in Category.query.all()}
    if not cat_map:
        create_demo_data()
        cat_map = {c.slug: c for c in Category.query.all()}

    campus_name = "Sri Venkateswara College of Engineering (SVCE)"
    campus_slug = "svce-sriperumbudur"

    campus = Campus.query.filter_by(slug=campus_slug).first()
    boundary_coords = [
        [79.9680, 12.9845],
        [79.9760, 12.9845],
        [79.9760, 12.9905],
        [79.9680, 12.9905],
        [79.9680, 12.9845]
    ]

    if not campus:
        campus = Campus(
            name=campus_name,
            slug=campus_slug,
            description="Sri Venkateswara College of Engineering (SVCE Autonomous), Pennalur, Sriperumbudur, Tamil Nadu. Established in 1985.",
            latitude=12.9871,
            longitude=79.9719,
            boundary={"type": "Polygon", "coordinates": [boundary_coords]},
            is_active=True
        )
        db.session.add(campus)
        db.session.flush()
    else:
        # Clear existing SVCE child records to reseed cleanly
        svce_node_ids = [n.id for n in NavigationNode.query.filter_by(campus_id=campus.id).all()]
        if svce_node_ids:
            NavigationEdge.query.filter(
                (NavigationEdge.source_node_id.in_(svce_node_ids)) |
                (NavigationEdge.destination_node_id.in_(svce_node_ids))
            ).delete(synchronize_session=False)
        
        bld_ids = [b.id for b in Building.query.filter_by(campus_id=campus.id).all()]
        if bld_ids:
            Room.query.filter(Room.building_id.in_(bld_ids)).delete(synchronize_session=False)

        Building.query.filter_by(campus_id=campus.id).delete()
        Facility.query.filter_by(campus_id=campus.id).delete()
        NavigationNode.query.filter_by(campus_id=campus.id).delete()
        db.session.commit()

    # Exact SVCE building footprints aligned with OpenStreetMap base layer
    buildings_data = [
        {
            "name": "Administration Block", "code": "ADM",
            "desc": "Principal Office, Dean Academics, Examination Cell, and Admissions.",
            "lat": 12.98695, "lng": 79.97195,
            "ent_lat": 12.98696, "ent_lng": 79.97195,
            "floors": 2, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.971643, 12.9869254], [79.9718625, 12.9869234], [79.9718625, 12.9869648], [79.9719443, 12.986964], [79.9719658, 12.9869638], [79.9721187, 12.9868099], [79.9722571, 12.9866707], [79.9722575, 12.9866219], [79.972258, 12.9865711], [79.9722155, 12.9865374], [79.9722571, 12.9866707], [79.9721973, 12.9868788], [79.9719612, 12.9871123], [79.9719469, 12.987112], [79.9718728, 12.9871104], [79.9718738, 12.9870766], [79.9718315, 12.9870709], [79.971792, 12.987132], [79.9716962, 12.987132], [79.9716417, 12.9870803], [79.971643, 12.9869254]]]}
        },
        {
            "name": "Dr. A.C. Muthiah Central Library", "code": "LIB",
            "desc": "Dr. A.C. Muthiah Central Library with digital archives, reference stacks, and quiet reading halls.",
            "lat": 12.986805, "lng": 79.971314,
            "ent_lat": 12.986904, "ent_lng": 79.971196,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9711958, 12.9869043], [79.9711992, 12.9870178], [79.9715351, 12.9870001], [79.9715403, 12.9869116], [79.9715423, 12.9868144], [79.971471, 12.9868125], [79.9714651, 12.9867812], [79.9714664, 12.9866281], [79.9712421, 12.9866326], [79.9712455, 12.9867027], [79.9711859, 12.9867018], [79.9711883, 12.9867473], [79.9712004, 12.9867474], [79.9712027, 12.9867878], [79.9711691, 12.9867872], [79.9711677, 12.986906], [79.9711958, 12.9869043]]]}
        },
        {
            "name": "Computer Science Block", "code": "CSB",
            "desc": "Department of Computer Science & Engineering, AI Lab, Systems Lab, and Cloud Infrastructure Hub.",
            "lat": 12.987423, "lng": 79.973043,
            "ent_lat": 12.987307, "ent_lng": 79.972913,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.97274, 12.9876], [79.9729234, 12.987684], [79.9730337, 12.9875588], [79.9730791, 12.9875501], [79.9730743, 12.9874213], [79.9730604, 12.9872884], [79.9730112, 12.9872945], [79.9729127, 12.9873066], [79.9729112, 12.987394], [79.9728287, 12.9873958], [79.9727492, 12.987484], [79.9726855, 12.9875546], [79.97274, 12.9876]]]}
        },
        {
            "name": "Mechanical Engineering Block", "code": "MEC",
            "desc": "Department of Mechanical Engineering, Thermal Engineering, and Dynamics Labs.",
            "lat": 12.987799, "lng": 79.972741,
            "ent_lat": 12.987716, "ent_lng": 79.972746,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9726841, 12.9876602], [79.9726213, 12.987662], [79.9726235, 12.9879128], [79.9727574, 12.9879093], [79.9728958, 12.9879056], [79.9728954, 12.9877158], [79.9729234, 12.987684], [79.97274, 12.9876], [79.9726841, 12.9876602]]]}
        },
        {
            "name": "Information Technology Block", "code": "ITB",
            "desc": "Department of Information Technology, Software Engineering, and Multimedia Labs.",
            "lat": 12.987086, "lng": 79.973097,
            "ent_lat": 12.987104, "ent_lng": 79.972967,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9730467, 12.9871972], [79.9731149, 12.9871947], [79.9731081, 12.9871133], [79.9732616, 12.9871047], [79.973256, 12.9870515], [79.9732529, 12.9870226], [79.9731292, 12.9870301], [79.9731173, 12.9869691], [79.9730707, 12.9869732], [79.973039, 12.986976], [79.9730503, 12.9871013], [79.9729672, 12.9871044], [79.9729704, 12.9871566], [79.9729758, 12.9872034], [79.9730467, 12.9871972]]]}
        },
        {
            "name": "Electronics & Communication Block", "code": "ECE",
            "desc": "Department of ECE, Embedded Systems, Signal Processing, and VLSI Design.",
            "lat": 12.987431, "lng": 79.972372,
            "ent_lat": 12.987346, "ent_lng": 79.972404,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9722192, 12.9876046], [79.9722168, 12.9874789], [79.9722143, 12.9873488], [79.972404, 12.9873455], [79.97245, 12.98742], [79.9725261, 12.9875105], [79.9725245, 12.987598], [79.9722192, 12.9876046]]]}
        },
        {
            "name": "MCA Block", "code": "MCA",
            "desc": "Department of Master of Computer Applications and Advanced Computing Labs.",
            "lat": 12.98723, "lng": 79.972578,
            "ent_lat": 12.987249, "ent_lng": 79.972489,
            "floors": 2, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.972404, 12.9873455], [79.9724895, 12.9872488], [79.9725427, 12.9871887], [79.97264, 12.9872448], [79.9727522, 12.9873504], [79.9726875, 12.9874219], [79.9726087, 12.9875089], [79.9725261, 12.9875105], [79.97245, 12.98742], [79.972404, 12.9873455]]]}
        },
        {
            "name": "Applied Science & Humanities", "code": "ASH",
            "desc": "Physics, Chemistry, Mathematics Departments, and First Year Lecture Halls.",
            "lat": 12.987121, "lng": 79.972681,
            "ent_lat": 12.986996, "ent_lng": 79.972679,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9725427, 12.9871887], [79.9725427, 12.986999], [79.9726794, 12.9869957], [79.9728149, 12.9869924], [79.9728164, 12.9872071], [79.9728166, 12.9872432], [79.9727539, 12.9872448], [79.97264, 12.9872448], [79.9725427, 12.9871887]]]}
        },
        {
            "name": "Chemical Engineering Block", "code": "CHE",
            "desc": "Department of Chemical Engineering, Mass Transfer, and Process Labs.",
            "lat": 12.987798, "lng": 79.97225,
            "ent_lat": 12.98768, "ent_lng": 79.972369,
            "floors": 2, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9720903, 12.9878701], [79.9720882, 12.9877674], [79.9722267, 12.9877636], [79.9722273, 12.987681], [79.9723693, 12.9876803], [79.9723711, 12.9877645], [79.9723012, 12.9877679], [79.9723058, 12.9879124], [79.972258, 12.9879127], [79.9722574, 12.9878639], [79.9720903, 12.9878701]]]}
        },
        {
            "name": "Biotechnology Block", "code": "BIO",
            "desc": "Department of Biotechnology, Genetic Engineering, and Bio-processing Labs.",
            "lat": 12.987281, "lng": 79.971484,
            "ent_lat": 12.987355, "ent_lng": 79.971437,
            "floors": 2, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9714374, 12.9873545], [79.9714469, 12.9874507], [79.9715564, 12.9874525], [79.9715508, 12.9873363], [79.9716496, 12.9873336], [79.9716521, 12.9872648], [79.9716248, 12.9872673], [79.9716271, 12.9871476], [79.9715175, 12.9871588], [79.9715227, 12.9872616], [79.9714478, 12.9872659], [79.9714384, 12.9871663], [79.9713332, 12.9871719], [79.9713417, 12.987244], [79.971294, 12.9872565], [79.971298, 12.987366], [79.9714374, 12.9873545]]]}
        },
        {
            "name": "Marine Engineering Block", "code": "MAR",
            "desc": "Department of Marine Engineering, Ship Simulators, and Marine Power Plant Labs.",
            "lat": 12.987911, "lng": 79.97141,
            "ent_lat": 12.987868, "ent_lng": 79.971333,
            "floors": 2, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9713181, 12.9876171], [79.9715781, 12.9876048], [79.9716011, 12.9880238], [79.9715016, 12.98803], [79.9714955, 12.9879321], [79.9713579, 12.9879382], [79.9713701, 12.9881065], [79.9712783, 12.9881112], [79.971263, 12.9878738], [79.9713334, 12.9878677], [79.9713181, 12.9876171]]]}
        },
        {
            "name": "Research & Development Center", "code": "RND",
            "desc": "Innovation Hub, Patent Cell, and Interdisciplinary Research Laboratories.",
            "lat": 12.988864, "lng": 79.971118,
            "ent_lat": 12.988753, "ent_lng": 79.970966,
            "floors": 2, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9709779, 12.9889894], [79.9712705, 12.9889766], [79.9712569, 12.9887381], [79.9709661, 12.9887531], [79.9709779, 12.9889894]]]}
        },
        {
            "name": "Multi Purpose Hall", "code": "MPH",
            "desc": "Indoor Auditorium, Cultural Arena, and Convocation Hall.",
            "lat": 12.989451, "lng": 79.971463,
            "ent_lat": 12.989317, "ent_lng": 79.971174,
            "floors": 2, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9711738, 12.9893166], [79.971204, 12.9896321], [79.97175, 12.9895859], [79.9717259, 12.9892702], [79.9711738, 12.9893166]]]}
        },
        {
            "name": "Class Room Block 1 (CRB 1)", "code": "CRB1",
            "desc": "Lecture Halls, Seminar Rooms, and Tutorial Classrooms.",
            "lat": 12.986636, "lng": 79.972398,
            "ent_lat": 12.986628, "ent_lng": 79.972446,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9723407, 12.9865213], [79.9724396, 12.9865224], [79.972497, 12.9865747], [79.9724456, 12.9866283], [79.9724985, 12.9866797], [79.9724272, 12.9867534], [79.9724175, 12.9867452], [79.9723718, 12.9867063], [79.9722571, 12.9866707], [79.9723407, 12.9865213]]]}
        },
        {
            "name": "Class Room Block 2 (CRB 2)", "code": "CRB2",
            "desc": "Lecture Halls, Smart Classrooms, and Faculty Rooms.",
            "lat": 12.986758, "lng": 79.972595,
            "ent_lat": 12.986803, "ent_lng": 79.972587,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9726043, 12.9868266], [79.9726572, 12.9868769], [79.9727314, 12.9868028], [79.9726745, 12.9867525], [79.9727261, 12.9866982], [79.9726586, 12.9866334], [79.972607, 12.9866844], [79.9725527, 12.9866347], [79.9724825, 12.9867075], [79.9725288, 12.9867485], [79.9724841, 12.9867978], [79.9724759, 12.9868068], [79.9725553, 12.9868822], [79.9726043, 12.9868266]]]}
        },
        {
            "name": "Class Room Block 3 (CRB 3)", "code": "CRB3",
            "desc": "Lecture Halls and Department Classrooms.",
            "lat": 12.988049, "lng": 79.972695,
            "ent_lat": 12.988089, "ent_lng": 79.972828,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9727017, 12.9881208], [79.9727597, 12.988167], [79.972828, 12.9880894], [79.9727659, 12.9880436], [79.9728132, 12.9879869], [79.9727607, 12.9879446], [79.9727391, 12.9879273], [79.9726916, 12.9879807], [79.9726322, 12.9879352], [79.9725679, 12.9880112], [79.9726183, 12.9880487], [79.9725701, 12.9881092], [79.9726199, 12.9881488], [79.9726572, 12.9881785], [79.9727017, 12.9881208]]]}
        },
        {
            "name": "Class Room Block 4 (CRB 4)", "code": "CRB4",
            "desc": "Multi-storey Class Room Block 4 with Modern Lecture Theatres.",
            "lat": 12.98738, "lng": 79.973284,
            "ent_lat": 12.987431, "ent_lng": 79.973234,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9732335, 12.9874314], [79.9732361, 12.9875044], [79.973341, 12.9875032], [79.9733354, 12.9874275], [79.9734103, 12.9874248], [79.9734074, 12.9873312], [79.9733349, 12.9873316], [79.9733308, 12.9872581], [79.9732297, 12.9872611], [79.9732341, 12.9873228], [79.9731556, 12.9873274], [79.9731596, 12.9874369], [79.9732335, 12.9874314]]]}
        },
        {
            "name": "Class Room Block 5 (CRB 5)", "code": "CRB5",
            "desc": "Class Room Block 5 and Examination Halls.",
            "lat": 12.988256, "lng": 79.974363,
            "ent_lat": 12.988362, "ent_lng": 79.974016,
            "floors": 2, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9740161, 12.9883618], [79.9743192, 12.9886255], [79.9747318, 12.9881524], [79.9743861, 12.9878859], [79.9740161, 12.9883618]]]}
        },
        {
            "name": "Central Cafeteria", "code": "CAF",
            "desc": "Campus Dining Hall, Student Cafeteria, Coffee and Refreshment Counters.",
            "lat": 12.986477, "lng": 79.972295,
            "ent_lat": 12.986491, "ent_lng": 79.972305,
            "floors": 1, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9722155, 12.9865374], [79.9721087, 12.9864527], [79.9721096, 12.9863729], [79.972196, 12.9863757], [79.972197, 12.986277], [79.9722844, 12.9862798], [79.97229, 12.9863785], [79.9723492, 12.986433], [79.972305, 12.9864912], [79.9722155, 12.9865374]]]}
        },
        {
            "name": "Central Workshops", "code": "WKS",
            "desc": "Machine Shop, Foundry, Welding Shop, Fitting, Carpentry, and CNC Labs.",
            "lat": 12.9882, "lng": 79.9716,
            "ent_lat": 12.988265, "ent_lng": 79.971876,
            "floors": 1, "acc": True,
            "footprint": {"type": "MultiPolygon", "coordinates": [[[[79.9714376, 12.9888805], [79.9719078, 12.9888561], [79.9718757, 12.9882649], [79.9714004, 12.9882914], [79.9714376, 12.9888805]]], [[[79.9720721, 12.9882463], [79.9720946, 12.988811], [79.9725554, 12.988784], [79.9725315, 12.9882224], [79.9720721, 12.9882463]]], [[[79.9709633, 12.9876262], [79.971208, 12.9876171], [79.971243, 12.9882043], [79.9709997, 12.9882196], [79.9709633, 12.9876262]]], [[[79.9717091, 12.9881044], [79.9720137, 12.9880895], [79.9720083, 12.9880049], [79.9719583, 12.9880081], [79.9719391, 12.9876358], [79.9717368, 12.9876422], [79.9717571, 12.9880196], [79.9717069, 12.9880235], [79.9717091, 12.9881044]]]]}
        },
        {
            "name": "Open Air Theatre", "code": "OAT",
            "desc": "Campus Open Air Amphitheatre for Cultural Events and Student Gatherings.",
            "lat": 12.987196, "lng": 79.971087,
            "ent_lat": 12.987188, "ent_lng": 79.971016,
            "floors": 1, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9709308, 12.9873007], [79.9712223, 12.9873284], [79.9712435, 12.9870904], [79.9709534, 12.9870652], [79.9709308, 12.9873007]]]}
        },
        {
            "name": "Mens Hostel 1", "code": "MH1",
            "desc": "Mens Residence Block 1.",
            "lat": 12.988558, "lng": 79.970229,
            "ent_lat": 12.988559, "ent_lng": 79.970349,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9703454, 12.988426], [79.9703494, 12.9885592], [79.970353, 12.9886809], [79.9701132, 12.9886885], [79.9701095, 12.9885604], [79.9701059, 12.9884324], [79.9703454, 12.988426]]]}
        },
        {
            "name": "Mens Hostel 2", "code": "MH2",
            "desc": "Mens Residence Block 2.",
            "lat": 12.988819, "lng": 79.970523,
            "ent_lat": 12.988699, "ent_lng": 79.970513,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9706574, 12.9889358], [79.9705181, 12.9889388], [79.9704024, 12.9889413], [79.9703968, 12.9887014], [79.9705129, 12.988699], [79.9706531, 12.9886962], [79.9706574, 12.9889358]]]}
        },
        {
            "name": "Mens Hostel 3", "code": "MH3",
            "desc": "Mens Residence Block 3.",
            "lat": 12.988832, "lng": 79.969924,
            "ent_lat": 12.988827, "ent_lng": 79.9699,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9697959, 12.9887133], [79.9699201, 12.9887117], [79.9700509, 12.9887101], [79.9700544, 12.98895], [79.9699255, 12.9889515], [79.9697981, 12.9889529], [79.9697959, 12.9887133]]]}
        },
        {
            "name": "Mens Hostel 4", "code": "MH4",
            "desc": "Mens Residence Block 4.",
            "lat": 12.989118, "lng": 79.97025,
            "ent_lat": 12.989115, "ent_lng": 79.97037,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9701328, 12.9892494], [79.97013, 12.9891172], [79.9701274, 12.9889944], [79.9703674, 12.988989], [79.9703699, 12.9891146], [79.9703724, 12.9892452], [79.9701328, 12.9892494]]]}
        },
        {
            "name": "Mens Hostel 5", "code": "MH5",
            "desc": "Mens Residence Block 5.",
            "lat": 12.989383, "lng": 79.970532,
            "ent_lat": 12.989261, "ent_lng": 79.970526,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9706823, 12.9895011], [79.970533, 12.9895039], [79.97039, 12.9895066], [79.9703844, 12.9892667], [79.9705263, 12.9892613], [79.970674, 12.9892556], [79.9706823, 12.9895011]]]}
        },
        {
            "name": "Mens Mess", "code": "MM",
            "desc": "Hostel Dining Mess for Resident Students.",
            "lat": 12.988474, "lng": 79.969808,
            "ent_lat": 12.988512, "ent_lng": 79.96991,
            "floors": 1, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9697598, 12.9885697], [79.9698621, 12.9885712], [79.96991, 12.9885121], [79.9699539, 12.9884578], [79.9699439, 12.9883582], [79.9696404, 12.9883657], [79.9696429, 12.9884777], [79.9697548, 12.9884777], [79.9697598, 12.9885697]]]}
        },
        {
            "name": "Ladies Hostel 1", "code": "LH1",
            "desc": "Ladies Residence Block 1.",
            "lat": 12.987498, "lng": 79.969348,
            "ent_lat": 12.987363, "ent_lng": 79.969528,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9692191, 12.9873794], [79.9694742, 12.9873761], [79.9694776, 12.9876161], [79.9692214, 12.987619], [79.9692191, 12.9873794]]]}
        },
        {
            "name": "Ladies Hostel 2", "code": "LH2",
            "desc": "Ladies Residence Block 2.",
            "lat": 12.986864, "lng": 79.969331,
            "ent_lat": 12.986854, "ent_lng": 79.969343,
            "floors": 3, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.9692021, 12.9867458], [79.9694571, 12.9867425], [79.9694606, 12.9869825], [79.9692044, 12.9869854], [79.9692021, 12.9867458]]]}
        },
        {
            "name": "Campus Medical Center / SVCE Clinic", "code": "CLINIC",
            "desc": "Campus Physician, First Aid, and Emergency Ambulatory Unit.",
            "lat": 12.988116, "lng": 79.970407,
            "ent_lat": 12.988116, "ent_lng": 79.970407,
            "floors": 1, "acc": True,
            "footprint": {"type": "Polygon", "coordinates": [[[79.97032, 12.98806], [79.97049, 12.98806], [79.97049, 12.98817], [79.97032, 12.98817], [79.97032, 12.98806]]]}
        }
    ]

    building_map = {}
    for b in buildings_data:
        b_obj = Building(
            campus_id=campus.id,
            name=b["name"],
            code=b["code"],
            description=b["desc"],
            latitude=b["lat"],
            longitude=b["lng"],
            entrance_latitude=b["ent_lat"],
            entrance_longitude=b["ent_lng"],
            footprint=b["footprint"],
            floors=b["floors"],
            accessible=b["acc"]
        )
        db.session.add(b_obj)
        db.session.flush()
        building_map[b["code"]] = b_obj

    # Load connected real SVCE OpenStreetMap road & walkway network
    net_path = os.path.join(os.path.dirname(__file__), "..", "data", "svce_network.json")
    with open(net_path, "r", encoding="utf-8") as f:
        net_data = json.load(f)

    osm_node_objs = {}
    for n_item in net_data["nodes"]:
        node = NavigationNode(
            campus_id=campus.id,
            building_id=None,
            node_type="JUNCTION",
            label="Campus Road",
            floor=0,
            latitude=n_item["lat"],
            longitude=n_item["lng"],
            is_active=True
        )
        db.session.add(node)
        osm_node_objs[n_item["id"]] = node
    db.session.flush()

    # Create real road edges
    for e in net_data["edges"]:
        u_node = osm_node_objs.get(e["u"])
        v_node = osm_node_objs.get(e["v"])
        if u_node and v_node:
            d = haversine_distance(u_node.latitude, u_node.longitude, v_node.latitude, v_node.longitude)
            edge = NavigationEdge(
                source_node_id=u_node.id,
                destination_node_id=v_node.id,
                distance=max(d, 2.5),
                accessible=True,
                stairs=False,
                path_type=e.get("ptype", "MAIN_AVENUE"),
                is_bidirectional=True
            )
            db.session.add(edge)

    # Connect each building entrance to the closest road network node
    bld_entrance_nodes = {}
    for b_code, b_obj in building_map.items():
        ent_lat = b_obj.entrance_latitude or b_obj.latitude
        ent_lng = b_obj.entrance_longitude or b_obj.longitude
        ent_node = NavigationNode(
            campus_id=campus.id,
            building_id=b_obj.id,
            node_type="ENTRANCE",
            label=f"{b_obj.name} Entrance",
            floor=0,
            latitude=ent_lat,
            longitude=ent_lng,
            is_active=True
        )
        db.session.add(ent_node)
        db.session.flush()
        bld_entrance_nodes[b_code] = ent_node

        closest_rn = min(
            osm_node_objs.values(),
            key=lambda rn: haversine_distance(ent_lat, ent_lng, rn.latitude, rn.longitude)
        )
        d = haversine_distance(ent_lat, ent_lng, closest_rn.latitude, closest_rn.longitude)
        db.session.add(NavigationEdge(
            source_node_id=ent_node.id,
            destination_node_id=closest_rn.id,
            distance=max(d, 3.0),
            accessible=True,
            stairs=False,
            path_type="PAVED_WALKWAY",
            is_bidirectional=True
        ))

    # CS Block Indoor Circulation
    cs_ent = bld_entrance_nodes["CSB"]
    cs_foyer = NavigationNode(campus_id=campus.id, building_id=building_map["CSB"].id, node_type="CORRIDOR", label="CSE Foyer", floor=0, latitude=12.98736, longitude=79.97296, is_active=True)
    cs_elev_g = NavigationNode(campus_id=campus.id, building_id=building_map["CSB"].id, node_type="ELEVATOR", label="CSE Elevator (G)", floor=0, latitude=12.98739, longitude=79.97298, is_active=True)
    cs_elev_1 = NavigationNode(campus_id=campus.id, building_id=building_map["CSB"].id, node_type="ELEVATOR", label="CSE Elevator (Floor 1)", floor=1, latitude=12.98739, longitude=79.97298, is_active=True)
    cs_lab1 = NavigationNode(campus_id=campus.id, building_id=building_map["CSB"].id, node_type="DOOR", label="Door CS-LAB-1", floor=1, latitude=12.98742, longitude=79.97302, is_active=True)
    cs_lab2 = NavigationNode(campus_id=campus.id, building_id=building_map["CSB"].id, node_type="DOOR", label="Door CS-LAB-2", floor=2, latitude=12.98742, longitude=79.97302, is_active=True)

    db.session.add_all([cs_foyer, cs_elev_g, cs_elev_1, cs_lab1, cs_lab2])
    db.session.flush()

    db.session.add_all([
        NavigationEdge(source_node_id=cs_ent.id, destination_node_id=cs_foyer.id, distance=6.0, accessible=True, stairs=False, path_type="CORRIDOR", is_bidirectional=True),
        NavigationEdge(source_node_id=cs_foyer.id, destination_node_id=cs_elev_g.id, distance=5.0, accessible=True, stairs=False, path_type="CORRIDOR", is_bidirectional=True),
        NavigationEdge(source_node_id=cs_elev_g.id, destination_node_id=cs_elev_1.id, distance=4.0, accessible=True, stairs=False, path_type="ELEVATOR", is_bidirectional=True),
        NavigationEdge(source_node_id=cs_elev_1.id, destination_node_id=cs_lab1.id, distance=8.0, accessible=True, stairs=False, path_type="CORRIDOR", is_bidirectional=True),
        NavigationEdge(source_node_id=cs_elev_1.id, destination_node_id=cs_lab2.id, distance=8.0, accessible=True, stairs=False, path_type="CORRIDOR", is_bidirectional=True),
    ])

    # Rooms at SVCE
    rooms_data = [
        {"bld": "CSB", "num": "CS-LAB-1", "name": "Artificial Intelligence & Deep Learning Lab", "floor": 1, "dept": "Computer Science", "node": cs_lab1},
        {"bld": "CSB", "num": "CS-LAB-2", "name": "Cloud Computing & Networks Lab", "floor": 2, "dept": "Computer Science", "node": cs_lab2},
        {"bld": "CSB", "num": "CS-201", "name": "CSE Smart Interactive Classroom", "floor": 1, "dept": "Computer Science", "node": cs_foyer},
        {"bld": "ECE", "num": "ECE-101", "name": "VLSI Design & Embedded Systems Lab", "floor": 1, "dept": "ECE", "node": bld_entrance_nodes.get("ECE")},
        {"bld": "MEC", "num": "ME-102", "name": "CAD / CAM Modeling Center", "floor": 0, "dept": "Mechanical", "node": bld_entrance_nodes.get("MEC")},
        {"bld": "ADM", "num": "ADM-01", "name": "Principal & Secretary Office", "floor": 0, "dept": "Administration", "node": bld_entrance_nodes.get("ADM")},
        {"bld": "LIB", "num": "LIB-REF", "name": "Digital Reference & E-Library", "floor": 0, "dept": "Library", "node": bld_entrance_nodes.get("LIB")},
    ]

    for r in rooms_data:
        b_obj = building_map[r["bld"]]
        door_node = r.get("node")
        room = Room(
            building_id=b_obj.id,
            room_number=r["num"],
            name=r["name"],
            floor=r["floor"],
            department=r["dept"],
            latitude=door_node.latitude if door_node else b_obj.latitude,
            longitude=door_node.longitude if door_node else b_obj.longitude,
            node_id=door_node.id if door_node else None,
            description=f"{r['name']} at SVCE {b_obj.name}."
        )
        db.session.add(room)


    # Facilities at SVCE
    facilities_data = [
        {"name": "SVCE Main Entrance Gate", "cat": "admin", "lat": 12.98550, "lng": 79.97180, "bld": None, "desc": "Security Gate on NH48 Chennai-Bengaluru Highway.", "hours": "24 Hours"},
        {"name": "Sri Venkateswara Temple", "cat": "admin", "lat": 12.987263, "lng": 79.971969, "bld": None, "desc": "Campus Sri Venkateswara Swamy Temple.", "hours": "06:00 - 18:00"},
        {"name": "SVCE Central Canteen & Cafeteria", "cat": "dining", "lat": 12.986477, "lng": 79.972295, "bld": "CAF", "desc": "Main Student Canteen, Coffee & Snacks Counter.", "hours": "08:00 - 19:30"},
        {"name": "Student Parking & Two-Wheeler Stand", "cat": "parking", "lat": 12.98580, "lng": 79.97240, "bld": None, "desc": "Designated parking area for students and visitors.", "hours": "07:00 - 20:00"},
        {"name": "Campus Medical Center / Dispensary", "cat": "medical", "lat": 12.988116, "lng": 79.970407, "bld": "CLINIC", "desc": "Campus Physician, first aid, and ambulance emergency response.", "hours": "08:00 - 18:00"},
        {"name": "Dr. A.P.J. Abdul Kalam Central Library", "cat": "library", "lat": 12.986805, "lng": 79.971314, "bld": "LIB", "desc": "Over 100,000 volumes, international journals, and quiet reading halls.", "hours": "08:00 - 20:00"},
        {"name": "Mens Hostel Complex & Mess", "cat": "admin", "lat": 12.98880, "lng": 79.97020, "bld": None, "desc": "Blocks 1-5 Mens Residence and Dining Hall.", "hours": "Residents"},
        {"name": "Ladies Hostel Complex & Mess", "cat": "admin", "lat": 12.98720, "lng": 79.96930, "bld": None, "desc": "Ladies Residence and Dining Hall.", "hours": "Residents"},
    ]

    for f in facilities_data:
        cat_obj = cat_map.get(f["cat"]) or cat_map["academic"]
        b_obj = building_map.get(f["bld"]) if f["bld"] else None
        facility = Facility(
            campus_id=campus.id,
            building_id=b_obj.id if b_obj else None,
            category_id=cat_obj.id,
            name=f["name"],
            description=f["desc"],
            latitude=f["lat"],
            longitude=f["lng"],
            accessible=True,
            opening_hours=f["hours"]
        )
        db.session.add(facility)

    db.session.commit()
    return campus


def register_commands(app):
    """Register CLI commands with Flask application."""

    @app.cli.command("seed-demo")
    @click.option("--reset", is_flag=True, help="Drop all existing tables before seeding.")
    def seed_demo_command(reset):
        """Seed database with Demo Engineering Campus and SVCE."""
        if reset:
            click.echo("Dropping and recreating all database tables...")
            db.drop_all()
        db.create_all()

        click.echo("Seeding Demo Engineering Campus...")
        c1 = create_demo_data()
        click.echo(f"Seeded: {c1.name}")

        click.echo("Seeding Sri Venkateswara College of Engineering (SVCE)...")
        c2 = create_svce_data()
        click.echo(f"Seeded: {c2.name} at Pennalur, Sriperumbudur ({c2.latitude}, {c2.longitude})")
        click.echo("Default Admin: admin / CampusAdmin2026!")

    @app.cli.command("seed-svce")
    def seed_svce_command():
        """Seed or update Sri Venkateswara College of Engineering (SVCE) campus."""
        db.create_all()
        campus = create_svce_data()
        click.echo(f"Successfully seeded: {campus.name} (Lat: {campus.latitude}, Lon: {campus.longitude})")

    @app.cli.command("init-db")
    def init_db_command():
        """Create database tables if they do not exist."""
        db.create_all()
        click.echo("Database initialized successfully.")