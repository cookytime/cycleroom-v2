import cProfile
import pstats
import io
from main import start_server


def profile_server():
    pr = cProfile.Profile()
    pr.enable()
    start_server()
    pr.disable()

    s = io.StringIO()
    sortby = "cumulative"
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


if __name__ == "__main__":
    profile_server()
