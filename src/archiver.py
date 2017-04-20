#!/env/python

import logging
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from datetime import date
from os import walk, scandir
from os.path import join
from threading import Thread
from zipfile import ZipFile, ZIP_LZMA

DEFAULT_DIR = "./"


class Archiver:
    def __init__(self, path=DEFAULT_DIR):
        self._step_archivers = [StepArchiver(path, 'archiver_root')]
        for dirname, dirnames, filenames in walk(path):
            for elem in dirnames:
                self._step_archivers.append(StepArchiver(join(dirname, elem), "archiver_" + elem))

    def execute(self):
        for archiver in self._step_archivers:
            archiver.start()

    def __repr__(self):
        names = []
        for step in self._step_archivers:
            names.append(str(step))

        return "Archiver manager on [" + ', '.join(names) + "]"


class StepArchiver(Thread):
    def __init__(self, path, name="Archiver"):
        super(StepArchiver, self).__init__(name=name)
        self.path = path
        today = date.today()
        self.archiveName = "archive_" + str(today.year) + "_" + str(today.month) + "_" + str(today.day) + ".7z"

    def run(self):
        logging.debug("Archiving directory %s...", self.path)

        fentries = []
        with scandir(self.path) as elements:
            for entry in elements:
                if entry.is_file() and entry.name.endswith((".txt", ".log")):
                    fentries.append(entry)
        logging.debug("%s : detected files to archive %s", self.getName(), fentries)

        if len(fentries) == 0:
            return

        with ZipFile(join(self.path, self.archiveName), 'a', compression=ZIP_LZMA) as archive:
            for entry in fentries:
                try:
                    archive.write(filename=join(self.path, entry.name), arcname=entry.name)
                except (ValueError, RuntimeError):
                    logging.error("Error during archiving file %s in %s", entry.name, self.path)

    def __repr__(self):
        return "StepArchiver " + self.getName() + " on " + self.path


if __name__ == "__main__":
    parser = ArgumentParser(prog='archiver', description='Archive some directory tree',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', '--root', action='store', nargs=1, dest='root', metavar='root', default=DEFAULT_DIR,
                        help='Root of the directory tree that must be archive')
    parser.add_argument('--log', action='store', nargs=1, dest='log_level', metavar='level',
                        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'), help='Logging level',
                        default=logging.getLevelName(logging.INFO))
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level[0])

    print("Archiving directory tree...")

    manager = Archiver(args.root[0])
    manager.execute()

    print("Archives are created")
