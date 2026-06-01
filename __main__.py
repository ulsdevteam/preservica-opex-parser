
from . import model
import sys

print(len(sys.argv), sys.argv)
if len(sys.argv) == 2 and sys.argv[1] == "test":
    from . import test
    test()
