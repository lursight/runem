import typing

import networkx as nx

from runem.dependency_execution import Dependencies


class InvalidDependencies(RuntimeError):
    """Thrown when the dependencies can't be processed."""


def sort_dependencies(dependencies: Dependencies) -> typing.List[str]:
    """Sort tasks based on their dependencies using networkx for topological sorting.

    Parameters:
    - dependencies: A dictionary where keys are task names, and values are lists
                    of task dependencies.

    Returns:
    - List[str]: A list of task names sorted in the order they should be
                 executed based on dependencies.
    """

    # Create a directed graph using networkx
    graph = nx.DiGraph(dependencies)

    try:
        # Perform topological sort using networkx
        sorted_tasks = list(nx.topological_sort(graph))
    except nx.NetworkXUnfeasible as err:
        # Handle the case where the graph has cycles and cannot be topologically sorted
        raise InvalidDependencies(
            "Error: The graph has cycles and cannot be topologically sorted."
        ) from err

    return sorted_tasks


if __name__ == "__main__":
    task_dependencies = {
        "TaskA": [],
        "TaskB": ["TaskA"],
        "TaskC": ["TaskA"],
        "TaskD": ["TaskB", "TaskC"],
    }

    sorted_tasks = sort_dependencies(task_dependencies)
    print("Sorted Tasks:", sorted_tasks)
