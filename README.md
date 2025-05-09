# AFL-Parity

![Python 3.10.12](https://img.shields.io/badge/Python-3.10.12-4B8BBE)
[![mypy 1.15.0](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) 
![Docker 4.38.0](https://img.shields.io/badge/Docker-4.38.0-0db7ed)
![docker-compose](https://img.shields.io/badge/dockercompose-2.32.4-0db7ed)

DFS search of AFL season to determine the when the first [hamiltonian cycle](https://en.wikipedia.org/wiki/Hamiltonian_path) occured each season (if at all).
Makes use of [Squiggle's](https://api.squiggle.com.au/#section_bots) wonderful API to get data, many thanks Squiggle for provide such a neat service.  

This is just a little fun project to apply DFS and play around with graph structures. What fun.

## Output

The output for each season is found in `output/<season>/`, with a `json` doc contained some details on the traversal, along with the details of the hamiltonian cycle (if found), and the game results of each that make up said hamiltonian cycle. A crude infographic is also generated for each also.  
There's also single combined `json` doc in the `output/` dir, but doesn't include all the game details because that would just be silly really.  

All the outputs are already provided in the repo.  

<div align="center">
<img alt="hamiltonian cycle for 1983" src="./output/1983/hamiltonian_cycle_infographic_1983.png" width="500" height="500">  
<br>
<em>Example Infographic for AFL Season 1983</em><br>
<em>Yeah it's proper crude</em>
</div>

## DFS

Depth-First-Search is a well suited as it has better memory space than Breadth-First-Search. We're literally looking for _full hamiltonian cycles only_ so we only need to keep the current path in memory at any one time, as it contains all the information we need in order to proceed correctly. Just makes sense.  As DFS is a linear algorithm, it isn't particularly assisted by parallism, especially for hamiltonian cycles, since each thread will all arrive at the exact same hamiltonian cycle(s) (but slightly offset due to different starting nodes, e.g. 1-2-3-4 is the same as 3-4-1-2 in this scenario).  

While time complexity for DFS is **O(V + E)** (**V**ectors plus **E**dges), the special requirement for a hamiltonian cycle makes it **O(n^n)** as its possible that every node must visit every other node. Space complexity remains **O(n)** as we only record a single path at a time, which is sweet.  

### Efficiencies

As we are searching only for the _first_ hamiltonian cycle per season, it allows some efficiencies when traversing. These have all been coded in to allow for (potentially...) quicker computation:

#### 1. All winners and losers  
Obvious one first: every team has either won or lost at least one match. No point traversing otherwise.


  
#### 2. Sequentially run, by round  
By checking results by round, there are less permutations to traverse and thus the first hamiltonian cycle will be quicker to reveal itself.  
Most beneficial when it happens to occur 'earlier' in the season, and the benefits on this sequential approach are reduced when it occurs later in the season.

  
  
#### 3. First outcome for a team  
By checking if that particular round include the first win or loss for a particular team, start the search with that winner. Any hamiltonian cycles found using that game cannot be bettered and can exit early.


  
#### 4. Start each round with the first game of the round  
Should a 'first outcome' not be apparent in that round, might as well start with the winner of first game of the round, if that permutation containing the first game of the round results in a hamiltonian cycle, then the result cannot be bettered and can exit early - else can just use all that teams than won the first matches of the round as a base parent (plural because there can be multiple simulatious 'first games of the round')


  
#### 5. Game occured after current hamiltonian cycle  
Again once a hamiltonian cycle has been found (which doesnt include the first game of the round, or a first event), before traversing next game check if it occured after the current last occuring game in the known hamiltonian cycle. If it occured after, there is no way the addition of that game improve on the result, so it can be skipped.  
While it is easy to count this as a single skipped step, by skipping these games it can prevent many hundreds or even thousands of pointless permutations.


  
#### 6. Multi-Threadding  
As DFS is a linear search algorithm, it requires a bit of a nudge to benefit from parallel processing. One such method is by undertaking the 'first step' of a DFS search (ie. a BFS search, a single parent and all their children) and starting a thread for each pair. While we have multiple possible early exit strategies, searching in parallel is always a good idea as it allows for potential early-exit outcomes to be found sooner, and by declaring a global `early_exit` Boolean flag, all threads can terminate should one be found on _any_ thread.  


  
#### 7. Backtrack-limiting  
Prevent backtracking from going 'too far', when beginning with a path > 1 length, want to ensure path backtracking doesnt go beyond this point, causing different threads to eventualy compute the exact same permuations.  


  
### Efficiency Notes

A good example of the benefits of these efficiencies were observed when traversing Season 2000. A hamiltonian cycle was above to be discovered in ~2 seconds. This particular efficiency was mainly due to efficiency #3, without which (i.e only using 1 and 2 from the above) it took _~610 million_ steps and nearly 2 hours to find the same hamiltonian cycle.

All these efficiencies combined have resulting in it only taken a combined _~4 minutes and 25 seconds_ to download the data, build the adjacency lists, traverse the graphs to find the first hamiltonian cycle of each season, and draw those awful infographics for all seasons from 1897 to 2024. My laptop isn't even that good really so this is all about massaging that algorithm until it's optimal for a particular use-case. Make the most of restrictions and conditions _they actually simplify_ things.

While all the above greatly improve performance and reduce computation time for traversing, they do not guarentee it and still rely on some favourable qualities in order to be taken advantage of. The key thing to remember here is understanding the data, the outcomes, and the algorithms themselves allow you to provide neat little hacks and shortcuts to reach goals and outcomes quicker. It is the combination of all the efficiencies that enable traversals to be done quickly, not just one individually or just throwing crazy parallel-epic-super-compute at it all.

## How to run

Easiest is with `vscode devcontainers`. Just need to open this repo in a devcontainer and all the environment hassle is taken care of. So very neat.  

Otherwise can use [uv](https://github.com/astral-sh/uv) for python versioning and environment management locally or however you like really. Just use `uv` its great.  

There are two pre-configured ways to run a traversal, both with shell scripts. One of them just runs it locally or within the devcontainer, another will build and run within a separate container (not a devcontainer) before shutting down the container after execution (more detail below).

### Local Execution

A helper script can be found in `scripts/run_local.sh`. By default it just runs for this current year, downloading the game results and running a traversal.

```
sh scripts/run_local.sh
```

Can provide argument after to indicate which season want to perform a hamilton cycle search on. So for season 2023 would use:
```
sh scripts/run_local.sh -s 2023
```

To run all seasons sequentially:
```
sh scripts/run_local.sh -s all
```

There is also a `-d` switch to provide debug logs, which contain every step of the search... yeah they get kinda big... probs best not to run this with the `-s all` switch.

### Dockerised Execution

Provides a few extra steps to the above - the `scripts/run_docker.sh` script will build a new image, spin up a container, and then run the script. If there is an output, it will also automatically push the results from `/output/<season>` to github (assumes all github credentials have been configured globally etc). It has been hard coded to only download / traverse the current year, main purpose of this script is for cronjob to just run at certain intervals a few times each weekend just to see if we've got a hamiltonian cycle or not. Had a crack at Squiggles Event Feed also but found it was a bit flakey to maintain a connection (plus dont need to compute this stuff within seconds of each game finishing.... but is possible if wanting)

### Logs

Logs are stored in the `.logs/` dir, with a single file per execution, named by DATE_TIME_LOGTYPE. There are 'main' logs which provide simple progress and outputs. If debug switch was provided, each individual thread gets it's own log output detailing _every step undertaken_ in the traversal. When `run_docker.sh` is run, this creates an additional 'run_docker' log so output can be inspected for non-code steps also.  
