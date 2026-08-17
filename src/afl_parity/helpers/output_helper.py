import json
from typing import Dict, Any

from afl_parity.paths import OUTPUT_DIR


class OutputHelper:
    @staticmethod
    def combine_all_json_outputs() -> None:
        output_dir = OUTPUT_DIR

        # output data
        combined_data: Dict[str, Any] = {}

        # sorted(...) to make the combined response neat and sequential _nice_
        for season_dir in sorted(p for p in output_dir.iterdir() if p.is_dir()):
            season = season_dir.name
            json_file_path = season_dir / f"{season}_dfs_traversal_output.json"

            if json_file_path.exists():
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
