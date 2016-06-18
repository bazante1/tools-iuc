#!/usr/bin/env python
import logging
import sys
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()
from BCBio import GFF
import wiggle

MODE = sys.argv[1]
assert MODE in ('heatmap', 'histogram')

# Pair up (file, extension) pairs from sys.argv
files = zip(sys.argv[2:][0::2], sys.argv[2:][1::2])

# Our output data structure. This could be much more efficient.
data = {}

# Handlers
def gff3(idx, path):
    for record in GFF.parse(path):
        if len(record.features) == 0:
            continue

        if record.id not in data:
            data[record.id] = {}

        for feature in record.features:
            if 'score' in feature.qualifiers:
                for i in xrange(feature.location.start, feature.location.end):
                    if i not in data[record.id]:
                        data[record.id][i] = {}

                    data[record.id][i][idx] = feature.qualifiers['score'][0]

def wig(idx, path):
    walker = wiggle.Wiggle()
    with open(path, 'r') as handle:
        for region, position, value in walker.walk(handle):
            if region not in data:
                data[region] = {}

            if position not in data[region]:
                data[region][position] = {}

            data[region][position][idx] = value

for idx, (file_path, file_type) in enumerate(files):
    log.info("Processing %s.%s", file_path, file_type)
    if file_type in globals():
        func = globals()[file_type]
        func(idx, file_path)

# Max number of files
max_idx = range(len(files))

serialized_values = None
region_start, region_end = (None, None)

for genome in data:
    for position in sorted(data[genome]):
        values = [
            '' if x not in data[genome][position] else data[genome][position][x]
            for x in max_idx
        ]
        if serialized_values is None:
            serialized_values = values
        if region_start is None:
            region_start = position
            region_end = position

        if values == serialized_values:
            region_end = position
        else:
            if MODE == 'histogram':
                print genome, region_start, region_end + 1, ','.join(values)
            elif MODE == 'heatmap':
                for x in max_idx:
                    if x in data[genome][position]:
                        print genome, region_start, region_end + 1, data[genome][position][x], 'id=hm%s' % x
                    else:
                        print genome, region_start, region_end + 1, 0.0, 'id=hm%s' % x
            # Update start of next array
            region_start = position
            region_end = position
            # And update with new array
            serialized_values = values

# histogram
# hs4 0 1999999 5.0000,3.0000,1.0000,19.0000

# heatmap
# hs1 2000000 3999999 0.0000 id=hs4
# hs1 4000000 5999999 2.0000 id=hs1
# hs1 4000000 5999999 0.0000 id=hs2
# hs1 4000000 5999999 0.0000 id=hs3
# hs1 4000000 5999999 0.0000 id=hs4
# hs1 6000000 7999999 4.0000 id=hs2

