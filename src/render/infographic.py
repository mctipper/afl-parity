from algo.data_structures import DFSTraversalOutput
from models import SeasonResults, Team, GameResult
import numpy as np
from typing import Any
from numpy.typing import NDArray
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox


class Infographic:
    """draws the ugly infographic of the parity for that season (if one exists)"""

    def __init__(
        self, season_results: SeasonResults, traversal_output: DFSTraversalOutput
    ):
        self.season_results = season_results
        self.traversal_output = traversal_output

    @property
    def _output_dir(self) -> Path:
        project_root: Path = Path(__file__).parents[2]  # yueck
        output_dir: Path = project_root / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    @property
    def _logo_dir(self) -> Path:
        logo_dir = self._output_dir / "logos"
        logo_dir.mkdir(parents=True, exist_ok=True)
        return logo_dir

    @property
    def _season_output_dir(self) -> Path:
        season_output_dir: Path = self._output_dir / str(self.season_results.season)
        season_output_dir.mkdir(parents=True, exist_ok=True)
        return season_output_dir

    def _generate_points(self) -> None:
        """generates an equidistant set of x and y points which will be placements for each team in the circle"""

        # generic parameters for the shape
        a: int = 10
        # b: int = 10 # (initially experimented with an ellipse, but stuck with a circle)

        # generate evenly spaced angles between 0 and 2pi
        theta: NDArray[np.floating[Any]] = np.linspace(
            0, 2 * np.pi, self.season_results.nteams + 1
        )
        x_flat: NDArray[np.float64] = a * np.cos(theta)
        y_flat: NDArray[np.float64] = a * np.sin(theta)

        # good grief numpy and mypy are not happy pappys
        self.x: list[float] = x_flat.tolist()  # type: ignore
        self.y: list[float] = y_flat.tolist()  # type: ignore

    def create_infographic(self) -> None:
        """using matplotlib to build an annotated circle, with team logos as points"""

        if self.traversal_output.first_hamiltonian_cycle:
            _, ax = plt.subplots(figsize=(20, 20))
            ax.set_axis_off()  # this aint no graph
            ax.set_facecolor("#FFFDD0")  # Prince would be so happy

            season = self.season_results.season
            rnd = self.traversal_output.first_hamiltonian_cycle.max_round
            dt = self.traversal_output.first_hamiltonian_cycle.max_date

            # info to put in the centre of the circle
            ax.annotate(
                f"Season {season}\nRound {rnd}\n{dt:%a. %d/%m/%Y}",
                xy=(0, 0),
                size=40,
                ha="center",
                va="center",
            )

            # plot the teams as points on the circle
            self._generate_points()
            ax.scatter(self.x, self.y)

            # NOTE
            # matplotlib renders based on generated order, hence images first then annotations
            # purposefully done in two independent loops

            # images
            hamiltonian_cycle = self.traversal_output.first_hamiltonian_cycle.cycle
            cur_loser: int
            for i, cur_winner in enumerate(hamiltonian_cycle):
                try:
                    cur_loser = hamiltonian_cycle[i + 1]
                except IndexError:
                    # if reached end of list, return first in list
                    cur_loser = hamiltonian_cycle[0]

                cur_team: Team = self.season_results.get_team(cur_winner)  # type: ignore[assignment]
                logo_filepath: Path = self._logo_dir / cur_team.logo_filename
                img: NDArray[np.float64] = plt.imread(logo_filepath, format="png")
                imagebox: OffsetImage = OffsetImage(img, zoom=0.8)
                imagebox.image.axes = ax

                # 'annotate' the logo on the image
                ab: AnnotationBbox = AnnotationBbox(
                    imagebox, (self.x[i], self.y[i]), bboxprops={"edgecolor": "none"}
                )
                ax.add_artist(ab)

            # annotations
            hamiltonian_cycle = self.traversal_output.first_hamiltonian_cycle.cycle
            for i, cur_winner in enumerate(hamiltonian_cycle):
                try:
                    cur_loser = hamiltonian_cycle[i + 1]
                except IndexError:
                    # if reached end of list, return first in list
                    cur_loser = hamiltonian_cycle[0]

                cur_game_deets: GameResult = self.season_results.get_first_game_result(  # type: ignore[assignment]
                    cur_winner, cur_loser
                )
                cur_round: int = cur_game_deets.round
                cur_winner_score: int = cur_game_deets.wscore  # type: ignore[assignment]
                cur_loser_score: int = cur_game_deets.lscore  # type: ignore[assignment]

                # the cur_x and next_x indicate the to-from for each arrow
                cur_x: float = self.x[i]
                cur_y: float = self.y[i]
                next_x: float
                next_y: float
                try:
                    next_x = self.x[i + 1]
                    next_y = self.y[i + 1]
                except IndexError:
                    # reached end of circle, so we want the last arrow to point to starting point
                    next_x = self.x[0]
                    next_y = self.y[0]
                # the 0.85 is to move the annotations slightly in, so they appear 'next' to the arrows
                mid_x: float = ((cur_x + next_x) / 2) * 0.85
                mid_y: float = ((cur_y + next_y) / 2) * 0.85

                # draw the arrow
                ax.annotate(
                    "",
                    xy=(next_x, next_y),
                    xytext=(cur_x, cur_y),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        lw=10,
                        shrinkA=60,
                        shrinkB=60,
                        mutation_scale=40,
                    ),
                )

                # draw the game result details
                ax.annotate(
                    f"Rnd. {cur_round}\n{cur_winner_score}-{cur_loser_score}",
                    xy=(mid_x, mid_y),
                    size=20,
                    ha="center",
                    va="center",
                )

            # neaten the presentation
            ax.set_aspect("equal")

            # output resulting infograph to file
            plt.savefig(
                self._season_output_dir
                / Path(
                    f"hamiltonian_cycle_infographic_{self.season_results.season}.png"
                )
            )
        else:
            # explicit "do nothing" when there is no hamiltonian cycle to draw
            pass
