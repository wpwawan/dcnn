import matplotlib.pyplot as plt
import numpy as np
import struct
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('fp', metavar='FILE', nargs='+', help='Path to binary file containing data')
parser.add_argument(
    '-v',
    '--val-only',
    dest='val_only',
    action='store_true',
    default=False,
    help='Show only the validation loss/accuracy')
args = parser.parse_args()

files = args.fp
val_only = args.val_only
data = {}
for f in files:
    d = open(f, 'rb').read()
    d = struct.unpack('f' * (len(d) // 4), d)
    d = np.array(d).reshape(-1, 4)
    data[f.split('/')[-1]] = d

try:
    import seaborn as sns
    sns.set()
    sns.set_style('darkgrid', {'axes.facecolor': '.88'})
except ImportError:
    pass

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
for k, d in data.items():
    d[:, [1, 3]] *= 100

    if not val_only:
        ax1.plot(d[:, 0], label=k + '-train')
        ax2.plot(d[:, 1], label=k + '-train')

    ax1.plot(d[:, 2], label=k + '-val')
    ax2.plot(d[:, 3], label=k + '-val')
#   ax2.hlines(
#       (d[:,1].max(), d[:,3].max()),
#       0, len(d)-1,
#       linestyle='dotted')
ax1.legend()
ax1.set_ylabel('Loss (cross entropy)')
ax2.legend(loc='lower right')
ax2.set_xlabel('Iterations')
ax2.set_ylabel('Accuracy')

plt.show()
