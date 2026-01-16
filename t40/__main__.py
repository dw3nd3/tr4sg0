import sys
from . import fetcher, parser, serializer
dest = sys.argv[1]

room = parser.parse(fetcher.fetch(dest))

print(serializer.serialize(room))