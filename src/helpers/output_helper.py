import os
import json
from pathlib import Path
from typing import Dict, Any


class OutputHelper:
    @staticmethod
    def combine_all_json_outputs() -> None:
        project_root: Path = Path(__file__).parents[2]
        output_dir: Path = project_root / "output"

        # output data
        combined_data: Dict[str, Any] = {}

        # walk through the dirs and get all the jsons
        for root, dirs, _ in os.walk(output_dir):
            # sorted(dirs) to make the combined response neat and sequential _nice_
            for dir_name in sorted(dirs):
                season = dir_name
                json_file_path = os.path.join(
                    root, dir_name, f"{season}_dfs_traversal_output.json"
                )

                if os.path.exists(json_file_path):
                    with open(json_file_path, "r") as f:
                        data = json.load(f)

                    # remove the games from the combined file, if want that details just look in the individual outputs
                    if data["first_hamiltonian_cycle"]:
                        if "games" in data["first_hamiltonian_cycle"]:
                            del data["first_hamiltonian_cycle"]["games"]

                    combined_data[season] = data

        combined_output_path = output_dir / "combined_outputs.json"
        with open(combined_output_path, "w") as f:
            json.dump(combined_data, f, indent=4)
