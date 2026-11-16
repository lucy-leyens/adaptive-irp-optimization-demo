from irp_demo.core.models import load_instance, load_route_structure
from irp_demo.core.objective import structurally_valid


def test_saved_start_is_structurally_valid():
    instance = load_instance("data/instances/small_6x3.json")
    structure = load_route_structure("data/initial_solutions/small_6x3.json")
    assert structurally_valid(instance, structure)
