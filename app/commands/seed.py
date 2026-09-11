"""
Campus Navigation System — Seed Tooling
Seeds realistic campus spatial dataset with verified buildings, rooms, facilities,
and a fully connected pedestrian graph with stairs and accessible paths.
"""
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
        Building.query.filter_by(campus_id=campus.id).delete()
        Facility.query.filter_by(campus_id=campus.id).delete()
        NavigationNode.query.filter_by(campus_id=campus.id).delete()
        db.session.commit()

    def make_box(lat, lng, dlat=0.00025, dlng=0.00035):
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
        {"name": "Computer Science Block", "code": "CSB", "desc": "Department of Computer Science & Engineering, IT, AI & Data Science.", "lat": 12.98742, "lng": 79.97304, "ent_lat": 12.98742, "ent_lng": 79.97290, "floors": 3, "acc": True},
        {"name": "Administration Block", "code": "ADM", "desc": "Principal Office, Dean Academics, Examination Cell, and Admissions.", "lat": 12.98698, "lng": 79.97204, "ent_lat": 12.98705, "ent_lng": 79.97204, "floors": 2, "acc": True},
        {"name": "Electronics & Communication Block", "code": "ECE", "desc": "Department of ECE, Embedded Systems, Signal Processing, and VLSI Design.", "lat": 12.98743, "lng": 79.97237, "ent_lat": 12.98743, "ent_lng": 79.97225, "floors": 3, "acc": True},
        {"name": "Mechanical Engineering Block", "code": "MEC", "desc": "Department of Mechanical Engineering, Thermal Engineering, and Dynamics Labs.", "lat": 12.98779, "lng": 79.97274, "ent_lat": 12.98770, "ent_lng": 79.97274, "floors": 3, "acc": True},
        {"name": "Chemical Engineering Block", "code": "CHE", "desc": "Department of Chemical Engineering, Mass Transfer, and Process Labs.", "lat": 12.98781, "lng": 79.97220, "ent_lat": 12.98770, "ent_lng": 79.97220, "floors": 2, "acc": True},
        {"name": "Applied Science & Humanities", "code": "ASH", "desc": "Physics, Chemistry, Mathematics Departments, and First Year Lecture Halls.", "lat": 12.98712, "lng": 79.97268, "ent_lat": 12.98712, "ent_lng": 79.97255, "floors": 3, "acc": True},
        {"name": "Central Library", "code": "LIB", "desc": "Dr. A.P.J. Abdul Kalam Central Library with digital archives and reference stacks.", "lat": 12.98705, "lng": 79.97240, "ent_lat": 12.98705, "ent_lng": 79.97235, "floors": 2, "acc": True},
        {"name": "Research & Development Center", "code": "RND", "desc": "Innovation Hub, Patent Cell, and Interdisciplinary Research Laboratories.", "lat": 12.98886, "lng": 79.97112, "ent_lat": 12.98875, "ent_lng": 79.97112, "floors": 2, "acc": True},
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
            footprint=make_box(b["lat"], b["lng"]),
            floors=b["floors"],
            accessible=b["acc"]
        )
        db.session.add(b_obj)
        db.session.flush()
        building_map[b["code"]] = b_obj

    # Navigation Nodes on SVCE Walkway Graph
    nodes_data = [
        {"key": "SVCE_GATE", "lat": 12.98550, "lng": 79.97180, "type": "ENTRANCE", "label": "SVCE Main Gate (NH48)", "floor": 0},
        {"key": "SVCE_AVENUE_1", "lat": 12.98620, "lng": 79.97190, "type": "JUNCTION", "label": "Main Entrance Avenue", "floor": 0},
        {"key": "SVCE_TEMPLE_JUNC", "lat": 12.98700, "lng": 79.97195, "type": "JUNCTION", "label": "SVCE Temple Circle", "floor": 0},
        {"key": "SVCE_CENTRAL_QUAD", "lat": 12.98730, "lng": 79.97250, "type": "JUNCTION", "label": "Academic Quadrangle Fountain", "floor": 0},
        {"key": "SVCE_NORTH_PATH", "lat": 12.98770, "lng": 79.97250, "type": "JUNCTION", "label": "Mechanical & Chemical Junction", "floor": 0},
        {"key": "SVCE_WEST_HOSTEL_JUNC", "lat": 12.98750, "lng": 79.97080, "type": "JUNCTION", "label": "Hostel Road Junction", "floor": 0},
        
        # Entrances
        {"key": "ENT_ADM", "lat": 12.98705, "lng": 79.97204, "type": "ENTRANCE", "label": "Admin Block Entrance", "bld": "ADM", "floor": 0},
        {"key": "ENT_LIB", "lat": 12.98705, "lng": 79.97235, "type": "ENTRANCE", "label": "Central Library Entrance", "bld": "LIB", "floor": 0},
        {"key": "ENT_CSB", "lat": 12.98742, "lng": 79.97290, "type": "ENTRANCE", "label": "Computer Science Block Entrance", "bld": "CSB", "floor": 0},
        {"key": "ENT_ECE", "lat": 12.98743, "lng": 79.97225, "type": "ENTRANCE", "label": "ECE Block Entrance", "bld": "ECE", "floor": 0},
        {"key": "ENT_MEC", "lat": 12.98770, "lng": 79.97274, "type": "ENTRANCE", "label": "Mechanical Block Entrance", "bld": "MEC", "floor": 0},
        {"key": "ENT_CHE", "lat": 12.98770, "lng": 79.97220, "type": "ENTRANCE", "label": "Chemical Block Entrance", "bld": "CHE", "floor": 0},
        {"key": "ENT_ASH", "lat": 12.98712, "lng": 79.97255, "type": "ENTRANCE", "label": "Applied Science Entrance", "bld": "ASH", "floor": 0},

        # CS Block Inside
        {"key": "CS_FOYER", "lat": 12.98742, "lng": 79.97300, "type": "CORRIDOR", "label": "CSE Foyer", "bld": "CSB", "floor": 0},
        {"key": "CS_LAB1_DOOR", "lat": 12.98744, "lng": 79.97305, "type": "DOOR", "label": "Door CS-LAB-1 (AI Lab)", "bld": "CSB", "floor": 1},
        {"key": "CS_LAB2_DOOR", "lat": 12.98740, "lng": 79.97305, "type": "DOOR", "label": "Door CS-LAB-2 (Cloud Lab)", "bld": "CSB", "floor": 2},
    ]

    node_map = {}
    for nd in nodes_data:
        b_id = building_map[nd["bld"]].id if "bld" in nd else None
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
        node_map[nd["key"]] = node

    # Walkway Edges
    edges_spec = [
        ("SVCE_GATE", "SVCE_AVENUE_1", True, False, "PAVED_WALKWAY"),
        ("SVCE_AVENUE_1", "SVCE_TEMPLE_JUNC", True, False, "PAVED_WALKWAY"),
        ("SVCE_TEMPLE_JUNC", "ENT_ADM", True, False, "PAVED_WALKWAY"),
        ("SVCE_TEMPLE_JUNC", "SVCE_CENTRAL_QUAD", True, False, "PAVED_WALKWAY"),
        ("SVCE_TEMPLE_JUNC", "SVCE_WEST_HOSTEL_JUNC", True, False, "PAVED_WALKWAY"),
        ("SVCE_CENTRAL_QUAD", "ENT_LIB", True, False, "PAVED_WALKWAY"),
        ("SVCE_CENTRAL_QUAD", "ENT_ASH", True, False, "PAVED_WALKWAY"),
        ("SVCE_CENTRAL_QUAD", "ENT_ECE", True, False, "PAVED_WALKWAY"),
        ("SVCE_CENTRAL_QUAD", "ENT_CSB", True, False, "PAVED_WALKWAY"),
        ("SVCE_CENTRAL_QUAD", "SVCE_NORTH_PATH", True, False, "PAVED_WALKWAY"),
        ("SVCE_NORTH_PATH", "ENT_MEC", True, False, "PAVED_WALKWAY"),
        ("SVCE_NORTH_PATH", "ENT_CHE", True, False, "PAVED_WALKWAY"),
        ("ENT_CSB", "CS_FOYER", True, False, "CORRIDOR"),
        ("CS_FOYER", "CS_LAB1_DOOR", True, False, "CORRIDOR"),
        ("CS_LAB1_DOOR", "CS_LAB2_DOOR", True, False, "CORRIDOR"),
    ]

    for src_k, dst_k, is_acc, has_stairs, ptype in edges_spec:
        src_node = node_map[src_k]
        dst_node = node_map[dst_k]
        dist = haversine_distance(src_node.latitude, src_node.longitude, dst_node.latitude, dst_node.longitude)
        edge = NavigationEdge(
            source_node_id=src_node.id,
            destination_node_id=dst_node.id,
            distance=max(dist, 3.0),
            accessible=is_acc,
            stairs=has_stairs,
            path_type=ptype,
            is_bidirectional=True
        )
        db.session.add(edge)

    # Rooms at SVCE
    rooms_data = [
        {"bld": "CSB", "num": "CS-LAB-1", "name": "Artificial Intelligence & Deep Learning Lab", "floor": 1, "dept": "Computer Science", "node": "CS_LAB1_DOOR"},
        {"bld": "CSB", "num": "CS-LAB-2", "name": "Cloud Computing & Networks Lab", "floor": 2, "dept": "Computer Science", "node": "CS_LAB2_DOOR"},
        {"bld": "CSB", "num": "CS-201", "name": "CSE Smart Interactive Classroom", "floor": 1, "dept": "Computer Science", "node": "CS_FOYER"},
        {"bld": "ECE", "num": "ECE-101", "name": "VLSI Design & Embedded Systems Lab", "floor": 1, "dept": "ECE", "node": "ENT_ECE"},
        {"bld": "MEC", "num": "ME-102", "name": "CAD / CAM Modeling Center", "floor": 0, "dept": "Mechanical", "node": "ENT_MEC"},
        {"bld": "ADM", "num": "ADM-01", "name": "Principal & Secretary Office", "floor": 0, "dept": "Administration", "node": "ENT_ADM"},
        {"bld": "LIB", "num": "LIB-REF", "name": "Digital Reference & E-Library", "floor": 0, "dept": "Library", "node": "ENT_LIB"},
    ]

    for r in rooms_data:
        b_obj = building_map[r["bld"]]
        door_node = node_map.get(r.get("node"))
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
        {"name": "Sri Venkateswara Temple", "cat": "admin", "lat": 12.98726, "lng": 79.97197, "bld": None, "desc": "Campus Sri Venkateswara Swamy Temple.", "hours": "06:00 - 18:00"},
        {"name": "SVCE Central Canteen & Cafeteria", "cat": "dining", "lat": 12.98648, "lng": 79.97230, "bld": None, "desc": "Main Student Canteen, Coffee & Snacks Counter.", "hours": "08:00 - 19:30"},
        {"name": "Student Parking & Two-Wheeler Stand", "cat": "parking", "lat": 12.98580, "lng": 79.97240, "bld": None, "desc": "Designated parking area for students and visitors.", "hours": "07:00 - 20:00"},
        {"name": "Campus Medical Center / Dispensary", "cat": "medical", "lat": 12.98670, "lng": 79.97120, "bld": None, "desc": "Campus Physician, first aid, and ambulance emergency response.", "hours": "08:00 - 18:00"},
        {"name": "Dr. A.P.J. Abdul Kalam Central Library", "cat": "library", "lat": 12.98705, "lng": 79.97240, "bld": "LIB", "desc": "Over 100,000 volumes, international journals, and quiet reading halls.", "hours": "08:00 - 20:00"},
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
