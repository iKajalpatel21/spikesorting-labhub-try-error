"""
Step Dependencies and Parameters Configuration
Based on the original qmodel project specification
"""

# Defines the dependency structure for each step function
# Each step maps to a list of required dependency slots
# Each slot can be satisfied by one of multiple acceptable function types
STEP_DEPENDENCIES = {
    "combined_recording": [],
    "recording": [],
    "load_recording": [],
    # Preprocessing needs only a recording
    "preprocessing": [("recording", "combined_recording")],
    # Loading a previously done preprocessing doesn't need anything
    "load_preprocessing": [],
    # Sorting needs one of: recording, combined_recording, preprocessing, load_preprocessing
    "sorting": [
        ("recording", "combined_recording", "preprocessing", "load_preprocessing")
    ],
    # Load a previously done sorting
    "load_sorting": [],
    # Analyzer: first arg is preprocessing/recording, second is sorting
    "analyzer": [
        ("recording", "combined_recording", "preprocessing", "load_preprocessing"),
        ("sorting", "load_sorting", "import_from_phy"),
    ],
    # Load a previously done analyzer
    "load_analyzer": [],
    # Phy export: first arg is preprocessing/recording, second is sorting
    "phy_export": [
        ("recording", "combined_recording", "preprocessing", "load_preprocessing"),
        ("sorting", "load_sorting"),
    ],
    # Importing from phy
    "import_from_phy": [],
    # Report requires analyzer
    "report": [("analyzer", "load_analyzer")],
    # Export to MatLab requires recording, sorting, analyzer, phy_export
    "export2matlab": [
        ("recording", "combined_recording"),
        ("sorting", "load_sorting", "import_from_phy"),
        ("analyzer", "load_analyzer"),
        ("phy_export", "import_from_phy"),
    ],
    # Upload everything
    "upload": [],
}

# Defines the parameter schema for each step function
# (Used for validation - not needed for job creation)
STEP_PARAMETERS = {
    "recording": {
        "*binfile": str,
        "*probe": str,
        "*sampling rate": (int, float),
        "*number of channels": int,
        ">remove": [int],
        ">bad_channels": [int],
        ">location": str,
        ">gain_to_uV": (int, float),
        ">offset_to_uV": (int, float),
        ">save": (bool, str),
    },
    "load_recording": {
        ">file": str,
    },
    "preprocessing": {
        "*methods": [
            (
                "centering",
                "highpass or band filtering",
                "referensing",
                "whitening",
                "zscore",
            )
        ],
        ">centering": {">mode": ("median", "mean")},
        ">highpass or band filtering": {
            "*btype": str,
            "*band": (list, float),
        },
        ">referensing": {
            ">reference": ("global", "single", "local"),
            ">operator": ("median", "average"),
            ">groups": (list, type(None)),
            ">local_radius": [int, int],
            ">ref_channel_ids": [int],
        },
        ">whitening": {
            ">mode": ("global", "local"),
            ">radius_um": (float, type(None)),
            ">apply_mean": bool,
            ">int_scale": (float, type(None)),
            ">eps": (float, type(None)),
        },
        ">zscore": {">mode": ("median+mad", "mean+std")},
        ">folder": str,
    },
    "load_preprocessing": {"*folder": str},
    "sorting": {
        "*name": str,
        "*parameters": dict,
        ">folder": str,
        ">image": str,
    },
    "load_sorting": {"*folder": str},
    "analyzer": {
        "*metrics": dict,
        ">folder": str,
    },
    "load_analyzer": {"*folder": str},
    "phy_export": {
        ">folder": str,
        ">do_not_update_config": bool,
    },
    "import_from_phy": {
        "*phy_folder": str,
        ">folder": str,
    },
    "report": {
        ">folder": str,
    },
    "export2matlab": {
        ">filename": str,
        ">marks": [str],
    },
    "upload": {
        "*destination": str,
        ">keep_base_directory": bool,
        ">suffix": (str, bool),
    },
}


def get_step_dependencies(function_name: str) -> list:
    """
    Get the list of dependencies for a given step function.

    Args:
        function_name: Name of the step function (e.g., 'preprocessing', 'sorting')

    Returns:
        List of dependency slots, each slot can be satisfied by one of multiple functions

    Example:
        get_step_dependencies('analyzer')
        → [
            ('recording', 'combined_recording', 'preprocessing', 'load_preprocessing'),
            ('sorting', 'load_sorting', 'import_from_phy')
          ]
    """
    return STEP_DEPENDENCIES.get(function_name, [])


def validate_dependencies(
    function_name: str, depends_on: list, available_functions: dict
) -> tuple:
    """
    Validate that the provided dependencies satisfy the requirements for a function.

    Args:
        function_name: Name of the step function
        depends_on: List of function names this step depends on
        available_functions: Dict mapping function names to their identifiers (hashes)

    Returns:
        (is_valid: bool, error_message: str or None)
    """
    required_deps = get_step_dependencies(function_name)

    # If no dependencies required, return True
    if not required_deps:
        if depends_on:
            return False, f"{function_name} should not have dependencies"
        return True, None

    # Check correct number of dependency slots
    if len(depends_on) != len(required_deps):
        return (
            False,
            f"{function_name} requires {len(required_deps)} dependencies, got {len(depends_on)}",
        )

    # Check each dependency satisfies its slot
    for slot_idx, (dep_func, required_funcs) in enumerate(
        zip(depends_on, required_deps)
    ):
        if dep_func not in available_functions:
            return False, f"Dependency {dep_func} not found in available functions"

        # Check if the dependency function type matches one of the acceptable types for this slot
        dep_func_type = available_functions[dep_func]["function"]
        if isinstance(required_funcs, tuple):
            if dep_func_type not in required_funcs:
                return (
                    False,
                    f"Slot {slot_idx + 1} of {function_name} requires one of {required_funcs}, got {dep_func_type}",
                )
        else:
            if dep_func_type != required_funcs:
                return (
                    False,
                    f"Slot {slot_idx + 1} of {function_name} requires {required_funcs}, got {dep_func_type}",
                )

    return True, None
